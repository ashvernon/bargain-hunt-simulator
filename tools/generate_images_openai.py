from __future__ import annotations

import argparse
import base64
import json
import os
import random
import time
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from openai import OpenAI


# -----------------------------
# Helpers
# -----------------------------
def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def jitter_sleep(base: float, jitter: float = 0.25) -> None:
    time.sleep(base * (1.0 + random.uniform(-jitter, jitter)))


def safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except Exception:
        return str(path)


# -----------------------------
# OpenAI image generation
# -----------------------------
def generate_image_bytes(
    client: OpenAI,
    prompt: str,
    size: str,
    quality: str,
    background: str,
    output_format: str,
) -> bytes:
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,
        background=background,
        output_format=output_format,
    )
    b64 = response.data[0].b64_json
    return base64.b64decode(b64)


# -----------------------------
# Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate item images into assets/ using OpenAI Image API (with logging + timeouts)"
    )
    parser.add_argument("--items", default="data/items_100.jsonl", help="Input items JSONL (repo-root relative)")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--size", default="1024x1024", help="1024x1024 | 1536x1024 | 1024x1536 | auto")
    parser.add_argument("--quality", default="low", help="low|medium|high|auto")
    parser.add_argument("--background", default="transparent", help="transparent|opaque|auto")
    parser.add_argument("--format", dest="output_format", default="png", help="png|jpeg|webp")
    parser.add_argument("--sleep", type=float, default=0.3, help="Base sleep between successful requests")
    parser.add_argument("--retries", type=int, default=5, help="Retries per item (your loop, not SDK)")
    parser.add_argument("--timeout", type=float, default=60.0, help="Hard timeout (seconds) per request")
    parser.add_argument("--resume", action="store_true", help="Write progress back into items JSONL")
    parser.add_argument("--verbose", action="store_true", help="Extra logging")
    parser.add_argument("--dry-run", action="store_true", help="No API calls; just prints planned outputs")
    args = parser.parse_args()

    # Resolve repo root (assumes script is tools/)
    repo_root = Path(__file__).resolve().parents[1]

    # Load API key (repo root .env is recommended; load_dotenv() searches CWD by default)
    # This will still work if you run from repo root. If you run elsewhere, it may not find .env.
    load_dotenv(repo_root / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY missing. Put it in .env at repo root.")

    # IMPORTANT: enforce request timeout and disable SDK retries (we handle retries ourselves)
    client = OpenAI(timeout=args.timeout, max_retries=0)

    items_path = repo_root / args.items
    if not items_path.exists():
        raise SystemExit(f"Items file not found: {items_path}")

    items = read_jsonl(items_path)
    end = min(len(items), args.start + args.limit)

    processed = skipped = failed = 0

    print(f"Repo root: {repo_root}")
    print(f"Items: {items_path} (rows={len(items)})")
    print(f"Range: start={args.start} limit={args.limit} -> [{args.start}, {end})")
    print(f"Saving under assets/: {repo_root / 'assets'}")
    print("----")

    for idx in range(args.start, end):
        item = items[idx]

        prompt = item.get("prompt_image")
        rel_out = item.get("image_filename")

        if not prompt or not rel_out:
            item["image_status"] = "missing_prompt_or_filename"
            failed += 1
            print(f"[{idx}] FAIL missing prompt or image_filename", flush=True)
            continue

        out_path = repo_root / rel_out
        ensure_parent(out_path)

        if out_path.exists() and out_path.stat().st_size > 0 and not args.overwrite:
            item["image_status"] = "skipped_exists"
            skipped += 1
            if args.verbose:
                print(f"[{idx}] SKIP exists -> {safe_relpath(out_path, repo_root)}", flush=True)
            continue

        print(f"[{idx}] generating -> {safe_relpath(out_path, repo_root)}", flush=True)

        if args.dry_run:
            item["image_status"] = "dry_run"
            processed += 1
            continue

        attempt = 0
        while True:
            try:
                if args.verbose:
                    title = item.get("title", "")
                    print(f"[{idx}] prompt title: {title}", flush=True)

                img_bytes = generate_image_bytes(
                    client,
                    prompt=prompt,
                    size=args.size,
                    quality=args.quality,
                    background=args.background,
                    output_format=args.output_format,
                )

                out_path.write_bytes(img_bytes)
                item["image_status"] = "ok"
                item["image_output_format"] = args.output_format
                processed += 1
                print(f"[{idx}] saved OK", flush=True)
                break

            except Exception as e:
                attempt += 1
                print(f"[{idx}] error: {type(e).__name__}: {str(e)[:200]}", flush=True)

                if attempt > args.retries:
                    item["image_status"] = f"failed:{type(e).__name__}"
                    item["image_error"] = str(e)[:300]
                    failed += 1
                    print(f"[{idx}] FAIL after {args.retries} retries", flush=True)
                    break

                # exponential backoff + jitter
                backoff = min(60.0, (2 ** (attempt - 1)) + random.random())
                item["image_status"] = f"retrying({attempt}/{args.retries})"
                if args.verbose:
                    print(f"[{idx}] backoff {backoff:.1f}s", flush=True)
                jitter_sleep(backoff)

        # sleep between items (keeps rate limiting happier)
        jitter_sleep(args.sleep)

        # periodic progress write
        if args.resume and (processed + skipped + failed) % 10 == 0:
            write_jsonl(items_path, items)
            if args.verbose:
                print("[progress] wrote JSONL checkpoint", flush=True)

    if args.resume:
        write_jsonl(items_path, items)
        if args.verbose:
            print("[final] wrote JSONL", flush=True)

    print("----")
    print(f"Done → processed={processed}, skipped={skipped}, failed={failed}")
    print("Images saved under:", repo_root / "assets")


if __name__ == "__main__":
    main()
