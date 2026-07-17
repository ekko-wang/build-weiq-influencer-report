# Input routing and creator verification

The workflow accepts a WEIQ URL, Xiaohongshu URL, or plain creator name. Resolve the input to exactly one WEIQ detail page and one Xiaohongshu profile before collecting the report.

## Classify the input

Use:

```bash
python3 scripts/classify_input.py "<user input>"
```

Short Xiaohongshu share links may redirect. Open them in the logged-in browser once, then classify the final address-bar URL.

## WEIQ URL

- A detail URL containing `media_id` is the strongest starting point. Read its creator name and Xiaohongshu UID, then open the corresponding Xiaohongshu profile.
- For a WEIQ marketplace/search URL, use the visible search field and the supplied or visible creator name. Open the result only after checking its name and profile attributes.

## Xiaohongshu profile URL

1. Open the profile and capture the creator name, Xiaohongshu number, UID, bio, location, follower metrics, and several recent note titles.
2. Search that exact creator name in WEIQ.
3. Prefer a WEIQ result whose Xiaohongshu UID or number matches. If stable IDs are not visible, require at least two supporting attributes plus overlapping recent note titles.
4. Continue only when one result is uniquely verified.

## Xiaohongshu note or share URL

1. Open the note in the logged-in browser and identify the author from the note header.
2. Open the author's profile rather than trusting a name copied from comments or mentions.
3. Route the verified profile through the Xiaohongshu profile procedure above.

## Creator name

1. Search the exact name in both WEIQ and Xiaohongshu.
2. Compare stable IDs first. Otherwise compare bio, location/category, profile metrics, avatar, and recent note-title overlap.
3. Minor punctuation or full-width/half-width differences are acceptable only when other attributes verify the identity.
4. If multiple plausible creators remain, present the candidates and ask the user to choose. Never silently select the first result.

## Required resolution record

Add these fields to the normalized dataset when available:

```json
{
  "input": "the original link or creator name",
  "input_type": "weiq_detail_url | weiq_url | xhs_profile_url | xhs_note_url | xhs_url | creator_name",
  "source_url": "the verified WEIQ detail URL",
  "xhs_profile_url": "the verified Xiaohongshu profile URL"
}
```

## Failure handling

- No WEIQ match: explain that current quotation data cannot be verified. Generate a content-only report only if the user accepts missing pricing.
- Ambiguous name: stop and request a choice between the visible candidates.
- Login or CAPTCHA: pause for the user; never attempt to bypass access controls.
- Deleted/private note: keep the WEIQ metrics and cover, mark the caption/link unresolved, and require user acceptance before using `--allow-missing-details`.
