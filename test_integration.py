#!/usr/bin/env python3
"""
Web Fetch 集成测试
测试真实的网页抓取功能

运行: python3 test_integration.py
"""

import sys
from pathlib import Path
import time

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web_fetch import smart_fetch

def test_fetch_example_com():
    """测试抓取 example.com"""
    print("测试 example.com...")
    
    start = time.time()
    content, method = smart_fetch("https://example.com", max_chars=5000)
    duration = time.time() - start
    
    assert content is not None, "应该成功抓取"
    assert "Example Domain" in content, "应该包含标题"
    assert method in ["Scrapling", "Jina Reader (备用)"], f"方案应该是 Scrapling 或 Jina，实际：{method}"
    assert duration < 10, f"应该在 10 秒内完成，实际：{duration:.2f}秒"
    
    print(f"  ✅ 成功 | 方案: {method} | 耗时: {duration:.2f}秒")
    print(f"  📊 内容长度: {len(content)} 字符")

def test_fetch_httpbin():
    """测试抓取 httpbin.org"""
    print("测试 httpbin.org...")
    
    start = time.time()
    content, method = smart_fetch("https://httpbin.org/html", max_chars=5000)
    duration = time.time() - start
    
    assert content is not None, "应该成功抓取"
    assert "Herman Melville" in content or "Moby-Dick" in content, "应该包含内容"
    assert duration < 10, f"应该在 10 秒内完成，实际：{duration:.2f}秒"
    
    print(f"  ✅ 成功 | 方案: {method} | 耗时: {duration:.2f}秒")

def test_fetch_invalid_domain():
    """测试无效域名"""
    print("测试无效域名...")
    
    start = time.time()
    content, error = smart_fetch("https://this-domain-does-not-exist-12345678.com")
    duration = time.time() - start
    
    # 注意：Jina Reader 可能会返回错误页面，所以我们检查内容是否很短
    if content is not None:
        # 如果返回了内容，应该是错误页面（很短）
        assert len(content) < 500, f"错误页面应该很短，实际：{len(content)} 字符"
        print(f"  ✅ 返回错误页面 | 方案: {error} | 长度: {len(content)} | 耗时: {duration:.2f}秒")
    else:
        # 如果返回 None，应该有错误信息
        assert "失败" in error, f"应该返回失败信息，实际：{error}"
        print(f"  ✅ 正确处理失败 | 错误: {error} | 耗时: {duration:.2f}秒")
    
    assert duration < 70, f"应该在 70 秒内超时，实际：{duration:.2f}秒"

def test_fetch_with_max_chars():
    """测试字符数限制"""
    print("测试字符数限制...")
    
    content, method = smart_fetch("https://example.com", max_chars=100)
    
    assert content is not None, "应该成功抓取"
    assert len(content) <= 150, f"内容应该被截断，实际长度：{len(content)}"  # 允许一些误差
    
    print(f"  ✅ 成功 | 内容长度: {len(content)} 字符")

def test_performance():
    """测试性能"""
    print("测试性能（5 次请求）...")
    
    durations = []
    for i in range(5):
        start = time.time()
        content, method = smart_fetch("https://example.com")
        duration = time.time() - start
        durations.append(duration)
        
        assert content is not None, f"第 {i+1} 次请求应该成功"
    
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    print(f"  ✅ 完成")
    print(f"  📊 平均耗时: {avg_duration:.2f}秒")
    print(f"  📊 最快: {min_duration:.2f}秒")
    print(f"  📊 最慢: {max_duration:.2f}秒")
    
    assert avg_duration < 5, f"平均耗时应该 < 5秒，实际：{avg_duration:.2f}秒"

def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")
    
    # 测试无效 URL
    content, error = smart_fetch("not-a-url")
    assert content is None, "无效 URL 应该失败"
    assert "无效的 URL" in error, f"应该返回 URL 错误，实际：{error}"
    print("  ✅ 无效 URL 正确处理")
    
    # 测试无效 maxChars
    content, error = smart_fetch("https://example.com", max_chars=-1)
    assert content is None, "负数 maxChars 应该失败"
    assert "100-100000" in error, f"应该返回范围错误，实际：{error}"
    print("  ✅ 无效参数正确处理")
    
    # 测试 NULL 字节
    content, error = smart_fetch("https://example.com\x00/evil")
    assert content is None, "NULL 字节应该被拒绝"
    assert "无效的 URL" in error, f"应该返回 URL 错误，实际：{error}"
    print("  ✅ NULL 字节正确拒绝")
    
    # 测试控制字符
    content, error = smart_fetch("https://example.com/\x01test")
    assert content is None, "控制字符应该被拒绝"
    assert "无效的 URL" in error, f"应该返回 URL 错误，实际：{error}"
    print("  ✅ 控制字符正确拒绝")

def run_all_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("Web Fetch 集成测试")
    print("=" * 60)
    print()
    
    tests = [
        ("基本功能", test_fetch_example_com),
        ("HTTP 测试", test_fetch_httpbin),
        ("无效域名", test_fetch_invalid_domain),
        ("字符限制", test_fetch_with_max_chars),
        ("性能测试", test_performance),
        ("错误处理", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"[{name}]")
            test_func()
            print()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ 失败: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            print()
            failed += 1
    
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("✅ 所有集成测试通过！")
        return 0
    else:
        print(f"❌ {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
