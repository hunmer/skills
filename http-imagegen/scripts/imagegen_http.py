#!/usr/bin/env python3
"""Direct OpenAI-compatible image generation and editing with stdlib only."""

import argparse
import base64
import json
import os
import pathlib
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.options |= getattr(ssl, "OP_IGNORE_UNEXPECTED_EOF", 0)
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

RETRIES = 2
RETRY_DELAY = 2


def endpoint(base_url: str, route: str) -> str:
    base = base_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return base + route


def write_result(payload: dict, out: pathlib.Path) -> str:
    items = payload.get("data") or []
    if not items:
        raise RuntimeError("Response did not contain data[0].")
    item = items[0]
    value = item.get("b64_json")
    if value:
        raw = base64.b64decode(value)
        source = "b64_json"
    else:
        url = item.get("url")
        if not url:
            raise RuntimeError("Response contained neither b64_json nor url.")
        download = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*"})
        with urllib.request.urlopen(download, timeout=300, context=SSL_CONTEXT) as response:
            raw = response.read()
        source = "url"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return source


def request(url: str, headers: dict, body: bytes) -> dict:
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", **headers}
    for attempt in range(RETRIES + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300, context=SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if (exc.code >= 500 or exc.code == 429) and attempt < RETRIES:
                print(f"HTTP {exc.code}, retrying ({attempt + 1}/{RETRIES})...", file=sys.stderr)
                time.sleep(RETRY_DELAY)
                continue
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, OSError) as exc:
            if attempt < RETRIES:
                print(f"Network error ({getattr(exc, 'reason', exc)}), retrying ({attempt + 1}/{RETRIES})...", file=sys.stderr)
                time.sleep(RETRY_DELAY)
                continue
            raise RuntimeError(f"Network error: {getattr(exc, 'reason', exc)}") from exc
    raise RuntimeError("Request failed after retries.")


def credentials() -> tuple[str, str]:
    key = os.environ.get("IMAGEGEN_OPENAI_API_KEY")
    base = os.environ.get("IMAGEGEN_OPENAI_BASE_URL")
    if not key or not base:
        raise RuntimeError("Set IMAGEGEN_OPENAI_API_KEY and IMAGEGEN_OPENAI_BASE_URL.")
    return key, base


def generate(args: argparse.Namespace) -> None:
    key, base = credentials()
    url = endpoint(base, "/images/generations")
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": args.n,
        "output_format": args.output_format,
    }
    if args.dry_run:
        print(json.dumps({"url": url, "payload": payload, "out": str(args.out)}, indent=2))
        return
    result = request(url, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json.dumps(payload).encode())
    print(f"IMAGE_SAVED={write_result(result, args.out)}:{args.out}")


def multipart(fields: dict[str, str], images: list[pathlib.Path]) -> tuple[bytes, str]:
    boundary = "----http-imagegen-" + uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks += [f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), value.encode(), b"\r\n"]
    for image in images:
        chunks += [f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="image"; filename="{image.name}"\r\nContent-Type: image/png\r\n\r\n'.encode(), image.read_bytes(), b"\r\n"]
    chunks += [f"--{boundary}--\r\n".encode()]
    return b"".join(chunks), boundary


def edit(args: argparse.Namespace) -> None:
    key, base = credentials()
    fields = {"model": args.model, "prompt": args.prompt, "size": args.size}
    body, boundary = multipart(fields, args.image)
    if args.dry_run:
        print(json.dumps({"url": endpoint(base, "/images/edits"), "fields": fields, "images": [str(image) for image in args.image], "out": str(args.out)}, indent=2))
        return
    result = request(endpoint(base, "/images/edits"), {"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"}, body)
    print(f"IMAGE_SAVED={write_result(result, args.out)}:{args.out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--model", default="gpt-image-2")
    gen.add_argument("--size", default="1024x1024")
    gen.add_argument("--quality", default="medium")
    gen.add_argument("--n", type=int, default=1)
    gen.add_argument("--output-format", default="png")
    gen.add_argument("--out", type=pathlib.Path, required=True)
    gen.add_argument("--dry-run", action="store_true")
    gen.set_defaults(func=generate)
    edit_parser = sub.add_parser("edit")
    edit_parser.add_argument("--image", type=pathlib.Path, action="append", required=True)
    edit_parser.add_argument("--prompt", required=True)
    edit_parser.add_argument("--model", default="gpt-image-2")
    edit_parser.add_argument("--size", default="1024x1024")
    edit_parser.add_argument("--out", type=pathlib.Path, required=True)
    edit_parser.add_argument("--dry-run", action="store_true")
    edit_parser.set_defaults(func=edit)
    args = parser.parse_args()
    try:
        args.func(args)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
