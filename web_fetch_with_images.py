#!/usr/bin/env python3
"""
Web Fetch with Images - 带图片下载的网页抓取工具
"""

import sys
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Optional
from web_fetch_enhanced import fetch_and_save, Article

def extract_image_urls(markdown: str, base_url: str) -> List[str]:
    """
    从 Markdown 中提取所有图片 URL
    
    Args:
        markdown: Markdown 内容
        base_url: 基础 URL（用于处理相对路径）
        
    Returns:
        图片 URL 列表
    """
    # 匹配 Markdown 图片语法：![alt](url)
    pattern = r'!\[.*?\]\((.*?)\)'
    matches = re.findall(pattern, markdown)
    
    # 处理相对路径
    image_urls = []
    for url in matches:
        # 跳过 base64 图片
        if url.startswith('data:'):
            continue
        
        # 处理相对路径
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        image_urls.append(url)
    
    return image_urls

def download_image(url: str, output_dir: Path, index: int) -> Optional[str]:
    """
    下载图片
    
    Args:
        url: 图片 URL
        output_dir: 输出目录
        index: 图片索引
        
    Returns:
        本地文件路径，失败返回 None
    """
    try:
        # 获取文件扩展名
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix
        if not ext or len(ext) > 5:
            ext = '.jpg'  # 默认扩展名
        
        # 生成文件名
        filename = f"image_{index:03d}{ext}"
        filepath = output_dir / filename
        
        # 使用 curl 下载
        cmd = [
            'curl', '-s', '-L',
            '--max-time', '30',
            '--max-redirs', '5',
            '-o', str(filepath),
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=35)
        
        if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
            return str(filepath)
        else:
            return None
            
    except Exception as e:
        print(f"⚠️ 下载图片失败 {url}: {e}", file=sys.stderr)
        return None

def update_markdown_images(markdown: str, image_mapping: dict) -> str:
    """
    更新 Markdown 中的图片路径
    
    Args:
        markdown: 原始 Markdown
        image_mapping: {原始URL: 本地路径} 映射
        
    Returns:
        更新后的 Markdown
    """
    result = markdown
    
    for original_url, local_path in image_mapping.items():
        # 只替换文件名（相对路径）
        local_filename = Path(local_path).name
        result = result.replace(f']({original_url})', f']({local_filename})')
    
    return result

def fetch_with_images(url: str, max_chars: int = 30000) -> Tuple[Optional[Article], Optional[str], Optional[Path]]:
    """
    抓取文章并下载所有图片
    
    Args:
        url: 目标 URL
        max_chars: 最大字符数
        
    Returns:
        (Article, filepath, images_dir) 或 (None, error, None)
    """
    # 1. 抓取文章
    print("🔍 正在抓取文章...", file=sys.stderr)
    article, result = fetch_and_save(url, max_chars)
    
    if not article:
        return None, result, None
    
    # 2. 提取图片 URL
    image_urls = extract_image_urls(article.content, url)
    
    if not image_urls:
        print("ℹ️ 文章中没有图片", file=sys.stderr)
        return article, result, None
    
    print(f"📷 发现 {len(image_urls)} 张图片", file=sys.stderr)
    
    # 3. 创建图片目录
    article_dir = Path(result).parent / f"{Path(result).stem}_images"
    article_dir.mkdir(exist_ok=True)
    
    # 4. 下载图片
    image_mapping = {}
    success_count = 0
    
    for i, img_url in enumerate(image_urls, 1):
        print(f"⬇️ 下载图片 {i}/{len(image_urls)}: {img_url[:60]}...", file=sys.stderr)
        local_path = download_image(img_url, article_dir, i)
        
        if local_path:
            image_mapping[img_url] = local_path
            success_count += 1
        else:
            print(f"❌ 下载失败: {img_url}", file=sys.stderr)
    
    print(f"✅ 成功下载 {success_count}/{len(image_urls)} 张图片", file=sys.stderr)
    
    # 5. 更新 Markdown
    if image_mapping:
        updated_content = update_markdown_images(article.content, image_mapping)
        article.content = updated_content
        
        # 重新保存文章（带更新的图片路径）
        with open(result, 'w', encoding='utf-8') as f:
            f.write(article.to_markdown())
    
    return article, result, article_dir

def main():
    if len(sys.argv) < 2:
        print("用法: python3 web_fetch_with_images.py <url> [max_chars]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    
    print(f"🔍 正在抓取: {url}", file=sys.stderr)
    
    # 抓取并下载图片
    article, result, images_dir = fetch_with_images(url, max_chars)
    
    if not article:
        print(f"❌ {result}", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果
    print(f"\n✅ 抓取成功！", file=sys.stderr)
    print(f"📄 标题: {article.title}", file=sys.stderr)
    print(f"📁 文件: {result}", file=sys.stderr)
    print(f"🔧 方案: {article.method}", file=sys.stderr)
    
    if images_dir:
        print(f"📷 图片目录: {images_dir}", file=sys.stderr)
        image_count = len(list(images_dir.glob('*')))
        print(f"📊 图片数量: {image_count}", file=sys.stderr)
    
    # 发送文件到 Telegram
    print(f"\nMEDIA:{result}")
    
    # 输出文章信息
    print(f"\n--- 文章信息 ---")
    print(f"标题: {article.title}")
    print(f"URL: {article.url}")
    print(f"抓取时间: {article.timestamp}")
    print(f"抓取方案: {article.method}")
    print(f"内容长度: {len(article.content)} 字符")
    
    if images_dir:
        print(f"图片目录: {images_dir}")
        print(f"图片数量: {image_count}")
    
    print(f"\n--- 内容预览（前 500 字符）---")
    print(article.content[:500])
    print(f"\n--- 完整内容已保存到文件 ---")

if __name__ == "__main__":
    main()
