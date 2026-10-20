#!/usr/bin/env python3
"""Pre-deploy checks for the built site.

    python3 tools/check_site.py [dist]

Verifies internal links, metadata, JSON-LD, image alt text, heading structure and
the sitemap. Exit code 1 if anything fails.
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DIST = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist"
PREFIX = ""

problems: list[str] = []
notes: list[str] = []


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: list[str] = []
        self.imgs: list[tuple[str, str | None]] = []
        self.headings: list[tuple[int, str]] = []
        self.canonical: str | None = None
        self.title = ""
        self.description: str | None = None
        self.lang: str | None = None
        self.jsonld: list[str] = []
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []
        self._heading_level: int | None = None
        self._heading_parts: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "html":
            self.lang = data.get("lang")
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])
        if data.get("id"):
            self.ids.append(data["id"])
        if tag == "img":
            self.imgs.append((data.get("src") or "", data.get("alt")))
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href")
        if tag == "meta" and data.get("name") == "description":
            self.description = data.get("content")
        if tag == "title":
            self._in_title = True
        if tag == "script" and data.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_parts = []
        if tag in ("h1", "h2", "h3", "h4"):
            self._heading_level = int(tag[1])
            self._heading_parts = []
        if tag == "style":
            self._in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._jsonld_parts))
            self._in_jsonld = False
        if tag in ("h1", "h2", "h3", "h4") and self._heading_level:
            text = re.sub(r"\s+", " ", "".join(self._heading_parts)).strip()
            self.headings.append((self._heading_level, text))
            self._heading_level = None
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_jsonld:
            self._jsonld_parts.append(data)
        if self._heading_level:
            self._heading_parts.append(data)


def rel_to_file(path: str) -> Path:
    parsed = urlparse(path)
    clean = parsed.path
    if PREFIX and (clean == PREFIX or clean.startswith(PREFIX + "/")):
        clean = clean[len(PREFIX):]
    clean = clean.lstrip("/")
    if not clean:
        return DIST / "index.html"
    target = DIST / clean
    if target.is_dir() or clean.endswith("/"):
        target = target / "index.html"
    return target


def main() -> int:
    pages = sorted(DIST.rglob("*.html"))
    if not pages:
        print("No HTML found in", DIST)
        return 1

    global PREFIX
    first = (DIST / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<link rel="canonical" href="(https://[^"]+)"', first)
    if match:
        PREFIX = urlparse(match.group(1)).path.rstrip("/")

    titles: dict[str, str] = {}
    descs: dict[str, str] = {}
    canonicals: set[str] = set()

    for path in pages:
        rel = path.relative_to(DIST).as_posix()
        raw = path.read_text(encoding="utf-8")
        if "{{" in raw:
            problems.append(f"{rel}: unreplaced template placeholder")

        parser = Page()
        parser.feed(raw)
        parser.close()

        if parser.lang != "en":
            problems.append(f"{rel}: html lang is {parser.lang!r}")
        if not parser.title.strip():
            problems.append(f"{rel}: missing <title>")
        if not parser.description:
            problems.append(f"{rel}: missing meta description")
        if not parser.canonical:
            problems.append(f"{rel}: missing canonical")
        else:
            canonicals.add(parser.canonical)

        if parser.title in titles and rel != "404.html":
            problems.append(f"{rel}: duplicate title with {titles[parser.title]}")
        titles.setdefault(parser.title, rel)
        if parser.description:
            if parser.description in descs and rel != "404.html":
                problems.append(f"{rel}: duplicate meta description")
            descs.setdefault(parser.description, rel)

        if len(parser.ids) != len(set(parser.ids)):
            problems.append(f"{rel}: duplicate id attributes")

        h1s = [h for h in parser.headings if h[0] == 1]
        if rel != "404.html" and len(h1s) != 1:
            problems.append(f"{rel}: expected 1 h1, found {len(h1s)}")

        last = 0
        for level, text in parser.headings:
            if last and level > last + 1:
                problems.append(f"{rel}: heading jump h{last} -> h{level} ({text[:40]!r})")
            last = level

        for img, alt in parser.imgs:
            if not alt:
                problems.append(f"{rel}: image without alt ({img})")
            elif img and not img.startswith(("http://", "https://", "data:")):
                if not rel_to_file(img).exists():
                    problems.append(f"{rel}: missing image {img}")

        for link in parser.links:
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if link.startswith("//"):
                continue
            target = rel_to_file(link)
            if not target.exists():
                problems.append(f"{rel}: broken internal link {link}")

        for block in parser.jsonld:
            try:
                data = json.loads(block)
            except json.JSONDecodeError as exc:
                problems.append(f"{rel}: invalid JSON-LD ({exc})")
                continue
            types = [item.get("@type") for item in data.get("@graph", [])]
            if not types:
                problems.append(f"{rel}: JSON-LD without @graph types")
            if rel == "index.html" and "FAQPage" not in types:
                problems.append(f"{rel}: homepage is missing FAQPage schema")

    sitemap = DIST / "sitemap.xml"
    if not sitemap.exists():
        problems.append("missing sitemap.xml")
    else:
        xml = sitemap.read_text(encoding="utf-8")
        locs = re.findall(r"<loc>(.*?)</loc>", xml)
        if len(locs) != len([p for p in pages if p.name != "404.html"]):
            problems.append(f"sitemap has {len(locs)} URLs for {len(pages) - 1} indexable pages")
        if any(not loc.startswith("https://") for loc in locs):
            problems.append("sitemap contains a non-https URL")
        if set(locs) != {c for c in canonicals if not c.endswith("/404.html")}:
            problems.append("sitemap URLs do not match page canonicals")

    robots = DIST / "robots.txt"
    if not robots.exists() or "Sitemap:" not in robots.read_text(encoding="utf-8"):
        problems.append("robots.txt missing or has no Sitemap line")

    notes.append(f"{len(pages)} HTML pages")
    notes.append(f"{len(canonicals)} canonicals")
    notes.append(f"{sum(1 for p in pages if 'og:' in p.read_text(encoding='utf-8'))} pages with OG tags")

    for note in notes:
        print("  " + note)
    if problems:
        print("\nFAIL")
        for item in problems:
            print("  - " + item)
        return 1
    print("\nOK — no problems found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
