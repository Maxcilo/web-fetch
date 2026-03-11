#!/usr/bin/env python3
"""
Web Fetch with PDF - 带 PDF 生成的网页抓取工具
同时生成 Markdown 和 PDF 文件
"""

import sys
import os
from pathlib import Path
from weasyprint import HTML, CSS
from markdown import markdown
from web_fetch_embedded import fetch_with_embedded_images, Article

def markdown_to_pdf(markdown_content: str, output_path: str, title: str = "Article") -> bool:
    """
    将 Markdown 转换为 PDF
    
    Args:
        markdown_content: Markdown 内容
        output_path: PDF 输出路径
        title: 文档标题
        
    Returns:
        成功返回 True，失败返回 False
    """
    try:
        # 转换 Markdown 到 HTML
        html_content = markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )
        
        # 添加 CSS 样式
        css_style = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: "Noto Sans CJK SC", "Microsoft YaHei", "SimHei", sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
        }
        
        h1 {
            font-size: 24pt;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 20px;
        }
        
        h2 {
            font-size: 20pt;
            color: #34495e;
            margin-top: 18px;
        }
        
        h3 {
            font-size: 16pt;
            color: #7f8c8d;
            margin-top: 15px;
        }
        
        p {
            margin: 10px 0;
            text-align: justify;
        }
        
        img {
            max-width: 100%;
            max-height: 800px;
            height: auto;
            display: block;
            margin: 15px auto;
            page-break-inside: avoid;
        }
        
        code {
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }
        
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 15px 0;
            color: #7f8c8d;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #3498db;
            color: white;
        }
        
        a {
            color: #3498db;
            text-decoration: none;
        }
        """
        
        # 完整的 HTML 文档
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 生成 PDF
        HTML(string=full_html).write_pdf(
            output_path,
            stylesheets=[CSS(string=css_style)]
        )
        
        return True
        
    except Exception as e:
        print(f"⚠️ PDF 生成失败: {e}", file=sys.stderr)
        return False

def fetch_with_pdf(url: str, max_chars: int = 30000):
    """
    抓取文章并生成 Markdown + PDF
    
    Returns:
        (Article, md_path, pdf_path) 或 (None, error, None)
    """
    # 1. 抓取文章
    print("🔍 正在抓取文章...", file=sys.stderr)
    article, md_path = fetch_with_embedded_images(url, max_chars)
    
    if not article:
        return None, md_path, None
    
    # 2. 生成 PDF
    print("📄 正在生成 PDF...", file=sys.stderr)
    pdf_path = md_path.replace('.md', '.pdf')
    
    success = markdown_to_pdf(article.content, pdf_path, article.title)
    
    if success:
        pdf_size = os.path.getsize(pdf_path) / 1024  # KB
        print(f"✅ PDF 生成成功（{pdf_size:.1f} KB）", file=sys.stderr)
    else:
        pdf_path = None
    
    return article, md_path, pdf_path

def main():
    if len(sys.argv) < 2:
        print("用法: python3 web_fetch_pdf.py <url> [max_chars]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    
    print(f"🔍 正在抓取: {url}", file=sys.stderr)
    
    # 抓取并生成 PDF
    article, md_path, pdf_path = fetch_with_pdf(url, max_chars)
    
    if not article:
        print(f"❌ {md_path}", file=sys.stderr)
        sys.exit(1)
    
    # 检查是否有图片
    has_images = '![](data:image/' in article.content
    
    # 输出结果
    print(f"\n✅ 抓取成功！", file=sys.stderr)
    print(f"📄 标题: {article.title}", file=sys.stderr)
    print(f"📁 Markdown: {md_path}", file=sys.stderr)
    
    if pdf_path:
        print(f"📕 PDF: {pdf_path}", file=sys.stderr)
    
    print(f"🔧 方案: {article.method}", file=sys.stderr)
    
    # 提示用户可选版本
    if has_images:
        print(f"\n💡 提示: 当前使用图片嵌入版本（文件较大）", file=sys.stderr)
        print(f"   如需不含图片的版本，请使用: web_fetch_enhanced.py", file=sys.stderr)
    
    # 发送 Markdown 文件到 Telegram
    print(f"\nMEDIA:{md_path}")
    
    # 发送 PDF 文件到 Telegram
    if pdf_path:
        print(f"MEDIA:{pdf_path}")
    
    # 输出文章信息
    print(f"\n--- 文章信息 ---")
    print(f"标题: {article.title}")
    print(f"URL: {article.url}")
    print(f"抓取时间: {article.timestamp}")
    print(f"抓取方案: {article.method}")
    print(f"Markdown: {md_path}")
    if pdf_path:
        print(f"PDF: {pdf_path}")
    
    print(f"\n--- 内容预览（前 500 字符）---")
    print(article.content[:500])
    print(f"\n--- 完整内容已保存到文件 ---")

if __name__ == "__main__":
    main()
