"""
EOT 方法, 目前没用上
"""
import re
from drain3 import TemplateMiner
from drain3.file_persistence import FilePersistence
from drain3.template_miner_config import TemplateMinerConfig
import logging
from collections import defaultdict
import pandas as pd
from drain3.template_miner_config import TemplateMinerConfig
# from Find_detect.scan.File_Scannor import fliter_Scannor
import os
import numpy as np
import re
from drain3 import TemplateMiner
import requests
import json
import time


# 定义设备类型与正则表达式的映射（可根据实际需求扩展）
def get_device_regex(keyword: str,log_line:str):
    """
    根据设备类型返回对应的命名规则正则表达式
    :keyword: 设备类型关键字（如 "db"、"database"）
    :return: 匹配该设备命名规则的正则表达式字符串
    """
    # 定义设备类型与正则表达式的映射（可根据实际需求扩展）
    if keyword == "db":
        db_pattern=r"^(\w{3} \d{2} \d{2}:\d{2}:\d{2}) (\S+ \S+?)(?=: ):\s(.*)$"
        match = re.match(db_pattern, log_line)
        if match:
            return {
                "timestamp": match.group(1),
                "orient": match.group(2),
                "level": "UNKNOWN",
                "content": match.group(3)
            }
        return None  # 不匹配的行返回'
    if keyword == "database":
        database_pattern = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\w+)\] (database) (\w+) (\w+)\s+(.*)$"
        match = re.match(database_pattern, log_line)
        if match:
            return {
                "timestamp": match.group(1),
                "level": match.group(2),
                "database": match.group(3),
                "process_id": match.group(4),
                "thread_id": match.group(5),
                "content": match.group(6)
            }
        return None  # 不匹配的行返回
    if keyword == "Huawei":
        huawei_pattern = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(.*?)(?=\s+Step\d|$)"
        match = re.match(huawei_pattern, log_line)
        if match:
            return {
                "timestamp": match.group(1),
                "sequence": match.group(2),
                "alarm_id": match.group(3),
                "type": match.group(4),
                "level": match.group(5),
                "description": match.group(6)
            }
        return None  # 不匹配的行返回
    if keyword == "OS":
        OS_pattern = r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2}) (Dky_app_00) ([\w/]+(?:\[\d+\])?):\s(.*)$"
        match = re.match(OS_pattern, log_line)
        if match:
            return {
                "timestamp": match.group(1),
                "hostname": match.group(2),
                "process": match.group(3),
                "content": match.group(4)
            }
        return None  # 不匹配的行返回
#读取文件夹下所有文件
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

def contains_keyword(path: str, keywords: list) -> bool:
    """
    检查路径中是否包含任意关键字
    :param path: 文件/目录路径
    :param keywords: 关键字列表
    :return: 是否包含关键字
    """
    path_lower = path.lower()
    return any(keyword.lower() in path_lower for keyword in keywords)

def find_log_files(root_dir: str, keywords: list) -> list:
    """
    递归查找包含指定关键字的日志文件
    :param root_dir: 根目录路径

    # print(f"成功解析出 {len(parsed_logs)} 条日志记录")
    # print(all_log_files)
    """
    fl = []
    file_ls = UpLoad_File(root_dir)
    for i in file_ls:
        if contains_keyword(i, keywords):
            fl.append(i)
    # HWL = []
    # HWL = filter_common_elements(fl,file_ls)
    return fl


def filter_common_elements(list1: list, list2: list) -> list:
    """
    剔除两个列表中相同的元素，返回只包含不同元素的列表
    :param list1: 第一个列表
    :param list2: 第二个列表
    :return: 包含不同元素的列表
    """
    # 使用集合操作找出差异元素
    set1 = set(list1)
    set2 = set(list2)
    
    # 返回两个列表中独有的元素
    return list(set1.symmetric_difference(set2))

