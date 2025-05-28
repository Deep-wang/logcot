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
    ROOT_PATH = '/Users/hy_mbp/PycharmProjects/LogDetect/log'
    LOG_RELATIVE_PATH = file_name
    LOG_FILE_PATH = os.path.join(ROOT_PATH, LOG_RELATIVE_PATH)
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
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    for file in file_ls:
        File_D(file,API_URL,OUTPUT_DIR)



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








# 基于Prompt的分析



def generate_prompt(prompt_header,logs: List[str],max_len=1000,no_reason=False) -> List[str]:
    prompt_parts_count=[]
    prompt_parts = []

    prompt=prompt_header
    log_count=0
    startStr=""
    for i, log in enumerate(logs):
        if no_reason:
            startStr+="("+str(i+1)+"x\n"
        else:
            startStr+="("+str(i+1)+"x-y\n"
        log_str = f"({i+1}) {log}"
        log_length = len(log_str)
        prompt_length=len(prompt)
        if log_length > max_len:
            print("warning: this log is too long")

        if prompt_length + log_length <= max_len:
            prompt += f" {log_str}"
            prompt_length += log_length + 1
            log_count+=1
            if i<(len(logs)-1) and (prompt_length+len(logs[i+1]))>=max_len:
                prompt_parts.append(prompt.replace("!!FormatControl!!",startStr).replace("!!NumberControl!!",str(log_count)))
                prompt_parts_count.append(log_count)
                log_count=0
                prompt=prompt_header
                startStr=""
                
                continue
            if i== (len(logs)-1):
                prompt_parts.append(prompt.replace("!!FormatControl!!",startStr).replace("!!NumberControl!!",str(log_count)))
                prompt_parts_count.append(log_count)
        else:
            if prompt!=prompt_header:
                log_count+=1
                prompt+=f" {log_str}"
                prompt_parts.append(prompt.replace("!!FormatControl!!",startStr).replace("!!NumberControl!!",str(log_count)))
                prompt_parts_count.append(log_count)
            else:
                prompt=prompt.replace("!!FormatControl!!",startStr)
                prompt=f"{prompt} ({i+1}) {log}"
                prompt_parts.append(prompt)
                prompt_parts_count.append(1)
            log_count=0
            prompt=prompt_header
            startStr=""
    return prompt_parts,prompt_parts_count


