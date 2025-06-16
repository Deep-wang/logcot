import pandas as pd
import os

def UpLoad_File(dir_path):
    file_ls = []
    for root, dirs, files in os.walk(dir_path):
        root_file_ls = [os.path.join(root, file) for file in files]
        for file in root_file_ls:
            file_ls.append(file)
    # 过滤 .DS_Store 文件
    file_ls = [file for file in file_ls if not file.endswith('.DS_Store')]
    return file_ls

def convert_log_to_csv(DIR_path):
    # 将日志文件转换为 CSV，并保存在与原文件相同的目录中
    file_ls = UpLoad_File(DIR_path)
    for file in file_ls:
        # 生成与原文件同目录、同名的 CSV 文件路径
        base, _ = os.path.splitext(file)
        OUTPUT_CSV_PATH = base + '.csv'
        
        # 读取日志文件（兼容非 UTF-8 编码，忽略无法解码的字符）
        try:
            with open(file, 'r', encoding='gbk', errors='ignore') as f:
                logs = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print(f"警告：文件 {file} 读取失败，错误：{str(e)}，跳过处理。")
            continue
        
        # 如果文件为空，则跳过
        if not logs:
            continue
            
        # 保存为 CSV
        df = pd.DataFrame({'log': logs})
        df.to_csv(OUTPUT_CSV_PATH, index=False)
        print(f"转换完成！CSV 文件已保存至：{OUTPUT_CSV_PATH}")

def main():
    DIR_path = './log/log'
    convert_log_to_csv(DIR_path)

if __name__ == "__main__":
    main()