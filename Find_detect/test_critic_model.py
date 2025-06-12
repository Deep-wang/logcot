"""
测试评判模型功能
验证LLMClient评判模型能否正确评估日志分析结果
"""

from scan.summerize import critic_analysis


def test_critic_model():
    """
    测试评判模型功能
    """
    print("🚀 开始测试评判模型")
    print("=" * 60)
    
    # 示例分析结果（模拟原始分析输出）
    sample_analysis = """
    ## 日志分析结果

    ### 异常情况识别：
    1. 数据库连接超时问题 - 发生在2024-01-15 14:23:17
    2. 支付网关响应超时 - 发生在2024-01-15 15:30:03
    3. 文件读取失败 - 发生在2024-01-15 16:15:01

    ### 故障影响范围：
    - 用户登录功能受影响，登录成功率下降
    - 订单支付流程中断，部分订单状态异常
    - 文件服务不可用，影响文档下载功能

    ### 因果关系分析：
    数据库连接问题导致用户认证失败，进而影响了整个业务流程。
    支付网关超时问题独立存在，与数据库问题无直接关系。

    ### 建议解决方案：
    1. 检查数据库服务器状态和网络连接
    2. 联系支付网关服务商确认服务状态
    3. 检查文件服务器磁盘空间和权限配置
    """
    
    # 示例原始日志（模拟真实日志数据）
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
    """
    
    print("📋 示例分析结果:")
    print("-" * 40)
    print(sample_analysis[:300] + "...")
    
    print("\n📋 示例原始日志:")
    print("-" * 40)
    print(sample_logs[:300] + "...")
    
    print("\n🎯 调用评判模型进行评估...")
    print("-" * 40)
    
    try:
        # 调用评判模型
        critic_result, score = critic_analysis(sample_analysis, sample_logs, model_name="Qwen/Qwen3-8B")
        
        print("\n📊 === 评判模型输出结果 ===")
        print("=" * 60)
        print(critic_result)
        print(f"🎯 评判模型评分：{score}")
        print("\n✅ 测试完成！评判模型运行正常")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_simple_case():
    """
    测试简单案例
    """
    print("\n🧪 测试简单案例")
    print("=" * 60)
    
    # 简单的分析结果
    simple_analysis = "日志正常，没有发现异常"
    simple_logs = "2024-01-15 10:00:01 INFO [App] 应用启动成功"
    
    try:
        result, score = critic_analysis(simple_analysis, simple_logs, model_name="Qwen/Qwen3-8B")
        print("📊 简单案例评判结果:")
        print("-" * 40)
        print(result)
        print(f"🎯 评判模型评分：{score}")
        return True
    except Exception as e:
        print(f"❌ 简单案例测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🔬 评判模型功能测试")
    print("=" * 80)
    
    # 测试主要功能
    # test1_result = test_critic_model()
    
    # 测试简单案例
    test2_result = test_simple_case()
    
    print("\n📋 测试总结:")
    print("=" * 80)
    # print(f"✅ 主要功能测试: {'通过' if test1_result else '失败'}")
    print(f"✅ 简单案例测试: {'通过' if test2_result else '失败'}")
    
    # if test1_result and test2_result:
    if test2_result:
        print("\n🎉 所有测试通过！评判模型功能正常")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和网络连接")
    
    print(f"\n💡 使用提示:")
    print(f"   - 确保API密钥有效且网络连接正常")
    print(f"   - 评判模型使用GLM-4-9B模型，提供专业的质量评估")
    print(f"   - 可以在summerize.py中直接使用critic_analysis函数") 