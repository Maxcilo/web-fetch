#!/usr/bin/env python3
"""
智能网页抓取工具 - 自动选择最佳方案
优先级：Scrapling > Jina Reader（节省配额）
特殊：推特必须用 Jina，微信公众号必须用 Scrapling

用法: python3 web_fetch.py <url> [maxChars]

示例：
    # 基本用法
    $ python3 web_fetch.py https://example.com
    
    # 指定最大字符数
    $ python3 web_fetch.py https://example.com 5000
    
    # Python 调用
    from web_fetch import smart_fetch
    content, method = smart_fetch("https://example.com")
    if content:
        print(f"成功抓取，使用方案：{method}")
"""

import sys
import subprocess
import time
import os
from urllib.parse import urlparse, quote
from pathlib import Path
from typing import Tuple, Optional

# 配置
def _get_int_env(key: str, default: int) -> int:
    """安全地获取整数环境变量"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

JINA_API_URL = os.getenv('JINA_API_URL', 'https://r.jina.ai')
JINA_TIMEOUT = _get_int_env('JINA_TIMEOUT', 30)
SCRAPLING_TIMEOUT = _get_int_env('SCRAPLING_TIMEOUT', 60)
MAX_RETRIES = _get_int_env('MAX_RETRIES', 2)
MIN_CONTENT_LENGTH_JINA = _get_int_env('MIN_CONTENT_LENGTH_JINA', 100)
MIN_CONTENT_LENGTH_SCRAPLING = _get_int_env('MIN_CONTENT_LENGTH_SCRAPLING', 50)
MAX_CONTENT_SIZE = _get_int_env('MAX_CONTENT_SIZE', 10 * 1024 * 1024)
ERROR_PREFIX = '❌'
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

def get_scrapling_path() -> str:
    """
    动态获取 Scrapling 脚本路径
    
    Returns:
        str: Scrapling 脚本的绝对路径
        
    Raises:
        FileNotFoundError: 如果找不到 Scrapling 脚本
    """
    # 优先使用环境变量
    env_path = os.getenv('SCRAPLING_PATH')
    if env_path:
        path = Path(env_path)
        if path.exists():
            return str(path)
    
    # 默认路径
    possible_paths = [
        Path(__file__).parent.parent / "scrapling" / "scrapling_fetch.py",
        Path.home() / ".openclaw/workspace/skills/scrapling/scrapling_fetch.py",
        Path("/root/.openclaw/workspace/skills/scrapling/scrapling_fetch.py"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    raise FileNotFoundError("找不到 Scrapling 脚本")

def is_valid_url(url: str) -> bool:
    """
    验证 URL 格式是否合法
    
    Args:
        url: 待验证的 URL
        
    Returns:
        bool: URL 是否合法
    """
    if not url or not isinstance(url, str):
        return False
    
    # 先检查长度（快速失败）
    if len(url) >= 2048:
        return False
    
    # 检查 NULL 字节（快速检查）
    if '\x00' in url:
        return False
    
    # 检查控制字符（一次遍历）
    for c in url:
        code = ord(c)
        # ASCII 控制字符（除了 \t\n\r）
        if code < 32 and c not in '\t\n\r':
            return False
        # Unicode 控制字符
        if (0x80 <= code <= 0x9F) or (0x2000 <= code <= 0x206F):
            return False
    
    # 最后解析 URL
    try:
        result = urlparse(url)
        return all([
            result.scheme in ('http', 'https'),
            result.netloc
        ])
    except (ValueError, TypeError):
        return False

def safe_quote_url(url: str) -> str:
    """
    安全地转义 URL，按组件分别处理
    
    Args:
        url: 原始 URL
        
    Returns:
        str: 转义后的 URL
    """
    try:
        parsed = urlparse(url)
        
        # 分别转义各个组件
        path = quote(parsed.path) if parsed.path else ''
        query = quote(parsed.query, safe='=&') if parsed.query else ''
        fragment = quote(parsed.fragment) if parsed.fragment else ''
        
        # 重新组装
        result = f"{parsed.scheme}://{parsed.netloc}{path}"
        if query:
            result += f"?{query}"
        if fragment:
            result += f"#{fragment}"
        
        return result
    except (ValueError, TypeError, AttributeError):
        # 如果解析失败，使用简单转义
        return quote(url, safe=':/')

def is_wechat_url(url: str) -> bool:
    """
    检查是否是微信公众号链接
    
    Args:
        url: 待检查的 URL
        
    Returns:
        bool: 是否是微信公众号链接
    """
    try:
        parsed = urlparse(url)
        return 'mp.weixin.qq.com' in parsed.netloc.lower()
    except:
        return False

def is_twitter_url(url: str) -> bool:
    """
    检查是否是推特链接（支持所有子域名）
    
    Args:
        url: 待检查的 URL
        
    Returns:
        bool: 是否是推特链接
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        # 精确匹配或子域名
        return (
            netloc in ('twitter.com', 'x.com') or
            netloc.endswith('.twitter.com') or
            netloc.endswith('.x.com')
        )
    except:
        return False

