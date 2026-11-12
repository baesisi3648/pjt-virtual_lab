"""Figures 3-6 (revision): decision trees of the representative report, drawn from its Mermaid source.

    python -B scripts/revision/make_fig34.py [--out reference/revision/figures_v1]

Nodes, edges and labels are taken unchanged from the report; only visual style lines are added.
Fig. 3 = SDN-1, Fig. 4 = SDN-2, Fig. 5 = ODM, Fig. 6 = SDN-3, one tree per figure. Requires npx (@mermaid-js/mermaid-cli) and Chrome.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments" / "runs_rev" / "results_v1"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CONFIG = {"theme": "base", "themeVariables": {"fontFamily": "Arial", "fontSize": "15px", "primaryColor": "#ffffff",
                                               "primaryBorderColor": "#555555", "primaryTextColor": "#000000", "lineColor": "#555555",
                                               "edgeLabelBackground": "#ffffff"},
          "flowchart": {"htmlLabels": True, "curve": "linear", "nodeSpacing": 40, "rankSpacing": 42, "wrappingWidth": 240}}
STYLE = ["classDef start fill:#d9d9d9,stroke:#555555,font-weight:bold", "classDef decide fill:#f1f3f5,stroke:#555555,font-weight:bold",
         "classDef done fill:#dce6f1,stroke:#4472c4,color:#1f3864,font-weight:bold"]


def tree(text: str, name: str) -> str:
    m = re.search(r"####\s*" + name + r"\s*\n+```mermaid\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("tree not found: " + name)
    return m.group(1).strip()


def styled(src: str) -> str:
    starts = sorted(set(re.findall(r"(\w+)\[\"[^\"]*start\"\]", src)))
    ends = sorted(set(re.findall(r"(\w+)\[\"Assessment complete\"\]", src)))
    decide = sorted(set(re.findall(r"(\w+)\{\{", src)))
    lines = [src] + ["    " + s for s in STYLE]
    for ids, cls in ((starts, "start"), (decide, "decide"), (ends, "done")):
        if ids:
            lines.append(f"    class {','.join(ids)} {cls}")
    return "\n".join(lines) + "\n"


def render(src: str, out: Path, tmp: Path) -> Image.Image:
    (tmp / "in.mmd").write_text(src, encoding="utf-8")
    (tmp / "cfg.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    (tmp / "pp.json").write_text(json.dumps({"executablePath": CHROME, "args": ["--no-sandbox"]}), encoding="utf-8")
    cmd = ["npx", "-y", "@mermaid-js/mermaid-cli@11", "-i", "in.mmd", "-o", out.name, "-c", "cfg.json", "-p", "pp.json", "-s", "3", "-b", "white"]
    subprocess.run(" ".join(cmd), shell=True, cwd=tmp, check=True, capture_output=True)
    return Image.open(tmp / out.name).convert("RGB")


def panels(images, letters):
    h = max(i.height for i in images)
    pad, top = 90, 150
    w = sum(i.width for i in images) + pad * (len(images) + 1)
    canvas = Image.new("RGB", (w, h + top + pad), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf"), 96)
    x = pad
    for im, letter in zip(images, letters):
        canvas.paste(im, (x, top))
        draw.text((x, 20), letter, fill="black", font=font)
        x += im.width + pad
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reference/revision/figures_v2")
    out = ROOT / ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    rep = json.loads((RES / "representative.json").read_text(encoding="utf-8"))["representative"]
    text = (ROOT / "experiments" / "runs_rev" / "main_v1" / rep / "attempt_01" / "final_report.md").read_text(encoding="utf-8")
    text = text.replace("‑", "-")
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        imgs = {n: render(styled(tree(text, n)), Path(f"{n}.png"), tmp).copy() for n in ("SDN-1", "SDN-2", "ODM", "SDN-3")}
    for n, name in ((3, "SDN-1"), (4, "SDN-2"), (5, "ODM"), (6, "SDN-3")):
        imgs[name].save(out / f"Fig{n}_v2.png", dpi=(300, 300))
    print({k: v.size for k, v in imgs.items()})


if __name__ == "__main__":
    main()
