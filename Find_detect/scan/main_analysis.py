"""
分块分析
输出output529,里面包含诊断为错误日志的块，txt文件
主函数做时间分组，然后调用File_D函数，然后调用analyze_log_directory函数，然后保存分析结果到output529/analysis_result目录下
"""

import os
import sys
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path

# 添加上级目录到路径，以便导入LLMClient和其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from summerize import analyze_log_directory
from llm_client import LLMClient

# 导入日志预处理模块
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from log_preprocessor import LogTimeGrouper
import time

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
    all_analysis = Scannor(LOG_FILE_PATH, LINES_PER_CHUNK, MAX_WORKERS, API_KEYS, ERROR_DIR, api_url)
    return all_analysis


@retry(stop=stop_after_attempt(7), wait=wait_exponential(multiplier=2, min=2, max=100))
def post_with_retry(payload, headers, API_URL):
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def analyze_log_chunk(chunk, idx, api_key, error_dir, API_URL):
    # 创建LLM客户端实例
    llm = LLMClient(
        api_url=API_URL,
        api_key=api_key,
        model="THUDM/GLM-4-9B-0414",
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

    try:
        # 使用LLM客户端进行调用
        content = f"日志第 {idx + 1} 部分：\n{chunk}\n\n请明确标注该部分是否正确，正确写为：日志正确，异常写为：日志异常，标明错误时间并截取出现异常点附近15行日志并给出简单说明"
        result = llm.forward(content)
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

    all_analysis = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx, chunk in enumerate(chunks):
            api_key = api_keys[idx % len(api_keys)]
            futures.append(executor.submit(analyze_log_chunk, chunk, idx, api_key, error_dir, api_url))

        for future in futures:
            result = future.result()
            all_analysis.append(result)

    # output = summarize_all_chunks(all_analysis, api_keys[0],api_url)
    return all_analysis

def UpLoad_File(dir_path):
    file_ls = []
    for root, dirs, files in os.walk(dir_path):
        root_file_ls = [os.path.join(root, file) for file in files]
        for file in root_file_ls:
            file_ls.append(file)
    # 过滤 .DS_Store 文件
    file_ls = [file for file in file_ls if not file.endswith('.DS_Store')]
    return file_ls


def parse_time_range_from_filename(filename):
    """
    从文件名中解析时间范围信息
    
    Args:
        filename: 文件名，格式如 "czp_db1_auth_2025-04-23_1400-1600.log"
        
    Returns:
        tuple: (时间范围字符串, 开始时间datetime对象) 或 (None, None)
    """
    import re
    from datetime import datetime
    
    # 匹配时间范围格式：YYYY-MM-DD_HHMM-HHMM
    pattern = r'(\d{4}-\d{2}-\d{2}_\d{4}-\d{4})'
    match = re.search(pattern, filename)
    
    if match:
        time_range_str = match.group(1)
        try:
            # 解析开始时间用于排序
            date_part, time_part = time_range_str.split('_')
            start_time_str = time_part.split('-')[0]
            
            # 组合完整的开始时间
            start_datetime_str = f"{date_part} {start_time_str[:2]}:{start_time_str[2:]}"
            start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
            
            return time_range_str, start_datetime
        except Exception as e:
            print(f"  ⚠️ 解析时间失败 {filename}: {e}")
            return None, None
    
    return None, None


def group_files_by_time_range(file_list):
    """
    按时间范围对文件进行分组
    
    Args:
        file_list: 文件路径列表
        
    Returns:
        dict: {时间范围: [文件列表]}，按时间排序
    """
    from collections import defaultdict
    from datetime import datetime
    
    time_groups = defaultdict(list)
    time_order = {}  # 用于排序的时间映射
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        time_range, start_datetime = parse_time_range_from_filename(filename)
        
        if time_range and start_datetime:
            time_groups[time_range].append(file_path)
            if time_range not in time_order:
                time_order[time_range] = start_datetime
        # 移除unknown_time处理，无法解析时间的文件直接跳过

    # 按时间排序
    sorted_time_ranges = sorted(time_order.keys(), key=lambda x: time_order[x])
    
    # 返回有序字典
    ordered_groups = {}
    for time_range in sorted_time_ranges:
        ordered_groups[time_range] = time_groups[time_range]
    
    return ordered_groups


def process_files_by_time_batches(output_base_dir, api_url, output_dir):
    """
    按时间范围批量处理日志文件
    
    Args:
        output_base_dir: 预处理后的日志文件目录
        api_url: API URL
        output_dir: 输出目录
    """
    from tqdm import tqdm
    
    print("\n" + "="*60)
    print("🔍 开始按时间批量分析日志文件")
    print("="*60)
    
    # 获取所有分组后的日志文件
    file_list = UpLoad_File(output_base_dir)
    log_files = [f for f in file_list if f.endswith('.log')]
    
    if not log_files:
        print("❌ 未找到分组后的日志文件")
        return
    
    print(f"📁 发现 {len(log_files)} 个分组日志文件")
    
    # 按时间范围分组
    time_groups = group_files_by_time_range(log_files)
    
    print(f"📊 共分为 {len(time_groups)} 个时间批次")
    
    # 按时间顺序处理每个批次
    batch_num = 1
    total_batches = len(time_groups)
    
    for time_range, files in time_groups.items():
        print(f"\n🕒 处理时间批次 {batch_num}/{total_batches}: {time_range}")
        print(f"   包含 {len(files)} 个文件")
        
        # 显示当前批次的文件列表
        for file_path in files:
            filename = os.path.basename(file_path)
            print(f"   📝 {filename}")
        
        # 对当前时间批次的所有文件进行处理
        print(f"   🚀 开始分析时间批次 {time_range} 的文件...")
        All_analysis = []
        for file_path in tqdm(files, desc=f"批次{batch_num}处理进度", leave=False):
            try:
                output_dir = f'./Find_detect/output_529/{time_range}'
                all_analysis = File_D(file_path, api_url, output_dir)
                All_analysis.append(all_analysis)
                print(f"   ✅ 完成: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"   ❌ 处理失败 {os.path.basename(file_path)}: {e}")
        
        print(f"   🎉 时间批次 {time_range} 处理完成！")
        batch_num += 1

        # 调用大模型汇总分析结果
        print(f"   🚀 开始汇总分析时间批次 {time_range} 的文件...")
        dir = f'./Find_detect/output_529/{time_range}'
        final_result = analyze_log_directory(dir)                                                                   #     调用最后的复杂模型完整根因分析
        # 保存日志分析结果
        analysis_result_dir = './Find_detect/output_529/analysis_result'
        os.makedirs(analysis_result_dir, exist_ok=True)
        
        # 创建包含时间范围的文件名
        safe_time_range = time_range.replace(':', '-').replace(' ', '_')
        result_filename = f"analysis_{safe_time_range}.txt"
        result_filepath = os.path.join(analysis_result_dir, result_filename)
        
        # 保存分析结果到文件
        try:
            with open(result_filepath, 'w', encoding='utf-8') as f:
                f.write(f"时间批次: {time_range}\n")
                f.write("="*60 + "\n")
                f.write(final_result)
            print(f"   💾 分析结果已保存到: {result_filepath}")
        except Exception as e:
            print(f"   ❌ 保存分析结果失败: {e}")
        break   # todo: debug
        # print(final_result)
    
    print(f"\n🎯 所有时间批次处理完成！")
    print(f"📂 分析结果已保存到: {output_dir}")


# File_D(r'C:\Users\pc\Desktop\code\log\logcot\log\log\log_controller_0_Event.txt','https://api.siliconflow.cn/v1/chat/completions',r'C:/Users/pc/Desktop/code/log/logcot/Find_detect/output_529')
def All_file(root_path, output_base_dir='./Find_detect/preprocessed_logs', group_hours=2):
    """
    处理root_path中的所有日志文件，按时间分组保存
    
    Args:
        root_path: 输入日志文件目录
        output_base_dir: 输出基础目录
        group_hours: 时间分组间隔（小时）
    
    Returns:
        dict: 处理结果统计
    """
    print("🚀 开始日志时间分组处理...")

    # debug 如果里面有output_base_dir里log文件，就跳过下面的时间分组功能
    if os.path.exists(output_base_dir): 
        processing_stats = {}
    else:
        # 创建时间分组器
        grouper = LogTimeGrouper(group_hours=group_hours)
        
        # 获取所有日志文件
        file_list = UpLoad_File(root_path)
        log_files = [f for f in file_list if grouper._is_log_file(os.path.basename(f))]
        
        print(f"📁 发现 {len(file_list)} 个文件，其中 {len(log_files)} 个日志文件")
        
        # 创建输出目录
        os.makedirs(output_base_dir, exist_ok=True)

        # 清空输出目录中的所有文件
        if os.path.exists(output_base_dir):
            print(f"🧹 清空输出目录: {output_base_dir}")
            for filename in os.listdir(output_base_dir):
                file_path = os.path.join(output_base_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path) 
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path) 
                except Exception as e:
                    print(f"  ⚠️ 删除失败 {filename}: {e}")
            print("✅ 输出目录清空完成")
        
        # 处理统计
        processing_stats = {
            'total_files': len(log_files),
            'processed_files': 0,
            'total_groups': 0,
            'total_logs': 0,
            'failed_files': [],
            'grouped_files': []
        }
        
        # 使用进度条显示处理进度
        from tqdm import tqdm
        
        for file_path in tqdm(log_files, desc="📊 时间分组进度"):
            try:
                print(f"\n🔍 正在处理: {os.path.basename(file_path)}")
                
                # 按时间分组处理日志文件，传递基础目录用于生成唯一文件名
                grouped_logs = grouper.process_log_file(file_path, output_base_dir, base_dir=root_path)
                
                if grouped_logs:
                    # 统计信息
                    file_groups = len(grouped_logs)
                    file_logs = sum(len(logs) for logs in grouped_logs.values())
                    
                    processing_stats['processed_files'] += 1
                    processing_stats['total_groups'] += file_groups
                    processing_stats['total_logs'] += file_logs
                    
                    # 记录生成的分组文件
                    # 生成与_save_grouped_logs一致的唯一文件名前缀
                    try:
                        rel_path = os.path.relpath(file_path, root_path)
                        # 将路径分隔符替换为下划线，生成唯一前缀
                        unique_prefix = rel_path.replace(os.sep, '_').replace('/', '_').replace('\\', '_')
                        # 移除文件扩展名
                        unique_prefix = os.path.splitext(unique_prefix)[0]
                    except ValueError:
                        # 如果无法计算相对路径，使用文件名
                        unique_prefix = os.path.splitext(os.path.basename(file_path))[0]
                    
                    for group_key in grouped_logs.keys():
                        if grouped_logs[group_key]:
                            grouped_file_path = os.path.join(output_base_dir, f"{unique_prefix}_{group_key}.log")
                            if os.path.exists(grouped_file_path):
                                processing_stats['grouped_files'].append({
                                    'file': grouped_file_path,
                                    'group': group_key,
                                    'log_count': len(grouped_logs[group_key])
                                })
                    
                    print(f"  ✅ 完成分组: {file_groups} 个时间组，{file_logs} 条日志")
                    
                    # 生成该文件的时间分析报告（可选）
                    # report = grouper.generate_time_analysis_report(grouped_logs)
                    # report_path = os.path.join(output_base_dir, f"{base_name}_time_report.txt")
                    # with open(report_path, 'w', encoding='utf-8') as f:
                    #     f.write(report)
                        
                else:
                    print(f"  ⚠️ 未找到有效时间信息")
                    
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                processing_stats['failed_files'].append({
                    'file': file_path,
                    'error': str(e)
                })
                continue
        
        # 输出处理结果统计
        print("\n" + "="*60)
        print("🎯 处理结果统计")
        print("="*60)
        print(f"📂 输入目录: {root_path}")
        print(f"📂 输出目录: {output_base_dir}")
        print(f"⏰ 时间分组间隔: {group_hours} 小时")
        print(f"📄 总文件数: {processing_stats['total_files']}")
        print(f"✅ 处理成功: {processing_stats['processed_files']}")
        print(f"❌ 处理失败: {len(processing_stats['failed_files'])}")
        print(f"📊 生成时间组: {processing_stats['total_groups']}")
        print(f"📝 总日志条数: {processing_stats['total_logs']}")
        print(f"📁 生成分组文件: {len(processing_stats['grouped_files'])}")
        
        # 显示生成的分组文件列表
        if processing_stats['grouped_files']:
            print(f"\n📋 生成的分组文件列表:")
            for item in processing_stats['grouped_files']:
                filename = os.path.basename(item['file'])
                print(f"  📝 {filename}: {item['log_count']} 条日志")
        
        # 显示失败的文件
        if processing_stats['failed_files']:
            print(f"\n⚠️ 处理失败的文件:")
            for item in processing_stats['failed_files']:
                filename = os.path.basename(item['file'])
                print(f"  ❌ {filename}: {item['error']}")
        
        print(f"\n🎉 日志时间分组处理完成！")
        print(f"📂 所有分组文件已保存到: {output_base_dir}")

    # 对预处理后的日志进行按时间批量分析
    # 清空输出目录中的所有文件
    output_dir = r'./Find_detect/output_529'
    if os.path.exists(output_dir):
        print(f"🧹 清空输出目录: {output_dir}")
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path) 
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path) 
            except Exception as e:
                print(f"  ⚠️ 删除失败 {filename}: {e}")
    else:
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 创建输出目录: {output_dir}")

    start_time = time.time()
    
    process_files_by_time_batches(
        output_base_dir=output_base_dir,
        api_url='https://api.siliconflow.cn/v1/chat/completions',
        output_dir=output_dir
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\n⏱️ 程序运行时间: {execution_time:.2f} 秒")
    print(f"⏱️ 程序运行时间: {execution_time/60:.2f} 分钟")
    
    return processing_stats


if __name__ == "__main__":
    # 数据预处理
    All_file(r'.\log\log')
