# WEIQ and Xiaohongshu extraction reference

## WEIQ detail URL

Supported detail form:

```text
https://www.weiq.com/owner/redbook/detail.html?media_id=<MEDIA_ID>
```

If the user supplies the marketplace URL instead, search the visible marketplace by creator name and verify the exact result before opening its detail page.

## Profile and pricing fields

Collect these visible values from the detail page:

- creator name
- Xiaohongshu number and UID
- location and category
- follower count and total likes/saves
- bio when available
- image-note price and video-note price
- estimated image/video cost per read
- follower growth when available

Do not trigger WEIQ's data-refresh action unless the user explicitly requests it because refresh quotas may be consumed.

## Note-list endpoint

Open this endpoint in the same logged-in WEIQ browser session:

```text
https://www.weiq.com/owner/redbook/redbook_note_list.html?media_id=<MEDIA_ID>&business_type=
```

Expected response:

```json
{
  "code": 200,
  "total": 16,
  "data": [
    {
      "pub_date": "2026-06-30",
      "note_cover": "http://ci.xiaohongshu.com/...",
      "note_content": "note title",
      "note_url": "https://www.xiaohongshu.com/explore/note_id...",
      "note_read_count": "50,565",
      "note_like_count": "3,222",
      "note_collect_count": "1,086"
    }
  ]
}
```

`note_content` is usually the title, not the full publishing caption. The endpoint's `note_url` may contain a literal `note_id` prefix and no `xsec_token`, so it can fail when opened directly.

## Resolving captions and working links

1. Open the Xiaohongshu profile using the UID shown by WEIQ:

   ```text
   https://www.xiaohongshu.com/user/profile/<XHS_UID>
   ```

2. Match each WEIQ note to a profile card using the exact title. Preserve order from the WEIQ response.
3. Open the matched card from the profile. Read the caption block authored by the creator, including hashtags but excluding comments.
4. Capture the address-bar URL after the card opens. It should resemble:

   ```text
   https://www.xiaohongshu.com/explore/<NOTE_ID>?xsec_token=...&xsec_source=pc_user
   ```

5. Derive `canonical_url` as `https://www.xiaohongshu.com/explore/<NOTE_ID>` and store the working URL as `note_url`.
6. If a title does not match uniquely, stop and surface that note as unresolved. Never attach a different creator's post.

Use fresh page state before each click. Avoid high-frequency searches; profile-title matching is safer and more efficient.

## Normalized input schema

```json
{
  "source_url": "https://www.weiq.com/owner/redbook/detail.html?media_id=...",
  "collected_at": "2026-07-17T10:30:00+08:00",
  "profile": {
    "name": "Creator",
    "xhs_id": "123456",
    "xhs_uid": "abcdef",
    "location": "Beijing",
    "category": "Technology",
    "followers": "47w",
    "likes_and_saves": "283w",
    "bio": ""
  },
  "pricing": {
    "image_text": 25000,
    "video": 10560
  },
  "performance": {
    "image_cpv": 1.93,
    "video_cpv": 1.68,
    "follower_growth": "0.4%"
  },
  "notes": [
    {
      "title": "...",
      "published_at": "2026-06-30",
      "cover_url": "https://ci.xiaohongshu.com/...",
      "note_url": "https://www.xiaohongshu.com/explore/...?xsec_token=...",
      "canonical_url": "https://www.xiaohongshu.com/explore/...",
      "caption": "full visible caption and hashtags",
      "views": 50565,
      "likes": 3222,
      "saves": 1086
    }
  ]
}
```

Numeric fields may be numbers or comma-formatted strings. The builder normalizes both.

## Failure handling

- WEIQ login missing: ask the user to sign in in the selected browser.
- Xiaohongshu shows error code `300031`: return to the creator profile and open the note card there to obtain a valid `xsec_token`.
- CAPTCHA: pause and ask the user before solving it.
- Missing caption/link: report the unresolved titles. Use `--allow-missing-details` only with user acceptance.
- Cover hotlink fails: keep the URL in data and show a neutral placeholder in the browser; do not silently substitute another image.
