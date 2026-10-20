#!/usr/bin/env python3
"""Render Open Graph cards and app icons (run after editing page metadata).

    python3 tools/make_assets.py

Uses headless Chrome for the 1200x630 cards and Pillow for the PNG icons.
Both outputs are copied into dist/ by build.py, so run this before deploying.
"""

from __future__ import annotations

import html
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OG_DIR = ROOT / "assets" / "og"
TMP = OG_DIR / "_render.html"

KICKERS = {
    "home": "THE MEANING",
    "what-is-a-vaporetto": "EXPLAINER",
    "pronunciation": "PRONUNCIATION",
    "etymology": "WORD HISTORY",
    "how-to-ride": "FIRST-TIMER'S GUIDE",
    "tickets-and-prices": "FARES · 2026",
    "line-1": "ROUTE GUIDE",
    "airport": "AIRPORT TRANSFER",
    "vaporetto-vs-gondola": "COMPARISON",
    "default": "FIELD GUIDE",
}

SUBS = {
    "home": "The word, the boats, and how to use them.",
    "what-is-a-vaporetto": "The public boat that moves Venice.",
    "pronunciation": "Four syllables. Stress on the third.",
    "etymology": "From Latin vapor to the 1881 steam launches.",
    "how-to-ride": "Buy, validate, board, and know your stop.",
    "tickets-and-prices": "€9.50 a ride, €25 a day — the maths.",
    "line-1": "Piazzale Roma to Lido, stop by stop.",
    "airport": "Boat, bus or water taxi — the real costs.",
    "vaporetto-vs-gondola": "Public transport or private ride?",
    "default": "An independent field guide to the Venetian water bus.",
}

