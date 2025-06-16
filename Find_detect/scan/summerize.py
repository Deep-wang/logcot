import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import time

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx" # 替换为你的实际 Key
MAX_CHARS_PER_CHUNK = 7000  # 控制模型单次最大输入

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1.5, min=2, max=10))
def call_model(prompt):
    print(f"🔗 开始调用 API...")
    print(f"   API URL: {API_URL}")
    print(f"   使用模型: Qwen/Qwen3-8B")
    print(f"   Prompt 长度: {len(prompt)} 字符")
    
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

    try:
        print(f"   发送请求中...")
        response = requests.post(API_URL, json=payload, headers=headers)
        print(f"   响应状态码: {response.status_code}")
        response.raise_for_status()
        
        result = response.json()["choices"][0]["message"]["content"]
        print(f"   ✅ API 调用成功，响应长度: {len(result)} 字符")
        return result
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API 请求失败: {e}")
        raise
    except KeyError as e:
        print(f"   ❌ API 响应格式错误: {e}")
        print(f"   响应内容: {response.text[:500]}...")
        raise
    except Exception as e:
        print(f"   ❌ 未知错误: {e}")
        raise

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

# 将大文本按字数切分为多个片段
def split_text_into_chunks(text, max_chars):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

# 主逻辑：读取+分段分析+最终总结
def analyze_log_directory(root_dir, option='dir', output_file=None):
    """
    分析日志的主函数
    
    Args:
        root_dir: 当option='dir'时为目录路径，当option='str'时为日志文本内容
        option: 'dir' 表示从目录读取文件，'str' 表示直接分析传入的文本
        output_file: 可选，指定输出文件路径保存分析结果
    """
    print(f"🔧 analyze_log_directory 函数开始执行")
    print(f"   选项: {option}")
    print(f"   输出文件: {output_file}")
    
    if option == 'dir':
        print(f"   目录路径: {root_dir}")
        all_logs = load_all_logs_to_string(root_dir)
        print(f"📄 日志总长度：{len(all_logs)} 字符")
    elif option == 'str':
        all_logs = root_dir  # 当option='str'时，root_dir实际上是文本内容
        print(f"📄 输入文本长度：{len(all_logs)} 字符")
    else:
        raise ValueError("option 参数必须是 'dir' 或 'str'")

    if not all_logs.strip():
        print("⚠️ 没有找到日志内容，跳过分析")
        return None

    chunks = split_text_into_chunks(all_logs, MAX_CHARS_PER_CHUNK)
    print(f"🔍 分为 {len(chunks)} 段进行分析")

    partial_results = []
    for i, chunk in enumerate(chunks):
        print(f"🚀 提交第 {i + 1} 段分析...")
        print(f"   当前段长度: {len(chunk)} 字符")
        prompt = (
            f"日志分析第 {i + 1} 部分：\n\n{chunk}\n\n"
            "请识别其中是否有异常情况、故障时间点、以及日志类型之间可能的因果关系。总结异常点并提取关键说明。"
        )
        
        try:
            print(f"   正在调用 LLM...")
            result = call_model(prompt)
            print(f"   LLM 响应长度: {len(result)} 字符")
            partial_results.append(result)
        except Exception as e:
            print(f"   ❌ 第 {i + 1} 段分析失败: {e}")
            partial_results.append(f"分析失败: {e}")

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

    try:
        print("🤖 正在进行最终整合分析...")
        final_result = call_model(final_prompt)
        print("\n✅ 最终整合总结：\n")
        print(final_result)
        print("\n" + "="*60 + "\n")
    except Exception as e:
        print(f"❌ 最终整合分析失败: {e}")
        final_result = f"最终分析失败: {e}"
    
    # 如果指定了输出文件，保存分析结果
    if output_file:
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== 日志分析报告 ===\n\n")
                f.write(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"分析模式: {'目录分析' if option == 'dir' else '文本分析'}\n")
                f.write(f"日志长度: {len(all_logs)} 字符\n")
                f.write(f"分段数量: {len(chunks)} 段\n\n")
                
                f.write("=== 分段分析结果 ===\n\n")
                for i, result in enumerate(partial_results, 1):
                    f.write(f"第{i}段分析结果：\n{result}\n\n")
                
                f.write("=== 最终整合总结 ===\n\n")
                f.write(final_result)
            
            print(f"📋 分析结果已保存至: {output_file}")
        except Exception as e:
            print(f"❌ 保存分析结果失败: {e}")
    
    print(f"🔧 analyze_log_directory 函数执行完成")
    return final_result

# 示例使用
# if __name__ == "__main__":
#     analyze_log_directory('/Users/hy_mbp/output3')  # 将此路径替换为你的实际日志文件目录