def fetch_with_jina(url: str, max_chars: int = 30000) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 Jina Reader 抓取网页内容（带重试）
    
    Args:
        url: 目标 URL
        max_chars: 最大字符数
        
    Returns:
        (content, error): 成功返回 (内容, None)，失败返回 (None, 错误信息)
    """
    url_safe = safe_quote_url(url)
    
    # 使用循环代替递归
    for retry in range(MAX_RETRIES + 1):
        try:
            # 使用列表参数避免 shell 注入
            cmd = [
                'curl', '-s', '-L',
                '--max-redirs', '5',  # 限制重定向次数
                '--max-time', str(JINA_TIMEOUT),
                f'{JINA_API_URL}/{url_safe}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=JINA_TIMEOUT + 5)
            
            if result.returncode == 0 and result.stdout:
                content = result.stdout
                
                # 检查内容大小
                if len(content) > MAX_CONTENT_SIZE:
                    return None, "Jina Reader 返回内容过大"
                
                # 检查各种错误情况
                error_indicators = [
                    ('403', 'Forbidden'),
                    ('404', 'Not Found'),
                    ('429', 'Too Many Requests'),
                    ('500', 'Internal Server Error'),
                    ('502', 'Bad Gateway'),
                    ('503', 'Service Unavailable'),
                ]
                
                for code, msg in error_indicators:
                    if code in content or msg in content:
                        # 429 可以重试（指数退避）
                        if code == '429' and retry < MAX_RETRIES:
                            delay = 2 ** retry  # 2, 4 秒
                            print(f"⚠️ Jina Reader 超限，等待 {delay} 秒后重试 {retry + 1}/{MAX_RETRIES}...", file=sys.stderr)
                            time.sleep(delay)
                            continue  # 继续下一次循环
                        return None, f"Jina Reader {msg}"
                
                # 优化：只 strip 一次
                content_stripped = content.strip()
                
                # 检查内容是否太短（可能是错误页面）
                if len(content_stripped) < MIN_CONTENT_LENGTH_JINA:
                    return None, "Jina Reader 返回内容过短"
                
                # 截断到指定字符数
                if len(content_stripped) > max_chars:
                    content_stripped = content_stripped[:max_chars] + "\n\n...(内容已截断)"
                
                return content_stripped, None
            else:
                if retry < MAX_RETRIES:
                    continue
                return None, f"Jina Reader 请求失败 (code: {result.returncode})"
                
        except subprocess.TimeoutExpired:
            if retry < MAX_RETRIES:
                continue
            return None, "Jina Reader 超时"
        except (subprocess.SubprocessError, OSError) as e:
            if DEBUG:
                return None, f"Jina Reader 错误: {str(e)}"
            return None, "Jina Reader 错误"
        except Exception as e:
            # 记录未预期的错误
            if DEBUG:
                import traceback
                traceback.print_exc(file=sys.stderr)
                return None, f"Jina Reader 未知错误: {type(e).__name__}"
            return None, "Jina Reader 未知错误"
    
    return None, "Jina Reader 重试次数耗尽"

def fetch_with_scrapling(url: str, max_chars: int = 30000) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 Scrapling 抓取网页内容
    
    Args:
        url: 目标 URL
        max_chars: 最大字符数
        
    Returns:
        (content, error): 成功返回 (内容, None)，失败返回 (None, 错误信息)
    """
    try:
        script_path = get_scrapling_path()
        
        # 使用列表参数避免 shell 注入
        cmd = ['python3', script_path, url, str(max_chars)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=SCRAPLING_TIMEOUT)
        
        if result.returncode == 0 and result.stdout:
            content = result.stdout
            
            # 检查内容大小
            if len(content) > MAX_CONTENT_SIZE:
                return None, "Scrapling 返回内容过大"
            
            # 检查是否是错误
            if content.startswith(ERROR_PREFIX):
                return None, content.strip()
            
            # 优化：只 strip 一次
            content_stripped = content.strip()
            
            # 检查内容是否太短
            if len(content_stripped) < MIN_CONTENT_LENGTH_SCRAPLING:
                return None, "Scrapling 返回内容过短"
            
            return content_stripped, None
        else:
            if DEBUG:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                return None, f"Scrapling 抓取失败: {error_msg}"
            return None, "Scrapling 抓取失败"
            
    except subprocess.TimeoutExpired:
        return None, "Scrapling 超时"
    except FileNotFoundError:
        return None, "Scrapling 脚本未找到"
    except (subprocess.SubprocessError, OSError) as e:
        if DEBUG:
            return None, f"Scrapling 错误: {str(e)}"
        return None, "Scrapling 错误"
    except Exception as e:
        if DEBUG:
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None, f"Scrapling 未知错误: {type(e).__name__}"
        return None, "Scrapling 未知错误"

