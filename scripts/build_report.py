#!/usr/bin/env python3
"""Validate normalized WEIQ data and build a standalone HTML report."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_ROOT / "assets" / "report-template.html"


def parse_number(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric metric")
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0
    multipliers = {"w": 10_000, "万": 10_000, "k": 1_000}
    suffix = text[-1].lower()
    if suffix in multipliers:
        return int(float(text[:-1]) * multipliers[suffix])
    return int(float(text))


def clean_url(value: object, *, cover: bool = False) -> str:
    url = str(value or "").strip()
    if cover and url.startswith("http://ci.xiaohongshu.com"):
        url = "https://" + url[len("http://") :]
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def money(value: object) -> str:
    if value in (None, "", "-"):
        return "待补充"
    return f"¥{parse_number(value):,}"


def number(value: int) -> str:
    return f"{value:,}"


def validate(data: dict, allow_missing: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(data.get("profile"), dict) or not data["profile"].get("name"):
        errors.append("profile.name is required")
    if not isinstance(data.get("pricing"), dict):
        errors.append("pricing object is required")
    notes = data.get("notes")
    if not isinstance(notes, list) or not notes:
        errors.append("notes must be a non-empty list")
        return errors
    for index, note in enumerate(notes, 1):
        if not isinstance(note, dict):
            errors.append(f"notes[{index}] must be an object")
            continue
        for key in ("title", "published_at", "cover_url", "views", "likes", "saves"):
            if note.get(key) in (None, ""):
                errors.append(f"notes[{index}].{key} is required")
        if not clean_url(note.get("cover_url"), cover=True):
            errors.append(f"notes[{index}].cover_url is invalid")
        if not allow_missing:
            if not note.get("caption"):
                errors.append(f"notes[{index}].caption is required")
            if not clean_url(note.get("note_url")):
                errors.append(f"notes[{index}].note_url is required and must be HTTP(S)")
        for key in ("views", "likes", "saves"):
            try:
                parse_number(note.get(key))
            except (TypeError, ValueError):
                errors.append(f"notes[{index}].{key} is not numeric")
    return errors


def build_note_cards(notes: list[dict]) -> tuple[str, dict[str, int | float]]:
    cards: list[str] = []
    total_views = 0
    total_interactions = 0
    max_views = 0
    for index, note in enumerate(notes, 1):
        views = parse_number(note.get("views"))
        likes = parse_number(note.get("likes"))
        saves = parse_number(note.get("saves"))
        interactions = likes + saves
        rate = interactions / views * 100 if views else 0
        total_views += views
        total_interactions += interactions
        max_views = max(max_views, views)
        cover_url = clean_url(note.get("cover_url"), cover=True)
        note_url = clean_url(note.get("note_url")) or clean_url(note.get("canonical_url")) or "#"
        caption = esc(note.get("caption") or "未获取到发布文案").replace("\n", "<br>")
        cards.append(
            f"""
            <article class="note-card">
              <a class="cover-wrap" href="{esc(note_url)}" target="_blank" rel="noreferrer">
                <img src="{esc(cover_url)}" alt="{esc(note.get('title'))}封面" loading="lazy" referrerpolicy="no-referrer">
                <span>{index:02d}</span>
              </a>
              <div class="note-card-body">
                <time>{esc(note.get('published_at'))}</time>
                <h3>{esc(note.get('title'))}</h3>
                <div class="main-metric"><span>阅读</span><strong>{number(views)}</strong></div>
                <div class="metric-row"><span>点赞 <b>{number(likes)}</b></span><span>收藏 <b>{number(saves)}</b></span></div>
                <div class="metric-row footer-metric"><span>互动 <b>{number(interactions)}</b></span><span class="rate{' hot' if rate >= 8 else ''}">{rate:.2f}%</span></div>
                <details class="caption-detail"><summary>查看发布文案</summary><p>{caption}</p></details>
                <a class="source-link" href="{esc(note_url)}" target="_blank" rel="noreferrer">查看原帖 <span aria-hidden="true">↗</span></a>
              </div>
            </article>"""
        )
    count = len(notes)
    return "\n".join(cards), {
        "count": count,
        "average_views": round(total_views / count) if count else 0,
        "total_interactions": total_interactions,
        "overall_rate": total_interactions / total_views * 100 if total_views else 0,
        "max_views": max_views,
    }


def build(data: dict, output_dir: Path) -> Path:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    profile = data.get("profile", {})
    pricing = data.get("pricing", {})
    performance = data.get("performance", {})
    notes = data.get("notes", [])
    cards, summary = build_note_cards(notes)
    collected = str(data.get("collected_at") or datetime.now().astimezone().isoformat(timespec="minutes"))
    collected_label = collected.replace("T", " ")[:16]
    replacements = {
        "__PAGE_TITLE__": esc(f"{profile.get('name', '达人')}｜小红书达人数据简报"),
        "__CREATOR_NAME__": esc(profile.get("name")),
        "__CREATOR_INITIAL__": esc(str(profile.get("name") or "达")[:1]),
        "__CREATOR_META__": esc(" · ".join(filter(None, [f"小红书号 {profile.get('xhs_id')}" if profile.get('xhs_id') else "", profile.get("location", ""), f"{profile.get('followers')}粉丝" if profile.get("followers") else ""]))),
        "__CATEGORY__": esc(profile.get("category") or "小红书达人"),
        "__COLLECTED_AT__": esc(collected_label),
        "__IMAGE_PRICE__": esc(money(pricing.get("image_text"))),
        "__VIDEO_PRICE__": esc(money(pricing.get("video"))),
        "__IMAGE_CPV__": esc(performance.get("image_cpv", "-")),
        "__VIDEO_CPV__": esc(performance.get("video_cpv", "-")),
        "__LIKES_AND_SAVES__": esc(profile.get("likes_and_saves", "-")),
        "__NOTE_COUNT__": str(summary["count"]),
        "__AVERAGE_VIEWS__": number(int(summary["average_views"])),
        "__TOTAL_INTERACTIONS__": number(int(summary["total_interactions"])),
        "__OVERALL_RATE__": f"{float(summary['overall_rate']):.2f}%",
        "__MAX_VIEWS__": number(int(summary["max_views"])),
        "__NOTE_CARDS__": cards,
        "__SOURCE_URL__": esc(clean_url(data.get("source_url")) or "https://www.weiq.com/"),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    unresolved = [token for token in replacements if token in template]
    if unresolved:
        raise RuntimeError(f"unresolved template tokens: {', '.join(unresolved)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "index.html"
    output_file.write_text(template, encoding="utf-8")
    with (output_dir / "report-data.json").open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="normalized report-data.json")
    parser.add_argument("--output", type=Path, default=Path("weiq-report"), help="output directory")
    parser.add_argument("--allow-missing-details", action="store_true", help="permit missing captions or post links")
    parser.add_argument("--validate-only", action="store_true", help="validate input without generating files")
    args = parser.parse_args()

    try:
        with args.input.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 2

    errors = validate(data, args.allow_missing_details)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"validated {len(data['notes'])} notes")
    if args.validate_only:
        return 0
    try:
        output_file = build(data, args.output.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: build failed: {exc}", file=sys.stderr)
        return 2
    print(f"created {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
