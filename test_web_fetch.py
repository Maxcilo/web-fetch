#!/usr/bin/env python3
"""
Web Fetch 单元测试
运行: python3 test_web_fetch.py
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web_fetch import (
    is_valid_url,
    is_wechat_url,
    is_twitter_url,
    safe_quote_url,
    smart_fetch
)

def test_is_valid_url():
    """测试 URL 验证"""
    print("测试 is_valid_url...")
    
    # 有效的 URL
    assert is_valid_url("https://example.com"), "https URL 应该有效"
    assert is_valid_url("http://example.com"), "http URL 应该有效"
    assert is_valid_url("https://example.com/path"), "带路径的 URL 应该有效"
    assert is_valid_url("https://example.com/path?query=value"), "带查询的 URL 应该有效"
    
    # 无效的 URL
    assert not is_valid_url(""), "空字符串应该无效"
    assert not is_valid_url("not-a-url"), "非 URL 字符串应该无效"
    assert not is_valid_url("ftp://example.com"), "FTP URL 应该无效"
    assert not is_valid_url("https://"), "不完整的 URL 应该无效"
    assert not is_valid_url("https://" + "a" * 3000), "超长 URL 应该无效"
    assert not is_valid_url(None), "None 应该无效"
    assert not is_valid_url(123), "数字应该无效"
    
    # 安全检查
    assert not is_valid_url("https://example.com\x00/evil"), "NULL 字节应该无效"
    assert not is_valid_url("https://example.com/\x01test"), "控制字符应该无效"
    assert not is_valid_url("https://example.com/\u202e"), "Unicode 控制字符应该无效"
    
    print("✅ is_valid_url 测试通过")

def test_is_wechat_url():
    """测试微信公众号 URL 识别"""
    print("测试 is_wechat_url...")
    
    # 微信公众号 URL
    assert is_wechat_url("https://mp.weixin.qq.com/s/xxxxx"), "标准微信 URL"
    assert is_wechat_url("https://MP.WEIXIN.QQ.COM/s/xxxxx"), "大写微信 URL"
    assert is_wechat_url("http://mp.weixin.qq.com/s/xxxxx"), "HTTP 微信 URL"
    
    # 非微信 URL
    assert not is_wechat_url("https://example.com"), "普通 URL"
    assert not is_wechat_url("https://weixin.qq.com"), "不完整的微信域名"
    
    # 修复后：不会误判包含微信 URL 的参数
    assert not is_wechat_url("https://example.com/path?redirect=https://mp.weixin.qq.com"), "参数中的微信 URL"
    
    print("✅ is_wechat_url 测试通过")

def test_is_twitter_url():
    """测试推特 URL 识别"""
    print("测试 is_twitter_url...")
    
    # 推特 URL
    assert is_twitter_url("https://x.com/user"), "x.com"
    assert is_twitter_url("https://twitter.com/user"), "twitter.com"
    assert is_twitter_url("https://mobile.twitter.com/user"), "mobile.twitter.com"
    assert is_twitter_url("https://www.x.com/user"), "www.x.com"
    assert is_twitter_url("https://m.twitter.com/user"), "m.twitter.com"
    
    # 非推特 URL
    assert not is_twitter_url("https://example.com"), "普通 URL"
    assert not is_twitter_url("https://twitter.com.fake.com"), "假推特域名"
    
    # 修复后：不会误判
    assert not is_twitter_url("https://faketwitter.com"), "faketwitter.com 不应该匹配"
    assert not is_twitter_url("https://notx.com"), "notx.com 不应该匹配"
    
    print("✅ is_twitter_url 测试通过")

def test_safe_quote_url():
    """测试 URL 转义"""
    print("测试 safe_quote_url...")
    
    # 基本 URL
    url = "https://example.com/path"
    result = safe_quote_url(url)
    assert "https://example.com/path" in result, "基本 URL 应该保持不变"
    
    # 带中文的 URL
    url = "https://example.com/中文路径"
    result = safe_quote_url(url)
    assert "中文" not in result, "中文应该被转义"
    assert "%E4%B8%AD%E6%96%87" in result or "example.com" in result, "应该包含转义后的内容"
    
    # 带查询参数的 URL
    url = "https://example.com/path?key=value&foo=bar"
    result = safe_quote_url(url)
    assert "?" in result, "应该保留查询符号"
    assert "=" in result, "应该保留等号"
    
    print("✅ safe_quote_url 测试通过")

def test_smart_fetch_validation():
    """测试 smart_fetch 参数验证"""
    print("测试 smart_fetch 参数验证...")
    
    # 无效 URL
    content, error = smart_fetch("not-a-url")
    assert content is None, "无效 URL 应该返回 None"
    assert "无效的 URL" in error, "应该返回错误信息"
    
    # 无效 maxChars
    content, error = smart_fetch("https://example.com", max_chars=-1)
    assert content is None, "负数 maxChars 应该返回 None"
    assert "100-100000" in error, "应该提示范围"
    
    content, error = smart_fetch("https://example.com", max_chars=999999)
    assert content is None, "超大 maxChars 应该返回 None"
    
    print("✅ smart_fetch 参数验证测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Web Fetch 单元测试")
    print("=" * 50)
    print()
    
    try:
        test_is_valid_url()
        test_is_wechat_url()
        test_is_twitter_url()
        test_safe_quote_url()
        test_smart_fetch_validation()
        
        print()
        print("=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"❌ 测试失败: {e}")
        print("=" * 50)
        return 1
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
