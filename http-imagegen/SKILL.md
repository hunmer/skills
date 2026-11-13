---
name: http-imagegen
description: Generate and edit raster images through an OpenAI-compatible HTTP image endpoint using IMAGEGEN_OPENAI_API_KEY and IMAGEGEN_OPENAI_BASE_URL. Use when image generation must bypass the built-in image tool or SDK, especially with custom proxies such as api.hyhawang.com, gpt-image-2 / gpt-image-2.5 / gpt-image-2.6 variants, gemini-3-pro-image-preview, gemini-nano-banana-2.1, synchronous generations, or image edits.
---

# HTTP Imagegen

Use the bundled `scripts/imagegen_http.py` for every request. It uses Python's
standard library and sends requests directly to `/v1/images/generations` or
`/v1/images/edits`, avoiding SDK-specific behavior and streaming issues.

## Credentials

Read `IMAGEGEN_OPENAI_API_KEY` and `IMAGEGEN_OPENAI_BASE_URL` from the
environment. Never print or request the key value. If the base URL has no
`/v1` suffix, the script adds it. The endpoint must accept OpenAI-compatible
image requests and the selected model, normally `gpt-image-2`.

## Generate

```powershell
python scripts/imagegen_http.py generate `
  --prompt "A clean product photo of a ceramic mug, no text" `
  --size 1024x1024 `
  --out outputs/mug.png
```

The script accepts JSON responses containing `data[0].b64_json`, a data URI,
or `data[0].url`, and writes decoded image bytes to the requested path.

## Edit

```powershell
python scripts/imagegen_http.py edit `
  --image input.png `
  --prompt "Replace only the background with a studio wall" `
  --out outputs/edited.png
```

Edits use multipart form data and preserve the input image as an explicit
reference. State invariants in the prompt (for example, "change only the
background; keep the subject unchanged").

### Multiple reference images

Pass `--image` more than once to upload multiple references in one edit
request. Images keep their command-line order and can be addressed in the
prompt as `#1`, `#2`, and so on. Give every reference one explicit role so the
model does not blend unrelated layout, subject, and style cues.

```powershell
python scripts/imagegen_http.py edit `
  --image structure-reference.png `
  --image style-reference.png `
  --prompt "#1 controls composition and proportions. #2 controls palette and rendering style." `
  --out outputs/edited.png
```

For style transfer, state what must come from each numbered reference and what
must not be copied. Do not combine references into a contact sheet when the
endpoint supports multiple images; direct numbered references preserve the
relationship more reliably.

## Models

Supported models (pass via `--model`; default is `gpt-image-2`):

- `gpt-image-2` (default)
- `gpt-image-2.5-flare`
- `gpt-image-2.5-sunburst`
- `gpt-image-2.6`
- `gpt-image-2.6-flare`
- `gpt-image-2.6-sunburst`
- `gemini-3-pro-image-preview`
- `gemini-nano-banana-2.1`

The script rejects any model not in this list, so typos fail fast before a
network request. Gemini models follow the same OpenAI-compatible image
endpoint contract.

## Diagnostics

Use `--dry-run` to inspect the normalized endpoint, model, payload, and output
path without making a network request. For a server rejection, the script
prints the HTTP status and response body without exposing authorization data.
Do not silently switch models or endpoints after a permission error; report the
service response and verify account/model access.

## Constraints

- Default model is `gpt-image-2`; `--model` accepts the models listed above.
- Use synchronous endpoints by default. Async image tasks require provider-side object storage and polling, which this skill does not implement.
- Keep generated assets in the user-requested location; otherwise use `outputs/`.
- Keep prompts original and avoid requesting exact copyrighted characters, logos, or game UI.
