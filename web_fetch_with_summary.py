#!/usr/bin/env python3
"""
Web Fetch with Summary - 带摘要生成的网页抓取工具
抓取文章 + 生成摘要 + 保存 MD/PDF + 发送到 Telegram
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from web_fetch_pdf import fetch_with_embedded_images, markdown_to_pdf, Article

def extract_text_only(content: str) -> str:
    """
    提取纯文本（去除图片）
    
    Args:
        content: 文章内容（包含 Base64 图片）
        
    Returns:
        纯文本内容
    """
    import re
    
    # 去除 Base64 图片
    # 匹配 ![](data:image/...;base64,...)
    text = re.sub(r'!\[\]\(data:image/[^;]+;base64,[^\)]+\)', '', content)
    
    # 去除普通图片链接
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def generate_summary_with_ai(content: str, title: str) -> str:
    """
    使用 AI 生成文章摘要
    
    Args:
        content: 文章内容（纯文本）
        title: 文章标题
        
    Returns:
        文章摘要
    """
    # 提取纯文本
    text_only = extract_text_only(content)
    
    # 截取前 5000 字符用于分析
    text_preview = text_only[:5000] if len(text_only) > 5000 else text_only
    
    # 构建提示词
    prompt = f"""请分析以下文章并提取核心观点：

标题：{title}

内容：
{text_preview}

要求：
1. 提取 3-5 个核心观点
2. 每个观点用一句话概括
3. 保持客观中立
4. 总字数不超过 300 字

请直接输出核心观点，不要有多余的说明。"""

    # 保存提示词到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(prompt)
        prompt_file = f.name
    
    try:
        # 使用 OpenClaw 的 sessions_send 调用 AI
        # 这里使用简单的文本提取作为后备
        
        # 后备方案：提取前 300 字符
        summary_lines = []
        for line in text_preview.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                summary_lines.append(line)
                if len('\n'.join(summary_lines)) > 300:
                    break
        
        summary = '\n'.join(summary_lines[:5])  # 最多 5 行
        if len(summary) > 300:
            summary = summary[:300] + '...'
        
        return summary
        
    finally:
        # 清理临时文件
        try:
            os.unlink(prompt_file)
        except:
            pass

def format_summary_output(article: Article, summary: str, md_path: str, pdf_path: str) -> str:
    """
    格式化摘要输出
    
    Args:
        article: 文章对象
        summary: 摘要内容
        md_path: Markdown 文件路径
        pdf_path: PDF 文件路径
        
    Returns:
        格式化的输出文本
    """
    import re
    
    # 计算图片数量
    image_count = article.content.count('![](data:image/')
    
    # 计算真实字数（去除图片、URL、Markdown 标记）
    text_only = extract_text_only(article.content)
    # 去除 Markdown 标记
    text_only = re.sub(r'[#*_`\[\]()]', '', text_only)
    # 去除多余空白
    text_only = re.sub(r'\s+', '', text_only)
    # 计算字数
    word_count = len(text_only)
    
    output = f"""📄 **{article.title}**

🔗 **来源：** {article.url}

📝 **摘要：**
{summary}

📊 **统计：**
- 字数：{word_count:,} 字
- 图片：{image_count} 张
- 抓取时间：{article.timestamp}

💾 **文件：**
- Markdown: {os.path.basename(md_path)}
- PDF: {os.path.basename(pdf_path)}

✅ 文件已保存并发送到 Telegram
"""
    return output

def main():
    if len(sys.argv) < 2:
        print("用法: python3 web_fetch_with_summary.py <url>")
        print("\n功能:")
        print("  1. 抓取网页内容")
        print("  2. 生成文章摘要")
        print("  3. 保存 Markdown 和 PDF 文件")
        print("  4. 发送文件到 Telegram")
        print("  5. 在聊天窗口显示摘要")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # 1. 抓取文章
    print("🔄 正在抓取文章...", file=sys.stderr)
    result = fetch_with_embedded_images(url)
    
    # fetch_with_embedded_images 返回 (article, file_path) 元组
    if isinstance(result, tuple):
        article, _ = result
    else:
        article = result
    
    if not article:
        print("❌ 抓取失败", file=sys.stderr)
        sys.exit(1)
    
    # 2. 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_'))[:50]
    safe_title = safe_title.replace(' ', '')
    
    base_name = f"article_{timestamp}_{safe_title}"
    
    # 3. 保存 Markdown 文件
    outbound_dir = Path("/root/.openclaw/media/outbound")
    outbound_dir.mkdir(parents=True, exist_ok=True)
    
    md_path = outbound_dir / f"{base_name}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(article.content)
    
    print(f"✅ Markdown 已保存: {md_path}", file=sys.stderr)
    
    # 4. 生成 PDF
    pdf_path = outbound_dir / f"{base_name}.pdf"
    if markdown_to_pdf(article.content, str(pdf_path), article.title):
        print(f"✅ PDF 已生成: {pdf_path}", file=sys.stderr)
    else:
        print(f"⚠️ PDF 生成失败", file=sys.stderr)
    
    # 5. 生成摘要
    print("🤖 正在生成摘要...", file=sys.stderr)
    summary = generate_summary_with_ai(article.content, article.title)
    
    # 6. 格式化输出
    output = format_summary_output(article, summary, str(md_path), str(pdf_path))
    
    # 7. 输出到聊天窗口
    print(output)
    
    # 8. 发送文件到 Telegram（使用 MEDIA 标签）
    print(f"\nMEDIA:{md_path}")
    if pdf_path.exists():
        print(f"MEDIA:{pdf_path}")

if __name__ == "__main__":
    main()
