#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志预处理模块测试脚本
测试各种时间格式的提取和分组功能
"""

from log_preprocessor import LogTimeExtractor, LogTimeGrouper
from datetime import datetime
import tempfile
import os

def test_time_extraction():
    """测试时间提取功能"""
    print("🧪 测试时间提取功能...")
    
    extractor = LogTimeExtractor()
    
    # 测试日志样例
    test_logs = [
        "Apr 23 14:56:46 czp-db1 sshd[307434]: Accepted password for dmdba from 10.33.240.40 port 52131 ssh2",
        "Apr 23 14:43:31 czp-db1 kernel: rport-15:0-18: blocked FC remote port time out",
        "Apr 23 13:04:01 czp-db1 linx[152972]: free -m",
        "2025-04-23 14:42:48.038 [INFO] database P0000010414 T0000000000000013572",
        "77493256    2025-04-23 14:39:24    0x100F02440006    Event    Informational",
        "2025-04-23T11:54:00.805445+08:00 Dky_app_00 kernel: sd 7:0:2:6: [sdu]",
        "Invalid log line without time",
        "2025-04-23 16:30:15 Another test log"
    ]
    
    print("提取时间结果:")
    print("-" * 60)
    
    for i, log in enumerate(test_logs, 1):
        extracted_time = extractor.extract_time_from_line(log)
        if extracted_time:
            print(f"{i}. ✅ {extracted_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   原始: {log[:80]}...")
        else:
            print(f"{i}. ❌ 无法提取时间")
            print(f"   原始: {log[:80]}...")
        print()

def test_time_grouping():
    """测试时间分组功能"""
    print("🧪 测试时间分组功能...")
    
    # 创建临时测试文件
    test_logs = [
        "Apr 23 12:56:46 czp-db1 sshd[307434]: Test log 1",
        "Apr 23 13:43:31 czp-db1 kernel: Test log 2",
        "Apr 23 14:04:01 czp-db1 linx[152972]: Test log 3",
        "Apr 23 14:42:48 czp-db1 database: Test log 4",
        "Apr 23 15:39:24 czp-db1 system: Test log 5",
        "Apr 23 16:54:00 czp-db1 kernel: Test log 6",
        "Apr 23 17:30:15 czp-db1 app: Test log 7",
        "Invalid log without time",
        "Apr 23 18:15:30 czp-db1 final: Test log 8"
    ]
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        for log in test_logs:
            f.write(log + '\n')
        temp_file = f.name
    
    try:
        # 创建分组器
        grouper = LogTimeGrouper(group_hours=2)
        
        # 处理文件
        grouped_logs = grouper.process_log_file(temp_file)
        
        print("分组结果:")
        print("-" * 60)
        
        for group_key, logs in sorted(grouped_logs.items()):
            print(f"时间组: {group_key}")
            print(f"日志数量: {len(logs)}")
            for i, log in enumerate(logs, 1):
                print(f"  {i}. {log}")
            print()
            
        # 生成报告
        report = grouper.generate_time_analysis_report(grouped_logs)
        print("分析报告:")
        print("=" * 60)
        print(report)
        
    finally:
        # 清理临时文件
        os.unlink(temp_file)

def test_with_sample_data():
    """使用您提供的示例数据进行测试"""
    print("🧪 使用示例数据测试...")
    
    # 创建包含您示例数据的测试文件
    sample_logs = [
        "Apr 23 14:56:46 czp-db1 sshd[307434]: Accepted password for dmdba from 10.33.240.40 port 52131 ssh2",
        "Apr 23 14:56:46 czp-db1 sshd[307434]: linx pam_sm_open_session",
        "Apr 23 14:56:46 czp-db1 sshd[307434]: pam_unix_session(sshd:session): session opened for user dmdba by (uid=500)",
        "Apr 23 14:56:46 czp-db1 sshd[307586]: Accepted password for dmdba from 10.33.240.40 port 52133 ssh2",
        "Apr 23 14:57:29 czp-db1 sshd[308611]: Accepted password for dmdba from 10.33.240.40 port 52136 ssh2",
        "Apr 23 14:43:31 czp-db1 kernel: rport-15:0-18: blocked FC remote port time out",
        "Apr 23 14:43:31 czp-db1 kernel: lpfc 0000:33:00.40: 0:(0):0203 Devloss timeout",
        "Apr 23 13:04:01 czp-db1 linx[152972]: free -m",
        "2025-04-23 14:42:48.038 [INFO] database P0000010414 T0000000000000013572 ckpt2_log_adjust: full_status: 160, ptx_lsn(28269421754563)",
        "2025-04-23 14:42:59.156 [INFO] database P0000010414 T0000000000000015201 utsk_get_dw_svr_info used 11 seconds",
        "77493256    2025-04-23 14:39:24    0x100F02440006    Event    Informational    --    None    The link between",
        "2025-04-23T11:54:00.805444+08:00 Dky_app_00 kernel: sd 7:0:2:6: [sdu] Result: hostbyte=DID_OK driverbyte=DRIVER_OK",
    ]
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        for log in sample_logs:
            f.write(log + '\n')
        temp_file = f.name
    
    try:
        # 创建分组器（2小时为一组）
        grouper = LogTimeGrouper(group_hours=2)
        
        # 处理文件
        grouped_logs = grouper.process_log_file(temp_file)
        
        print("示例数据分组结果:")
        print("-" * 60)
        
        for group_key, logs in sorted(grouped_logs.items()):
            print(f"📅 时间组: {group_key}")
            print(f"📊 日志数量: {len(logs)}")
            print("📝 日志内容:")
            for i, log in enumerate(logs, 1):
                print(f"  {i}. {log}")
            print("-" * 40)
            
    finally:
        # 清理临时文件
        os.unlink(temp_file)

def main():
    """主测试函数"""
    print("=" * 70)
    print("日志预处理模块测试")
    print("=" * 70)
    
    # 测试时间提取
    test_time_extraction()
    print("\n" + "=" * 70)
    
    # 测试时间分组
    test_time_grouping()
    print("\n" + "=" * 70)
    
    # 测试示例数据
    test_with_sample_data()
    print("\n" + "=" * 70)
    
    print("✅ 所有测试完成!")

if __name__ == "__main__":
    main() 