"""
分块分析
输出output529,里面包含诊断为错误日志的块，txt文件
"""

import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path
def File_D(file_name,api_url,OUTPUT_DIR):
    current_dir = Path.cwd()
    LOG_RELATIVE_PATH = file_name 
    LOG_FILE_PATH = os.path.join(current_dir, LOG_RELATIVE_PATH)
    LINES_PER_CHUNK = 130 * 2
    MAX_WORKERS = 5
    API_KEYS = [
        "sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "sk-kbucebwhrsoimqttlosgtxncyvmuvdyioncbadavayiovrns",
        "sk-zzuykfebwbxkurfftzuvujqpwqzxxljegnxhhwtzddvwiigf",
        "sk-qgsqryixuqdmtzkgubxpvdzollysgtonnvcrwmikwegmaogn",
        "sk-hvxqvahoplbhdadwtaomisdamxqhquvummcfpvlafeovpqus",
    ]

    log_path_sanitized = LOG_RELATIVE_PATH.replace("\\", '_')
    ERROR_DIR = os.path.join(OUTPUT_DIR, log_path_sanitized + "_errors")
    print(ERROR_DIR)
    os.makedirs(ERROR_DIR, exist_ok=True)
    Scannor(LOG_FILE_PATH, LINES_PER_CHUNK, MAX_WORKERS, API_KEYS, ERROR_DIR, api_url)


@retry(stop=stop_after_attempt(7), wait=wait_exponential(multiplier=2, min=2, max=100))
def post_with_retry(payload, headers, API_URL):
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def analyze_log_chunk(chunk, idx, api_key, error_dir, API_URL):
    payload = {
        "model": "THUDM/GLM-4-9B-0414",
        "stream": False,
        "max_tokens": 8192,   # debug
        "enable_thinking": True,
        "thinking_budget": 4096,
        "min_p": 0.1,
        "temperature": 0.1,
        "top_p": 0.3,
        "top_k": 20,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.0,
        "n": 1,
        "stop": [],
        "messages": [
            {
                "role": "user",
                "content": f"日志第 {idx + 1} 部分：\n{chunk}\n\n请明确标注该部分是否正确，正确写为：日志正确，异常写为：日志异常，标明错误时间并截取出现异常点附近15行日志并给出简单说明"
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        text = post_with_retry(payload, headers, API_URL)
        result = text['choices'][0]['message']['content']
        print(f"✅ 第 {idx + 1} 块日志分析完成")

        if "日志异常" in result:
            error_path = os.path.join(error_dir, f"error_block_{idx + 1}.txt")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write("分析结果：\n")
                f.write(result)
            print(f"⚠️ 发现异常，已写入：{error_path}")
        return f"第 {idx + 1} 部分分析结果：\n{result}\n"

    except Exception as e:
        print(f"❌ 第 {idx + 1} 块日志分析失败：{e}")
        return f"第 {idx + 1} 部分分析结果：\n分析失败：{e}\n"

def read_file_in_line_chunks(path, lines_per_chunk):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return ["".join(lines[i:i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]

def summarize_all_chunks(all_analysis, api_key, api_url):
    summary_prompt = "\n\n".join(all_analysis)
    payload = {
        "model": "Qwen/Qwen3-8B",
        "stream": False,
        "max_tokens": 8192,  # debug
        "enable_thinking": True,
        "thinking_budget": 4096,
        "min_p": 0.05,
        "temperature": 0,
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
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = post_with_retry(payload, headers, api_url)
        output = response['choices'][0]['message']['content']
        print("\n🧾 最终汇总分析结果：\n")
        print(output)
    except Exception as e:
        print(f"⚠️ 汇总分析失败：{e}")
    return output

def Scannor(log_file_path, lines_per_chunk, max_workers, api_keys, error_dir, api_url):
    chunks = read_file_in_line_chunks(log_file_path, lines_per_chunk)
    print(f"共读取 {len(chunks)} 个日志块，开始并发分析...\n")

    # all_analysis = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx, chunk in enumerate(chunks):
            api_key = api_keys[idx % len(api_keys)]
            futures.append(executor.submit(analyze_log_chunk, chunk, idx, api_key, error_dir, api_url))

        # for future in futures:
        #     result = future.result()
        #     all_analysis.append(result)

    # output = summarize_all_chunks(all_analysis, api_keys[0],api_url)

def UpLoad_File(dir_path):
    file_ls = []
    for root, dirs, files in os.walk(dir_path):
        root_file_ls = [os.path.join(root, file) for file in files]
        for file in root_file_ls:
            file_ls.append(file)
    # 过滤 .DS_Store 文件
    file_ls = [file for file in file_ls if not file.endswith('.DS_Store')]
    return file_ls


# File_D(r'C:\Users\pc\Desktop\code\log\logcot\log\log\log_controller_0_Event.txt','https://api.siliconflow.cn/v1/chat/completions',r'C:/Users/pc/Desktop/code/log/logcot/Find_detect/output_529')
def All_file(root_path):

    file_list = UpLoad_File(root_path)
    for file in tqdm(file_list, desc="处理文件进度"):
        File_D(file,'https://api.siliconflow.cn/v1/chat/completions',r'./Find_detect/output_529')

if __name__ == "__main__":
    # 数据预处理
    from tqdm import tqdm
    All_file(r'.\log\log')
