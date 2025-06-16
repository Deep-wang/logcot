import os
import re
import argparse
from datetime import datetime, timedelta
import shutil
from tqdm import tqdm
import sys
import time
from log_split_bytime import split_logs_by_time, extract_timestamp

def get_log_source(log_file):
    """
    根据日志文件路径和内容判断日志来源
    """
    # 从文件路径判断
    if 'database' in log_file.lower():
        return 'database'
    elif 'auth' in log_file.lower():
        return 'auth'
    elif 'messages' in log_file.lower():
        return 'system'
    elif 'controller' in log_file.lower():
        return 'controller'
    elif 'kernel' in log_file.lower():
        return 'kernel'
    else:
        # 从文件内容判断
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = ''.join(f.readlines()[:10])
                if 'database' in first_lines.lower():
                    return 'database'
                elif 'auth' in first_lines.lower():
                    return 'auth'
                elif 'kernel' in first_lines.lower():
                    return 'kernel'
                elif 'controller' in first_lines.lower():
                    return 'controller'
                else:
                    return 'other'
        except:
            return 'other'

def get_time_dirs_in_range(split_dir, start_time, end_time):
    """
    获取指定时间范围内的所有时间目录
    
    Args:
        split_dir: 分割后的日志目录
        start_time: 开始时间 (YYYYMMDD_HHMM)
        end_time: 结束时间 (YYYYMMDD_HHMM)
    
    Returns:
        时间范围内的目录列表
    """
    try:
        start_dt = datetime.strptime(start_time, '%Y%m%d_%H%M')
        end_dt = datetime.strptime(end_time, '%Y%m%d_%H%M')
    except ValueError:
        print("❌ 时间格式错误，请使用 YYYYMMDD_HHMM 格式")
        sys.exit(1)
    
    print(f"\n🔍 搜索时间范围: {start_time} 到 {end_time}")
    print(f"📂 在目录 {split_dir} 中搜索")
    
    # 检查目录是否存在
    if not os.path.exists(split_dir):
        print(f"❌ 分割目录不存在: {split_dir}")
        return []
    
    # 列出目录中的所有内容
    print("\n📋 目录内容:")
    for item in os.listdir(split_dir):
        item_path = os.path.join(split_dir, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}")
        else:
            print(f"  📄 {item}")
    
    time_dirs = []
    for d in os.listdir(split_dir):
        if os.path.isdir(os.path.join(split_dir, d)):
            try:
                dir_dt = datetime.strptime(d, '%Y%m%d_%H%M')
                if start_dt <= dir_dt <= end_dt:
                    time_dirs.append(d)
                    print(f"✅ 找到匹配的时间目录: {d}")
            except ValueError:
                print(f"⚠️ 跳过非时间格式目录: {d}")
                continue
    
    return sorted(time_dirs)

def analyze_time_dir(time_dir_path):
    """
    分析指定时间目录下的日志
    
    Args:
        time_dir_path: 时间目录路径
    """
    print(f"\n📊 开始分析时间段: {os.path.basename(time_dir_path)}")
    
    try:
        import COT
        
        # 对每个来源的日志进行分析
        for source in ['database', 'auth', 'system', 'controller', 'kernel', 'other']:
            log_file = os.path.join(time_dir_path, f"{source}.log")
            if os.path.exists(log_file):
                print(f"\n📊 正在分析 {source} 日志...")
                
                # 设置COT的输入输出目录
                cot_output_dir = os.path.join(time_dir_path, f'cot_analysis_{source}')
                
                # 修改COT的全局变量
                COT.INPUT_DIR = time_dir_path
                COT.OUTPUT_DIR = cot_output_dir
                
                # 调用COT进行分析
                COT.main()
                
                print(f"✅ {source} 日志分析完成！结果保存在: {cot_output_dir}")
        
        print(f"\n✅ 时间段 {os.path.basename(time_dir_path)} 分析完成！")
        return True
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='分析指定时间段的日志文件')
    parser.add_argument('--split_dir', required=True, help='log_split_bytime.py分割后的目录路径')
    parser.add_argument('--start_time', required=True, help='开始时间 (格式: YYYYMMDD_HHMM)')
    parser.add_argument('--end_time', required=True, help='结束时间 (格式: YYYYMMDD_HHMM)')
    parser.add_argument('--output', default='./log/time_filtered', help='输出目录 (默认: ./log/time_filtered)')
    
    args = parser.parse_args()
    
    print(f"\n🔍 开始分析日志...")
    print(f"📂 分割目录: {args.split_dir}")
    print(f"⏰ 时间范围: {args.start_time} 到 {args.end_time}")
    print(f"📁 输出目录: {args.output}")
    
    # 如果分割目录不存在，创建它
    if not os.path.exists(args.split_dir):
        print(f"📁 创建分割目录: {args.split_dir}")
        os.makedirs(args.split_dir, exist_ok=True)
    
    # 获取时间范围内的所有时间目录
    time_dirs = get_time_dirs_in_range(args.split_dir, args.start_time, args.end_time)
    if not time_dirs:
        print(f"❌ 在指定时间范围内未找到任何日志目录")
        print("💡 提示: 请确保已经使用 log_split_bytime.py 分割了日志文件")
        sys.exit(1)
    
    print(f"\n📅 找到 {len(time_dirs)} 个时间目录:")
    for d in time_dirs:
        print(f"  - {d}")
    
    # 创建输出目录
    output_time_dir = os.path.join(args.output, f"{args.start_time}_{args.end_time}")
    os.makedirs(output_time_dir, exist_ok=True)
    print(f"\n📁 创建输出目录: {output_time_dir}")
    
    # 获取该时间范围内的所有日志文件
    source_logs = {
        'database': [],
        'auth': [],
        'system': [],
        'controller': [],
        'kernel': [],
        'other': []
    }
    
    total_logs = 0
    # 处理每个时间目录下的日志文件
    for time_dir in time_dirs:
        time_dir_path = os.path.join(args.split_dir, time_dir)
        print(f"\n📊 处理时间段: {time_dir}")
        
        # 检查目录是否存在
        if not os.path.exists(time_dir_path):
            print(f"❌ 时间目录不存在: {time_dir_path}")
            continue
        
        # 列出目录中的所有文件
        files = os.listdir(time_dir_path)
        print(f"📋 目录中的文件:")
        for f in files:
            print(f"  - {f}")
        
        for log_file in files:
            if log_file.endswith('.log'):
                log_path = os.path.join(time_dir_path, log_file)
                source = get_log_source(log_path)
                
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        logs = f.readlines()
                    source_logs[source].extend(logs)
                    total_logs += len(logs)
                    print(f"✅ 成功读取 {log_file}: {len(logs)} 行日志")
                except Exception as e:
                    print(f"❌ 读取文件失败 {log_file}: {e}")
    
    print(f"\n📊 总共读取了 {total_logs} 行日志")
    
    # 保存按来源组织的日志
    saved_files = 0
    for source, logs in source_logs.items():
        if logs:
            output_file = os.path.join(output_time_dir, f"{source}.log")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(logs)
            print(f"✅ 已保存 {source} 日志到: {output_file} ({len(logs)} 行)")
            saved_files += 1
    
    if saved_files == 0:
        print("\n⚠️ 警告: 没有找到任何日志内容")
        print("💡 提示: 请检查日志文件是否包含有效内容")
    else:
        print(f"\n✅ 成功保存了 {saved_files} 个日志文件")
    
    # 分析日志
    print("\n📊 开始COT分析...")
    analyze_time_dir(output_time_dir)
    
    print("\n🎉 分析完成！")

if __name__ == "__main__":
    main() 