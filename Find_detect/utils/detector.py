from openai import OpenAI
import os

# 设置 API Key（强烈建议使用环境变量方式）
client = OpenAI(api_key="sk-YDY2HpwyWystUICYh4ui9KhI6IY3b3aDU1HRJMsrT5WLz4H2",base_url='https://api.nuwaapi.com/v1') #=== 配置参数 ===
LOG_FILE_PATH = "/log/log/123.log"  # 替换为你的日志文件路径
MAX_LINES = 140  # 控制读取的日志行数

# === 函数：提取日志内容 ===
def load_log_tail(file_path, max_lines=100):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return "".join(lines[-max_lines:])

# === 函数：发送日志并提出问题 ===
def ask_log_question(log_text, question):
    messages = [
        {"role": "system", "content": "你是一个擅长定位日志错误的运维专家。请从日志中找出异常并提供清晰解释。"},
        {"role": "user", "content": f"以下是日志片段：\n{log_text}\n\n请分析：{question}"}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.3
    )
    return response.choices[0].message.content

# === 主程序 ===
if __name__ == "__main__":
    print("读取日志内容中...")
    log_data = load_log_tail(LOG_FILE_PATH, MAX_LINES)

    print("日志加载完成。请输入你要询问的问题，例如：'分析错误原因' 或 '是否存在网络异常？'\n")
    user_question = input("请输入你的问题：")

    print("\nAI 正在分析，请稍候...\n")
    result = ask_log_question(log_data, user_question)
    print("\n--- 分析结果 ---")
    print(result)