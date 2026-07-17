---
name: build-weiq-influencer-report
description: Generate a polished standalone HTML Xiaohongshu influencer report from a WEIQ creator link, Xiaohongshu profile or note link, or creator name. Resolve and verify the creator across logged-in WEIQ and Xiaohongshu, then collect current image/video pricing, profile metrics, every note shown by WEIQ, remote covers, note performance, original post links, and full publishing captions. Use when the user supplies any supported link or a blogger name and wants a local webpage or repeatable creator-report workflow.
---

# Build a WEIQ influencer report

Create a self-contained static report from the user's logged-in WEIQ and Xiaohongshu sessions. Keep account credentials and cookies out of generated files.

## Required resources

- Read [references/extraction.md](references/extraction.md) before browser collection.
- Read [references/input-routing.md](references/input-routing.md) to resolve the supplied link or name to one verified creator.
- Run [scripts/classify_input.py](scripts/classify_input.py) first when the input type is not already certain.
- Run [scripts/build_report.py](scripts/build_report.py) to validate the dataset and generate `index.html`.
- The builder uses [assets/report-template.html](assets/report-template.html); do not recreate the template unless the user asks for a new design.

## Workflow

1. Accept one of these inputs: a WEIQ creator/detail URL, a Xiaohongshu profile/note/share URL, or a creator name. Classify it and follow `references/input-routing.md`. Never guess a creator match.
2. Use the browser containing the user's existing login. If authentication is missing, ask the user to sign in there and tell you when ready.
3. Resolve a verified WEIQ detail page and Xiaohongshu profile. Confirm the identity using stable IDs when possible; otherwise use multiple visible attributes and note-title overlap.
4. Extract profile, pricing, and performance values from the WEIQ detail page. Open WEIQ's note-list endpoint in the same logged-in browser and capture its complete JSON response. Follow `references/extraction.md`.
5. Match every WEIQ note to the creator's Xiaohongshu profile by exact title. Open each profile card to obtain the visible full caption and the working address-bar URL with `xsec_token`. Do not use an unverified guessed link.
6. Write the normalized dataset as `report-data.json` in a new output directory. Do not include cookies, local storage, browser history, or unrelated account data.
7. Generate the report:

   ```bash
   python3 scripts/build_report.py report-data.json --output <output-directory>
   ```

8. Verify that `index.html` exists, the reported note count matches WEIQ's `total`, and every remote cover returns an image response. Build with `--allow-missing-details` only when the user explicitly accepts missing captions, links, or WEIQ pricing.
9. Serve locally when requested:

   ```bash
   python3 -m http.server 8000 --directory <output-directory>
   ```

10. Return the local URL and the output directory. Keep the site local unless the user asks to publish it.

## Output rules

- Use WEIQ `note_cover` URLs directly; upgrade `http://ci.xiaohongshu.com` to HTTPS.
- Preserve the creator's visible wording and hashtags. Do not rewrite captions.
- Compute interaction count as likes plus saves because WEIQ's note-list endpoint does not provide comments.
- State the collection date and data-source limitations in the report.
- Make captions collapsible and open original posts in a new tab.
- Treat `xsec_token` links as working access links that may expire; retain canonical note IDs in `report-data.json` when available.
- For a name or Xiaohongshu input, record both the original input and the resolved WEIQ detail URL in the normalized dataset.

## GitHub distribution

Keep `SKILL.md`, `agents/`, `scripts/`, `references/`, and `assets/` at the repository root. Do not commit generated creator reports, login material, cookies, or downloaded private data. A repository in this layout can be installed by passing its GitHub URL to Codex's skill installer.
