from openai import OpenAI
import os

client = OpenAI(api_key="sk-YDY2HpwyWystUICYh4ui9KhI6IY3b3aDU1HRJMsrT5WLz4H2",base_url='https://api.nuwaapi.com/v1') #=== 配置参数 ===

# 配置项
LOG_FILE_PATH = "/log/log/123.log"
CHUNK_SIZE = 10000  # 每块最多 10000 字符，避免 token 超限
MODEL = "gpt-4"

def read_file_in_chunks(path, chunk_size):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]

def analyze_log_chunk(chunk, idx):
    messages = [
        {"role": "system", "content": "你是专业的日志分析专家，请阅读以下日志并找出异常、错误原因。"},
        {"role": "user", "content": f"日志第 {idx + 1} 部分：\n{chunk}\n\n请指出其中是否有错误或异常，并分析原因。"}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2
    )
    return response.choices[0].message.content

def main():
    chunks = read_file_in_chunks(LOG_FILE_PATH, CHUNK_SIZE)
    all_analysis = []

    print(f"共读取 {len(chunks)} 个日志块，开始逐个分析...\n")

    for idx, chunk in enumerate(chunks):
        print(f"分析第 {idx + 1} 块日志...")
        analysis = analyze_log_chunk(chunk, idx)
        all_analysis.append(f"第 {idx + 1} 部分分析结果：\n{analysis}\n")

    summary_prompt = "\n\n".join(all_analysis)
    print("\n整理汇总所有分析...\n")

    # 汇总整体分析
    summary_messages = [
        {"role": "system", "content": "你是日志分析专家，请汇总多个日志片段的分析结果，提炼出总体错误原因及建议。"},
        {"role": "user", "content": summary_prompt}
    ]

    summary = client.chat.completions.create(
        model=MODEL,
        messages=summary_messages,
        temperature=0.2
    )

    print("\n🧾 最终汇总分析结果：\n")
    print(summary.choices[0].message.content)

if __name__ == "__main__":
    main()