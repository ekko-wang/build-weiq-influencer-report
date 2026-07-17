#!/usr/bin/env python3
"""Classify a WEIQ/Xiaohongshu URL or a plain creator name."""

from __future__ import annotations

import argparse
import json
from urllib.parse import parse_qs, urlparse


XHS_HOSTS = {"xiaohongshu.com", "www.xiaohongshu.com", "xhslink.com", "www.xhslink.com", "xhs.cn", "www.xhs.cn"}


def classify(raw: str) -> dict[str, str]:
    value = raw.strip()
    if not value:
        raise ValueError("input must not be empty")

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"input": value, "input_type": "creator_name"}

    host = parsed.netloc.lower().split(":", 1)[0]
    path = parsed.path.rstrip("/")
    if host == "weiq.com" or host.endswith(".weiq.com"):
        media_id = parse_qs(parsed.query).get("media_id", [""])[0]
        result = {"input": value, "input_type": "weiq_detail_url" if media_id else "weiq_url"}
        if media_id:
            result["media_id"] = media_id
        return result

    if host in XHS_HOSTS or host.endswith(".xiaohongshu.com"):
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 3 and parts[:2] == ["user", "profile"]:
            return {"input": value, "input_type": "xhs_profile_url", "xhs_uid": parts[2]}
        if len(parts) >= 2 and parts[0] in {"explore", "discovery"}:
            note_id = parts[-1]
            return {"input": value, "input_type": "xhs_note_url", "note_id": note_id}
        return {"input": value, "input_type": "xhs_url"}

    raise ValueError("unsupported URL; provide a WEIQ/Xiaohongshu link or a creator name")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="WEIQ/Xiaohongshu URL or creator name")
    args = parser.parse_args()
    try:
        print(json.dumps(classify(args.input), ensure_ascii=False, indent=2))
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
