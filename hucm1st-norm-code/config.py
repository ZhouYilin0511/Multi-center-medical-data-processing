# config.py

# API 令牌
API_TOKEN = "sk-wuqvxrrevdtmwsbvjcimgqrxdrkqrjsdaxrywlhqhpkckmpw"  # Replace with your actual token

# 批量调用API
# 使用API密钥列表替代单个密钥
API_TOKENS = [
    "sk-xcjevpqpkmmwxgzknurmaprjxggthtllpnaecjjvpldyvowr",   # 实例0使用
    "",   # 实例1使用
    "",   # 实例2使用
    ""    # 实例3使用
    # 添加更多密钥...
]

# 定义输入目录、输出目录和提示文件的路径
INPUT_DIR = 'step1-totxt'   # 输入目录（包含患者文件夹）
OUTPUT_DIR = 'step2-tojoint'    # 输出目录（处理结果将保存到这里）
PROMPT_DIR = 'prompts'   # 提示词文件目录

# API请求方法：'siliconflow' 或 'deepseek'
REQUEST_METHOD = 'siliconflow'  # Change to 'deepseek' to use DeepSeek API  siliconflow