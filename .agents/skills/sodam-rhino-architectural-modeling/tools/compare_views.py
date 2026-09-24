#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat


def fit_same(img, size):
    return ImageOps.fit(img.convert("RGB"), size, method=Image.Resampling.LANCZOS)

def edge(img):
    g = ImageOps.grayscale(img)
    return g.filter(ImageFilter.FIND_EDGES)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("model")
    ap.add_argument("--out", default="comparison_packet")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    ref0 = Image.open(args.reference).convert("RGB")
    mod0 = Image.open(args.model).convert("RGB")
    target = ref0.size

    ref = fit_same(ref0, target)
    mod = fit_same(mod0, target)

    ref.save(out/"reference_normalized.png")
    mod.save(out/"model_normalized.png")

    side = Image.new("RGB", (target[0]*2, target[1]), "white")
    side.paste(ref, (0,0))
    side.paste(mod, (target[0],0))
    side.save(out/"side_by_side.png")

    overlay = Image.blend(ref, mod, 0.5)
    overlay.save(out/"overlay_50.png")

    diff = ImageChops.difference(ref, mod)
    ImageOps.grayscale(diff).save(out/"abs_difference_gray.png")

    er = edge(ref)
    em = edge(mod)
    er.save(out/"reference_edges.png")
    em.save(out/"model_edges.png")

    # Visual edge overlay: reference edges in red, model edges in cyan.
    rp = er.point(lambda p: 255 if p > 25 else 0)
    mp = em.point(lambda p: 255 if p > 25 else 0)
    ref_layer = Image.new("RGB", target, (255,0,0))
    mod_layer = Image.new("RGB", target, (0,255,255))
    black = Image.new("RGB", target, "black")
    a = Image.composite(ref_layer, black, rp)
    b = Image.composite(mod_layer, black, mp)
    eo = Image.blend(a, b, 0.5)
    eo.save(out/"edge_overlay.png")

    stat = ImageStat.Stat(ImageOps.grayscale(diff))
    metrics = {
        "reference_size": target,
        "model_original_size": mod0.size,
        "mean_absolute_pixel_difference_0_255": stat.mean[0],
        "note": "Supporting evidence only; lighting/background differences can dominate this metric."
    }
    (out/"comparison_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out.resolve())

if __name__ == "__main__":
    main()