#通过关键字筛选日志文件并返回被规则化的日志列表
def parse_logs(dir_path: str, device_type = ['Huawei','db','database','OS']) -> list:
    """
    解析日志文件，返回日志列表
    device_type: 关键字
    :param file_path: 日志文件路径
    find_log_files('/Users/hy_mbp/PycharmProjects/LogDetect/log/log', ['Event'])
    """
    # file_list = UpLoad_File(dir_path)
    keyWords = ['Huawei','db','database','OS']#文件请重命名为以下特征的文件名
    db_list = find_log_files(dir_path, ['db'])
    huawei_list = find_log_files(dir_path, ['Event'])
    os_list = find_log_files(dir_path, ['sample'])
    database_list = find_log_files(dir_path, ['database'])
    print(os_list)
    print(database_list)
    print(db_list)
    db_log_list = []
    huawei_log_list = []
    os_log_list = []
    database_log_list = []
    for db_file in db_list:
        with open(db_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parsed = get_device_regex('db', line)
                if parsed:
                    db_log_list.append(parsed)
    # for huawei_file in huawei_list:
    #     with open(huawei_file, 'r', encoding='utf-8', errors='ignore') as f:
    #         for line in f:
    #             parsed = get_device_regex('Huawei', line)
    #             if parsed:
    #                 huawei_log_list.append(parsed)  
    # print(db_log_list)
    for os_file in os_list:
        with open(os_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parsed = get_device_regex('OS', line)
                if parsed:
                    os_log_list.append(parsed)
    for database_file in database_list:
        with open(database_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parsed = get_device_regex('database', line)
                if parsed:
                    database_log_list.append(parsed)
    return [db_log_list,huawei_log_list,os_log_list,database_log_list]
    
#Drain3 日志模板提取 （输入来源是我们自己的数据集）
def drain3(log_lists: list, output_path: str = "/Users/hy_mbp/PycharmProjects/LogDetect/Find_detect/summerize/drain3_results"):
    """
    使用drain3提取不同日志列表的模板
    :param log_lists: 包含多个日志列表的列表
    :param output_path: 结果输出目录
    #temp0来自db
    #temp1来自huawei
    #temp2来自OS
    #temp3来自database
    """
    config = TemplateMinerConfig()
    config.load("/Users/hy_mbp/PycharmProjects/LogDetect/Find_detect/defulte/drain3.ini")
    config.drain_sim_th = 0.7
    config.drain_max_depth = 5
    config.drain_max_children = 100
    
    # 为每种日志类型创建单独的模板提取器
    for i, log_list in enumerate(log_lists):
        if not log_list:
            continue
            
        persistence = FilePersistence(f"{output_path}_type{i}.json")
        template_miner = TemplateMiner(persistence, config)
        
        # 提取模板
        for log_item in log_list:
            log_content = log_item.get('content', '').strip()
            if log_content:
                template_miner.add_log_message(log_content)
        
        # 保存结果
        templates = template_miner.drain.clusters
        with open(f"{output_path}_type{i}_templates.txt", 'w') as f:
            for cluster in templates:
                f.write(f"Template: {cluster.get_template()}\n")
                f.write(f"Size: {cluster.size}\n\n")
# drain3(parse_logs('/Users/hy_mbp/PycharmProjects/LogDetect/log/log'))


def sge_analysis(log_data: list, analysis_type: str = "abnormal") -> dict:
    """
    应用SGE方法进行日志异常分析
    :param log_data: 解析后的日志列表
    :param analysis_type: 分析类型(abnormal/performance)
    :return: 分析结果字典
    """
    trajectories = []
    
    # 生成3条分析轨迹
    for i in range(3):
        trajectory = {
            "id": f"trajectory_{i+1}",
            "steps": [],
            "hypothesis": ""
        }
        
        # 轨迹1: 基于时间序列的异常检测
        if i == 0:
            trajectory["hypothesis"] = "时间序列异常检测"
            trajectory["steps"] = [
                "统计日志时间分布",
                "检测时间间隔异常",
                "标记异常时间点"
            ]
        
        # 轨迹2: 基于内容模式的异常检测
        elif i == 1:
            trajectory["hypothesis"] = "内容模式异常检测" 
            trajectory["steps"] = [
                "提取日志模板",
                "建立正常模式基线",
                "检测偏离基线的异常"
            ]
        
        # 轨迹3: 基于资源使用的异常检测
        else:
            trajectory["hypothesis"] = "资源使用异常检测"
            trajectory["steps"] = [
                "解析资源相关字段",
                "建立资源使用基线",
                "检测资源异常波动"
            ]
        
        trajectories.append(trajectory)
    
    # 执行分析并生成报告
    report = {
        "analysis_type": analysis_type,
        "trajectories": trajectories,
        "abnormal_findings": [],
        "suggestions": []
    }
    
    # 实际分析逻辑(示例)
    for log in log_data:
        # 这里添加实际分析代码
        pass
        
    return report


