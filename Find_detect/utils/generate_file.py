import os
import numpy as np
# dir_path = r'/Users/hy_mbp/Desktop/log_file'
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

def file2word(file_ls):
    word_ls = []
    for file in file_ls:
        with open(file, 'r') as f:
            word_ls.append(f.read())
    return word_ls