CARD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><style>
  @page {{ margin: 0; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
  body {{
    background: #f6f1e6;
    color: #17211f;
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    position: relative;
  }}
  .edge {{ position: absolute; left: 0; top: 0; bottom: 0; width: 14px; background: #b8472a; }}
  .inner {{ position: absolute; inset: 0 0 0 14px; padding: 58px 72px 0; }}
  .top {{ display: flex; align-items: center; gap: 14px; font-family: -apple-system, "Segoe UI", Arial, sans-serif; }}
  .top b {{ font-size: 17px; letter-spacing: .26em; font-weight: 700; color: #0d4a45; }}
  .top span {{ font-size: 12px; letter-spacing: .2em; color: #5c6762; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; background: #e0a33e; }}
  .kick {{ margin: 64px 0 16px; font-family: -apple-system, "Segoe UI", Arial, sans-serif;
           font-size: 13px; font-weight: 700; letter-spacing: .24em; color: #b8472a; }}
  h1 {{ margin: 0; font-size: {size}px; line-height: 1.02; letter-spacing: -.03em;
        font-weight: 500; max-width: 820px; text-wrap: balance; }}
  .sub {{ margin: 24px 0 0; font-family: -apple-system, "Segoe UI", Arial, sans-serif;
          font-size: 21px; line-height: 1.45; color: #4c5752; max-width: 640px; }}
  .foot {{ position: absolute; left: 72px; right: 72px; bottom: 34px;
           border-top: 1px solid #d8cdb9; padding-top: 14px;
           display: flex; justify-content: space-between;
           font-family: -apple-system, "Segoe UI", Arial, sans-serif;
           font-size: 11px; letter-spacing: .18em; color: #7d877f; text-transform: uppercase; }}
  .art {{ position: absolute; right: -10px; bottom: 72px; width: 470px; opacity: .85; }}
</style></head>
<body>
  <div class="edge"></div>
  <div class="inner">
    <div class="top"><span class="dot"></span><b>VAPORETTO GUIDE</b><span>VENICE · WATER BUS</span></div>
    <p class="kick">{kick}</p>
    <h1>{title}</h1>
    <p class="sub">{sub}</p>
  </div>
  <div class="foot"><span>Independent field guide</span><span>Vaporetto Guide</span></div>
  <svg class="art" viewBox="0 0 520 260" aria-hidden="true">
    <g fill="none" stroke="#0d4a45" stroke-width="2.4" opacity=".55">
      <path d="M20 196h480"/>
      <path d="M0 220c20-8 40-8 60 0s40 8 60 0 40-8 60 0 40 8 60 0 40-8 60 0 40 8 60 0 40-8 60 0 40 8 60 0"/>
      <path d="M0 244c20-8 40-8 60 0s40 8 60 0 40-8 60 0 40 8 60 0 40-8 60 0 40 8 60 0 40-8 60 0 40 8 60 0"/>
    </g>
    <g fill="#f6f1e6" stroke="#0d4a45" stroke-width="2.4">
      <path d="M92 150h300l38 16-6 18c-3 8-10 12-19 12H122c-9 0-16-4-19-12l-11-34Z"/>
      <path d="M138 96h210v54H138z"/>
      <path d="M118 96h250l-10-14H128z"/>
      <path d="M348 96l26 14v40h-26z"/>
    </g>
    <g fill="#0d4a45">
      <rect x="150" y="108" width="30" height="30"/>
      <rect x="190" y="108" width="30" height="30"/>
      <rect x="230" y="108" width="30" height="30"/>
      <rect x="270" y="108" width="30" height="30"/>
      <rect x="310" y="108" width="24" height="30"/>
    </g>
    <g fill="#b8472a">
      <path d="M92 158h300l4 8H96z"/>
      <circle cx="438" cy="176" r="9" fill="none" stroke="#b8472a" stroke-width="4"/>
    </g>
    <g stroke="#0d4a45" stroke-width="2.4">
      <path d="M404 170l14-14h30l18 14"/>
      <circle cx="470" cy="66" r="26" fill="#e0a33e" stroke="none"/>
    </g>
  </svg>
</body></html>
"""


def make_og() -> None:
    if not Path(CHROME).exists():
        raise SystemExit("Chrome not found: " + CHROME)
    OG_DIR.mkdir(parents=True, exist_ok=True)
    pages = [page for page in build.PAGES if page["og"] != "default"]
    cards = [{"og": page["og"], "title": page["title"].split(":")[0], "kick": KICKERS[page["og"]]} for page in pages]
    cards.append({"og": "default", "title": "Vaporetto Guide", "kick": KICKERS["default"]})

    for card in cards:
        title = html.escape(card["title"])
        size = 84 if len(card["title"]) <= 24 else 70 if len(card["title"]) <= 38 else 58
        body = CARD.format(size=size, kick=KICKERS[card["og"]], title=title, sub=SUBS[card["og"]])
        TMP.write_text(body, encoding="utf-8")
        out = OG_DIR / f"{card['og']}.png"
        subprocess.run(
            [
                CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--force-prefers-reduced-motion", "--window-size=1200,630",
                "--screenshot=" + str(out), TMP.as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("og", out.name, out.stat().st_size)

    if TMP.exists():
        TMP.unlink()


def make_icons() -> None:
    from PIL import Image, ImageDraw

    scale = 4
    size = 512 * scale
    img = Image.new("RGB", (size, size), "#0d4a45")
    draw = ImageDraw.Draw(img)

    def box(*values: float) -> list[float]:
        return [value * scale for value in values]

    # sun
    draw.ellipse(box(344, 84, 424, 164), fill="#e0a33e")
    # hull
    draw.polygon(box(60, 300, 452, 300, 408, 374, 104, 374), fill="#f6f1e6")
    # cabin
    draw.rectangle(box(150, 214, 360, 300), fill="#f6f1e6")
    # windows
    for x in (174, 232, 290):
        draw.rectangle(box(x, 236, x + 44, 276), fill="#0d4a45")
    # ochre stripe
    draw.rectangle(box(64, 306, 448, 320), fill="#e0a33e")
    # waves
    import math

    for y, width in ((430, 7), (462, 5)):
        points = []
        for i in range(0, 391, 3):
            px = 60 + i
            py = y + math.sin(i / 16.0) * 6
            points.append((px * scale, py * scale))
        draw.line(points, fill="#f6f1e6", width=width * scale, joint="curve")

    for pixels in (512, 192):
        img.resize((pixels, pixels), Image.LANCZOS).save(ROOT / "assets" / f"icon-{pixels}.png")
        print("icon", pixels)


if __name__ == "__main__":
    make_og()
    make_icons()
