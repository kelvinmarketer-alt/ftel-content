"""SEO checks for article drafts. Errors block publishing; warnings are advisory."""
import re

TITLE_MIN, TITLE_MAX = 30, 65
META_MIN, META_MAX = 120, 160
MIN_WORDS = 600


def _strip(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)      # code blocks
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)         # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links -> text
    text = re.sub(r"[#>*_`-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def lint(meta: dict, body: str):
    errors, warnings = [], []
    title = (meta.get("title") or "").strip()
    slug = (meta.get("slug") or "").strip()
    kw = (meta.get("focus_keyword") or "").strip().lower()
    desc = (meta.get("meta_description") or "").strip()

    if not title:
        errors.append("Thiếu title")
    elif not (TITLE_MIN <= len(title) <= TITLE_MAX):
        warnings.append(f"Title {len(title)} ký tự (nên {TITLE_MIN}-{TITLE_MAX})")

    if not slug:
        errors.append("Thiếu slug")
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append("Slug phải chữ thường + gạch nối, không dấu/space")

    if not kw:
        errors.append("Thiếu focus_keyword")

    if not desc:
        errors.append("Thiếu meta_description")
    elif not (META_MIN <= len(desc) <= META_MAX):
        warnings.append(f"Meta description {len(desc)} ký tự (nên {META_MIN}-{META_MAX})")

    plain = _strip(body)
    words = plain.split()
    if len(words) < MIN_WORDS:
        errors.append(f"Bài chỉ {len(words)} từ (tối thiểu {MIN_WORDS})")

    headings = re.findall(r"^(#{1,6})\s+(.*)$", body, flags=re.M)
    h1 = [h for lvl, h in headings if len(lvl) == 1]
    h2 = [h for lvl, h in headings if len(lvl) == 2]
    if h1:
        errors.append("Không dùng H1 (#) trong body — title đã là H1")
    if not h2:
        errors.append("Cần ít nhất 1 H2 (##)")

    if kw and title and kw not in title.lower():
        warnings.append("focus_keyword không có trong title")
    if kw and desc and kw not in desc.lower():
        warnings.append("focus_keyword không có trong meta_description")
    if kw and words:
        first100 = " ".join(words[:100]).lower()
        if kw not in first100:
            warnings.append("focus_keyword không xuất hiện trong 100 từ đầu")
        if not any(kw in h.lower() for h in h2):
            warnings.append("focus_keyword không có trong H2 nào")

    links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", body)
    internal = [u for u in links if "2bkin.io.vn" in u or u.startswith("/")]
    external = [u for u in links if u.startswith("http") and "2bkin.io.vn" not in u]
    if not internal:
        warnings.append("Chưa có internal link về 2bkin.io.vn")
    if not external:
        warnings.append("Chưa có external link tới nguồn uy tín")

    for alt, src in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", body):
        if not alt.strip():
            warnings.append(f"Ảnh thiếu alt: {src}")

    return errors, warnings


if __name__ == "__main__":
    import sys, glob, frontmatter
    paths = sys.argv[1:] or glob.glob("content/posts/*.md")
    failed = 0
    for p in paths:
        post = frontmatter.load(p)
        errs, warns = lint(post.metadata, post.content)
        if errs or warns:
            print(f"\n{p}")
            for e in errs:
                print(f"  ✗ {e}")
            for w in warns:
                print(f"  ⚠ {w}")
        if errs:
            failed += 1
    if failed:
        print(f"\n{failed} bài có lỗi chặn đăng.")
        sys.exit(1)
    print("\nSEO lint OK.")
