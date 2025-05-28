"""
COT 方法，最新方法
"""

from math import log
from tkinter import W
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
# 基于Prompt的分析
from tenacity import retry, stop_after_attempt, wait_exponential
import scan.summerize as analyze_log_final

@retry(stop=stop_after_attempt(7), wait=wait_exponential(multiplier=2, min=2, max=100))
def post_with_retry(payload, headers, API_URL):
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def generate_prompt(prompt_header,logs: List[str],max_len=1000,no_reason=False) -> tuple:
    """
    生成prompt并保存对应的原始log及编号
    :return: (prompt_parts, prompt_parts_count, log_parts)
    """
    prompt_parts_count=[]
    prompt_parts = []
    log_parts = []  # 保存每个prompt对应的原始log列表
    prompt=prompt_header
    log_count=0
    current_logs = []  # 当前prompt对应的log列表
    
    for i, log in enumerate(logs):
        log_str = f"({i+1}) {log}"  # 为每个log添加编号
        log_length = len(log_str)
        prompt_length=len(prompt)

        if log_length > max_len:
            print("warning: this log is too long")

        if prompt_length + log_length <= max_len:
            prompt += f" {log_str}"
            current_logs.append(f"({i+1}) {log}")  # 保存编号和原始log
            prompt_length += log_length + 1
            log_count+=1
            
            if i<(len(logs)-1) and (prompt_length+len(logs[i+1]))>=max_len:
                prompt_parts.append(prompt.replace("!!NumberControl!!",str(log_count)))
                prompt_parts_count.append(log_count)
                log_parts.append(current_logs)
                log_count=0
                current_logs = []
                prompt=prompt_header
                continue
                
            if i== (len(logs)-1):
                prompt_parts.append(prompt.replace("!!NumberControl!!",str(log_count)))
                prompt_parts_count.append(log_count)
                log_parts.append(current_logs)
        else:
            if prompt!=prompt_header:
                log_count+=1
                prompt+=f" {log_str}"
                current_logs.append(f"({i+1}) {log}")
                prompt_parts.append(prompt.replace("!!NumberControl!!",str(log_count)))
                prompt_parts_count.append(log_count)
                log_parts.append(current_logs)
            else:
                prompt=f"{prompt} ({i+1}) {log}"
                current_logs.append(f"({i+1}) {log}")
                prompt_parts.append(prompt)
                prompt_parts_count.append(1)
                log_parts.append(current_logs)
                
            log_count=0
            current_logs = []
            prompt=prompt_header
            
    return prompt_parts, prompt_parts_count, log_parts




