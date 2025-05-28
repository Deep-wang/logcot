import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

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
def analyze_log_directory(root_dir):
    all_logs = load_all_logs_to_string(root_dir)
    print(f"📄 日志总长度：{len(all_logs)} 字符")

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

    final_result = call_model(final_prompt)
    print("\n✅ 最终整合总结：\n")
    print(final_result)
    

# 示例使用
# if __name__ == "__main__":
#     analyze_log_directory('/Users/hy_mbp/output3')  # 将此路径替换为你的实际日志文件目录
