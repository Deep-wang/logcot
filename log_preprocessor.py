import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
from collections import defaultdict

class LogTimeExtractor:
    """日志时间提取器，支持多种时间格式"""
    
    def __init__(self):
        # 定义不同的时间格式正则表达式
        self.time_patterns = {
            # 格式1: Apr 23 14:56:46 (月 日 时:分:秒)
            'syslog_format': r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',
            
            # 格式2: 2025-04-23 14:42:48.038 (年-月-日 时:分:秒.毫秒)
            'standard_format': r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d{3})?)',
            
            # 格式3: 2025-04-23T11:54:00.805444+08:00 (ISO 8601格式)
            'iso_format': r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{6})?[+-]\d{2}:\d{2})',
            
            # 格式4: 仅日期时间，用于表格格式 2025-04-23 14:39:24
            'simple_datetime': r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        }
        
        # 月份映射
        self.month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
    
    def extract_time_from_line(self, log_line: str, current_year: int = 2025) -> Optional[datetime]:
        """
        从单行日志中提取时间信息
        
        Args:
            log_line: 日志行内容
            current_year: 当前年份，用于syslog格式的年份补充
            
        Returns:
            datetime对象或None
        """
        log_line = log_line.strip()
        
        # 尝试匹配各种格式
        for format_name, pattern in self.time_patterns.items():
            match = re.search(pattern, log_line)
            if match:
                time_str = match.group(1)
                try:
                    parsed_time = self._parse_time_string(time_str, format_name, current_year)
                    if parsed_time:
                        return parsed_time
                except Exception as e:
                    continue
        
        return None
    
    def _parse_time_string(self, time_str: str, format_name: str, current_year: int) -> Optional[datetime]:
        """解析时间字符串为datetime对象"""
        
        try:
            if format_name == 'syslog_format':
                # 处理 Apr 23 14:56:46 格式
                parts = time_str.split()
                month_str = parts[0]
                day = int(parts[1])
                time_part = parts[2]
                hour, minute, second = map(int, time_part.split(':'))
                
                month = int(self.month_map[month_str])
                return datetime(current_year, month, day, hour, minute, second)
                
            elif format_name == 'standard_format':
                # 处理 2025-04-23 14:42:48.038 格式
                if '.' in time_str:
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    
            elif format_name == 'iso_format':
                # 处理 2025-04-23T11:54:00.805444+08:00 格式
                # 移除时区信息进行简单解析
                # 先分离时区部分
                if '+' in time_str:
                    base_time = time_str.split('+')[0]
                elif time_str.count('-') > 2:  # 有时区的负号
                    # 找到最后一个'-'，它应该是时区分隔符
                    parts = time_str.split('-')
                    if len(parts) >= 4:  # 至少有年-月-日-时区
                        base_time = '-'.join(parts[:-1])
                    else:
                        base_time = time_str
                else:
                    base_time = time_str
                
                # 将T替换为空格
                if 'T' in base_time:
                    base_time = base_time.replace('T', ' ')
                
                # 处理微秒精度
                if '.' in base_time:
                    # 确保微秒部分不超过6位
                    dot_pos = base_time.find('.')
                    base_part = base_time[:dot_pos]
                    microsec_part = base_time[dot_pos+1:]
                    # 截取或填充到6位
                    if len(microsec_part) > 6:
                        microsec_part = microsec_part[:6]
                    else:
                        microsec_part = microsec_part.ljust(6, '0')
                    base_time = base_part + '.' + microsec_part
                    return datetime.strptime(base_time, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    return datetime.strptime(base_time, '%Y-%m-%d %H:%M:%S')
                    
            elif format_name == 'simple_datetime':
                # 处理 2025-04-23 14:39:24 格式
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                
        except Exception as e:
            pass
            
        return None

class LogTimeGrouper:
    """按时间分组日志处理器"""
    
    def __init__(self, group_hours: int = 2):
        """
        初始化分组器
        
        Args:
            group_hours: 分组时间间隔（小时）
        """
        self.group_hours = group_hours
        self.extractor = LogTimeExtractor()
    
    def process_log_file(self, log_file_path: str, output_dir: str = None, base_dir: str = None) -> Dict[str, List[str]]:
        """
        处理单个日志文件，按时间分组
        
        Args:
            log_file_path: 日志文件路径
            output_dir: 输出目录，如果指定则保存分组文件
            base_dir: 基础目录，用于生成唯一文件名
            
        Returns:
            按时间分组的日志字典
        """
        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"日志文件不存在: {log_file_path}")
            
        # 读取日志文件
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 按时间分组
        grouped_logs = self._group_logs_by_time(lines)
        
        # 如果指定输出目录，保存分组文件
        if output_dir:
            self._save_grouped_logs(grouped_logs, output_dir, log_file_path, base_dir)
            
        return grouped_logs
    
    def process_log_directory(self, input_dir: str, output_dir: str = None) -> Dict[str, Dict[str, List[str]]]:
        """
        处理整个目录的日志文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            
        Returns:
            按文件和时间分组的日志字典
        """
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
            
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        all_grouped_logs = {}
        
        # 遍历目录中的所有文件
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)
            
            # 跳过目录和非日志文件
            if os.path.isdir(file_path) or not self._is_log_file(filename):
                continue
                
            print(f"正在处理日志文件: {filename}")
            
            try:
                grouped_logs = self.process_log_file(file_path, output_dir, input_dir)
                all_grouped_logs[filename] = grouped_logs
                print(f"✅ {filename} 处理完成，共分为 {len(grouped_logs)} 个时间组")
            except Exception as e:
                print(f"❌ 处理 {filename} 时出错: {e}")
                
        return all_grouped_logs
    
    def _group_logs_by_time(self, lines: List[str]) -> Dict[str, List[str]]:
        """按时间分组日志行"""
        grouped_logs = defaultdict(list)
        current_group_key = None  # 记录当前的时间组
        
        for line in lines:
            if not line.strip():
                continue
                
            # 提取时间
            log_time = self.extractor.extract_time_from_line(line)
            
            if log_time:
                # 能够解析时间，计算时间组标识
                group_key = self._get_time_group_key(log_time)
                grouped_logs[group_key].append(line.strip())
                current_group_key = group_key  # 更新当前时间组
            else:
                # 无法提取时间的日志，放入当前时间组（如果有的话）
                if current_group_key:
                    grouped_logs[current_group_key].append(line.strip())
                # 如果还没有任何时间组，暂时跳过这行（通常是文件开头的一些无关信息）
                
        return dict(grouped_logs)
    
    def _get_time_group_key(self, log_time: datetime) -> str:
        """获取时间分组键"""
        # 计算该时间属于哪个时间组
        base_hour = (log_time.hour // self.group_hours) * self.group_hours
        group_start = log_time.replace(hour=base_hour, minute=0, second=0, microsecond=0)
        group_end = group_start + timedelta(hours=self.group_hours)
        
        return f"{group_start.strftime('%Y-%m-%d_%H%M')}-{group_end.strftime('%H%M')}"
    
    def _save_grouped_logs(self, grouped_logs: Dict[str, List[str]], output_dir: str, log_file_path: str, base_dir: str):
        """保存分组后的日志"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成唯一的文件名前缀
        if base_dir:
            # 计算相对于base_dir的相对路径
            try:
                rel_path = os.path.relpath(log_file_path, base_dir)
                # 将路径分隔符替换为下划线，生成唯一前缀
                unique_prefix = rel_path.replace(os.sep, '_').replace('/', '_').replace('\\', '_')
                # 移除文件扩展名
                unique_prefix = os.path.splitext(unique_prefix)[0]
            except ValueError:
                # 如果无法计算相对路径，使用文件名
                unique_prefix = os.path.splitext(os.path.basename(log_file_path))[0]
        else:
            unique_prefix = os.path.splitext(os.path.basename(log_file_path))[0]
        
        for group_key, logs in grouped_logs.items():
            if not logs:
                continue
                
            output_filename = f"{unique_prefix}_{group_key}.log"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(log + '\n')
                    
            print(f"  📝 保存时间组 {group_key}: {len(logs)} 条日志 -> {output_filename}")
    
    def _is_log_file(self, filename: str) -> bool:
        """判断是否为日志文件"""
        log_extensions = ['.log', '.txt', '.out', '']
        return any(filename.lower().endswith(ext) for ext in log_extensions)
    
    def generate_time_analysis_report(self, grouped_logs: Dict[str, List[str]]) -> str:
        """生成时间分析报告"""
        report = []
        report.append("=" * 60)
        report.append("日志时间分析报告")
        report.append("=" * 60)
        
        total_logs = sum(len(logs) for logs in grouped_logs.values())
        report.append(f"总日志条数: {total_logs}")
        report.append(f"时间分组数: {len(grouped_logs)}")
        report.append(f"分组间隔: {self.group_hours} 小时")
        report.append("-" * 60)
        
        # 按时间组排序
        sorted_groups = sorted(grouped_logs.items(), 
                             key=lambda x: x[0] if x[0] != 'unknown_time' else 'zzz')
        
        for group_key, logs in sorted_groups:
            report.append(f"时间组: {group_key}")
            report.append(f"  日志条数: {len(logs)}")
            if logs:
                # 显示该时间组的前几条日志作为示例
                report.append("  示例日志:")
                for i, log in enumerate(logs[:3]):
                    report.append(f"    {i+1}. {log[:100]}..." if len(log) > 100 else f"    {i+1}. {log}")
            report.append("-" * 40)
            
        return "\n".join(report)

def main():
    """主函数示例"""
    # 创建时间分组器（2小时为一组）
    grouper = LogTimeGrouper(group_hours=2)
    
    # 处理示例：处理单个文件
    # grouped_logs = grouper.process_log_file('sample.log', 'output/')
    
    # 处理示例：处理整个目录
    # all_grouped = grouper.process_log_directory('./log/log/', './log/preprocessed/')
    
    # 生成报告示例
    # report = grouper.generate_time_analysis_report(grouped_logs)
    # print(report)
    
    print("日志预处理模块已加载。使用方法:")
    print("1. grouper = LogTimeGrouper(group_hours=2)")
    print("2. grouped_logs = grouper.process_log_file('your_log.log', 'output_dir/')")
    print("3. report = grouper.generate_time_analysis_report(grouped_logs)")

if __name__ == "__main__":
    main() 