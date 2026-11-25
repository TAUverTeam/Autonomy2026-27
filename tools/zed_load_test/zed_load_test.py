#!/usr/bin/env python3
"""Measure how much of the Jetson the ZED cameras use, with 1, 2 or 3 cameras at once.

Part of ``tools/zed_load_test`` (see the README next to this file). It answers REQ-AUT-ISS-06:
what the main computer can run at the same time, established by measurement.

What it does, for one configuration (resolution, frame rate, depth mode, number of cameras):

1. Opens the requested cameras by serial number, one after another.
2. Starts one thread per camera. Each thread grabs frames as fast as the camera delivers them
   and, if asked, copies the depth map or point cloud to CPU memory, as a ROS driver would
   before publishing it.
3. After a warm-up, measures for a fixed time: frames received per camera, frames the SDK
   reports as dropped, and the Jetson's CPU, GPU, memory, power and temperature (read from
   ``tegrastats`` once per second).
4. Prints a summary and appends it as one JSON line to the results file.

This measures the ZED SDK alone, without ROS and without object detection. It is therefore a
lower bound: a full system adds ROS message passing, the planner and detection on top.

Usage:
    python3 zed_load_test.py run --serials 31718458 32514439 33289078 \
        --resolution HD720 --fps 15 --depth-mode PERFORMANCE --retrieve pointcloud
    python3 zed_load_test.py summarize results.jsonl

Requires: ZED SDK with its Python API (``pyzed``), and ``tegrastats`` (part of JetPack).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime

# What can be copied to CPU memory after each grab, and the ZED call that does it.
# "none" leaves the data on the GPU (cheapest); "pointcloud" is what a ROS driver must do
# to publish a sensor_msgs/PointCloud2, so it is the realistic worst case.
RETRIEVE_CHOICES = ("none", "image", "depth", "pointcloud")


# --------------------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------------------


@dataclass
class CameraResult:
    """Measurements for one camera during the measuring window.

    Attributes:
        serial: Camera serial number.
        opened: True if the camera opened successfully.
        error: ZED error text if opening or grabbing failed, else None.
        frames: Frames grabbed successfully during the window.
        grab_failures: Grab calls that returned an error during the window.
        dropped_frames: Frames the SDK reports as dropped during the window.
        measured_fps: ``frames`` divided by the window length, in frames per second.
        grab_ms_mean: Mean time of one grab-and-retrieve cycle, in milliseconds.
        grab_ms_p95: 95th percentile of that time, in milliseconds.
    """

    serial: int
    opened: bool = False
    error: str | None = None
    frames: int = 0
    grab_failures: int = 0
    dropped_frames: int = 0
    measured_fps: float = 0.0
    grab_ms_mean: float = 0.0
    grab_ms_p95: float = 0.0
    # Raw cycle times, used to compute the statistics above; not saved to the results file.
    _cycle_ms: list[float] = field(default_factory=list, repr=False)


@dataclass
class SystemSample:
    """One ``tegrastats`` reading.

    Attributes:
        cpu_percent: Mean load over all CPU cores that are online, 0 to 100.
        gpu_percent: GPU load (GR3D_FREQ), 0 to 100.
        ram_used_mb: Memory in use, in megabytes.
        power_mw: Total board input power (VDD_IN), in milliwatts.
        temp_c: Hottest junction temperature (tj), in degrees Celsius.
    """

    cpu_percent: float
    gpu_percent: float
    ram_used_mb: float
    power_mw: float
    temp_c: float


# --------------------------------------------------------------------------------------
# System monitor (tegrastats)
# --------------------------------------------------------------------------------------

_RAM_RE = re.compile(r"RAM (\d+)/\d+MB")
_CPU_RE = re.compile(r"CPU \[([^\]]*)\]")
_GPU_RE = re.compile(r"GR3D_FREQ (\d+)%")
_POWER_RE = re.compile(r"VDD_IN (\d+)mW")
_TEMP_RE = re.compile(r"tj@([\d.]+)C")


def parse_tegrastats_line(line: str) -> SystemSample | None:
    """Turn one line of ``tegrastats`` output into a SystemSample.

    Example line (shortened, JetPack 6 on Orin NX)::

        RAM 1693/15656MB ... CPU [1%@729,0%@1984,off,...] GR3D_FREQ 0% ... tj@47.6C ...
        VDD_IN 5704mW/5704mW ...

    Args:
        line: One line printed by ``tegrastats``.

    Returns:
        The parsed sample, or None if the line is missing a field (for example a format
        from another JetPack version).
    """
    ram = _RAM_RE.search(line)
    cpu = _CPU_RE.search(line)
    gpu = _GPU_RE.search(line)
    power = _POWER_RE.search(line)
    temp = _TEMP_RE.search(line)
    if not (ram and cpu and gpu and power and temp):
        return None

    # Each core reads "12%@1984" (load % at MHz), or "off" when the core is shut down.
    core_loads = [float(c.split("%")[0]) for c in cpu.group(1).split(",") if "%" in c]
    if not core_loads:
        return None

    return SystemSample(
        cpu_percent=statistics.fmean(core_loads),
        gpu_percent=float(gpu.group(1)),
        ram_used_mb=float(ram.group(1)),
        power_mw=float(power.group(1)),
        temp_c=float(temp.group(1)),
    )


class TegrastatsMonitor:
    """Run ``tegrastats`` in the background and keep the samples taken while recording.

    Call ``start()`` once, set ``recording`` to True for the measuring window, then ``stop()``.
    """

    def __init__(self, interval_ms: int = 1000) -> None:
        """Prepare the monitor.

        Args:
            interval_ms: Time between samples, in milliseconds.
        """
        self._interval_ms = interval_ms
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self.recording = False
        self.samples: list[SystemSample] = []

    def start(self) -> None:
        """Start ``tegrastats`` and a thread that reads its output."""
        self._proc = subprocess.Popen(
            ["tegrastats", "--interval", str(self._interval_ms)],
            stdout=subprocess.PIPE,
            text=True,
        )
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()

    def _read(self) -> None:
        """Read lines until ``tegrastats`` exits; keep those that arrive while recording."""
        assert self._proc is not None and self._proc.stdout is not None
        for line in self._proc.stdout:
            if self.recording:
                sample = parse_tegrastats_line(line)
                if sample is not None:
                    self.samples.append(sample)

    def stop(self) -> None:
        """Stop ``tegrastats``."""
        if self._proc is not None:
            self._proc.terminate()
            self._proc.wait(timeout=5)


def summarize_samples(samples: list[SystemSample]) -> dict:
    """Return mean and maximum of each system value.

    Args:
        samples: Readings taken during the measuring window.

    Returns:
        A dict such as ``{"cpu_percent_mean": 41.2, "cpu_percent_max": 55.0, ...}``,
        or an empty dict if there are no samples.
    """
    if not samples:
        return {}
    out = {"samples": len(samples)}
    for name in ("cpu_percent", "gpu_percent", "ram_used_mb", "power_mw", "temp_c"):
        values = [getattr(s, name) for s in samples]
        out[f"{name}_mean"] = round(statistics.fmean(values), 1)
        out[f"{name}_max"] = round(max(values), 1)
    return out


# --------------------------------------------------------------------------------------
# Cameras
# --------------------------------------------------------------------------------------


def open_camera(sl, serial: int, args: argparse.Namespace):
    """Open one ZED camera with the settings under test.

    Args:
        sl: The imported ``pyzed.sl`` module (imported late so ``summarize`` works without it).
        serial: Camera serial number, from the label on the camera or ``ZED_Explorer --all``.
        args: Parsed command-line arguments (resolution, fps, depth mode).

    Returns:
        A tuple ``(camera, error)``: the open ``sl.Camera`` and None, or None and the error text.
    """
    init = sl.InitParameters()
    # Select by serial, never by USB order: USB order changes between boots.
    init.set_from_serial_number(serial)
    init.camera_resolution = getattr(sl.RESOLUTION, args.resolution)
    init.camera_fps = args.fps
    init.depth_mode = getattr(sl.DEPTH_MODE, args.depth_mode)
    init.coordinate_units = sl.UNIT.METER
    init.sdk_verbose = 0

    cam = sl.Camera()
    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        return None, repr(status)
    return cam, None


def grab_loop(sl, cam, result: CameraResult, args: argparse.Namespace,
              state: dict, stop: threading.Event) -> None:
    """Grab frames from one camera until ``stop`` is set (runs in its own thread).

    ``grab()`` blocks until the camera delivers a new frame, so the number of successful
    grabs per second is the frame rate actually achieved.

    Args:
        sl: The imported ``pyzed.sl`` module.
        cam: An open ``sl.Camera``.
        result: Where to store this camera's measurements.
        args: Parsed command-line arguments (what to retrieve, and how often).
        state: Shared dict; ``state["measuring"]`` is True during the measuring window.
        stop: Set by the main thread to end the loop.
    """
    runtime = sl.RuntimeParameters()
    mat = sl.Mat()
    retrieve_period_s = 1.0 / args.retrieve_hz if args.retrieve_hz > 0 else 0.0
    last_retrieve = 0.0
    dropped_at_start: int | None = None

    while not stop.is_set():
        t0 = time.perf_counter()
        err = cam.grab(runtime)
        ok = err == sl.ERROR_CODE.SUCCESS

        if ok and args.retrieve != "none" and t0 - last_retrieve >= retrieve_period_s:
            last_retrieve = t0
            if args.retrieve == "image":
                cam.retrieve_image(mat, sl.VIEW.LEFT, sl.MEM.CPU)
            elif args.retrieve == "depth":
                cam.retrieve_measure(mat, sl.MEASURE.DEPTH, sl.MEM.CPU)
            else:  # pointcloud
                cam.retrieve_measure(mat, sl.MEASURE.XYZRGBA, sl.MEM.CPU)

        cycle_ms = (time.perf_counter() - t0) * 1000.0

        if state["measuring"]:
            if dropped_at_start is None:
                dropped_at_start = cam.get_frame_dropped_count()
            if ok:
                result.frames += 1
                result._cycle_ms.append(cycle_ms)
            else:
                result.grab_failures += 1
                result.error = repr(err)

    if dropped_at_start is not None:
        result.dropped_frames = cam.get_frame_dropped_count() - dropped_at_start


def run(args: argparse.Namespace) -> int:
    """Run one configuration, print the summary and append it to the results file.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Process exit code: 0 if every camera opened, 1 otherwise.
    """
    import pyzed.sl as sl  # Imported here so "summarize" runs on machines without the SDK.

    if args.depth_mode == "NONE" and args.retrieve in ("depth", "pointcloud"):
        print("Depth mode NONE computes no depth: use --retrieve none or image.", file=sys.stderr)
        return 2

    results = [CameraResult(serial=s) for s in args.serials]
    cameras = []
    # Open one at a time, as Stereolabs' multi-camera samples do; opening in parallel can
    # make the USB enumeration of several cameras fail.
    for res in results:
        cam, error = open_camera(sl, res.serial, args)
        res.opened, res.error = cam is not None, error
        if cam is not None:
            cameras.append((cam, res))
        print(f"camera {res.serial}: {'opened' if cam else 'FAILED ' + str(error)}", flush=True)

    monitor = TegrastatsMonitor()
    monitor.start()
    state = {"measuring": False}
    stop = threading.Event()
    threads = [
        threading.Thread(target=grab_loop, args=(sl, cam, res, args, state, stop), daemon=True)
        for cam, res in cameras
    ]
    for t in threads:
        t.start()

    # Warm-up: the first seconds after opening are slower (auto-exposure, GPU start-up),
    # so they are not counted.
    time.sleep(args.warmup)
    state["measuring"] = True
    monitor.recording = True
    window_start = time.perf_counter()
    time.sleep(args.duration)
    state["measuring"] = False
    monitor.recording = False
    window_s = time.perf_counter() - window_start

    stop.set()
    for t in threads:
        t.join(timeout=5)
    monitor.stop()
    for cam, _ in cameras:
        cam.close()

    for res in results:
        if res.frames:
            res.measured_fps = round(res.frames / window_s, 2)
            res.grab_ms_mean = round(statistics.fmean(res._cycle_ms), 1)
            res.grab_ms_p95 = round(statistics.quantiles(res._cycle_ms, n=20)[-1], 1) \
                if len(res._cycle_ms) >= 20 else round(max(res._cycle_ms), 1)

    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "label": args.label,
        "num_cameras": len(args.serials),
        "resolution": args.resolution,
        "fps_target": args.fps,
        "depth_mode": args.depth_mode,
        "retrieve": args.retrieve,
        "retrieve_hz": args.retrieve_hz,
        "window_s": round(window_s, 1),
        "cameras": [
            {k: v for k, v in asdict(r).items() if not k.startswith("_")} for r in results
        ],
        "system": summarize_samples(monitor.samples),
    }
    print(json.dumps(record, indent=2))
    with open(args.output, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return 0 if all(r.opened for r in results) else 1


# --------------------------------------------------------------------------------------
# Summary table
# --------------------------------------------------------------------------------------


def summarize(args: argparse.Namespace) -> int:
    """Print a Markdown table of every run in a results file.

    Args:
        args: Parsed command-line arguments (``results`` is the JSON-lines file).

    Returns:
        Process exit code (always 0).
    """
    header = (
        "| Label | Cams | Resolution | Target fps | Depth | Retrieve | fps per camera "
        "| Dropped | CPU % mean/max | GPU % mean/max | RAM MB max | Power W mean | Temp °C max |"
    )
    print(header)
    print("|" + "---|" * (header.count("|") - 1))
    with open(args.results, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            s = r["system"]
            fps = " / ".join(
                f"{c['measured_fps']:.1f}" if c["opened"] else "fail" for c in r["cameras"]
            )
            dropped = sum(c["dropped_frames"] for c in r["cameras"])
            retrieve = r["retrieve"] + (f"@{r['retrieve_hz']:g}Hz" if r["retrieve_hz"] else "")
            print(
                f"| {r['label']} | {r['num_cameras']} | {r['resolution']} | {r['fps_target']} "
                f"| {r['depth_mode']} | {retrieve} | {fps} | {dropped} "
                f"| {s.get('cpu_percent_mean', '-')}/{s.get('cpu_percent_max', '-')} "
                f"| {s.get('gpu_percent_mean', '-')}/{s.get('gpu_percent_max', '-')} "
                f"| {s.get('ram_used_mb_max', '-')} "
                f"| {s.get('power_mw_mean', 0) / 1000:.1f} | {s.get('temp_c_max', '-')} |"
            )
    return 0


# --------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Define the command-line options (shown with ``--help``)."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Measure one camera configuration.")
    p_run.add_argument("--serials", type=int, nargs="+", required=True,
                       help="Serial numbers of the cameras to open.")
    p_run.add_argument("--resolution", default="HD720",
                       help="ZED resolution name, e.g. VGA, HD720, HD1080, HD2K.")
    p_run.add_argument("--fps", type=int, default=15, help="Requested frame rate, frames/s.")
    p_run.add_argument("--depth-mode", default="PERFORMANCE",
                       help="ZED depth mode: NONE, PERFORMANCE, QUALITY, ULTRA, "
                            "NEURAL_LIGHT, NEURAL, NEURAL_PLUS.")
    p_run.add_argument("--retrieve", choices=RETRIEVE_CHOICES, default="pointcloud",
                       help="What to copy to CPU memory after each grab.")
    p_run.add_argument("--retrieve-hz", type=float, default=0.0,
                       help="Copy at most this often, in Hz. 0 = every frame.")
    p_run.add_argument("--warmup", type=float, default=5.0,
                       help="Seconds to run before measuring.")
    p_run.add_argument("--duration", type=float, default=30.0,
                       help="Length of the measuring window, in seconds.")
    p_run.add_argument("--label", default="", help="Short name for this run in the table.")
    p_run.add_argument("--output", default="results.jsonl",
                       help="JSON-lines file the result is appended to.")
    p_run.set_defaults(func=run)

    p_sum = sub.add_parser("summarize", help="Print a Markdown table of a results file.")
    p_sum.add_argument("results", help="JSON-lines file written by 'run'.")
    p_sum.set_defaults(func=summarize)
    return parser


def main() -> int:
    """Entry point."""
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
