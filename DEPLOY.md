# 上线与域名

## 0. 当前状态

- 线上地址：`https://fasten888.github.io/vaporetto-guide/`（GitHub Pages 项目站，HTTPS）
- 目标正式域名：`vaporettoguide.com`
- 站点根路径：现在是 `/vaporetto-guide`，换上正式域名后是 `/`
- 已核实（Verisign RDAP，2026-10-20）：`vaporettoguide.com` **可注册**；
  `vaporettomeaning.com` 已被注册（Cloudflare NS），不要用精确匹配域名。

> 注意：`BASE_PATH` 决定所有站内链接、canonical 和资源路径。换域名时必须把
> `BASE_PATH` 改成空字符串重新构建，否则整站 404。

---

## 1. 买域名（约 10 分钟，约 $11/年）

推荐 **Cloudflare Registrar**（成本价、免费 WHOIS 隐私、DNS 直接托管）：

1. 登录 https://dash.cloudflare.com → **Domain Registration → Register Domains**
2. 搜索 `vaporettoguide.com`，付款（.com 约 $10–11/年）
3. 注册后域名会出现在 **Websites** 列表，DNS 由 Cloudflare 托管
4. 顺手开启 **Email Routing**，把 `hello@vaporettoguide.com` 转到常用邮箱
   （站点页脚目前用 GitHub Issue 作为联系方式，以后可换）

备选（同样先查 RDAP）：`vaporetto.guide`、`thevaporetto.com`。

---

## 2. 现在这个 GitHub Pages 站

仓库：`fasten888/vaporetto-guide`（public）。发布由 Actions 完成：

```bash
cd vaporetto-guide
git add -A
git commit -m "Launch Vaporetto Guide"
git push
```

工作流 `.github/workflows/deploy.yml` 会：

1. `SITE_URL=https://fasten888.github.io BASE_PATH=/vaporetto-guide python3 build.py`
2. `python3 tools/check_site.py`
3. 上传 `dist/` 并由 `actions/deploy-pages` 发布

第一次需要在仓库 **Settings → Pages → Build and deployment → Source** 选
**GitHub Actions**（或用 API 设置 `build_type=workflow`）。

本地检查：

```bash
./deploy.sh
python3 -m http.server 8899 --directory dist
# 打开 http://127.0.0.1:8899/vaporetto-guide/
./verify-live.sh https://fasten888.github.io/vaporetto-guide
```

---

## 3. 换成正式域名（约 15 分钟）

### 3.1 GitHub Pages 绑定

仓库 → **Settings → Pages → Custom domain** 填 `vaporettoguide.com` → Save。
GitHub 会在仓库根写入 `CNAME`，并自动申请证书。再添加 `www`。

### 3.2 Cloudflare DNS

| 类型 | 名称 | 内容 | 代理 |
|---|---|---|---|
| A | `@` | `185.199.108.153` | DNS only |
| A | `@` | `185.199.109.153` | DNS only |
| A | `@` | `185.199.110.153` | DNS only |
| A | `@` | `185.199.111.153` | DNS only |
| CNAME | `www` | `fasten888.github.io` | DNS only |

证书签发期间先关掉 Cloudflare 代理（灰云），拿到证书后再决定是否开橙云。
开启 **SSL/TLS → Always Use HTTPS**。

### 3.3 用根路径重新构建

修改两处：

1. `.github/workflows/deploy.yml`：
   ```yaml
   SITE_URL: https://vaporettoguide.com
   BASE_PATH: ""
   ```
2. `deploy.sh` 的默认值（可选，方便本地构建）。

然后 push。构建产物里 canonical、OG、sitemap、站内链接都会变成
`https://vaporettoguide.com/...`。

> 旧地址 `fasten888.github.io/vaporetto-guide/` 会失效。因为站点是新站、还没被
> 收录，直接切换即可；如果已经有外链，可在旧仓库首页放一个提示页，或在
> Cloudflare 用 Redirect Rule 把旧路径 301 到新域名（GitHub Pages 自身不支持
> 子路径级 301）。

### 3.4 验收

```bash
curl -sI https://vaporettoguide.com | head -3            # 200
curl -sI http://vaporettoguide.com | grep -i location    # 301 → https
curl -s  https://vaporettoguide.com/sitemap.xml | grep -c "<loc>"
./verify-live.sh https://vaporettoguide.com
```

---

## 4. 提交搜索引擎（约 20 分钟）

### Google Search Console

1. https://search.google.com/search-console → 添加资源 → **域名**（不是网址前缀）
2. 按提示在 Cloudflare 添加 TXT 记录验证
3. **Sitemaps** → 提交 `sitemap.xml`
4. **网址检查** → 依次请求编入索引：
   - `/`
   - `/tickets-and-prices/`
   - `/how-to-ride/`
   - `/pronunciation/`
   - `/etymology/`
   - `/what-is-a-vaporetto/`
   - `/vaporetto-vs-gondola/`

### Bing Webmaster Tools

https://www.bing.com/webmasters → 从 GSC 导入 → 确认 sitemap。

### 可选

- Cloudflare Web Analytics（无 cookie，开之前先更新 `/privacy/`）
- IndexNow（Bing 即时推送；静态站可手动提交）

---

## 5. 上线验收清单

- [ ] 首页 200，英雄图、票价表、FAQ 正常
- [ ] 7 个内容页 + about/contact/privacy 全部 200
- [ ] `/robots.txt` 里的 Sitemap 是正式域名
- [ ] `/sitemap.xml` 10 个 URL，全部 https
- [ ] 任意页面源码里 canonical / og:url / og:image 都是正式域名
- [ ] 404 返回 404 状态
- [ ] Rich Results Test 抽查首页（DefinedTerm + FAQPage）和票价页（Article + FAQPage）
- [ ] PageSpeed Insights 移动端 ≥ 95（无第三方 JS，正常应接近满分）
- [ ] 手机真机点开菜单、横向滑动票价表、点发音按钮
- [ ] GSC 里 sitemap 状态为 Success

---

## 6. 成本

| 项 | 成本 |
|---|---|
| 域名 `.com` | 约 $11/年 |
| GitHub Pages（public repo） | $0 |
| HTTPS 证书 | $0 |
| Cloudflare DNS | $0 |
| **合计** | **约 $11/年** |
