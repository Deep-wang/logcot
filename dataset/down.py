from datasets import load_dataset
import json

def download_math500(save_path="math500.jsonl"):
    # 从 Hugging Face 加载 MATH‑500（共 500 道题 + 答案）
    ds = load_dataset("HuggingFaceH4/MATH-500", split="train")  # 可替换为 train、validation 等
    print(f"共 {len(ds)} 道题")

    # 将数据写入 JSON Lines 文件
    with open(save_path, "w", encoding="utf-8") as f:
        for item in ds:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"已保存至 {save_path}")



# requirements: pip install datasets

from datasets import load_dataset
import json

def download_aime24(save_path="aime24.jsonl"):
    # 加载 AIME 2024 数据集
    ds = load_dataset("HuggingFaceH4/aime_2024", split="all")
    print(f"共 {len(ds)} 条题目记录")

    # 保存为 JSON Lines 格式
    with open(save_path, "w", encoding="utf-8") as f:
        for item in ds:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"已保存至 {save_path}")


from datasets import load_dataset
import json

from datasets import load_dataset
import json
import os
import sys

from datasets import load_dataset
import json

def download_gpqa_main(save_path="gpqa_extended.jsonl", token=None):
    ds = load_dataset(
        "idavidrein/gpqa",
        "gpqa_extended",          # 正确的 config 名称
        split="train",
        use_auth_token=token  # 或 use_auth_token=True（前提是已 CLI 登录）
    )
    with open(save_path, "w", encoding="utf-8") as f:
        for item in ds:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved {len(ds)} items to {save_path}")

if __name__ == "__main__":
    # 检测是否在 Notebook 中运行
    notebook = False
    try:
        get_ipython
        notebook = True
    except NameError:
        pass

    download_gpqa_main(save_path="gpqa_extended.jsonl", token=os.environ.get("HUGGINGFACE_TOKEN"))


# if __name__ == "__main__":
#     download_gpqa(save_path="gpqa_main.jsonl", subset="gpqa_main")
#     # download_gpqa(save_path="gpqa_diamond.jsonl", subset="diamond")


