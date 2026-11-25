# 澳門會展 × AI 每日精選電子報

網站：https://macau-mice-daily.chekelvin1976.workers.dev/

## 結構

- `src/` — 每期原稿，取自 Google Drive「AI-News」資料夾，檔名 `macau-mice-ai-newsletter-YYYYMMDD.html`
- `build.py` — 由 `src/` 生成 `site/`（每期頁面加導航列、往期目錄、issues.json、_redirects、404）
- `site/` — 部署內容（由 build.py 生成，勿手改）
- `wrangler.jsonc` — Cloudflare Workers 靜態資產設定

## 新增一期

```bash
cp macau-mice-ai-newsletter-YYYYMMDD.html src/
python3 build.py src site
git add -A && git commit -m "新增 YYYY-MM-DD 電子報" && git push
```

推送到 `main` 後，Cloudflare 會自動部署。

## 網址

- `/` 及 `/latest` → 最新一期
- `/YYYY/MM/DD/` → 指定一期
- `/archive/` → 往期目錄
