#!/usr/bin/env python3
"""Register a Rhino capture against the reference on two VISIBLE features, and
detect silent scale drift before anything is cropped.

Why this exists: `-_ViewCaptureToFile` output scale depends on the Rhino
viewport's own pixel size. If the Rhino window is resized mid-session, the same
lens and the same requested capture size yield a different number of pixels per
metre -- silently invalidating every earlier registration. Hard-coding a crop
offset from a previous capture is therefore unsafe. Always measure, then crop.

Register on features that are visible in BOTH images (a facade edge, a parapet),
never on an assumed datum such as an occluded ground line.

Usage:
  register_capture.py RAW.png OUT.png --width W --height H \\
      --expect-width PX --ref-x X --ref-y Y [--threshold 245] [--band 0.25 0.5]

  --expect-width  building's expected pixel width in the raw capture
  --ref-x/--ref-y where that feature sits in the reference image
"""
import argparse
import sys

import numpy as np
from PIL import Image


def measure(path, threshold, band):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(float).mean(axis=2)
    h, w = a.shape
    y0, y1 = int(h * band[0]), int(h * band[1])
    strip = a[y0:y1, :]
    xs = [x for x in range(w) if strip[:, x].min() < threshold]
    if not xs:
        raise SystemExit("no object found in the measurement band -- check threshold/band")
    x_lo, x_hi = xs[0], xs[-1]
    # scan the full height only within the object's own columns, so neighbouring
    # content and ground shadow do not pull the top edge
    sub = a[:, x_lo + 40:x_hi - 40] if x_hi - x_lo > 120 else a[:, x_lo:x_hi + 1]
    ys = [y for y in range(h) if sub[y, :].min() < threshold]
    return im, (w, h), x_lo, x_hi, ys[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("raw")
    p.add_argument("out")
    p.add_argument("--width", type=int, required=True, help="crop width (reference image width)")
    p.add_argument("--height", type=int, required=True, help="crop height (reference image height)")
    p.add_argument("--expect-width", type=float, required=True)
    p.add_argument("--ref-x", type=float, required=True)
    p.add_argument("--ref-y", type=float, required=True)
    p.add_argument("--threshold", type=float, default=245.0)
    p.add_argument("--band", type=float, nargs=2, default=[0.25, 0.5])
    p.add_argument("--tolerance", type=float, default=2.0, help="allowed px drift in building width")
    a = p.parse_args()

    im, size, x_lo, x_hi, top = measure(a.raw, a.threshold, a.band)
    bw = x_hi - x_lo + 1
    factor = a.expect_width / bw

    print(f"raw capture      : {size[0]}x{size[1]}")
    print(f"building extent  : x {x_lo}..{x_hi}  width {bw}  top {top}")
    print(f"expected width   : {a.expect_width:.1f}")
    print(f"lens correction  : {factor:.5f}")

    if abs(bw - a.expect_width) > a.tolerance:
        print()
        print(f"*** SCALE DRIFT — {bw - a.expect_width:.1f} px off. Do NOT crop. ***")
        print("The viewport pixel size or the capture width changed. Multiply the")
        print(f"lens by {factor:.5f}, re-capture at the SAME requested size, and re-run.")
        return 1

    cx, cy = round(x_lo - a.ref_x), round(top - a.ref_y)
    if cx < 0 or cy < 0 or cx + a.width > size[0] or cy + a.height > size[1]:
        print()
        print("*** CROP OUT OF BOUNDS — capture a larger frame. ***")
        print(f"needed origin ({cx},{cy}) size {a.width}x{a.height} from {size[0]}x{size[1]}")
        return 1

    im.crop((cx, cy, cx + a.width, cy + a.height)).save(a.out)
    print(f"crop offset      : ({cx}, {cy})  ->  {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