def reprompt(raw_file_name,j,df_raw_answer,api_key,api_url,temperature):
    prompt=df_raw_answer.loc[j,"prompt"]
    msgs=[]
    payload = {
        "model": "Qwen/Qwen3-8B",  #  "THUDM/GLM-4-9B-0414",
        "stream": False,
        "max_tokens": 8192,
        "enable_thinking": False,
        "thinking_budget": 4096,
        "min_p": 0.05,
        "temperature": temperature,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "stop": [],
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    parsed_log=""
    try:
        text = post_with_retry(payload, headers, api_url)
        parsed_log =  text['choices'][0]['message']['content']
    except Exception as e:
        print(f"error! 处理 prompt 失败 (密钥: {api_key[:10]}...): {e}")
        # return f"分析失败: {e}"

    df_raw_answer.loc[j,"answer"]=parsed_log
    df_raw_answer.to_excel(raw_file_name,index=False)
    return parsed_log

def extract_log_index(prompts):
    log_numbers=[]
    for prompt in prompts:
        log_number=re.findall(r'\((\d{1,4})',prompt.split("Organize your answer to be the following format")[1].split('a binary choice between')[0])
    # log_number=re.findall(r'\((\d+)\)',prompt.split("Organize your answer to be the following format")[1].split('a binary choice between')[0])
        log_numbers.append(sorted(list(set([int(x) for x in log_number]))))
    return log_numbers

def filter_numbers(text):
    pattern = r'\(\d+\)'
    return re.sub(pattern, '', text)

def write_to_excel(raw_file_name,df_raw_answer,logs):
    answer_list = df_raw_answer.iloc[:, 2].tolist()
    logs.insert(0, "log_content")
    # 匹配所有(x,y)格式的数据
    pattern = r'\((\d+),\s*([^)]*)\)'  # 匹配(数字,内容)
    matched_results = []
    for text in answer_list:
        matches = re.findall(pattern, str(text))
        for match in matches:
            matched_results.append((int(match[0]), match[1].strip()))  # 转换为(数字,内容)元组
    pattern1 = r'\((\d+),([^)]*)\)'  # (数字,内容)
    # pattern2 = r'\((\d+),\)'         # (数字,)
    # pattern3 = r'\((\d+),'
    # 使用集合来存储唯一结果
    unique_results = []
    for text in answer_list:
        # 定义三种匹配模式
        matches = re.findall(pattern1, str(text))
        for match in matches:
            unique_results.append(list(match))
    for ls in unique_results:
        ls[0]=int(ls[0])
        if ls[1]=='0' or ls[1]==' 0' or ls[1]=='0 ':
            ls[1]='normal'
        elif ls[1]=='1' or ls[1]==' 1' or ls[1]=='1 ':
            ls[1]='abnormal'
    sorted_results = sorted(unique_results, key=lambda x: x[0])[:-3]
    # print(sorted_results[:-3] )
    for ls in sorted_results:
        ls[0]=int(ls[0])
    # for i in range(len(sorted_results)):
    #     print(logs[i])
    ANSWER_LIST = []
    for rel in sorted_results:
        try:
            index=rel[0]
            result=rel[1]
            # print(index)
            log_content = logs[index]
            ANSWER_LIST.append([index, log_content, result])
        except:
            continue
    # 将结果写入Excel文件
    # 找出缺失的index
    all_indices = set(range(1, len(logs)))  # 所有可能的index
    found_indices = {x[0] for x in sorted_results}  # 已找到的index
    missing_indices = sorted(all_indices - found_indices)  # 缺失的index
    
    # 创建结果DataFrame
    ANSWER_LIST = []
    for rel in sorted_results:
        try:   # todo: 这块后续要解决掉
            index = rel[0]
            result = rel[1]
            log_content = logs[index] if index < len(logs) else ""
            ANSWER_LIST.append([index, log_content, result])
        except:
            continue
    
    # 添加缺失的index记录
    for missing_idx in missing_indices:
        log_content = logs[missing_idx] if missing_idx < len(logs) else ""
        ANSWER_LIST.append([missing_idx, log_content, 'UNKNOWN'])
    
    # 按index排序最终结果
    ANSWER_LIST = sorted(ANSWER_LIST, key=lambda x: x[0])
    OUT_raw_path = raw_file_name.replace('.xlsx', 'Aligned_final.xlsx')
    df = pd.DataFrame(ANSWER_LIST, columns=['index', 'log_content', 'result'])
    df.set_index('index', inplace=True)
    df.to_excel(OUT_raw_path, index=False)
    return OUT_raw_path

def parse_logs(api_keys, api_url, prompt_parts: List[str], prompt_parts_count,log_parts,raw_file_name) -> List[str]:
    parsed_logs = []
    
    # 定义单任务处理函数（接收 prompt 和对应的 api_key）
    def process_prompt(prompt, api_key):
        payload = {
            "model": "THUDM/GLM-4-9B-0414",
            "stream": False,
            "max_tokens": 8192,
            "enable_thinking": True,
            "thinking_budget": 4096,
            "min_p": 0.05,
            # "temperature": 0.4,
            # "top_p": 0.7,
            # "top_k": 50,
            # "frequency_penalty": 0.5,
            "temperature": 0.1,        # 降低随机性，提高准确性
            "top_p": 0.3,             # 更保守的选择
            "top_k": 20,              # 减少候选词数量
            "frequency_penalty": 0.2,  # 轻微减少重复
            "n": 1,
            "stop": [],
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            text = post_with_retry(payload, headers, api_url)
            return text['choices'][0]['message']['content']
        except Exception as e:
            print(f"error! 处理 prompt 失败 (密钥: {api_key[:10]}...): {e}")
            return f"分析失败: {e}"

    # 多线程并发处理（结合 API 密钥轮询）
    max_workers = min(5, len(api_keys))  # 根据密钥数量限制并发（避免单密钥超限制）
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 为每个 prompt 分配对应的 API 密钥（轮询）
        futures = []
        for idx, prompt in enumerate(prompt_parts):
            selected_key = api_keys[idx % len(api_keys)]  # 轮询选择密钥
            futures.append(executor.submit(process_prompt, prompt, selected_key))
        
        # 带进度条的结果收集
        for future in tqdm(as_completed(futures), total=len(prompt_parts), desc="日志解析进度"):
            parsed_log = future.result()
            parsed_logs.append(parsed_log)
    pd.DataFrame(data=list(zip(prompt_parts,parsed_logs,log_parts)),columns=['prompt','answer','logs']).to_excel(raw_file_name)
    return parsed_logs


def read_error_logs(file_path):
   df = pd.read_excel(file_path)
   unkonwn_logs = df[df['result'] == 'UNKNOWN']['log_content'].tolist()
   error_logs = df[df['result'] == 'abnormal']['log_content'].tolist()
   bool_logs = (df['result'] == 'abnormal') | (df['result'] == 'UNKNOWN')
   unknown_error_logs = df[bool_logs]['log_content'].tolist()
   return unkonwn_logs, error_logs, unknown_error_logs

def anylysis_error_logs(unknown_error_logs, api_keys, api_url, analyze_out_dir):
    def analyze_batch(batch, log_type, api_key):
        prompt = f"分析以下{str(log_type)}日志的共同特征和可能原因:\n" + "\n".join(str(batch))
        payload = {
            "model": "THUDM/GLM-4-9B-0414",
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            return {
                "type": log_type,
                "batch": batch,
                "analysis": response.json()['choices'][0]['message']['content']
            }
        except Exception as e:
            return {
                "type": log_type,
                "batch": batch,
                "error": f"分析失败: {e}"
            }

    # 确保输出目录存在
    os.makedirs(analyze_out_dir, exist_ok=True)
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=len(api_keys)) as executor:
        # 提交错误日志分析任务
        error_futures = []
        for i in range(0, len(error_logs), 10):
            batch = error_logs[i:i+10]
            selected_key = api_keys[i % len(api_keys)]
            error_futures.append(executor.submit(analyze_batch, batch, "错误", selected_key))
        
        # 提交未知日志分析任务
        unknown_futures = []
        for i in range(0, len(unkonwn_logs), 10):
            batch = unkonwn_logs[i:i+10]
            selected_key = api_keys[i % len(api_keys)]
            unknown_futures.append(executor.submit(analyze_batch, batch, "未知", selected_key))
        
        # 收集并保存结果
        results = []
        for future in as_completed(error_futures + unknown_futures):
            result = future.result()
            results.append(result)
            
            # 为每个批次创建单独的文件
            timestamp = int(time.time())
            filename = f"{result['type']}_analysis_{timestamp}.txt"
            filepath = os.path.join(analyze_out_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if 'analysis' in result:
                    f.write(f"=== {result['type']}日志分析结果 ===\n")
                    f.write(f"分析批次:\n{result['batch']}\n\n")
                    f.write(f"分析结果:\n{result['analysis']}\n")
                else:
                    f.write(f"=== {result['type']}日志分析失败 ===\n")
                    f.write(f"错误信息:\n{result['error']}\n")
    print(results)
    return results



# unkonwn_logs, error_logs = read_error_logs('/Users/hy_mbp/PycharmProjects/temp/Aligned_final.xlsx')
# anylysis_error_logs(unkonwn_logs, error_logs, API_KEYS, API_URL)


def analyze(PROMPT_STRATEGIES,INPUT_FILE,raw_file_name,API_URL,API_KEYS,analyze_log_directory):
    
    df = pd.read_excel(INPUT_FILE)
    if PROMPT_STRATEGIES == 'CoT':
        df=df.sample(frac=1).reset_index(drop=True)
        # answer_desc="a binary choice between normal and abnormal"
        # prompt_header="Classify the given log entries into normal and abnormal categories. Do it with these steps: \
        # (a) Mark it normal when values (such as memory address, floating number and register value) in a log are invalid. \
        # (b) Mark it normal when lack of information. (c) Never consider <*> and missing values as abnormal patterns. \
        # (d) Mark it abnormal when and only when the alert is explicitly expressed in textual content (such as keywords like error or interrupt). \
        # Common label prompts do not explan and cannot be skipped. Organize your answer to be the following format: (x,y) x is log index and y is a binary choice between normal and abnormal \
        # There are !!NumberControl!! logs, the logs begin: "

        prompt_header='''You are a log anomaly classifier.

        You will be given a list of log entries, each with a unique index.  
        Your task is to determine whether each log is **abnormal (1)** or **normal (0)**.  
        Only output in the following format, without any extra explanation or comments.

        ## Output Format:
        (log_idx, status)

        ## Output Rules:
        - status must be 1 if the log entry indicates an error, failure, crash, or unusual behavior.
        - status must be 0 if the log entry is a normal operation or informational message.
        - Output **only** a list of tuples. No extra text or explanation.

        ## Input Logs:
        '''
        logs=df['log'].tolist()

        ########## generate prompts ######################
        prompt_parts,prompt_parts_count,log_parts= generate_prompt(prompt_header,logs,max_len=5000)    
        ########## obtain raw answers from GPT ###########
        lst = parse_logs(API_KEYS,API_URL,prompt_parts,prompt_parts_count,log_parts,raw_file_name)
        ######### Align each log with its results #######
        df_raw_answer = pd.read_excel(raw_file_name)
        OUT_raw_path = write_to_excel(raw_file_name,df_raw_answer,logs)
        unkonwn_logs, error_logs, unknown_error_logs = read_error_logs(OUT_raw_path)
        # results = anylysis_error_logs(unknown_error_logs, API_KEYS, API_URL,analyze_log_directory)
        return {'unkonwn_logs':unkonwn_logs, 'error_logs':error_logs, 'unknown_error_logs':unknown_error_logs}

        # write_to_excel(raw_file_name,df_raw_answer,logs,'sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx',API_URL)
    # region 
    # if PROMPT_STRATEGIES == 'InContext':
    #     df_examples=pd.read_excel(EXAMPLE_FILE)
    #     df=df.sample(frac=1).reset_index(drop=True)
    #     answer_desc="a binary choice between 0 and 1"
    #     examples=' '.join(["(%d) Log: %s. Category: %s"%(i+1,df_examples.loc[i,'log'],int(df_examples.loc[i,'label']=='abnormal')) for i in range(len(df_examples))])
    #     prompt_header="Classify the given log entries into 0 and 1 categories based on semantic similarity to the following labelled example logs: %s.\
    #     Organize your answer to be the following format: !!FormatControl!!, where x is %s. There are !!NumberControl!! logs, the logs begin: "%(examples,answer_desc)
    #     logs=df['log'].tolist()
    #     ########### generate prompts ######################
    #     prompt_parts,prompt_parts_count = generate_prompt(prompt_header,logs,max_len=3000,no_reason=True)
    #     ########### obtain raw answers from GPT ###########
    #     parse_logs = parse_logs(OUTPUT_FILE,prompt_parts,prompt_parts_count)
    #     ########### Align each log with its results #######
    #     df_raw_answer = pd.read_excel(OUTPUT_FILE)
    #     write_to_excel(OUTPUT_FILE,df_raw_answer,logs)   
    # endregion

    if PROMPT_STRATEGIES == "Self":
        #candidate selection
        df=df[:100]
        prompt_candidates=[]
        with open('/Users/hy_mbp/PycharmProjects/LogDetect/Find_detect/prompt_candidates.txt') as f:
            for line in f.readlines():
                prompt_candidates.append(line.strip('\n'))
        for i,prompt_candidate in tqdm(enumerate(prompt_candidates)):
            print('prompt %d'%(i+1))
            answer_desc="a parsed log template"
            prompt_header = "%s Organize your answer to be the following format: !!FormatControl!!, where x is %s. There are !!NumberControl!! logs, the logs begin: "%(prompt_candidate,answer_desc)
            logs=df['log'].tolist()
            ########### generate prompts ######################
            prompt_parts,prompt_parts_count,log_parts = generate_prompt(prompt_header,logs,max_len=3000,no_reason=True)
            ########### obtain raw answers from GPT ###########
            # print(prompt_parts)
            # print(prompt_parts_count)
            # lts = parse_logs(API_KEYS,API_URL,prompt_parts,prompt_parts_count,'Candidate_%d_'%(i+1)+raw_file_name)
            ########## Align each log with its results #######
            # df_raw_answer = pd.read_excel(raw_file_name)
            # write_to_excel(raw_file_name+'Candidate_%d_'%(i+1)+'.xlsx',df_raw_answer,logs,'sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx',API_URL)
        return None


# analyze('CoT','/Users/hy_mbp/PycharmProjects/LogDetect/log/OUTPUT_FILE/kernel.xlsx','/Users/hy_mbp/PycharmProjects/temp/raw_file_name1.xlsx','','')

import pandas as pd
import os
import numpy as np

def UpLoad_File(dir_path):
    file_ls = []
    for root, dirs, files in os.walk(dir_path):
        root_file_ls = [os.path.join(root, file) for file in files]
        for file in root_file_ls:
            file_ls.append(file)
    # 过滤 .DS_Store 文件
    file_ls = [file for file in file_ls if not file.endswith('.DS_Store')]
    return file_ls

def convert_log_to_excel(DIR_path):
    # 统一输出目录（避免路径拼接错误）
    OUTPUT_DIR = os.path.join(DIR_path, 'OUTPUT_FILE')
    os.makedirs(OUTPUT_DIR, exist_ok=True)  # 确保输出目录存在
    
    file_ls = UpLoad_File(DIR_path)
    for file in file_ls:
        # 生成安全的 Excel 文件名（替换路径中的斜杠为下划线）
        safe_filename = os.path.basename(file).replace('/', '_') 
        safe_filename = safe_filename.replace('.', '_') + '.xlsx'  # 替换 Windows 路径分隔符
        OUTPUT_EXCEL_PATH = os.path.join(OUTPUT_DIR, safe_filename)
        
        # 读取日志文件（兼容非 UTF-8 编码，忽略无法解码的字符）
        try:
            with open(file, 'r', encoding='gbk', errors='ignore') as f:
                logs = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"警告：文件 {file} 读取失败，错误：{str(e)}，跳过处理。")
            continue
        
        # 保存为 Excel
        df = pd.DataFrame({'log': logs})
        df.to_excel(OUTPUT_EXCEL_PATH, index=False)
        print(f"转换完成！Excel 文件已保存至：{OUTPUT_EXCEL_PATH}")


def main():
    # 设置默认编码为UTF-8，避免Windows下的GBK编码问题
    import sys
    import io

    import os
    import platform
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEYS = [
        "sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "sk-kbucebwhrsoimqttlosgtxncyvmuvdyioncbadavayiovrns",
        "sk-zzuykfebwbxkurfftzuvujqpwqzxxljegnxhhwtzddvwiigf",
        "sk-qgsqryixuqdmtzkgubxpvdzollysgtonnvcrwmikwegmaogn",
        "sk-hvxqvahoplbhdadwtaomisdamxqhquvummcfpvlafeovpqus",
    ]
    if platform.system() == "Darwin":
        # macOS 系统
        INPUT_DIR = './log/OUTPUT_FILE'
        OUTPUT_DIR = './Find_detect/output_528'  
        PROMPT_STRATEGIES = 'CoT'
        analyze_log_path = './Find_detect/output_528'
    elif platform.system() == "Windows":
        # Windows 系统
        INPUT_DIR = "C:\\Users\\yourname\\somepath"
        OUTPUT_DIR = './Find_detect/output_528'  
        PROMPT_STRATEGIES = 'CoT'
        analyze_log_path = './Find_detect/output_528'
    else:
        # 其他系统（如 Linux）
        INPUT_DIR = '/home/yourname/somepath'
        OUTPUT_DIR = './Find_detect/output_528'  
        PROMPT_STRATEGIES = 'CoT'
        analyze_log_path = './Find_detect/output_528'

    file_list = UpLoad_File(INPUT_DIR)
    # file_list = file_list[:1]   # debug 
    Error_logs = []
    for i, file in enumerate(file_list):
        INPUT_FILE = file
        # INPUT_FILE = file
        raw_file_name = os.path.join(OUTPUT_DIR, os.path.basename(file).replace('.xlsx', '_raw.xlsx'))
        print(raw_file_name)
        error_log = analyze(PROMPT_STRATEGIES, INPUT_FILE, raw_file_name, API_URL, API_KEYS,analyze_log_path)
        Error_logs.append(error_log)
    # 根据每个日志的分析result和error_logs，再次调用最终模型完成最终的分析
    error_logs = []
    for i in range(len(Error_logs)): 
        error_logs.extend(Error_logs[i]['unknown_error_logs'])
    error_logs = '\n'.join(error_logs)


    # 将error_logs保存为txt文件
    # error_logs_file = os.path.join(OUTPUT_DIR, 'error_logs.txt')
    # with open(error_logs_file, 'w', encoding='utf-8') as f:
    #     f.write(error_logs)
    # print(f"错误日志已保存至: {error_logs_file}")

    analyze_log_final.analyze_log_directory(error_logs, option='str')
    
if __name__ == "__main__":
    main()