# LogDetect - 日志异常检测系统

## 项目概述

LogDetect 是一个基于大语言模型的日志异常检测系统，采用 Chain of Thought (COT) 方法对系统日志进行智能分析和异常检测。该系统支持多种日志格式，能够自动识别和分类异常日志条目。

## 项目结构

```
LogDetect/
├── Find_detect/                    # 核心检测模块
│   ├── COT.py                     # COT方法主要实现
│   ├── run_analysis_pipeline.py   # 完整分析流程主控脚本
│   ├── log_split_bytime.py        # 日志时间分割脚本
│   ├── prompt_candidates.txt      # 提示词候选文件
│   ├── Prompt_summerize.py        # 提示词总结脚本
│   ├── time_analyzer.py           # 时间分析器
│   ├── test_analyze.py            # 测试分析脚本
│   ├── main.py                    # 主入口文件
│   └── utils/                     # 工具函数目录
├── quick_delete_txt.py            # 快速删除txt文件工具
├── log/                           # 日志文件目录
├── OUTPUT_FILE/                   # 输出文件目录
└── README.md                      # 项目说明文档
```

## 核心功能模块

### 1. COT.py - 日志异常检测核心模块

**功能**: 使用Chain of Thought方法对日志进行异常检测和分类

**主要特性**:
- 支持多种提示策略（CoT、Self、InContext）
- 多线程并发处理，提高检测效率
- 自动重试机制，确保处理稳定性
- 支持多个API密钥轮询使用

**使用方法**:
```python
from Find_detect import COT

# 设置参数
INPUT_DIR = "./log/log"                    # 输入日志目录
OUTPUT_DIR = "./analysis_results"          # 输出结果目录
ANALYZE_LOG_PATH = "./analysis_results"    # 分析日志路径

# 执行分析
COT.main(INPUT_DIR, OUTPUT_DIR, ANALYZE_LOG_PATH)
```

**输出文件**:
- CSV格式的分析结果文件
- 包含原始日志、分析结果和异常分类

### 2. run_analysis_pipeline.py - 完整分析流程主控脚本

**功能**: 整合日志分割和COT分析的完整流程控制器

**使用方法**:
```bash
python Find_detect/run_analysis_pipeline.py \
    --raw_log_dir ./log/log \
    --split_output_dir ./split_logs \
    --final_analysis_dir ./analysis_results \
    --target_time 20250425_1400 \
    --interval_hours 2
```

**参数说明**:
- `--raw_log_dir`: 原始日志文件目录（默认: ./log/log）
- `--split_output_dir`: 时间分割后日志输出目录（默认: ./split_logs）
- `--final_analysis_dir`: 最终分析结果输出目录（默认: ./Find_detect/analysis_results）
- `--target_time`: 目标分析时间（格式: YYYYMMDD_HHMM）**[必需]**
- `--interval_hours`: 日志分割时间间隔，单位小时（默认: 2）

### 3. log_split_bytime.py - 日志时间分割脚本

**功能**: 按时间间隔分割日志文件，同时生成CSV格式文件

**主要特性**:
- 支持多种时间戳格式自动识别
- 按指定时间间隔分组日志
- 同时输出.log和.csv两种格式
- 支持递归处理子目录

**使用方法**:
```python
from Find_detect import log_split_bytime

# 方法一：直接调用函数
log_split_bytime.split_logs_by_time(
    input_dir="./log/log",        # 输入目录
    output_dir="./split_logs",    # 输出目录
    interval_hours=2              # 时间间隔（小时）
)

# 方法二：命令行运行
python Find_detect/log_split_bytime.py
```

**支持的时间格式**:
- `2025-04-23 14:42:36.060`
- `2025-04-23T11:52:18.732433+08:00`
- `Apr 21 16:12:24`
- `Apr 23 13:04:01`

### 4. quick_delete_txt.py - 文件清理工具

**功能**: 快速删除指定目录下的所有.txt文件

**使用方法**:
```python
# 修改脚本中的目标目录
TARGET_DIRECTORY = "./Find_detect/output_528"

# 运行清理
python quick_delete_txt.py
```

**或直接调用函数**:
```python
from quick_delete_txt import quick_delete_txt_files

# 删除指定目录的txt文件
quick_delete_txt_files("/path/to/directory", recursive=False)

# 递归删除子目录中的txt文件
quick_delete_txt_files("/path/to/directory", recursive=True)
```

### 5. Prompt_summerize.py - 结果汇总脚本

**功能**: 汇总和整理分析结果，生成最终报告

**使用方法**:
```python
python Find_detect/Prompt_summerize.py
```

## 完整使用流程

### 步骤1: 准备日志文件
将待分析的日志文件放置在 `./log/log/` 目录下

### 步骤2: 执行完整分析流程
```bash
python Find_detect/run_analysis_pipeline.py \
    --target_time 20250425_1400 \
    --interval_hours 2
```

### 步骤3: 查看分析结果
分析结果将保存在 `./Find_detect/analysis_results/` 目录下

### 步骤4: 清理临时文件（可选）
```bash
python quick_delete_txt.py
```

## 配置说明

### API配置
系统使用大语言模型API进行日志分析，需要配置以下参数：

```python
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEYS = [
    "your-api-key-1",
    "your-api-key-2",
    # 可添加多个API密钥实现负载均衡
]
```

### 提示词配置
系统支持三种提示策略：

1. **CoT (Chain of Thought)**: 逐步推理分析
2. **Self**: 基于候选提示词自动选择
3. **InContext**: 基于示例进行上下文学习

## 输出格式

### 分析结果CSV文件包含以下字段：
- `log_idx`: 日志索引号
- `log_content`: 原始日志内容
- `classification`: 分类结果（normal/abnormal）
- `confidence`: 置信度分数

### 统计摘要包含：
- 总日志条数
- 正常日志条数
- 异常日志条数
- 异常检出率

## 注意事项

1. **系统要求**: Python 3.7+
2. **依赖库**: 请先安装所需依赖包
3. **API限制**: 注意API调用频率限制
4. **内存使用**: 大量日志处理时注意内存使用情况
5. **文件编码**: 系统支持UTF-8编码，其他编码会自动忽略无法解码的字符

## 依赖安装

```bash
pip install pandas requests tenacity tqdm numpy concurrent-futures
```

## 故障排除

### 常见问题：
1. **导入模块失败**: 确保脚本在正确的目录下运行
2. **API调用失败**: 检查API密钥和网络连接
3. **内存不足**: 减少并发线程数或分批处理日志
4. **时间格式识别失败**: 检查日志时间戳格式是否被支持

### 日志文件：
系统运行过程中的详细日志会保存在相应的输出目录中，便于问题诊断。

## 联系方式

如有问题或建议，请通过项目仓库提交Issue。 