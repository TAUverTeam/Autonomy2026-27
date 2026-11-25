#!/usr/bin/env python3
"""Record raw stereo video (SVO files) from one or more ZED cameras at the same time.

Part of ``tools/zed_depth_compare`` (see the README next to this file). An SVO file holds both
lenses' images plus the camera's sensor data, so depth can be computed from it later, with any
depth mode, as if the camera were live. This lets us record a scene once (for example in the
Mars Yard) and compare depth modes on exactly the same images (``depth_compare.py``).

Depth is switched off while recording: only the images are saved, so recording costs little
and every depth mode can be tried afterwards.

Usage:
    python3 record_svo.py --serials 31718458 32514439 33289078 --duration 30 --out recordings/lab

Output: one file per camera, ``<out>/<position>_<serial>.svo2``, plus ``<out>/info.txt``
describing the recording.

Compression: the default, LOSSLESS (PNG per frame), keeps every pixel exact, so depth from the
file equals depth from the live camera. It is large: about 1.1 GB per camera per minute at
HD720 (measured 2026-11-25: 75 MB for 4 s). H265_LOSSLESS gave a file 37 times smaller on the
bench Jetson, so it is probably not truly lossless there; use it (or H265) only for long
recordings where depth-quality comparisons are not needed.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from datetime import datetime

# Camera positions on the mast, by serial number. Keep in sync with docs/hardware.md.
POSITIONS = {
    31718458: "front",
    32514439: "rear_right",
    33289078: "rear_left",
}


def record_one(sl, serial: int, path: str, args: argparse.Namespace,
               ready: threading.Barrier, stop: threading.Event, frames: dict) -> None:
    """Open one camera, record to ``path`` until ``stop`` is set (runs in its own thread).

    Args:
        sl: The imported ``pyzed.sl`` module.
        serial: Camera serial number.
        path: Output SVO file path.
        args: Parsed command-line arguments (resolution, fps, compression).
        ready: Barrier all camera threads wait at, so that recordings start together.
        stop: Set by the main thread to end the recording.
        frames: Shared dict; this thread stores its frame count (or error text) under ``serial``.
    """
    init = sl.InitParameters()
    init.set_from_serial_number(serial)
    init.camera_resolution = getattr(sl.RESOLUTION, args.resolution)
    init.camera_fps = args.fps
    # No depth while recording: it is computed later from the file, in any mode.
    init.depth_mode = sl.DEPTH_MODE.NONE
    init.sdk_verbose = 0

    cam = sl.Camera()
    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        frames[serial] = f"open failed: {status!r}"
        ready.wait()
        return

    rec = sl.RecordingParameters(path, getattr(sl.SVO_COMPRESSION_MODE, args.compression))
    status = cam.enable_recording(rec)
    if status != sl.ERROR_CODE.SUCCESS:
        frames[serial] = f"recording failed: {status!r}"
        cam.close()
        ready.wait()
        return

    ready.wait()  # Start grabbing only when every camera is open and recording.
    runtime = sl.RuntimeParameters()
    count = 0
    while not stop.is_set():
        # Each successful grab writes one frame to the SVO file.
        if cam.grab(runtime) == sl.ERROR_CODE.SUCCESS:
            count += 1
    cam.disable_recording()
    cam.close()
    frames[serial] = count


def main() -> int:
    """Parse arguments, record from every camera at once, and write ``info.txt``.

    Returns:
        Process exit code: 0 if every camera recorded, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--serials", type=int, nargs="+", required=True,
                        help="Serial numbers of the cameras to record.")
    parser.add_argument("--duration", type=float, default=30.0, help="Recording length, s.")
    parser.add_argument("--resolution", default="HD720", help="ZED resolution, e.g. HD720.")
    parser.add_argument("--fps", type=int, default=15, help="Frame rate, frames/s.")
    parser.add_argument("--compression", default="LOSSLESS",
                        help="LOSSLESS, H264, H265, H264_LOSSLESS or H265_LOSSLESS.")
    parser.add_argument("--out", required=True, help="Output folder (created if missing).")
    parser.add_argument("--note", default="", help="What was recorded, saved in info.txt.")
    args = parser.parse_args()

    import pyzed.sl as sl  # Imported after argument parsing so --help works without the SDK.

    os.makedirs(args.out, exist_ok=True)
    paths = {s: os.path.join(args.out, f"{POSITIONS.get(s, 'camera')}_{s}.svo2")
             for s in args.serials}
    for p in paths.values():
        if os.path.exists(p):
            print(f"{p} already exists; choose another --out folder.", file=sys.stderr)
            return 2

    ready = threading.Barrier(len(args.serials) + 1)
    stop = threading.Event()
    frames: dict = {}
    threads = [threading.Thread(target=record_one,
                                args=(sl, s, paths[s], args, ready, stop, frames))
               for s in args.serials]
    for t in threads:
        t.start()

    ready.wait()
    start = datetime.now()
    print(f"Recording {len(args.serials)} camera(s) for {args.duration:.0f} s...", flush=True)
    time.sleep(args.duration)
    stop.set()
    for t in threads:
        t.join()

    lines = [
        f"start: {start.isoformat(timespec='seconds')}",
        f"duration_s: {args.duration}",
        f"resolution: {args.resolution}",
        f"fps: {args.fps}",
        f"compression: {args.compression}",
        f"note: {args.note}",
    ]
    for s in args.serials:
        size = os.path.getsize(paths[s]) / 1e6 if os.path.exists(paths[s]) else 0
        lines.append(f"{POSITIONS.get(s, 'camera')} {s}: frames={frames.get(s)} size_MB={size:.0f}")
    with open(os.path.join(args.out, "info.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    return 0 if all(isinstance(frames.get(s), int) and frames[s] > 0 for s in args.serials) else 1


if __name__ == "__main__":
    sys.exit(main())
