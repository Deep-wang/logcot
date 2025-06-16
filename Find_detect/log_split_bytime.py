import os
import re
import pandas as pd
from datetime import datetime, timedelta
import shutil
from tqdm import tqdm

def extract_timestamp(log_line):
    """
    Extract timestamp from log line
    Supports multiple common time formats
    """
    # Common timestamp format patterns
    patterns = [
        # 2025-04-23 14:42:36.060
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)',
        # 2025-04-23T11:52:18.732433+08:00
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2})?)',
        # Apr 21 16:12:24
        r'([A-Za-z]{3}\s+\d{2}\s+\d{2}:\d{2}:\d{2})',
        # Apr 23 13:04:01
        r'([A-Za-z]{3}\s+\d{2}\s+\d{2}:\d{2}:\d{2})',
        # 2025-04-23 15:01:56
        r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_line)
        if match:
            timestamp_str = match.group(1)
            try:
                # Handle timestamps with timezone
                if 'T' in timestamp_str:
                    # Remove timezone information
                    timestamp_str = timestamp_str.split('+')[0].split('-')[0]
                    return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
                
                # Handle timestamps with milliseconds
                if '.' in timestamp_str:
                    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                
                # Handle month abbreviation format
                if timestamp_str[0].isalpha():
                    month_map = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    parts = timestamp_str.split()
                    month = month_map[parts[0]]
                    day = parts[1]
                    time = parts[2]
                    year = datetime.now().year
                    timestamp_str = f"{year}-{month}-{day} {time}"
                    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Handle standard format
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
    
    return None

def split_logs_by_time(input_dir, output_dir, interval_hours=2):
    """
    Split log files by time intervals and simultaneously generate CSV files
    
    Args:
        input_dir: Input log files directory
        output_dir: Output directory
        interval_hours: Time interval (hours)
    """
    print(f"🔍 Starting to process log files...")
    print(f"📂 Input directory: {input_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⏰ Time interval: {interval_hours} hours")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all log files
    log_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.log', '.txt', 'auth', 'messages')) and not file.endswith('.csv'):
                log_files.append(os.path.join(root, file))
    
    print(f"📋 Found {len(log_files)} log files")
    
    # Process each log file
    for log_file in tqdm(log_files, desc="Processing log files"):
        print(f"\n📄 Processing file: {os.path.basename(log_file)}")
        
        # Read log file
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.readlines()
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            continue
        
        # Group logs by timestamp
        time_groups = {}
        current_group = None
        current_logs = []
        
        for log in logs:
            timestamp = extract_timestamp(log)
            if timestamp:
                # Calculate time group
                group_time = timestamp.replace(
                    minute=0, second=0, microsecond=0
                ) - timedelta(hours=timestamp.hour % interval_hours)
                
                if group_time != current_group:
                    # Save previous log group
                    if current_group and current_logs:
                        if current_group not in time_groups:
                            time_groups[current_group] = []
                        time_groups[current_group].extend(current_logs)
                    current_group = group_time
                    current_logs = []
                
                current_logs.append(log)
            else:
                # If current line has no timestamp, add to current group
                if current_group is not None:
                    current_logs.append(log)
        
        # Save the last group of logs
        if current_group and current_logs:
            if current_group not in time_groups:
                time_groups[current_group] = []
            time_groups[current_group].extend(current_logs)
        
        # Save grouped logs
        if time_groups:
            base_name = os.path.splitext(os.path.basename(log_file))[0]
            for group_time, group_logs in time_groups.items():
                # Create timestamp directory
                time_dir = os.path.join(
                    output_dir,
                    group_time.strftime('%Y%m%d_%H%M')
                )
                os.makedirs(time_dir, exist_ok=True)
                
                # Define output file name (without extension)
                output_base_name = os.path.join(
                    time_dir,
                    f"{base_name}_{group_time.strftime('%H%M')}"
                )

                # Save grouped logs (.log)
                output_log_file = output_base_name + '.log'
                with open(output_log_file, 'w', encoding='utf-8') as f:
                    f.writelines(group_logs)
                
                print(f"✅ Saved logs for time period {group_time} to: {output_log_file}")

                # Also generate .csv file
                if group_logs:
                    cleaned_logs = [log.strip() for log in group_logs if log.strip()]
                    if cleaned_logs:
                        output_csv_file = output_base_name + '.csv'
                        df = pd.DataFrame({'log': cleaned_logs})
                        df.to_csv(output_csv_file, index=False, encoding='utf-8')
                        print(f"✅ Generated corresponding CSV file: {output_csv_file}")
        else:
            print(f"⚠️ No valid timestamps found in file")
    
    print("\n🎉 Log splitting and CSV conversion completed!")
    print(f"📁 Results saved in: {output_dir}")

def main():
    # Set input and output directories
    input_dir = './log/log'  # Log files directory
    output_dir = './split_logs'  # Directory to save split logs
    
    # Split logs by 2-hour intervals
    split_logs_by_time(input_dir, output_dir, interval_hours=2)

if __name__ == "__main__":
    main() 