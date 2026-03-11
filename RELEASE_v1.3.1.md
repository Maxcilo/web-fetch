# Web Fetch v1.3.1 - 标题提取修复

## 🐛 Bug Fixes

### 修复微信文章标题提取问题
- **问题：** 微信文章标题被错误提取为图片链接
- **原因：** 标题提取逻辑从内容第一行提取，而微信文章第一行可能是图片
- **修复：** 从 HTML meta 标签 `og:title` 提取标题
- **效果：** 文件名从 `httpsmmbizqpiccn...` 变为 `游戏DAU刚破9000万...`

### 改进标题提取逻辑
- ✅ 优先从 Scrapling 返回的标题行提取（`标题: ...`）
- ✅ 跳过图片 Markdown 语法 `![](...)` 
- ✅ 跳过空行
- ✅ 支持 Markdown 标题 `# ...`
- ✅ 支持普通文本标题

## 🔧 Technical Changes

### Scrapling 返回格式变更
```python
# 修复前
content = fetch_article(url)

# 修复后
content, title = fetch_article(url)
```

### 标题提取来源
1. `meta[property="og:title"]` - 微信公众号、推特等
2. `<title>` 标签 - 普通网页
3. `<h1>` 标签 - 备用方案

## ✅ Testing

### 测试用例
- **URL:** https://mp.weixin.qq.com/s/xP9981TcTxmscx3xySbc9A
- **标题：** 游戏DAU刚破9000万，他们做的短剧也爆了？全网播放量超3.3亿
- **图片：** 41 张（包含 3 个 GIF）
- **PDF：** 13 MB
- **Markdown：** 44 MB

### 修复前后对比
| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| 标题 | `![](https://mmbiz.qpic.cn/...` | `游戏DAU刚破9000万...` |
| 文件名 | `article_..._httpsmmbizqpiccn...` | `article_..._游戏DAU刚破9000万...` |
| 可读性 | ❌ 无法识别 | ✅ 清晰易读 |

## 📦 Installation

```bash
# 克隆仓库
git clone https://github.com/Maxcilo/web-fetch.git
cd web-fetch

# 安装依赖
pip install scrapling html2text curl-cffi browserforge
pip install weasyprint markdown Pillow

# 使用
python3 web_fetch_pdf.py <url>
```

## 🚀 Usage

```bash
# 抓取微信文章（自动提取正确标题）
python3 web_fetch_pdf.py "https://mp.weixin.qq.com/s/xxxxx"

# 生成文件：
# - article_20260311_221253_游戏DAU刚破9000万....md
# - article_20260311_221253_游戏DAU刚破9000万....pdf
```

## 📝 Changelog

### v1.3.1 (2026-03-11)
- 🐛 修复微信文章标题提取
- 🔧 改进标题提取逻辑
- ✅ 文件名使用正确的中文标题

### v1.3.0 (2026-03-11)
- 📕 PDF 生成功能
- 🎨 美化样式
- 🖼️ 图片适配

### v1.2.0 (2026-03-11)
- 📷 图片下载
- 🖼️ Base64 嵌入

### v1.1.0 (2026-03-11)
- 💾 自动保存
- 📤 Telegram 集成

### v1.0.0 (2026-03-11)
- 🎯 智能路由
- 📱 微信公众号支持
- 🐦 推特支持

## 🙏 Credits

**作者：** [@Go8888I](https://twitter.com/Go8888I)  
**仓库：** https://github.com/Maxcilo/web-fetch  
**代码质量：** 9.3/10 ⭐⭐⭐⭐⭐

---

**Full Changelog:** https://github.com/Maxcilo/web-fetch/compare/v1.3.0...v1.3.1