def smart_fetch(url: str, max_chars: int = 30000) -> Tuple[Optional[str], Optional[str]]:
    """
    智能选择抓取方案（优先 Scrapling，节省 Jina 配额）
    
    Args:
        url: 目标 URL
        max_chars: 最大字符数（100-100000）
        
    Returns:
        (content, method): 成功返回 (内容, 方案名称)，失败返回 (None, 错误信息)
    """
    # 验证 URL 格式
    if not is_valid_url(url):
        return None, "无效的 URL（必须是合法的 http:// 或 https:// 地址）"
    
    # 验证 max_chars 范围
    if not (100 <= max_chars <= 100000):
        return None, f"maxChars 必须在 100-100000 之间（当前：{max_chars}）"
    
    # 微信公众号直接用 Scrapling（Jina 会 403）
    if is_wechat_url(url):
        print("🔍 检测到微信公众号，使用 Scrapling...", file=sys.stderr)
        content, error = fetch_with_scrapling(url, max_chars)
        if content:
            return content, "Scrapling"
        else:
            return None, f"Scrapling 失败: {error}"
    
    # 推特必须用 Jina（Scrapling 抓不到）
    if is_twitter_url(url):
        print("🔍 检测到推特链接，使用 Jina Reader...", file=sys.stderr)
        content, error = fetch_with_jina(url, max_chars)
        if content:
            return content, "Jina Reader"
        else:
            return None, f"Jina Reader 失败: {error}"
    
    # 其他网站：优先 Scrapling（节省 Jina 配额），失败后用 Jina
    print("🔍 使用 Scrapling...", file=sys.stderr)
    content, error = fetch_with_scrapling(url, max_chars)
    
    if content:
        return content, "Scrapling"
    
    print(f"⚠️ Scrapling 失败 ({error})，尝试 Jina Reader...", file=sys.stderr)
    content, error = fetch_with_jina(url, max_chars)
    
    if content:
        return content, "Jina Reader (备用)"
    
    return None, f"所有方案均失败 - Scrapling: {error}"

def main() -> None:
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 web_fetch.py <url> [maxChars]", file=sys.stderr)
        print("\n示例:", file=sys.stderr)
        print("  python3 web_fetch.py https://example.com", file=sys.stderr)
        print("  python3 web_fetch.py https://mp.weixin.qq.com/s/xxxxx 50000", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = 30000
    
    if len(sys.argv) > 2:
        try:
            max_chars = int(sys.argv[2])
            if not (100 <= max_chars <= 100000):
                print("⚠️ maxChars 应在 100-100000 之间，使用默认值 30000", file=sys.stderr)
                max_chars = 30000
        except ValueError:
            print("⚠️ maxChars 必须是数字，使用默认值 30000", file=sys.stderr)
            max_chars = 30000
    
    content, method = smart_fetch(url, max_chars)
    
    if content:
        print(content)
        print(f"\n---\n✅ 抓取成功 | 方案: {method}", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"❌ 抓取失败: {method}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
