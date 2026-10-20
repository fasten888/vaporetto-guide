#!/usr/bin/env python3
"""Static site builder for Vaporetto Guide.

Usage:
    python3 build.py                                   # default GitHub Pages URL
    SITE_URL=https://vaporettoguide.com BASE_PATH= python3 build.py

Every page is a content/*.html fragment wrapped by templates/base.html. Metadata,
navigation, breadcrumbs, JSON-LD and the sitemap are generated here, so a page is
never hand-wired twice.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"

SITE_NAME = "Vaporetto Guide"
SITE_URL = os.environ.get("SITE_URL", "https://fasten888.github.io").rstrip("/")
BASE_PATH = os.environ.get("BASE_PATH", "/vaporetto-guide").rstrip("/")
CUSTOM_DOMAIN = os.environ.get("CUSTOM_DOMAIN", "").strip()
SITE = f"{SITE_URL}{BASE_PATH}"

CONTACT_URL = "https://github.com/fasten888/vaporetto-guide/issues"
UPDATED_ISO = "2026-10-20"
UPDATED_HUMAN = "20 October 2026"
FARES_CHECKED = "20 October 2026"

# slug, nav label, <title>, meta description, schema kind, priority
PAGES: list[dict] = [
    {
        "slug": "",
        "file": "index.html",
        "nav": "Meaning",
        "title": "Vaporetto Meaning: What Venice's Water Bus Really Is",
        "desc": (
            "Vaporetto means \u201clittle steamer\u201d \u2014 Venice's public water bus. "
            "Definition, pronunciation, etymology, 2026 fares and how to ride it, explained plainly."
        ),
        "kind": "home",
        "priority": "1.0",
        "og": "home",
    },
    {
        "slug": "what-is-a-vaporetto",
        "crumb": "What is a vaporetto?",
        "file": "what-is-a-vaporetto.html",
        "nav": "Water bus",
        "title": "What Is a Vaporetto? Venice's Water Bus, Explained",
        "desc": (
            "A vaporetto is Venice's scheduled public boat: who runs it, how the network works, "
            "what the boats are like and how they differ from gondolas and water taxis."
        ),
        "kind": "article",
        "priority": "0.9",
        "og": "what-is-a-vaporetto",
    },
    {
        "slug": "pronunciation",
        "crumb": "Pronunciation",
        "file": "pronunciation.html",
        "nav": "Pronounce",
        "title": "How to Pronounce Vaporetto: IPA, Syllables, Audio Tips",
        "desc": (
            "Say vaporetto correctly: English IPA /\u02ccv\u00e6p\u0259\u02c8r\u025bto\u028a/, "
            "Italian [vapo\u02c8retto], stress on the third syllable, plus the mistakes to avoid."
        ),
        "kind": "article",
        "priority": "0.8",
        "og": "pronunciation",
    },
    {
        "slug": "etymology",
        "crumb": "Etymology",
        "file": "etymology.html",
        "nav": "Origin",
        "title": "Vaporetto Etymology: Why It Means \u201cLittle Steamer\u201d",
        "desc": (
            "From Latin vapor to Italian vaporetto: how a 19th-century steam launch gave Venice's "
            "water buses a name that outlived the steam engine."
        ),
        "kind": "article",
        "priority": "0.8",
        "og": "etymology",
    },
    {
        "slug": "how-to-ride",
        "crumb": "How to ride",
        "file": "how-to-ride.html",
        "nav": "Ride",
        "title": "How to Ride the Vaporetto in Venice: Step by Step",
        "desc": (
            "First time on a Venetian water bus? Find the right line, validate your ticket, board "
            "without the crush, and avoid the mistakes that cost visitors time and money."
        ),
        "kind": "article",
        "priority": "0.9",
        "og": "how-to-ride",
    },
    {
        "slug": "tickets-and-prices",
        "crumb": "Tickets & prices",
        "file": "tickets-and-prices.html",
        "nav": "Tickets",
        "title": "Vaporetto Tickets & Prices 2026: What You'll Pay",
        "desc": (
            "ACTV vaporetto fares for 2026: \u20ac9.50 single, \u20ac25 for 24 hours, "
            "\u20ac45 for 72 hours. Pass maths, where to buy and what is not included."
        ),
        "kind": "article",
        "priority": "0.9",
        "og": "tickets-and-prices",
    },
    {
        "slug": "vaporetto-vs-gondola",
        "crumb": "Vaporetto vs gondola",
        "file": "vaporetto-vs-gondola.html",
        "nav": None,
        "title": "Vaporetto vs Gondola: Which Venice Boat Should You Take?",
        "desc": (
            "A vaporetto is public transport; a gondola is a private ride. Compare cost, duration "
            "and when each is worth it \u2014 plus the \u20ac2 traghetto shortcut."
        ),
        "kind": "article",
        "priority": "0.8",
        "og": "vaporetto-vs-gondola",
    },
    {
        "slug": "about",
        "crumb": "About",
        "file": "about.html",
        "nav": None,
        "title": "About Vaporetto Guide",
        "desc": (
            "Who publishes Vaporetto Guide, how fares and facts are checked, and how to send a "
            "correction. Independent, unaffiliated with ACTV."
        ),
        "kind": "page",
        "priority": "0.3",
        "og": "default",
    },
    {
        "slug": "contact",
        "crumb": "Contact",
        "file": "contact.html",
        "nav": None,
        "title": "Contact Vaporetto Guide",
        "desc": "Send a correction, a question or a source suggestion to the Vaporetto Guide team.",
        "kind": "page",
        "priority": "0.3",
        "og": "default",
    },
    {
        "slug": "privacy",
        "crumb": "Privacy",
        "file": "privacy.html",
        "nav": None,
        "title": "Privacy Policy",
        "desc": "What Vaporetto Guide does and does not collect: no accounts, no cookies, no analytics.",
        "kind": "page",
        "priority": "0.2",
        "og": "default",
    },
]

NAV_SLUGS = ["", "what-is-a-vaporetto", "pronunciation", "etymology", "how-to-ride", "tickets-and-prices"]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def page_url(slug: str) -> str:
    return f"{SITE}/" if not slug else f"{SITE}/{slug}/"


def render(text: str, **values: str) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def strip_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def extract_faqs(body: str) -> list[dict]:
    pattern = re.compile(
        r'<details class="faq">\s*<summary>(?P<q>.*?)</summary>\s*'
        r'<div class="faq-a">(?P<a>.*?)</div>\s*</details>',
        re.S,
    )
    faqs = []
    for match in pattern.finditer(body):
        question = strip_html(match.group("q"))
        answer = strip_html(match.group("a"))
        if question and answer:
            faqs.append({"q": question, "a": answer})
    return faqs


def breadcrumb(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": index + 1, "name": name, "item": url}
            for index, (name, url) in enumerate(items)
        ],
    }


def build_jsonld(page: dict, faqs: list[dict]) -> str:
    slug = page["slug"]
    url = page_url(slug)
    graph: list[dict] = []

    org = {
        "@type": "Organization",
        "@id": f"{SITE}/#organization",
        "name": SITE_NAME,
        "url": f"{SITE}/",
        "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/icon-512.png", "width": 512, "height": 512},
    }
    website = {
        "@type": "WebSite",
        "@id": f"{SITE}/#website",
        "url": f"{SITE}/",
        "name": SITE_NAME,
        "description": "An independent field guide to the Venetian vaporetto: what the word means, how to say it, and how to use the water bus.",
        "inLanguage": "en",
        "publisher": {"@id": f"{SITE}/#organization"},
    }
    graph.extend([org, website])

    crumbs = [("Home", f"{SITE}/")]
    if slug:
        crumbs.append((page["crumb"], url))
    graph.append(breadcrumb(crumbs))

    if page["kind"] == "home":
        graph.append(
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["desc"],
                "isPartOf": {"@id": f"{SITE}/#website"},
                "about": {"@id": f"{url}#term"},
                "inLanguage": "en",
                "dateModified": UPDATED_ISO,
            }
        )
        graph.append(
            {
                "@type": "DefinedTerm",
                "@id": f"{url}#term",
                "name": "vaporetto",
                "alternateName": "vaporetti",
                "description": (
                    "A vaporetto is a public water bus in Venice, Italy: a scheduled passenger boat "
                    "operated by ACTV. The Italian word means \u201clittle steamer\u201d."
                ),
                "inDefinedTermSet": {
                    "@type": "DefinedTermSet",
                    "name": "Venice water transport",
                    "url": f"{SITE}/what-is-a-vaporetto/",
                },
            }
        )
    elif page["kind"] == "article":
        graph.append(
            {
                "@type": "Article",
                "@id": f"{url}#article",
                "headline": page["title"],
                "description": page["desc"],
                "url": url,
                "mainEntityOfPage": {"@id": f"{url}#webpage"},
                "datePublished": "2026-10-18",
                "dateModified": UPDATED_ISO,
                "inLanguage": "en",
                "author": {"@id": f"{SITE}/#organization"},
                "publisher": {"@id": f"{SITE}/#organization"},
                "image": f"{SITE}/assets/og/{page['og']}.png",
                "isPartOf": {"@id": f"{SITE}/#website"},
            }
        )
        graph.append(
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["desc"],
                "isPartOf": {"@id": f"{SITE}/#website"},
                "inLanguage": "en",
                "dateModified": UPDATED_ISO,
            }
        )
    else:
        graph.append(
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": page["title"],
                "description": page["desc"],
                "isPartOf": {"@id": f"{SITE}/#website"},
                "inLanguage": "en",
                "dateModified": UPDATED_ISO,
            }
        )

    if faqs:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{url}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                    }
                    for item in faqs
                ],
            }
        )

    payload = {"@context": "https://schema.org", "@graph": graph}
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    return '<script type="application/ld+json">\n' + data + "\n</script>"


def build_nav(current: str) -> str:
    links = []
    for slug in NAV_SLUGS:
        page = next(item for item in PAGES if item["slug"] == slug)
        href = "{{BASE}}/" if not slug else "{{BASE}}/" + slug + "/"
        active = ' aria-current="page"' if slug == current else ""
        links.append('<a href="' + href + '"' + active + ">" + esc(page["nav"]) + "</a>")
    return "\n        ".join(links)


def build_crumbs(page: dict) -> str:
    if not page["slug"]:
        return ""
    label = page["crumb"]
    return (
        '<nav class="crumbs" aria-label="Breadcrumb">'
        '<a href="{{BASE}}/">Home</a><span aria-hidden="true">/</span>'
        '<span aria-current="page">' + esc(label) + "</span></nav>"
    )


def reading_time(body: str) -> int:
    words = len(strip_html(body).split())
    return max(2, round(words / 220))


def build_page(page: dict, base: str) -> str:
    body = (CONTENT / page["file"]).read_text(encoding="utf-8")
    faqs = extract_faqs(body)
    minutes = reading_time(body)
    slug = page["slug"]
    url = page_url(slug)
    is_root = not slug

    ctx = {
        "TITLE": esc(page["title"]),
        "DESC": esc(page["desc"]),
        "CANONICAL": url,
        "OG_IMAGE": f"{SITE}/assets/og/{page['og']}.png",
        "OG_TYPE": "website" if is_root else "article",
        "BASE": base,
        "BODY": body,
        "NAV": build_nav(slug),
        "CRUMBS": build_crumbs(page),
        "JSONLD": build_jsonld(page, faqs),
        "MINUTES": str(minutes),
        "UPDATED_HUMAN": UPDATED_HUMAN,
        "UPDATED_ISO": UPDATED_ISO,
        "FARES_CHECKED": FARES_CHECKED,
        "YEAR": "2026",
        "SITE_NAME": SITE_NAME,
        "CONTACT_URL": CONTACT_URL,
        "SITE_URL": SITE,
        "HOME": f"{SITE}/",
        "ROBOTS": "index,follow,max-image-preview:large",
    }

    shell = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    out = render(shell, **ctx)
    # Content fragments carry the same placeholders, so finish the pass over the whole page.
    for key, value in ctx.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out


def build_404(base: str) -> str:
    shell = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    body = (CONTENT / "404.html").read_text(encoding="utf-8")
    ctx = {
        "TITLE": "Page not found | Vaporetto Guide",
        "DESC": "That page is not here. Start with the meaning of vaporetto.",
        "CANONICAL": f"{SITE}/404.html",
        "OG_IMAGE": f"{SITE}/assets/og/default.png",
        "OG_TYPE": "website",
        "BASE": base,
        "BODY": body,
        "NAV": build_nav("__none__"),
        "CRUMBS": "",
        "JSONLD": "",
        "MINUTES": "1",
        "UPDATED_HUMAN": UPDATED_HUMAN,
        "UPDATED_ISO": UPDATED_ISO,
        "FARES_CHECKED": FARES_CHECKED,
        "YEAR": "2026",
        "SITE_NAME": SITE_NAME,
        "CONTACT_URL": CONTACT_URL,
        "SITE_URL": SITE,
        "HOME": f"{SITE}/",
        "ROBOTS": "noindex,follow",
    }
    out = render(shell, **ctx)
    for key, value in ctx.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out


def build_sitemap() -> str:
    entries = []
    for page in PAGES:
        entries.append(
            "  <url>\n"
            f"    <loc>{page_url(page['slug'])}</loc>\n"
            f"    <lastmod>{UPDATED_ISO}</lastmod>\n"
            f"    <changefreq>{'weekly' if page['slug'] in ('', 'tickets-and-prices') else 'monthly'}</changefreq>\n"
            f"    <priority>{page['priority']}</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    for page in PAGES:
        target = DIST / page["slug"] / "index.html" if page["slug"] else DIST / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_page(page, BASE_PATH), encoding="utf-8")

    (DIST / "404.html").write_text(build_404(BASE_PATH), encoding="utf-8")

    # Assets: copy everything, dropping the OG source template.
    shutil.copytree(ASSETS, DIST / "assets")
    for junk in (DIST / "assets" / "og" / "_template.html",):
        if junk.exists():
            junk.unlink()

    (DIST / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + f"{SITE}/sitemap.xml\n",
        encoding="utf-8",
    )
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    if CUSTOM_DOMAIN:
        (DIST / "CNAME").write_text(CUSTOM_DOMAIN + "\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n"
        "  X-Content-Type-Options: nosniff\n"
        "  X-Frame-Options: SAMEORIGIN\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Permissions-Policy: geolocation=(), microphone=(), camera=()\n\n"
        "/assets/*\n"
        "  Cache-Control: public, max-age=31536000, immutable\n",
        encoding="utf-8",
    )

    pages = len(list(DIST.rglob("*.html")))
    print(f"Built {pages} pages -> {DIST}")
    print(f"  site: {SITE}/")
    print(f"  sitemap: {SITE}/sitemap.xml")


if __name__ == "__main__":
    main()
