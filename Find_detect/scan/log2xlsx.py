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
        safe_filename = file.replace('/', '_') 
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
    DIR_path = '/Users/hy_mbp/PycharmProjects/LogDetect/log/log'
    convert_log_to_excel(DIR_path)

if __name__ == "__main__":
    main()