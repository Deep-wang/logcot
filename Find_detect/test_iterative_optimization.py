"""
测试迭代优化功能
演示如何使用多轮对话来改进日志分析结果
"""

import os
import sys

# 添加当前目录到路径，以便导入scan模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scan.summerize import iterative_improve_analysis


def test_iterative_optimization():
    """
    测试迭代优化功能
    """
    print("🚀 开始测试迭代优化功能")
    print("=" * 80)
    
    # 模拟一个质量较低的初始分析结果
    initial_analysis = """
    ## 日志分析结果
    
    发现了一些错误，数据库有问题，支付也有问题。
    
    时间大概在下午。
    
    建议检查服务器。
    """
    
    # 模拟原始日志样本
    sample_logs = """
    2024-01-15 14:23:15 INFO [UserController] 处理用户登录请求: user_id=12345
    2024-01-15 14:23:16 INFO [AuthService] 验证用户凭据
    2024-01-15 14:23:17 ERROR [DatabaseConnection] 连接超时: Connection timeout after 30 seconds
    2024-01-15 14:23:18 WARN [AuthService] 数据库连接失败，尝试重连
    2024-01-15 14:23:19 ERROR [AuthService] 重连失败，服务不可用
    2024-01-15 14:23:20 INFO [UserController] 返回登录失败响应
    
    2024-01-15 15:30:01 INFO [OrderService] 开始处理订单创建请求
    2024-01-15 15:30:02 INFO [PaymentService] 验证支付信息
    2024-01-15 15:30:03 ERROR [PaymentService] 支付网关响应超时
    2024-01-15 15:30:04 WARN [OrderService] 支付验证失败，订单状态设为待支付
    
    2024-01-15 16:15:01 ERROR [FileService] 文件读取失败: FileNotFound
    2024-01-15 16:15:02 WARN [FileService] 尝试从备份位置读取
    2024-01-15 16:15:03 ERROR [FileService] 备份文件也不存在
    
    2024-01-15 16:20:01 INFO [SystemHealth] CPU使用率: 85%
    2024-01-15 16:20:02 WARN [SystemHealth] 内存使用率超过阈值: 92%
    2024-01-15 16:20:03 ERROR [SystemHealth] 磁盘空间不足: 剩余空间 < 5%
    """
    
    print("📋 初始分析结果（质量较低）:")
    print("-" * 50)
    print(initial_analysis)
    
    print("\n📋 原始日志样本:")
    print("-" * 50)
    print(sample_logs[:400] + "...")
    
    try:
        # 执行迭代优化
        final_result, final_score, history = iterative_improve_analysis(
            initial_result=initial_analysis,
            logs_sample=sample_logs,
            max_iterations=3,
            target_score=8.0,
            model_name="Qwen/Qwen3-8B"
        )
        
        print("\n" + "=" * 80)
        print("🎯 优化完成！")
        print("=" * 80)
        
        print(f"\n📊 最终评分: {final_score}")
        print(f"📊 优化轮数: {len(history)}")
        
        print(f"\n✨ 最终优化后的分析结果:")
        print("-" * 50)
        print(final_result)
        
        # 显示优化历程
        print(f"\n📈 优化历程:")
        print("-" * 50)
        for i, item in enumerate(history):
            print(f"第 {item['iteration']} 轮:")
            print(f"  📊 评分: {item['score']}")
            if i == 0:
                print(f"  📝 分析摘要: {item['result'][:100]}...")
            else:
                # 显示改进点
                print(f"  ✏️ 基于评判建议进行了改进")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_simple_optimization():
    """
    测试简单的优化案例
    """
    print("\n🧪 测试简单优化案例")
    print("=" * 60)
    
    # 一个稍微好一点的初始分析
    simple_analysis = """
    日志分析结果：
    1. 发现数据库连接超时错误
    2. 支付网关有响应超时
    3. 文件服务无法访问文件
    
    这些问题可能影响用户体验。
    """
    
    simple_logs = """
    2024-01-15 14:23:17 ERROR [DatabaseConnection] 连接超时
    2024-01-15 15:30:03 ERROR [PaymentService] 支付网关响应超时
    2024-01-15 16:15:01 ERROR [FileService] 文件读取失败
    """
    
    try:
        final_result, final_score, history = iterative_improve_analysis(
            initial_result=simple_analysis,
            logs_sample=simple_logs,
            max_iterations=2,  # 只优化2轮
            target_score=7.5,  # 较低的目标评分
            model_name="Qwen/Qwen3-8B"
        )
        
        print(f"\n📊 简单案例最终评分: {final_score}")
        print(f"📊 优化轮数: {len(history)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 简单案例测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🔬 迭代优化功能测试")
    print("=" * 100)
    
    # 测试主要功能
    test1_result = test_iterative_optimization()
    
    # 测试简单案例
    test2_result = test_simple_optimization()
    
    print("\n📋 测试总结:")
    print("=" * 100)
    print(f"✅ 完整优化测试: {'通过' if test1_result else '失败'}")
    print(f"✅ 简单优化测试: {'通过' if test2_result else '失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！迭代优化功能正常")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和网络连接")
    
    print(f"\n💡 功能特点:")
    print(f"   🔄 基于评判结果的多轮自我优化")
    print(f"   📊 自动评分和质量提升追踪")
    print(f"   🎯 可设置目标评分和最大迭代次数")
    print(f"   📈 完整的优化历程记录")
    print(f"   🤖 利用多轮对话保持优化上下文")
    
    print(f"\n🔧 使用方法:")
    print(f"   在analyze_log_directory函数中已集成")
    print(f"   可通过参数调整优化策略:")
    print(f"   - max_iterations: 最大迭代次数")
    print(f"   - target_score: 目标评分阈值")
    print(f"   - model_name: 使用的模型") 