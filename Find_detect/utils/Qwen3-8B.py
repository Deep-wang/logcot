import requests
import json
url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "Qwen/Qwen3-8B",
    "stream": False,
    "max_tokens": 8192,
    "enable_thinking": True,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "stop": [],
    "messages": [
        {
            "role": "user",
            "content": ""
        }
    ],


}
headers = {
    "Authorization": "Bearer sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
    "Content-Type": "application/json"
}
response = requests.request("POST", url, json=payload, headers=headers)
text = json.loads(response.text)
print(text['choices'][0]['message']['content'])