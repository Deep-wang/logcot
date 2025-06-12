import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import copy


class LLMClient:
    """
    大模型客户端类，用于调用API接口
    支持单次调用和多轮对话功能
    """
    
    def __init__(
        self,
        api_url="https://api.siliconflow.cn/v1/chat/completions",
        api_key="sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
        model="THUDM/GLM-4-9B-0414",
        stream=False,
        max_tokens=8192,
        enable_thinking=True,
        thinking_budget=4096,
        min_p=0.1,
        temperature=0.1,
        top_p=0.3,
        top_k=20,
        frequency_penalty=0.1,
        presence_penalty=0.0,
        n=1,
        stop=None,
        retry_attempts=7,
        retry_wait_multiplier=2,
        retry_wait_min=2,
        retry_wait_max=100,
        max_history_length=50,  # 最大历史对话轮数
        auto_truncate=True      # 是否自动截断过长的对话历史
    ):
        """
        初始化LLM客户端
        
        Args:
            api_url: API调用地址
            api_key: API密钥
            model: 模型名称
            stream: 是否流式输出
            max_tokens: 最大输出token数
            enable_thinking: 是否启用思考模式
            thinking_budget: 思考预算token数
            min_p: 最小概率阈值
            temperature: 温度参数，控制输出随机性
            top_p: 核采样参数
            top_k: Top-K采样参数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
            n: 生成回复数量
            stop: 停止词列表
            retry_attempts: 重试次数
            retry_wait_multiplier: 重试等待时间倍数
            retry_wait_min: 最小等待时间
            retry_wait_max: 最大等待时间
            max_history_length: 最大历史对话轮数
            auto_truncate: 是否自动截断过长的对话历史
        """
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.stream = stream
        self.max_tokens = max_tokens
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget
        self.min_p = min_p
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.n = n
        self.stop = stop if stop is not None else []
        
        # 重试配置
        self.retry_attempts = retry_attempts
        self.retry_wait_multiplier = retry_wait_multiplier
        self.retry_wait_min = retry_wait_min
        self.retry_wait_max = retry_wait_max
        
        # 多轮对话配置
        self.max_history_length = max_history_length
        self.auto_truncate = auto_truncate
        
        # 对话历史存储
        self.conversation_history = []
        self.system_prompt = None
        
        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(7), wait=wait_exponential(multiplier=2, min=2, max=100))
    def _post_with_retry(self, payload):
        """
        带重试机制的POST请求
        
        Args:
            payload: 请求载荷
            
        Returns:
            dict: API响应
        """
        response = requests.post(self.api_url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def forward(self, content, system_prompt=None, role="user"):
        """
        前向推理，调用大模型获取响应（单次调用，不保存历史）
        
        Args:
            content: 用户输入内容
            system_prompt: 系统提示词（可选）
            role: 消息角色，默认为"user"
            
        Returns:
            str: 大模型输出的文本内容
            
        Raises:
            Exception: 调用API失败时抛出异常
        """
        # 构建消息列表
        messages = []
        
        # 添加系统提示词（如果提供）
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 添加用户消息
        messages.append({
            "role": role,
            "content": content
        })
        
        return self._call_api(messages)
    
    def chat(self, content, role="user"):
        """
        多轮对话功能，会保存对话历史
        
        Args:
            content: 用户输入内容
            role: 消息角色，默认为"user"
            
        Returns:
            str: 大模型输出的文本内容
            
        Raises:
            Exception: 调用API失败时抛出异常
        """
        # 添加用户消息到历史
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # 构建完整的消息列表
        messages = self._build_messages_with_history()
        
        # 调用API
        response = self._call_api(messages)
        
        # 将助手回复添加到历史
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # 检查历史长度并自动截断
        if self.auto_truncate:
            self._truncate_history()
        
        return response
    
    def _call_api(self, messages):
        """
        调用API的核心方法
        
        Args:
            messages: 消息列表
            
        Returns:
            str: API响应内容
        """
        # 构建请求载荷
        payload = {
            "model": self.model,
            "stream": self.stream,
            "max_tokens": self.max_tokens,
            "enable_thinking": self.enable_thinking,
            "thinking_budget": self.thinking_budget,
            "min_p": self.min_p,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "n": self.n,
            "stop": self.stop,
            "messages": messages,
        }
        
        try:
            # 调用API
            response = self._post_with_retry(payload)
            # 提取响应内容
            result = response['choices'][0]['message']['content']
            return result
            
        except Exception as e:
            raise Exception(f"LLM调用失败: {e}")
    
    def _build_messages_with_history(self):
        """
        构建包含历史对话的消息列表
        
        Returns:
            list: 完整的消息列表
        """
        messages = []
        
        # 添加系统提示词（如果有）
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # 添加对话历史
        messages.extend(self.conversation_history)
        
        return messages
    
    def _truncate_history(self):
        """
        截断过长的对话历史
        保留最近的对话，确保不超过最大长度限制
        """
        if len(self.conversation_history) > self.max_history_length:
            # 保留最近的对话
            excess_count = len(self.conversation_history) - self.max_history_length
            self.conversation_history = self.conversation_history[excess_count:]
            print(f"⚠️ 对话历史已截断，移除了 {excess_count} 条早期消息")
    
    def set_system_prompt(self, system_prompt):
        """
        设置系统提示词（用于多轮对话）
        
        Args:
            system_prompt: 系统提示词内容
        """
        self.system_prompt = system_prompt
        print(f"✅ 系统提示词已设置")
    
    def clear_history(self):
        """
        清空对话历史
        """
        self.conversation_history = []
        print("🧹 对话历史已清空")
    
    def get_history(self, format_type="list"):
        """
        获取对话历史
        
        Args:
            format_type: 返回格式，"list"返回原始列表，"text"返回格式化文本
            
        Returns:
            list or str: 对话历史
        """
        if format_type == "text":
            history_text = ""
            for i, msg in enumerate(self.conversation_history):
                role_emoji = "🧑" if msg["role"] == "user" else "🤖"
                history_text += f"{role_emoji} {msg['role'].title()}: {msg['content']}\n\n"
            return history_text
        else:
            return copy.deepcopy(self.conversation_history)
    
    def get_history_length(self):
        """
        获取当前对话历史长度
        
        Returns:
            int: 对话历史中的消息数量
        """
        return len(self.conversation_history)
    
    def save_conversation(self, filepath):
        """
        保存对话到文件
        
        Args:
            filepath: 保存文件路径
        """
        conversation_data = {
            "system_prompt": self.system_prompt,
            "conversation_history": self.conversation_history,
            "model": self.model,
            "timestamp": self._get_timestamp()
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            print(f"💾 对话已保存到: {filepath}")
        except Exception as e:
            print(f"❌ 保存对话失败: {e}")
    
    def load_conversation(self, filepath):
        """
        从文件加载对话
        
        Args:
            filepath: 对话文件路径
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            self.system_prompt = conversation_data.get("system_prompt")
            self.conversation_history = conversation_data.get("conversation_history", [])
            
            print(f"📂 对话已从 {filepath} 加载")
            print(f"📊 加载了 {len(self.conversation_history)} 条历史消息")
            
        except Exception as e:
            print(f"❌ 加载对话失败: {e}")
    
    def _get_timestamp(self):
        """
        获取当前时间戳
        
        Returns:
            str: 格式化的时间戳
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def start_interactive_chat(self):
        """
        启动交互式聊天模式
        """
        print("🚀 进入交互式聊天模式")
        print("💡 输入 'quit' 或 'exit' 退出")
        print("💡 输入 'clear' 清空历史")
        print("💡 输入 'history' 查看对话历史")
        print("💡 输入 'save <filename>' 保存对话")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n🧑 您: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 再见！")
                    break
                elif user_input.lower() == 'clear':
                    self.clear_history()
                    continue
                elif user_input.lower() == 'history':
                    history = self.get_history("text")
                    if history:
                        print("\n📋 对话历史:")
                        print("-" * 30)
                        print(history)
                    else:
                        print("📋 暂无对话历史")
                    continue
                elif user_input.lower().startswith('save '):
                    filename = user_input[5:].strip()
                    if filename:
                        self.save_conversation(filename)
                    else:
                        print("❌ 请指定文件名")
                    continue
                
                # 正常对话
                print("🤖 AI正在思考...")
                response = self.chat(user_input)
                print(f"🤖 AI: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
    
    def update_config(self, **kwargs):
        """
        更新配置参数
        
        Args:
            **kwargs: 要更新的参数
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                # 如果更新了API相关配置，需要更新headers
                if key == "api_key":
                    self.headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                print(f"警告: 未知参数 {key}")
    
    def get_config(self):
        """
        获取当前配置
        
        Returns:
            dict: 当前配置参数
        """
        return {
            "api_url": self.api_url,
            "model": self.model,
            "stream": self.stream,
            "max_tokens": self.max_tokens,
            "enable_thinking": self.enable_thinking,
            "thinking_budget": self.thinking_budget,
            "min_p": self.min_p,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "n": self.n,
            "stop": self.stop,
            "max_history_length": self.max_history_length,
            "auto_truncate": self.auto_truncate,
            "history_length": len(self.conversation_history)
        }


# ===== Demo 示例 =====
if __name__ == "__main__":
    print("🚀 LLMClient Demo 开始")
    print("="*50)
    
    # 创建LLM客户端实例
    llm = LLMClient(
        api_key="sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",  # 请替换为您的API密钥
        model="THUDM/GLM-4-9B-0414",
        temperature=0.7,  # 稍微提高随机性
        max_tokens=1024,   # 降低最大token数用于demo
        max_history_length=10  # 限制历史长度用于demo
    )
    
    # 示例1：单次调用（不保存历史）
    print("\n📝 示例1：单次调用（forward方法）")
    try:
        response = llm.forward("你好，请介绍一下你自己")
        print(f"🤖 回复: {response}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 示例2：设置系统提示词并开始多轮对话
    print("\n📝 示例2：多轮对话功能")
    llm.set_system_prompt("你是一个专业的日志分析助手，请用简洁专业的语言回答问题。")
    
    try:
        # 第一轮对话
        print("👤 用户: 什么是日志异常检测？")
        response1 = llm.chat("什么是日志异常检测？")
        print(f"🤖 AI: {response1}")
        
        # 第二轮对话（基于历史上下文）
        print("\n👤 用户: 有哪些常见的检测方法？")
        response2 = llm.chat("有哪些常见的检测方法？")
        print(f"🤖 AI: {response2}")
        
        # 第三轮对话
        print("\n👤 用户: 能给个具体例子吗？")
        response3 = llm.chat("能给个具体例子吗？")
        print(f"🤖 AI: {response3}")
        
    except Exception as e:
        print(f"❌ 多轮对话错误: {e}")
    
    # 示例3：查看对话历史
    print("\n📝 示例3：查看对话历史")
    print(f"📊 当前历史长度: {llm.get_history_length()} 条消息")
    
    history_text = llm.get_history("text")
    if history_text:
        print("📋 对话历史摘要:")
        print("-" * 30)
        # 只显示前200个字符避免输出过长
        print(history_text[:200] + "..." if len(history_text) > 200 else history_text)
    
    # 示例4：保存和加载对话
    print("\n📝 示例4：保存对话功能")
    try:
        conversation_file = "demo_conversation.json"
        llm.save_conversation(conversation_file)
        print(f"💾 对话已保存到 {conversation_file}")
        
        # 创建新的客户端实例并加载对话
        llm2 = LLMClient(
            api_key="sk-dpadryupxccpbkigoduasfosszucawczlmfraqhtevaxlokx",
            model="THUDM/GLM-4-9B-0414"
        )
        llm2.load_conversation(conversation_file)
        print(f"📂 新客户端已加载对话，历史长度: {llm2.get_history_length()}")
        
    except Exception as e:
        print(f"❌ 保存/加载错误: {e}")
    
    # 示例5：清空历史并重新开始
    print("\n📝 示例5：清空历史")
    print(f"清空前历史长度: {llm.get_history_length()}")
    llm.clear_history()
    print(f"清空后历史长度: {llm.get_history_length()}")
    
    # 示例6：配置管理
    print("\n📝 示例6：配置管理")
    print("原始配置（部分）:")
    config = llm.get_config()
    for key in ['temperature', 'max_tokens', 'max_history_length', 'history_length']:
        print(f"  {key}: {config[key]}")
    
    # 更新配置
    llm.update_config(temperature=0.1, max_history_length=20)
    print("\n更新后配置:")
    new_config = llm.get_config()
    for key in ['temperature', 'max_tokens', 'max_history_length', 'history_length']:
        print(f"  {key}: {new_config[key]}")
    
    # 示例7：交互式聊天演示（注释掉，避免阻塞demo）
    print("\n📝 示例7：交互式聊天模式")
    print("💡 要启动交互式聊天，请取消下面一行的注释：")
    print("# llm.start_interactive_chat()")
    
    print("\n🎉 Demo 结束")
    print("\n💡 使用提示:")
    print("  🔹 使用 forward() 进行单次调用，不保存历史")
    print("  🔹 使用 chat() 进行多轮对话，自动保存历史")
    print("  🔹 使用 set_system_prompt() 设置系统角色")
    print("  🔹 使用 clear_history() 清空对话历史")
    print("  🔹 使用 save_conversation() 和 load_conversation() 管理对话")
    print("  🔹 使用 start_interactive_chat() 启动交互式聊天") 