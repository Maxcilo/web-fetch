#!/usr/bin/env python3
"""
Web Fetch with Embedded Images - 图片嵌入版网页抓取工具
将图片转换为 base64 嵌入到 Markdown 中
"""

import sys
import re
import subprocess
import base64
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Optional
from web_fetch_enhanced import fetch_and_save, Article

def extract_image_urls(markdown: str, base_url: str) -> List[str]:
    """从 Markdown 中提取所有图片 URL"""
    pattern = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(pattern, markdown)
    
    image_urls = []
    for url in matches:
        if url.startswith('data:'):
            continue
        
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        image_urls.append(url)
    
    return image_urls

def download_image_to_memory(url: str) -> Optional[bytes]:
    """下载图片到内存"""
    try:
        cmd = [
            'curl', '-s', '-L',
            '--max-time', '30',
            '--max-redirs', '5',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=35)
        
        if result.returncode == 0 and result.stdout and len(result.stdout) > 0:
            return result.stdout
        else:
            return None
            
    except Exception as e:
        print(f"⚠️ 下载图片失败 {url}: {e}", file=sys.stderr)
        return None

def image_to_base64(image_data: bytes, url: str) -> str:
    """将图片转换为 base64 data URL"""
    # 根据 URL 推测 MIME 类型
    ext = Path(urlparse(url).path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
    }
    mime_type = mime_types.get(ext, 'image/jpeg')
    
    # 转换为 base64
    b64_data = base64.b64encode(image_data).decode('utf-8')
    
    return f"data:{mime_type};base64,{b64_data}"

def embed_images_in_markdown(markdown: str, base_url: str) -> Tuple[str, int, int]:
    """
    将 Markdown 中的图片转换为 base64 嵌入
    
    Returns:
        (updated_markdown, total_images, embedded_images)
    """
    image_urls = extract_image_urls(markdown, base_url)
    
    if not image_urls:
        return markdown, 0, 0
    
    print(f"📷 发现 {len(image_urls)} 张图片", file=sys.stderr)
    
    result = markdown
    embedded_count = 0
    
    for i, img_url in enumerate(image_urls, 1):
        print(f"⬇️ 下载并转换图片 {i}/{len(image_urls)}: {img_url[:60]}...", file=sys.stderr)
        
        # 下载图片
        image_data = download_image_to_memory(img_url)
        
        if image_data:
            # 转换为 base64
            base64_url = image_to_base64(image_data, img_url)
            
            # 替换 Markdown 中的 URL
            result = result.replace(f']({img_url})', f']({base64_url})')
            embedded_count += 1
            
            print(f"✅ 图片已嵌入 ({len(image_data) / 1024:.1f} KB)", file=sys.stderr)
        else:
            print(f"❌ 下载失败: {img_url}", file=sys.stderr)
    
    return result, len(image_urls), embedded_count

def fetch_with_embedded_images(url: str, max_chars: int = 30000) -> Tuple[Optional[Article], Optional[str]]:
    """
    抓取文章并嵌入图片
    
    Returns:
        (Article, filepath) 或 (None, error)
    """
    # 1. 抓取文章
    print("🔍 正在抓取文章...", file=sys.stderr)
    article, result = fetch_and_save(url, max_chars)
    
    if not article:
        return None, result
    
    # 2. 嵌入图片
    updated_content, total, embedded = embed_images_in_markdown(article.content, url)
    
    if total > 0:
        print(f"✅ 成功嵌入 {embedded}/{total} 张图片", file=sys.stderr)
        
        # 更新文章内容
        article.content = updated_content
        
        # 重新保存文章
        with open(result, 'w', encoding='utf-8') as f:
            f.write(article.to_markdown())
        
        print(f"💾 文件已更新（包含嵌入图片）", file=sys.stderr)
    else:
        print("ℹ️ 文章中没有图片", file=sys.stderr)
    
    return article, result

def main():
    if len(sys.argv) < 2:
        print("用法: python3 web_fetch_embedded.py <url> [max_chars]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    
    print(f"🔍 正在抓取: {url}", file=sys.stderr)
    
    # 抓取并嵌入图片
    article, result = fetch_with_embedded_images(url, max_chars)
    
    if not article:
        print(f"❌ {result}", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果
    print(f"\n✅ 抓取成功！", file=sys.stderr)
    print(f"📄 标题: {article.title}", file=sys.stderr)
    print(f"📁 文件: {result}", file=sys.stderr)
    print(f"🔧 方案: {article.method}", file=sys.stderr)
    
    # 发送文件到 Telegram
    print(f"\nMEDIA:{result}")
    
    # 输出文章信息
    print(f"\n--- 文章信息 ---")
    print(f"标题: {article.title}")
    print(f"URL: {article.url}")
    print(f"抓取时间: {article.timestamp}")
    print(f"抓取方案: {article.method}")
    print(f"内容长度: {len(article.content)} 字符")
    
    print(f"\n--- 内容预览（前 500 字符）---")
    print(article.content[:500])
    print(f"\n--- 完整内容（含嵌入图片）已保存到文件 ---")

if __name__ == "__main__":
    main()
