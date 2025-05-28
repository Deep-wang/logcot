#apikey = sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx
import requests
import json


LOG_FILE_PATH = "/log/log/czp_db2/log1.txt"
CHUNK_SIZE = 10000  # 每块最多 10000 字符，避免 token 超限
url = "https://api.siliconflow.cn/v1/chat/completions"
def chat(question):
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
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ],

    }
    headers = {
        "Authorization": "Bearer sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    text = json.loads(response.text)
    print(text['choices'][0]['message']['content'])

def read_file_in_chunks(path, chunk_size):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
#f"日志第 {idx + 1} 部分：\n{chunk}\n\n请指出日志错误时间，并截取前后适量部分保存"
def analyze_log_chunk(chunk, idx):
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
        "messages": [
            {
                "role": "user",
                "content": f"日志第 {idx + 1} 部分：\n{chunk}\n\n请指出日志出现错误时间，并截取前后适量部分保存,不需要总结"
            }
        ],

    }
    headers = {
        "Authorization": "Bearer sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    text = json.loads(response.text)
    print(text['choices'][0]['message']['content'])
    return text['choices'][0]['message']['content']
def main():
    chunks = read_file_in_chunks(LOG_FILE_PATH, CHUNK_SIZE)
    all_analysis = []
    print(f"共读取 {len(chunks)} 个日志块，开始逐个分析...\n")
    for idx, chunk in enumerate(chunks):
        print(f"分析第 {idx + 1} 块日志...")
        # print(chunk)
        # print("/n")
        # print("/n")
        # print("/n")
        # print("/n")
        # print("/n")
        # print("/n")
        analysis = analyze_log_chunk(chunk, idx)
        all_analysis.append(f"第 {idx + 1} 部分分析结果：\n{analysis}\n")
    summary_prompt = "\n\n".join(all_analysis)
    print("\n整理汇总所有分析...\n")
    # 汇总整体分析
    summary = payload = {
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
        "messages": [
            {
                "role": "user",
                "content": summary_prompt
            }
        ],

    }
    headers = {
        "Authorization": "Bearer sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    text = json.loads(response.text)
    print("\n🧾 最终汇总分析结果：\n")
    print(text['choices'][0]['message']['content'])

if __name__ == "__main__":
    main()
