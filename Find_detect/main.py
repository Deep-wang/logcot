
"""
初始版本，用于作为对比方法
"""


from scan.summerize import *
from scan.File_Scannor import *
# from scan.Thread_File import *


if __name__ == "__main__":
    api_url = 'https://api.siliconflow.cn/v1/chat/completions'
    api_key = 'sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx'
    OUTPUT_DIR = 'C:/Users/pc/Desktop/code/log/logcot/Find_detect/output_528'
    INPUT_DIR = 'C:/Users/pc/Desktop/code/log/logcot/log'
    print('开始文件读取分析分割')
    fliter_Scannor(INPUT_DIR,OUTPUT_DIR)
    print('开始总体分析')
    analyze_log_directory(OUTPUT_DIR)