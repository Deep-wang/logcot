#!/usr/bin/env python3
"""
测试 analyze_log_directory 函数的简单脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scan import summerize as analyze_log_final

def test_analyze_function():
    print("🧪 开始测试 analyze_log_directory 函数...")
    
    # 创建测试日志内容
    test_logs = """
[2024-01-01 10:00:01] INFO: System startup completed
[2024-01-01 10:00:05] ERROR: Database connection failed - Connection timeout
[2024-01-01 10:00:10] WARN: Retrying database connection...
[2024-01-01 10:00:15] ERROR: Authentication failed for user 'admin'
[2024-01-01 10:00:20] CRITICAL: Service crashed with exit code 1
[2024-01-01 10:00:25] INFO: Attempting service restart...
[2024-01-01 10:00:30] ERROR: Failed to bind to port 8080 - Address already in use
    """
    
    print(f"📋 测试日志内容 ({len(test_logs)} 字符):")
    print(test_logs[:200] + "...")
    
    try:
        # 测试字符串模式
        print("\n🔧 调用 analyze_log_directory (str 模式)...")
        result = analyze_log_final.analyze_log_directory(
            test_logs, 
            option='str', 
            output_file='./test_output.txt'
        )
        
        print(f"\n📊 函数返回结果:")
        if result:
            print(f"   结果长度: {len(result)} 字符")
            print(f"   前200字符: {result[:200]}...")
        else:
            print("   返回结果为空")
            
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    test_analyze_function() 