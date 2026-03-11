#!/usr/bin/env python3
"""
Scrapling 网页抓取工具
用法: python3 scrapling_fetch.py <url> [maxChars]
"""

import sys
import html2text
from scrapling import Fetcher

def fetch_article(url, max_chars=30000):
    """
    使用 Scrapling 抓取网页并转换为 Markdown
    
    Args:
        url: 目标 URL
        max_chars: 最大字符数（默认 30000）
    
    Returns:
        (markdown_content, title) 元组
    """
    try:
        # 使用 Fetcher 抓取
        response = Fetcher.get(url)
        
        # 提取标题
        title = "无标题"
        try:
            # 尝试从 meta 标签提取
            meta_title = response.css('meta[property="og:title"]')
            if meta_title:
                title = meta_title[0].attrib.get('content', '').strip()
            
            # 如果没有，尝试 title 标签
            if not title or title == "无标题":
                title_elem = response.css('title')
                if title_elem:
                    title = title_elem[0].text.strip() if hasattr(title_elem[0], 'text') else ''
            
            # 如果还是没有，尝试 h1
            if not title or title == "无标题":
                h1_elem = response.css('h1')
                if h1_elem:
                    title = h1_elem[0].text.strip() if hasattr(h1_elem[0], 'text') else ''
        except:
            pass
        
        # 按优先级尝试正文选择器
        selectors = [
            '#js_content',  # 微信公众号
            'article',
            'main',
            '.post-content',
            '[class*="content"]',
            '[class*="body"]',
            '[class*="article"]',
            '[id*="content"]',
            '[id*="article"]',
            'body'
        ]
        
        element = None
        for selector in selectors:
            try:
                elements = response.css(selector)
                if elements:
                    element = elements[0]
                    break
            except:
                continue
        
        if not element:
            # 直接使用整个响应
            element = response
        
        # 获取 HTML 内容
        if hasattr(element, 'html_content'):
            html_content = element.html_content
        elif hasattr(element, 'html'):
            html_content = element.html
        else:
            html_content = str(element.body) if hasattr(element, 'body') else str(element)
        
        # 转换为字符串（处理 TextHandler 等特殊类型）
        html_content = str(html_content)
        
        # 如果是 bytes，转换为字符串
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')
        
        # 修复微信图片：将 data-src 转换为 src
        import re
        html_content = re.sub(
            r'<img([^>]*?)data-src="([^"]+)"([^>]*?)>',
            r'<img\1src="\2"\3>',
            html_content
        )
        
        # 使用 html2text 转换为 Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # 不自动折行
        h.ignore_emphasis = False
        
        markdown = h.handle(html_content)
        
        # 截断到指定字符数
        if len(markdown) > max_chars:
            markdown = markdown[:max_chars] + "\n\n...(内容已截断)"
        
        return markdown, title
        
    except Exception as e:
        return f"❌ 抓取失败: {str(e)}", "错误"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 scrapling_fetch.py <url> [maxChars]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    
    result, title = fetch_article(url, max_chars)
    print(f"标题: {title}")
    print(result)
