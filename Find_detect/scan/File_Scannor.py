import pandas as pd
import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential
import re
import textwrap
from typing import List
from tqdm import tqdm
import time
import warnings
import requests
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

def File_D(file_name,api_url,OUTPUT_DIR):
    ROOT_PATH = './log'
    LOG_RELATIVE_PATH = file_name
    LOG_FILE_PATH = os.path.join(ROOT_PATH, LOG_RELATIVE_PATH)
    print(LOG_FILE_PATH)
    LINES_PER_CHUNK = 130
    MAX_WORKERS = 5
    API_KEYS = [
        "sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "sk-kbucebwhrsoimqttlosgtxncyvmuvdyioncbadavayiovrns",
        "sk-zzuykfebwbxkurfftzuvujqpwqzxxljegnxhhwtzddvwiigf",
        "sk-qgsqryixuqdmtzkgubxpvdzollysgtonnvcrwmikwegmaogn",
        "sk-hvxqvahoplbhdadwtaomisdamxqhquvummcfpvlafeovpqus",
    ]
    log_path_sanitized = LOG_RELATIVE_PATH.replace('/', '_')
    ERROR_DIR = os.path.join(OUTPUT_DIR, log_path_sanitized + "_errors")
    os.makedirs(ERROR_DIR, exist_ok=True)
    # Scannor(LOG_FILE_PATH, LINES_PER_CHUNK, MAX_WORKERS, API_KEYS, ERROR_DIR, api_url)





@retry(stop=stop_after_attempt(7), wait=wait_exponential(multiplier=2, min=2, max=100))
def post_with_retry(payload, headers, API_URL):
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def analyze_log_chunk(chunk, idx, api_key, error_dir, API_URL):
    payload = {
        "model": "THUDM/GLM-4-9B-0414",
        "stream": False,
        "max_tokens": 8192,
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
        "max_tokens": 8192,
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
        print("\n🧾 最终汇总分析结果：\n")
        print(response['choices'][0]['message']['content'])
    except Exception as e:
        print(f"⚠️ 汇总分析失败：{e}")

def Scannor(log_file_path, lines_per_chunk, max_workers, api_keys, error_dir, api_url):
    chunks = read_file_in_line_chunks(log_file_path, lines_per_chunk)
    print(f"共读取 {len(chunks)} 个日志块，开始并发分析...\n")
    all_analysis = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx, chunk in enumerate(chunks):
            api_key = api_keys[idx % len(api_keys)]
            futures.append(executor.submit(analyze_log_chunk, chunk, idx, api_key, error_dir, api_url))

        for future in futures:
            result = future.result()
            all_analysis.append(result)

    summarize_all_chunks(all_analysis, api_keys[0],api_url)


def UpLoad_File(dir_path):
    file_ls = []
    for root, dirs, files in os.walk(dir_path):
        root_file_ls = [os.path.join(root, file) for file in files]
        for file in root_file_ls:
            file_ls.append(file)
    file_ls1 = [file for file in file_ls if file.endswith('.DS_Store')]
    for name in file_ls1:
        file_ls.remove(name)
    return file_ls

#文件夹下的文件进行分段
def fliter_Scannor(dir_path,OUTPUT_DIR):
    file_ls = UpLoad_File(dir_path)
    print(file_ls) 
    # API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    # for file in file_ls:
    #     File_D(file,API_URL,OUTPUT_DIR)


# fliter_Scannor('./log/log','./Find_detect/output_529')  















def summerize_File(dir_path):
    all_text = ""
    file_ls = UpLoad_File(dir_path)
    for file in file_ls:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                all_text += f"\n--- 文件：{file} ---\n"
                all_text += f.read()
        except Exception as e:
            print(f"❌ 无法读取 {file}：{e}")
    return all_text

def summerize_Scannor(dir_path,api_url,api_key):
    content = summerize_File(dir_path)
    content1 = "分析以下不同类型错误日志"+content+"总结日志错误顺序并总结错误原因"

    payload = {
        "model": "Qwen/Qwen3-8B",
        "stream": False,
        "max_tokens": 8192,
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
                "content": content1
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = post_with_retry(payload, headers, api_url)
        print("\n🧾 最终汇总分析结果：\n")
        print(response['choices'][0]['message']['content'])
    except Exception as e:
        print(f"⚠️ 汇总分析失败：{e}")



File_D = ('/Users/hy_mbp/Desktop/WU/logcot/log/log/log_controller_0_Event.txt','./Find_detect/out_put_529')