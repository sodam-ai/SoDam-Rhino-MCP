#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from PIL import Image


def clamp01(v):
    return max(0.0, min(1.0, float(v)))

def crop_norm(img, box):
    w, h = img.size
    x0, y0, x1, y1 = [clamp01(v) for v in box]
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"Invalid normalized crop: {box}")
    px = (round(x0*w), round(y0*h), round(x1*w), round(y1*h))
    return img.crop(px), px

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", default="reference_packet")
    ap.add_argument("--crops-json", help='JSON file: [{"name":"top","box":[x0,y0,x1,y1]}, ...]')
    args = ap.parse_args()

    src = Path(args.image)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    w, h = img.size

    img.save(out / "REF_FAR.png")

    manifest = {
        "source": str(src),
        "width": w,
        "height": h,
        "aspect_ratio": w / h,
        "outputs": [{"name":"FAR","path":"REF_FAR.png","box_norm":[0,0,1,1],"box_px":[0,0,w,h]}]
    }

    auto = [
        ("MID_TOP",    [0.0, 0.0, 1.0, 0.45]),
        ("MID_CENTER", [0.0, 0.275, 1.0, 0.725]),
        ("MID_BOTTOM", [0.0, 0.55, 1.0, 1.0]),
        ("MID_LEFT",   [0.0, 0.0, 0.60, 1.0]),
        ("MID_RIGHT",  [0.40, 0.0, 1.0, 1.0]),
    ]
    for name, box in auto:
        c, px = crop_norm(img, box)
        fn = f"{name}.png"
        c.save(out / fn)
        manifest["outputs"].append({"name":name,"path":fn,"box_norm":box,"box_px":list(px)})

    if args.crops_json:
        specs = json.loads(Path(args.crops_json).read_text(encoding="utf-8"))
        for item in specs:
            name = item["name"]
            box = item["box"]
            c, px = crop_norm(img, box)
            fn = f"NEAR_{name}.png"
            c.save(out / fn)
            manifest["outputs"].append({"name":f"NEAR_{name}","path":fn,"box_norm":box,"box_px":list(px)})

    (out / "reference_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out.resolve())

if __name__ == "__main__":
    main()
