"""Publish 'ready' Markdown drafts to WordPress via REST API.

Env: WP_URL, WP_USER, WP_APP_PASSWORD
Flow: find status=ready posts -> SEO lint -> create WP post (+ Rank Math meta)
      -> write back post_id/url + status=published.
Use --check to lint only (no publishing).
"""
import base64
import glob
import mimetypes
import os
import sys

import frontmatter
import markdown as md
import requests

from seo_lint import lint

WP_URL = os.environ.get("WP_URL", "https://ftel.net.vn").rstrip("/")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")
API = f"{WP_URL}/wp-json/wp/v2"
TIMEOUT = 60


def auth_header():
    token = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def term_id(taxonomy: str, name: str) -> int | None:
    name = (name or "").strip()
    if not name:
        return None
    r = requests.get(f"{API}/{taxonomy}", params={"search": name}, headers=auth_header(), timeout=TIMEOUT)
    r.raise_for_status()
    for t in r.json():
        if t["name"].lower() == name.lower():
            return t["id"]
    r = requests.post(f"{API}/{taxonomy}", json={"name": name}, headers=auth_header(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["id"]


def upload_media(path_or_url: str, alt: str) -> int | None:
    if not path_or_url:
        return None
    if path_or_url.startswith("http"):
        data = requests.get(path_or_url, timeout=TIMEOUT).content
        filename = path_or_url.split("/")[-1].split("?")[0]
    else:
        with open(path_or_url, "rb") as f:
            data = f.read()
        filename = os.path.basename(path_or_url)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    headers = {**auth_header(),
               "Content-Disposition": f'attachment; filename="{filename}"',
               "Content-Type": ctype}
    r = requests.post(f"{API}/media", headers=headers, data=data, timeout=TIMEOUT)
    r.raise_for_status()
    media_id = r.json()["id"]
    if alt:
        requests.post(f"{API}/media/{media_id}", json={"alt_text": alt, "title": alt},
                      headers=auth_header(), timeout=TIMEOUT)
    return media_id


def publish_one(path: str) -> bool:
    post = frontmatter.load(path)
    meta = post.metadata
    errs, warns = lint(meta, post.content)
    for w in warns:
        print(f"  ⚠ {w}")
    if errs:
        for e in errs:
            print(f"  ✗ {e}")
        print(f"  → BỎ QUA {path} (chưa đạt SEO)")
        return False

    # GATE bắt buộc: phải có ảnh đại diện đã thiết kế (Canva) mới được đăng
    if not (meta.get("featured_image") or "").strip():
        print("  ✗ Chưa có featured_image (ảnh đại diện Canva)")
        print(f"  → BỎ QUA {path} (chưa thiết kế ảnh)")
        return False

    html = md.markdown(post.content, extensions=["extra", "sane_lists"])
    payload = {
        "title": meta["title"],
        "slug": meta["slug"],
        "content": html,
        "excerpt": meta.get("meta_description", ""),
        "status": "publish",
        "meta": {
            "rank_math_focus_keyword": meta.get("focus_keyword", ""),
            "rank_math_title": meta.get("title", ""),
            "rank_math_description": meta.get("meta_description", ""),
        },
    }

    publish_at = (meta.get("publish_at") or "").strip()
    if publish_at:
        payload["status"] = "future"
        payload["date"] = publish_at

    cat = term_id("categories", meta.get("category"))
    if cat:
        payload["categories"] = [cat]
    tag_ids = [t for t in (term_id("tags", t) for t in meta.get("tags", []) or []) if t]
    if tag_ids:
        payload["tags"] = tag_ids

    media_id = upload_media(meta.get("featured_image"), meta.get("featured_image_alt", ""))
    if media_id:
        payload["featured_media"] = media_id

    r = requests.post(f"{API}/posts", json=payload, headers=auth_header(), timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()

    meta["post_id"] = data["id"]
    meta["url"] = data["link"]
    meta["status"] = "published"
    with open(path, "wb") as f:
        frontmatter.dump(post, f)
    print(f"  ✓ Đăng: {data['link']}")
    return True


def main():
    check_only = "--check" in sys.argv
    ready = []
    for p in sorted(glob.glob("content/posts/*.md")):
        post = frontmatter.load(p)
        if str(post.metadata.get("status", "")).lower() == "ready":
            ready.append(p)

    if not ready:
        print("Không có bài status=ready.")
        return

    if check_only:
        failed = 0
        for p in ready:
            post = frontmatter.load(p)
            errs, warns = lint(post.metadata, post.content)
            if errs or warns:
                print(f"\n{p}")
                for e in errs:
                    print(f"  ✗ {e}")
                for w in warns:
                    print(f"  ⚠ {w}")
            failed += 1 if errs else 0
        sys.exit(1 if failed else 0)

    if not WP_USER or not WP_APP_PASSWORD:
        sys.exit("Thiếu WP_USER / WP_APP_PASSWORD.")

    published = 0
    for p in ready:
        print(f"\n{p}")
        if publish_one(p):
            published += 1
    print(f"\nXong: đăng {published}/{len(ready)} bài.")


if __name__ == "__main__":
    main()
