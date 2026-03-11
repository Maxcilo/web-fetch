#!/usr/bin/env python3
"""
Web Fetch Enhanced - 增强版网页抓取工具
支持保存 MD 文件、AI 处理、Telegram 推送
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
from web_fetch import smart_fetch

class Article:
    """文章数据结构"""
    
    def __init__(self, url: str, content: str, method: str):
        self.url = url
        self.content = content
        self.method = method
        self.timestamp = datetime.now().isoformat()
        self.title = self._extract_title(content)
        
    def _extract_title(self, content: str) -> str:
        """从内容中提取标题"""
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                return line[:100]  # 取前100个字符作为标题
            elif line.startswith('# '):
                return line[2:].strip()
        return "无标题"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "method": self.method,
            "timestamp": self.timestamp
        }
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        return f"""# {self.title}

**URL:** {self.url}  
**抓取时间:** {self.timestamp}  
**抓取方案:** {self.method}

---

{self.content}

---

*由 Web Fetch 抓取 | 作者: [@Go8888I](https://twitter.com/Go8888I)*
"""
    
    def save_to_file(self, output_dir: str = "/root/.openclaw/media/outbound") -> str:
        """保存为 MD 文件"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in self.title if c.isalnum() or c in (' ', '-', '_'))[:50]
        filename = f"article_{timestamp}_{safe_title}.md"
        filepath = Path(output_dir) / filename
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_markdown())
        
        return str(filepath)


def fetch_and_save(url: str, max_chars: int = 30000) -> Tuple[Optional[Article], Optional[str]]:
    """
    抓取文章并保存
    
    Returns:
        (Article, filepath) 或 (None, error_message)
    """
    # 抓取内容
    content, method = smart_fetch(url, max_chars)
    
    if not content:
        return None, f"抓取失败: {method}"
    
    # 创建文章对象
    article = Article(url, content, method)
    
    # 保存文件
    try:
        filepath = article.save_to_file()
        return article, filepath
    except Exception as e:
        return article, f"保存失败: {str(e)}"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 web_fetch_enhanced.py <url> [max_chars]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    
    print(f"🔍 正在抓取: {url}", file=sys.stderr)
    
    # 抓取并保存
    article, result = fetch_and_save(url, max_chars)
    
    if not article:
        print(f"❌ {result}", file=sys.stderr)
        sys.exit(1)
    
    # 输出到终端（AI 处理区域）
    print(f"\n✅ 抓取成功！", file=sys.stderr)
    print(f"📄 标题: {article.title}", file=sys.stderr)
    print(f"📁 文件: {result}", file=sys.stderr)
    print(f"🔧 方案: {article.method}", file=sys.stderr)
    
    # 发送文件到 Telegram（通过 MEDIA 标签）
    print(f"\nMEDIA:{result}")
    
    # 输出文章信息供 AI 处理
    print(f"\n--- 文章信息 ---")
    print(f"标题: {article.title}")
    print(f"URL: {article.url}")
    print(f"抓取时间: {article.timestamp}")
    print(f"抓取方案: {article.method}")
    print(f"内容长度: {len(article.content)} 字符")
    print(f"\n--- 内容预览（前 500 字符）---")
    print(article.content[:500])
    print(f"\n--- 完整内容已保存到文件 ---")


if __name__ == "__main__":
    main()
