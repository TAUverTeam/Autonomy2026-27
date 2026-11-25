#!/usr/bin/env python3
"""Compare ZED depth modes on the same recording: how complete, how steady and how fast.

Part of ``tools/zed_depth_compare`` (see the README next to this file). It replays SVO files
(recorded with ``record_svo.py``) once per depth mode and measures, for each mode:

- **Fill rate**: the share of pixels that get a valid depth. Missing depth (holes) is what
  makes plain sand or blank walls look like gaps or hides real trenches.
- **Fill rate, lower half**: the same for the lower half of the image, which is mostly the
  ground in front of the rover.
- **Temporal noise**: how much a pixel's depth jumps from frame to frame, as a percentage of its
  distance (median over the image). Only meaningful if the camera did not move during the
  recording; noise is what makes flat ground look like small obstacles.
- **Processing speed**: frames per second the Jetson computes in that mode when replaying as
  fast as it can (the camera's own frame rate does not limit it).

It also saves a picture per recording: the left camera image next to the depth map from each
mode, taken from the same frame, so the differences can be seen.

Usage:
    python3 depth_compare.py recordings/lab/*.svo2 --out results/lab
    python3 depth_compare.py front.svo2 --modes PERFORMANCE NEURAL_LIGHT --max-frames 100

Output in ``--out``: ``results.jsonl`` (one line per file and mode), ``results.md`` (table)
and ``<recording>_compare.png`` (pictures).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

DEFAULT_MODES = ["PERFORMANCE", "QUALITY", "ULTRA", "NEURAL_LIGHT", "NEURAL", "NEURAL_PLUS"]

# Width of each tile in the comparison picture, in pixels. Small enough to view on a laptop.
TILE_WIDTH = 640


class DepthStats:
    """Accumulate per-frame and per-pixel depth statistics over a recording.

    Per pixel it keeps the count, sum and sum of squares of valid depths, which is enough to get
    each pixel's mean and standard deviation at the end without storing every frame.
    """

    def __init__(self, shape: tuple[int, int]) -> None:
        """Create empty accumulators.

        Args:
            shape: Depth image size as (height, width) in pixels.
        """
        self.frames = 0
        self.fill = []        # Valid share of the whole image, per frame (0 to 1).
        self.fill_lower = []  # Valid share of the lower half, per frame (0 to 1).
        # float64 for the sums: float32 loses precision after a few hundred frames.
        self.count = np.zeros(shape, np.int32)
        self.sum = np.zeros(shape, np.float64)
        self.sum_sq = np.zeros(shape, np.float64)

    def add(self, depth_m: np.ndarray) -> None:
        """Add one depth frame.

        Args:
            depth_m: Depth image in metres. Invalid pixels are NaN (no match found) or
                ±inf (closer or further than the allowed range), as the ZED SDK returns them.
        """
        valid = np.isfinite(depth_m)
        half = depth_m.shape[0] // 2
        self.frames += 1
        self.fill.append(float(valid.mean()))
        self.fill_lower.append(float(valid[half:].mean()))
        d = np.where(valid, depth_m, 0.0)
        self.count += valid
        self.sum += d
        self.sum_sq += d.astype(np.float64) ** 2

    def summary(self, steady_share: float = 0.9) -> dict:
        """Return the mode's results.

        Args:
            steady_share: A pixel counts for the noise figure only if it was valid in at least
                this share of the frames (0 to 1), so that noise is measured on surfaces the
                mode sees reliably.

        Returns:
            Dict with fill rates (in %), median relative noise (in %), the median distance of the
            pixels used for the noise figure (in metres) and the frame count.
        """
        steady = self.count >= max(1, int(steady_share * self.frames))
        if steady.any():
            n = self.count[steady]
            mean = self.sum[steady] / n
            var = np.maximum(self.sum_sq[steady] / n - mean ** 2, 0.0)
            rel_noise = np.sqrt(var) / mean
            noise_pct = float(np.median(rel_noise) * 100)
            noise_dist = float(np.median(mean))
        else:
            noise_pct = noise_dist = float("nan")
        return {
            "frames": self.frames,
            "fill_pct": round(100 * float(np.mean(self.fill)), 1),
            "fill_lower_pct": round(100 * float(np.mean(self.fill_lower)), 1),
            "noise_pct": round(noise_pct, 2),
            "noise_median_distance_m": round(noise_dist, 2),
        }


def colorize_depth(cv2, depth_m: np.ndarray, min_m: float, max_m: float) -> np.ndarray:
    """Turn a depth image into a colour picture: near = red, far = blue, no depth = black.

    Args:
        cv2: The imported OpenCV module.
        depth_m: Depth image in metres (NaN/inf where invalid).
        min_m: Distance shown as the nearest colour, in metres.
        max_m: Distance shown as the furthest colour, in metres; further is clipped.

    Returns:
        A BGR image (uint8) of the same size.
    """
    valid = np.isfinite(depth_m)
    scaled = np.clip((np.nan_to_num(depth_m, nan=max_m, posinf=max_m, neginf=min_m) - min_m)
                     / (max_m - min_m), 0.0, 1.0)
    # TURBO goes blue → red; invert so that near objects are red (warm = close = danger).
    img = cv2.applyColorMap(((1.0 - scaled) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    img[~valid] = 0
    return img


def label(cv2, img: np.ndarray, text: str) -> np.ndarray:
    """Resize an image to the tile width and write ``text`` in its top-left corner."""
    h = int(img.shape[0] * TILE_WIDTH / img.shape[1])
    tile = cv2.resize(img, (TILE_WIDTH, h), interpolation=cv2.INTER_AREA)
    cv2.rectangle(tile, (0, 0), (TILE_WIDTH, 30), (0, 0, 0), -1)
    cv2.putText(tile, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                cv2.LINE_AA)
    return tile


def process(sl, cv2, svo_path: str, mode: str, args: argparse.Namespace, tiles: list) -> dict:
    """Replay one SVO file with one depth mode and return its statistics.

    Args:
        sl: The imported ``pyzed.sl`` module.
        cv2: The imported OpenCV module.
        svo_path: Path to the SVO file.
        mode: ZED depth mode name, e.g. ``"NEURAL_LIGHT"``.
        args: Parsed command-line arguments (depth range, frame limits).
        tiles: List the picture tiles are appended to (the left image is added once, by the
            first mode, followed by one depth tile per mode).

    Returns:
        A result dict for ``results.jsonl``.
    """
    init = sl.InitParameters()
    init.set_from_svo_file(svo_path)
    # Replay as fast as the Jetson can compute, not at the recorded frame rate, so the
    # processing speed is measured and no frames are skipped.
    init.svo_real_time_mode = False
    init.depth_mode = getattr(sl.DEPTH_MODE, mode)
    init.coordinate_units = sl.UNIT.METER
    init.depth_minimum_distance = args.min_depth
    init.depth_maximum_distance = args.max_depth
    init.sdk_verbose = 0

    cam = sl.Camera()
    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        return {"file": os.path.basename(svo_path), "mode": mode, "error": repr(status)}

    total = cam.get_svo_number_of_frames()
    n_frames = min(total, args.max_frames) if args.max_frames else total
    snapshot_at = n_frames // 2
    res = cam.get_camera_information().camera_configuration.resolution
    stats = DepthStats((res.height, res.width))
    depth = sl.Mat()
    image = sl.Mat()
    runtime = sl.RuntimeParameters()

    # Skip the first frames: some modes smooth depth over time and need a moment to settle.
    for _ in range(args.skip):
        cam.grab(runtime)

    failures = 0
    t0 = time.perf_counter()
    while stats.frames < n_frames - args.skip:
        err = cam.grab(runtime)
        if err == sl.ERROR_CODE.END_OF_SVOFILE_REACHED:
            break
        if err != sl.ERROR_CODE.SUCCESS:
            # A damaged frame is skipped; many in a row means the file is unusable.
            failures += 1
            if failures > 30:
                break
            continue
        cam.retrieve_measure(depth, sl.MEASURE.DEPTH, sl.MEM.CPU)
        d = depth.get_data()
        stats.add(d)

        if stats.frames == snapshot_at - args.skip:
            if not tiles:  # The left image is the same for every mode; add it once.
                cam.retrieve_image(image, sl.VIEW.LEFT, sl.MEM.CPU)
                tiles.append(label(cv2, image.get_data()[:, :, :3].copy(), "left image"))
            fill_now = 100 * float(np.isfinite(d).mean())
            tiles.append(label(cv2, colorize_depth(cv2, d, args.min_depth, args.vis_max),
                               f"{mode}  (fill {fill_now:.0f}%)"))
    elapsed = time.perf_counter() - t0
    cam.close()

    out = {"file": os.path.basename(svo_path), "mode": mode, "error": None}
    out.update(stats.summary())
    out["processing_fps"] = round(stats.frames / elapsed, 1) if elapsed > 0 else 0.0
    return out


def save_montage(cv2, tiles: list, path: str) -> None:
    """Arrange tiles in a grid of two columns and save it as a PNG file."""
    if not tiles:
        return
    h, w = tiles[0].shape[:2]
    tiles = [cv2.resize(t, (w, h)) for t in tiles]
    if len(tiles) % 2:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)]
    cv2.imwrite(path, np.vstack(rows))


def main() -> int:
    """Parse arguments, process every file in every mode, and write the results.

    Returns:
        Process exit code: 0 if every file opened in every mode, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("svo", nargs="+", help="SVO files to compare.")
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES, help="Depth modes to try.")
    parser.add_argument("--out", required=True, help="Output folder (created if missing).")
    parser.add_argument("--min-depth", type=float, default=0.3,
                        help="Closest distance accepted, m (ZED 2i minimum is about 0.3 m).")
    parser.add_argument("--max-depth", type=float, default=20.0,
                        help="Furthest distance accepted, m.")
    parser.add_argument("--vis-max", type=float, default=10.0,
                        help="Furthest distance shown in the pictures, m.")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="Use at most this many frames per file; 0 = all.")
    parser.add_argument("--skip", type=int, default=15,
                        help="Frames skipped at the start of each file (settling time).")
    args = parser.parse_args()

    import cv2
    import pyzed.sl as sl

    os.makedirs(args.out, exist_ok=True)
    results = []
    for svo in args.svo:
        tiles: list = []
        for mode in args.modes:
            print(f"{os.path.basename(svo)}  {mode} ...", flush=True)
            r = process(sl, cv2, svo, mode, args, tiles)
            print("   ", r, flush=True)
            results.append(r)
            with open(os.path.join(args.out, "results.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(r) + "\n")
        name = os.path.splitext(os.path.basename(svo))[0]
        save_montage(cv2, tiles, os.path.join(args.out, f"{name}_compare.png"))

    lines = ["| File | Mode | Frames | Fill % | Fill % lower half | Noise % (at m) | Processing fps |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        if r.get("error"):
            lines.append(f"| {r['file']} | {r['mode']} | error: {r['error']} | | | | |")
        else:
            lines.append(f"| {r['file']} | {r['mode']} | {r['frames']} | {r['fill_pct']} "
                         f"| {r['fill_lower_pct']} | {r['noise_pct']} "
                         f"({r['noise_median_distance_m']}) | {r['processing_fps']} |")
    table = "\n".join(lines)
    with open(os.path.join(args.out, "results.md"), "w", encoding="utf-8") as f:
        f.write(table + "\n")
    print(table)
    return 0 if all(not r.get("error") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
