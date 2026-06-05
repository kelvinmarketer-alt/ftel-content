# ftel-content — Pipeline đăng bài tự động cho ftel.net.vn

Cỗ máy nội dung SEO cho **ftel.net.vn** (WordPress, FPT Telecom). Nhân bản từ pipeline 2bkin, thêm 2 cửa chặn bắt buộc: **SEO** và **ảnh Canva**.

## Luồng (5 chặng)

```
① TẠO     → Claude viết (skill seo-article) HOẶC bạn đưa bài  →  status: draft
② SEO     → tối ưu SEO (title/meta/heading/internal link)     →  status: seo-done
③ ẢNH     → thiết kế ảnh đại diện Canva (brand FPT) + gắn vào   →  status: image-done
④ DUYỆT   → bạn đọc, gật                                        →  status: ready
⑤ ĐĂNG    → GitHub Actions tự đăng lên ftel.net.vn (REST API)   →  status: published
```

**Cửa chặn ở bước ⑤** (`scripts/publish.py`): chỉ đăng bài `status: ready` VÀ
- đạt SEO lint (`scripts/seo_lint.py`), VÀ
- **có `featured_image`** (ảnh Canva). Thiếu 1 trong 2 → bỏ qua, không đăng.

## Mỗi bài 1 file

Copy `content/_template.md` → `content/posts/ten-bai.md`, điền frontmatter + nội dung.
Ảnh để trong `content/images/`. Pipeline tự upload ảnh lên WP, set Rank Math SEO, ghi ngược `post_id`/`url`.

## Cài 1 lần

- **GitHub secrets** (Settings → Secrets → Actions): `WP_URL=https://ftel.net.vn`, `WP_USER=<user admin>`, `WP_APP_PASSWORD=<Application Password>`.
- **(Tùy chọn, để SEO sâu)** cài plugin **Rank Math** trên ftel.net.vn + thả `wp/ftel-rankmath-rest.php` vào `wp-content/mu-plugins/` (mở field rank_math_* qua REST). Không có thì bài vẫn đăng, chỉ là không set sẵn meta SEO của Rank Math.

## Lệnh

```bash
python scripts/publish.py --check   # chỉ kiểm SEO, không đăng
python scripts/publish.py           # đăng các bài status=ready
```

Cron chạy 08:00 VN mỗi ngày (`.github/workflows/publish.yml`), hoặc bấm tay ở tab Actions.
