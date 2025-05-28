import pandas as pd
import re

# 读取两个文件
df_raw = pd.read_excel("/Users/hy_mbp/PycharmProjects/LogDetect/raw_file_name.xlsx")
df_kernel = pd.read_excel("/Users/hy_mbp/PycharmProjects/LogDetect/log/OUTPUT_FILE/kernel.xlsx")

# 从 answer 中提取编号，例如 (14x-normal) 提取为 14
def extract_index(text):
    if isinstance(text, str):
        match = re.match(r'\((\d+)x-', text)
        if match:
            return int(match.group(1))
    return None

df_raw["index"] = df_raw["answer"].apply(extract_index)
print(df_raw["index"])
# 从 log 中寻找每个块起始行
block_starts = []
for i, row in enumerate(df_kernel["log"]):
    if isinstance(row, str):
        match = re.match(r'\((\d+)x-', row)
        if match:
            block_starts.append((int(match.group(1)), i))
print(block_starts)
# 构建块编号 -> log内容字典
blocks = {}
for idx, (block_num, start) in enumerate(block_starts):
    end = block_starts[idx + 1][1] if idx + 1 < len(block_starts) else len(df_kernel)
    blocks[block_num] = df_kernel.iloc[start:end]["log"].tolist()

print(blocks)
# 将块内容映射回 raw 表格
df_raw["log_block"] = df_raw["index"].apply(lambda x: blocks.get(x))

# print(df_raw)
# 保存结果
# df_raw.to_excel("merged_output.xlsx", index=False)

print("已生成文件：merged_output.xlsx")