def reprompt(raw_file_name,j,df_raw_answer,api_key,api_url,temperature):
    prompt=df_raw_answer.loc[j,"prompt"]
    msgs=[]
    payload = {
        "model": "THUDM/GLM-4-9B-0414",
        "stream": False,
        "max_tokens": 8192,
        "enable_thinking": True,
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


def write_to_excel(raw_file_name,df_raw_answer: pd.DataFrame, logs: List[str],api_key,api_url) -> tuple:
    reprompt_num=0
    prompts=df_raw_answer['prompt'].tolist()
    log_numbers=extract_log_index(prompts)
    parsed_logs=df_raw_answer['answer'].tolist()
    parsed_logs_per_log = []
    for i, parsed_log in enumerate(parsed_logs):
        log_parts = parsed_log
        parsed_logs_per_log.append(log_parts)
        
    parsed_logs_df = pd.DataFrame()
    index=0
    # print(parsed_logs_per_log)
    for j, parsed_log in tqdm(enumerate(parsed_logs_per_log)):
        # print(str(parsed_log))
        # print(parsed_log)
        parsed_log = str(parsed_log)
        while 1:
            temperature=0.1
            try:
                pattern = r"\({0}\).*?\({1}\)"
                xx_list=[]
                log_number=log_numbers[j]
                for i in range(len(log_number)-1):
                    start=log_number[i]
                    end=log_number[i+1]
                    if start!=end-1:
                        print('start:',start,'end:',end)
                        continue
                    match=re.search(pattern.format(start,end),parsed_log.replace('\n',''))
                    print(match)
                    xx=match.group().split(f"({start})")[1].split(f"({end})")[0].strip()
                    xx_list.append(xx)
                last_log_number=log_number[-1]
                pattern=r"\({0}\).*".format(last_log_number)
                match=re.search(pattern,parsed_log.replace('\n',''))
                xx=match.group().split(f"({last_log_number})")[1].strip()
                xx_list.append(xx)
                for parsed_log_part in xx_list:
                    if parsed_log_part ==None or parsed_log_part=="":
                        continue
                    pred_raw=filter_numbers(parsed_log_part.replace('<*>','')).strip(' ')
                    pred_label=pred_raw
                    parsed_logs_df=parsed_logs_df.append({'log':logs[index],'pred':pred_label},ignore_index=True)
                    index+=1
                break
            except Exception as e:
                print(e,"reprompting...")
                temperature+=0.2
                parsed_log=reprompt(raw_file_name,j,df_raw_answer,api_key,api_url,temperature)
    parsed_logs_df.to_excel('/Users/hy_mbp/PycharmProjects/temp'+'Aligned_'+'final.xlsx',index=False)


def parse_logs(api_keys, api_url, prompt_parts: List[str], prompt_parts_count,raw_file_name) -> List[str]:
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
            "temperature": 0,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
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
    pd.DataFrame(data=list(zip(prompt_parts,parsed_logs)),columns=['prompt','answer']).to_excel('/Users/hy_mbp/PycharmProjects/temp/raw_file_name1.xlsx')
    return parsed_logs



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

def analyze(PROMPT_STRATEGIES,INPUT_FILE,OUTPUT_FILE,raw_file_name,api_url,api_key):
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEYS = [
        "sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        "sk-kbucebwhrsoimqttlosgtxncyvmuvdyioncbadavayiovrns",
        "sk-zzuykfebwbxkurfftzuvujqpwqzxxljegnxhhwtzddvwiigf",
        "sk-qgsqryixuqdmtzkgubxpvdzollysgtonnvcrwmikwegmaogn",
        "sk-hvxqvahoplbhdadwtaomisdamxqhquvummcfpvlafeovpqus",
    ]
    df = pd.read_excel(INPUT_FILE)
    if PROMPT_STRATEGIES == 'CoT':
        df=df.sample(frac=1).reset_index(drop=True)
        answer_desc="a binary choice between normal and abnormal"
        prompt_header="Classify the given log entries into normal an abnormal categories. Do it with these steps: \
        (a) Mark it normal when values (such as memory address, floating number and register value) in a log are invalid. \
        (b) Mark it normal when lack of information. (c) Never consider <*> and missing values as abnormal patterns. \
        (d) Mark it abnormal when and only when the alert is explicitly expressed in textual content (such as keywords like error or interrupt). \
        Concisely explain your reason for each log. Organize your answer to be the following format: !!FormatControl!!, where x is %s and y is the reason. \
        There are !!NumberControl!! logs, the logs begin: "%(answer_desc)
        logs=df['log'].tolist()
        ########### generate prompts ######################
        prompt_parts,prompt_parts_count = generate_prompt(prompt_header,logs,max_len=3000)
        ########### obtain raw answers from GPT ###########
        lst = parse_logs(API_KEYS,API_URL,prompt_parts,prompt_parts_count,raw_file_name)
        ########## Align each log with its results #######
        # df_raw_answer = pd.read_excel(raw_file_name)
        # write_to_excel(raw_file_name,df_raw_answer,logs,'sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx',API_URL)
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
            prompt_parts,prompt_parts_count = generate_prompt(prompt_header,logs,max_len=3000,no_reason=True)
            ########### obtain raw answers from GPT ###########
            # print(prompt_parts)
            # print(prompt_parts_count)
            # lts = parse_logs(API_KEYS,API_URL,prompt_parts,prompt_parts_count,'Candidate_%d_'%(i+1)+raw_file_name)
            ########## Align each log with its results #######
            # df_raw_answer = pd.read_excel(raw_file_name)
            # write_to_excel(raw_file_name+'Candidate_%d_'%(i+1)+'.xlsx',df_raw_answer,logs,'sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx',API_URL)

            
if __name__ == "__main__":
    analyze('CoT','/Users/hy_mbp/PycharmProjects/LogDetect/log/OUTPUT_FILE/kernel.xlsx','','/Users/hy_mbp/PycharmProjects/temp/raw_file_name1.xlsx','','')