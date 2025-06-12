"""
整合分析
输入：output_529文件夹
输出：整合一个总结，分析错误日志
"""

import os
import sys
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
# 导入LLMClient类

import re

# 添加上级目录到路径，以便导入LLMClient
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import LLMClient

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx" # 替换为你的实际 Key
MAX_CHARS_PER_CHUNK = 7000  # 控制模型单次最大输入

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1.5, min=2, max=10))
def call_model(prompt):
    payload = {
        "model": "Qwen/Qwen3-8B",
        "stream": False,
        "max_tokens": 8192,
        "enable_thinking": True,
        "thinking_budget": 4096,
        "min_p": 0.05,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "stop": [],
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def create_critic_model(model_name="THUDM/GLM-4-9B-0414"):
    """
    创建评判模型，用于评估分析结果的质量并提供改进建议
    
    Returns:
        LLMClient: 配置好的评判模型实例
    """
    critic_llm = LLMClient(
        api_key=API_KEY,
        api_url=API_URL,
        model=model_name,  # 使用更强的模型作为评判者
        temperature=0.3,  # 较低温度确保评判的一致性
        max_tokens=4096,
        enable_thinking=True,
        thinking_budget=2048,
        top_p=0.8,
        frequency_penalty=0.2
    )
    return critic_llm

def critic_analysis(analysis_result, original_logs_sample="", model_name="THUDM/GLM-4-9B-0414"):
    """
    使用评判模型对分析结果进行评估和改进建议
    
    Args:
        analysis_result: 原始分析结果
        original_logs_sample: 原始日志样本（可选）
        
    Returns:
        str: 评判结果和改进建议
    """
    # Meta Prompt - 赋予大模型评判者身份
    meta_prompt = """
    你是一位资深的日志分析专家和质量评估师，具有以下专业能力：
    
    【身份定位】
    - 拥有10年以上的系统运维和日志分析经验
    - 熟悉各种类型的系统日志、应用日志、错误日志
    - 擅长识别日志分析中的盲点、误判和遗漏
    - 具备敏锐的质量评估能力和改进方案设计能力
    
    【评估维度】
    请从以下维度对日志分析结果进行专业评估：
    
    1. **准确性评估**：
       - 异常识别是否准确？是否存在误报或漏报？
       - 时间点定位是否精确？
       - 因果关系分析是否合理？
    
    2. **完整性评估**：
       - 是否遗漏了重要的异常信息？
       - 分析深度是否足够？
       - 关键细节是否被忽视？
    
    3. **逻辑性评估**：
       - 分析逻辑是否清晰合理？
       - 结论是否与证据匹配？
       - 推理过程是否存在跳跃或矛盾？
    
    4. **实用性评估**：
       - 分析结果对问题解决的帮助程度
       - 是否提供了具体可行的排查方向？
       - 优先级判断是否合理？
    
    【输出要求】
    请按照以下格式提供评估结果：
    
    ## 🎯 综合评分
    [给出1-10分的评分，并简要说明评分理由, 注意评分需要按照下面格式给出(例子：评分：5分)]
    
    ## ✅ 分析优点
    [列出当前分析的亮点和正确之处]
    
    ## ⚠️ 存在问题
    [指出分析中的不足、错误或遗漏]
    
    ## 🚀 改进建议
    [提供具体的改进方向和优化建议]
    
    ## 📋 补充分析
    [如果发现遗漏的重要信息，请补充分析]
    
    请保持客观、专业、建设性的评估态度。
    """
    
    # 构建评判输入内容
    content = f"""
    请对以下日志分析结果进行专业评估：
    
    ## 待评估的分析结果：
    {analysis_result}
    
    ## 原始日志样本（参考）：
    {original_logs_sample if original_logs_sample else "暂无原始日志样本"}
    
    请根据你的专业经验，对上述分析结果进行全面评估并提供改进建议。
    """
    
    # 创建评判模型
    critic = create_critic_model(model_name=model_name)
        
    try:
        # 调用评判模型
        critic_result = critic.forward(content, system_prompt=meta_prompt)
        score = extract_score_from_critic_result(critic_result) 
        return critic_result, score
    except Exception as e:
        return f"❌ 评判模型调用失败: {e}", None

# 读取目录下所有 .txt 文件并合并为一大段文本
def load_all_logs_to_string(root_dir):
    combined = ""
    for root, _, files in os.walk(root_dir):
        for fname in files:
            if fname.endswith(".txt"):
                path = os.path.join(root, fname)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        combined += f"\n【文件】：{os.path.relpath(path, root_dir)}\n{content}\n"
                except Exception as e:
                    print(f"❌ 无法读取文件 {path}: {e}")
    return combined


def extract_score_from_critic_result(critic_result):
    """
    从评判模型结果中提取评分
    
    Args:
        critic_result: 评判模型的输出结果
        
    Returns:
        float: 提取的评分，如果提取失败返回None
    """
    if not critic_result:
        return None
        
    # 多种正则表达式模式来匹配评分
    score_patterns = [
        r'综合评分[：:]\s*(\d+(?:\.\d+)?)',  # 综合评分：8.5
        r'评分[：:]\s*(\d+(?:\.\d+)?)',      # 评分：8
        r'(\d+(?:\.\d+)?)\s*分',             # 8.5分
        r'(\d+(?:\.\d+)?)/10',               # 8/10
        r'得分[：:]\s*(\d+(?:\.\d+)?)',      # 得分：8.5
        r'分数[：:]\s*(\d+(?:\.\d+)?)',      # 分数：8.5
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, critic_result, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
                # 确保评分在合理范围内
                if 0 <= score <= 10:
                    return score
            except ValueError:
                continue
                
    return None


# 将大文本按字数切分为多个片段
def split_text_into_chunks(text, max_chars):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

def iterative_improve_analysis(initial_result, logs_sample, max_iterations=3, target_score=8.0, model_name="Qwen/Qwen3-8B"):
    """
    基于评判结果的迭代优化分析
    
    Args:
        initial_result: 初始分析结果
        logs_sample: 原始日志样本
        max_iterations: 最大迭代次数
        target_score: 目标评分阈值
        model_name: 使用的模型名称
        
    Returns:
        tuple: (最终优化结果, 最终评分, 迭代历史)
    """
    print(f"\n🔄 开始迭代优化分析（最大迭代次数: {max_iterations}, 目标评分: {target_score}）")
    print("=" * 60)
    
    # 创建用于优化的LLM客户端
    optimization_llm = LLMClient(
        api_url=API_URL,
        api_key=API_KEY,
        model=model_name,
        temperature=0.3,  # 较低温度确保优化的一致性
        max_tokens=8192,
        enable_thinking=True,
        thinking_budget=4096,
        max_history_length=20,  # 保留足够的优化历史
        auto_truncate=True
    )
    
    # 设置系统提示词
    system_prompt = """
    你是一个专业的日志分析专家，正在优化和改进自己的分析结果。

    你的任务是：
    1. 仔细阅读评判专家提供的评估报告和改进建议
    2. 根据评判结果中指出的问题和不足，改进你的分析
    3. 提供更准确、更完整、更有用的日志分析结果
    4. 确保改进后的分析逻辑清晰、证据充分、结论合理

    请保持分析的专业性和准确性，同时根据评判建议进行针对性改进。
    """
    
    optimization_llm.set_system_prompt(system_prompt)
    
    current_result = initial_result
    iteration_history = []
    
    for iteration in range(max_iterations):
        print(f"\n🔍 === 第 {iteration + 1} 轮优化 ===")
        
        # 获取当前结果的评判
        critic_result, score = critic_analysis(current_result, logs_sample, model_name=model_name)
        
        print(f"📊 当前评分: {score}")
        
        # 记录本轮历史
        iteration_info = {
            "iteration": iteration + 1,
            "result": current_result,
            "score": score,
            "critic_result": critic_result
        }
        iteration_history.append(iteration_info)
        
        # 检查是否达到目标评分
        if score is not None and score >= target_score:
            print(f"🎯 已达到目标评分 {target_score}，优化完成！")
            break
        
        # 检查是否是最后一轮
        if iteration == max_iterations - 1:
            print(f"📋 已达到最大迭代次数 {max_iterations}，优化结束")
            break
        
        # 构建优化提示
        improvement_prompt = f"""
        请根据以下评判结果改进你的日志分析：

        ## 当前分析结果：
        {current_result}

        ## 评判专家的评估报告：
        {critic_result}

        ## 原始日志样本（参考）：
        {logs_sample[:1500] if logs_sample else "无日志样本"}

        请根据评判专家的建议，改进上述分析结果。特别关注：
        1. 评判中指出的准确性问题
        2. 遗漏的重要信息
        3. 逻辑性和完整性方面的不足
        4. 实用性和可操作性的改进空间

        请提供改进后的完整分析结果：
        """
        
        try:
            print("🤖 AI正在基于评判结果进行优化...")
            improved_result = optimization_llm.chat(improvement_prompt)
            current_result = improved_result
            print(f"✅ 第 {iteration + 1} 轮优化完成")
            
        except Exception as e:
            print(f"❌ 第 {iteration + 1} 轮优化失败: {e}")
            break
    
    # 最终评估
    print(f"\n🏁 === 优化过程完成 ===")
    final_critic_result, final_score = critic_analysis(current_result, logs_sample, model_name=model_name)
    
    # 输出优化总结
    print(f"\n📈 优化总结:")
    print(f"  🔢 总迭代次数: {len(iteration_history)}")
    print(f"  📊 初始评分: {iteration_history[0]['score'] if iteration_history else 'N/A'}")
    print(f"  📊 最终评分: {final_score}")
    
    if len(iteration_history) > 0 and iteration_history[0]['score'] is not None and final_score is not None:
        improvement = final_score - iteration_history[0]['score']
        print(f"  📈 评分提升: {improvement:+.1f}")
        if improvement > 0:
            print(f"  ✅ 分析质量得到改善")
        elif improvement == 0:
            print(f"  ➖ 分析质量保持稳定")
        else:
            print(f"  ⚠️ 评分有所下降")
    
    return current_result, final_score, iteration_history

# 主逻辑：读取+分段分析+最终总结
def analyze_log_directory(root_dir, option='dir'):
    if option == 'dir':
        all_logs = load_all_logs_to_string(root_dir)
        print(f"📄 日志总长度：{len(all_logs)} 字符")
        # 保存日志样本用于评判模型参考
        logs_sample = all_logs[:2000] if len(all_logs) > 2000 else all_logs
    elif option == 'str':
        all_logs = root_dir
        logs_sample = all_logs[:2000] if len(all_logs) > 2000 else all_logs

    chunks = split_text_into_chunks(all_logs, MAX_CHARS_PER_CHUNK)
    print(f"🔍 分为 {len(chunks)} 段进行分析")

    partial_results = []
    for i, chunk in enumerate(chunks):
        print(f"🚀 提交第 {i + 1} 段分析...")
        prompt = (
            f"日志分析第 {i + 1} 部分：\n\n{chunk}\n\n"
            "请识别其中是否有异常情况、故障时间点、以及日志类型之间可能的因果关系。总结异常点并提取关键说明。"
        )
        result = call_model(prompt)
        partial_results.append(result)

    print("🧠 准备提交整合分析...")
    full_summary_input = "\n\n".join(
        f"第{i+1}段分析结果：\n{res}" for i, res in enumerate(partial_results)
    )
    final_prompt = (
        f"以下是多个日志分析部分的结果，请综合这些信息回答：\n"
        f"1. 是否存在共性或重复的问题？\n"
        f"2. 是否可以判断故障原因或影响范围？\n"
        f"3. 各日志类型之间是否存在依赖或因果联系？\n\n"
        f"{full_summary_input}"
    )

    # final_result = call_model(final_prompt)
    llm = LLMClient(
        api_url=API_URL,
        api_key=API_KEY,
        model="Qwen/Qwen3-8B",
        stream=False,
        max_tokens=8192,
        enable_thinking=True,
        thinking_budget=4096,
        min_p=0.1,
        temperature=0.1,
        top_p=0.3,
        top_k=20,
        frequency_penalty=0.1,
        presence_penalty=0.0,
        n=1,
        stop=[]
    )
    initial_result = llm.forward(final_prompt)

    print("\n✅ 初始分析结果：\n")
    print(initial_result)
    
    # 使用迭代优化功能改进分析结果
    final_result, final_score, optimization_history = iterative_improve_analysis(
        initial_result=initial_result,
        logs_sample=logs_sample,
        max_iterations=3,  # 最多3轮优化
        target_score=8.0,  # 目标评分8分
        model_name="Qwen/Qwen3-8B"
    )
    
    print(f"\n🎯 最终优化评分：{final_score}")
    print(f"\n✨ === 最终优化后的分析结果 ===")
    print(final_result)
    
    return final_result

# 示例使用
if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output_529')
    analyze_log_directory(path)  # 将此路径替换为你的实际日志文件目录
