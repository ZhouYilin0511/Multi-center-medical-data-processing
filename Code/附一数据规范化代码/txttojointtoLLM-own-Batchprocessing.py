import os
import requests
import re
import time
import sys  # 添加sys模块用于命令行参数
import math  # 添加math模块用于计算分片

# 修改：导入API_TOKENS（列表）代替API_TOKEN
from config import API_TOKENS, INPUT_DIR, OUTPUT_DIR, REQUEST_METHOD, PROMPT_DIR

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 定义文件类型与提示词的映射关系（17种-静态匹配）
PROMPT_MAPPING = {
    "入院记录-主诉.txt": "入院记录-主诉提示词.txt",  # 入院记录-主诉提示词
    "入院记录-现病史.txt": "入院记录-现病史提示词.txt",  # 入院记录-现病史提示词
    "入院记录-中医望诊.txt": "入院记录-中医望诊提示词.txt",  # 入院记录-中医望诊提示词
    "入院记录-专科检查.txt": "入院记录-专科检查提示词.txt",  # 入院记录-专科检查提示词
    "入院记录-辅助检查.txt": "入院记录-辅助检查提示词.txt",  # 入院记录-辅助检查提示词
    "其他记录.txt": "其他记录提示词.txt",  # 其他记录提示词
    "(合并)出院记录诊断.txt": "出院记录诊断提示词.txt",  # 出院记录诊断提示词
    "出院记录-诊疗经过.txt": "出院记录-诊疗经过提示词.txt",  # 出院记录-诊疗经过提示词
    "出院记录-入院情况.txt": "出院记录-入院情况提示词.txt",  # 出院记录-入院情况提示词
    "出院记录-出院情况.txt": "出院记录-出院情况提示词.txt",  # 出院记录-出院情况提示词
    "出院记录-出院医嘱.txt": "出院记录-出院医嘱提示词.txt",  # 出院记录-出院医嘱提示词
    "首次病程记录-首次病程-中医诊断.txt": "首次病程-中医诊断提示词.txt",  # 首次病程-中医诊断提示词
    "首次病程记录-首次病程-专科检查.txt": "首次病程-专科检查提示词.txt",  # 首次病程-专科检查提示词
    "首次病程记录-诊疗计划.txt": "首次病程-诊疗计划提示词.txt",  # 首次病程-诊疗计划提示词
    "首次病程记录-诊断依据.txt": "首次病程-诊断依据提示词.txt",  # 首次病程-诊断依据提示词
    "首次病程记录-病例特点.txt": "首次病程-病例特点提示词.txt",  # 首次病程-病例特点提示词
    "首次病程记录-首次病程-西医诊断.txt": "首次病程-西医诊断提示词.txt"  # 首次病程-西医诊断提示词
}
# 动态匹配日常病程记录文件名的正则表达式
DAILY_COURSE_PATTERN = re.compile(r'^(\(拆分\))?日常病程记录(\d+)?\.txt$')

# API调用参数
API_DELAY = 0.5  # API调用之间的秒延迟
MAX_RETRIES = 5
BASE_RETRY_DELAY = 1  # 第一次重试的秒数

# ============================== 新增部分：命令行参数处理 ==============================
if len(sys.argv) < 2:
    print("请指定实例索引（0到总实例数-1）")
    sys.exit(1)

try:
    INSTANCE_INDEX = int(sys.argv[1])
    TOTAL_INSTANCES = len(API_TOKENS)

    if INSTANCE_INDEX < 0 or INSTANCE_INDEX >= TOTAL_INSTANCES:
        print(f"错误：实例索引必须在0到{TOTAL_INSTANCES - 1}之间")
        sys.exit(1)

    print(f"当前实例索引: {INSTANCE_INDEX}/{TOTAL_INSTANCES - 1}")
    print(f"使用的API密钥: ...{API_TOKENS[INSTANCE_INDEX][-6:]}")

except Exception as e:
    print(f"参数错误: {e}")
    sys.exit(1)

# ============================== 新增部分：获取并分配患者文件夹 ==============================
# 获取所有患者文件夹并排序
all_patient_dirs = sorted([
    d for d in os.listdir(INPUT_DIR)
    if os.path.isdir(os.path.join(INPUT_DIR, d))
])

total_patients = len(all_patient_dirs)
patients_per_instance = math.ceil(total_patients / TOTAL_INSTANCES)
start_index = INSTANCE_INDEX * patients_per_instance
end_index = min(start_index + patients_per_instance, total_patients)

print(f"总患者数: {total_patients} | 本实例处理: {start_index}-{end_index - 1}")

# ============================== 主处理循环 ==============================
# 修改：只处理分配范围内的患者文件夹
for idx in range(start_index, end_index):
    patient_dir_name = all_patient_dirs[idx]
    patient_path = os.path.join(INPUT_DIR, patient_dir_name)

    # 创建对应的输出目录
    output_patient_dir = os.path.join(OUTPUT_DIR, patient_dir_name)
    if not os.path.exists(output_patient_dir):
        os.makedirs(output_patient_dir)

    print(f"\n处理患者 {idx + 1}/{total_patients}: {patient_dir_name}")

    # 处理患者文件夹中的每个文件
    for filename in os.listdir(patient_path):
        file_path = os.path.join(patient_path, filename)
        if not os.path.isfile(file_path):
            continue  # 跳过非文件项

        # 确定输出文件路径，检查是否已经处理
        output_filename = f"{os.path.splitext(filename)[0]}_response.txt"
        output_file_path = os.path.join(output_patient_dir, output_filename)

        # --- 优化：缓存结果 ---
        if os.path.exists(output_file_path):
            print(f"✓ {filename} 已处理")
            continue  # 跳到下一个文件

        # 根据文件名获取对应的提示词
        # 优先检查是否是日常病程记录（动态文件名）
        if DAILY_COURSE_PATTERN.match(filename):
            prompt_file = "病程记录提示词.txt"  # 所有日常病程记录使用同一个提示词
        else:
            # 其他文件使用静态映射
            prompt_file = PROMPT_MAPPING.get(filename)

        if not prompt_file:
            print(f"未找到 {filename} 的提示词映射，跳过处理")
            continue

        # Read prompt file
        prompt_path = os.path.join(PROMPT_DIR, prompt_file)
        if not os.path.exists(prompt_path):
            print(f"提示词文件 {prompt_path} 不存在，跳过处理")
            continue

        with open(prompt_path, 'r', encoding='utf-8') as prompt_f:
            prompt = prompt_f.read().strip()

        # 读取病历文件内容
        with open(file_path, 'r', encoding='utf-8') as record_file:
            file_content = record_file.read()

        # 组合提示词和文件内容
        content = prompt + "\n\n" + file_content
        message_content = ""  # 为重试循环初始化message_content

        # --- 优化：具有指数回退的重试机制 ---
        for attempt in range(MAX_RETRIES):
            try:
                if REQUEST_METHOD == 'siliconflow':
                    payload = {
                        "model": "deepseek-ai/DeepSeek-R1",
                        "messages": [{"role": "user", "content": content}],
                        "stream": False,
                        "max_tokens": 4096,
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "top_k": 20,
                        "frequency_penalty": 0.0,
                        "response_format": {"type": "text"}
                    }
                    headers = {
                        # 修改：使用当前实例的API密钥
                        "Authorization": f"Bearer {API_TOKENS[INSTANCE_INDEX]}",
                        "Content-Type": "application/json"
                    }
                    response = requests.post(
                        "https://api.siliconflow.cn/v1/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    print(response)
                    response.raise_for_status()  # 引发HTTP错误异常
                    response_data = response.json()
                    message_content = response_data['choices'][0]['message']['content']
                    break  # 成功, 打破重试循环

                elif REQUEST_METHOD == 'deepseek':
                    from openai import OpenAI

                    # 修改：使用当前实例的API密钥
                    client = OpenAI(
                        api_key=API_TOKENS[INSTANCE_INDEX],
                        base_url="https://api.deepseek.com"
                    )
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": content}],
                        stream=False,
                        timeout=30  # 添加超时设置
                    )
                    message_content = response.choices[0].message.content
                    break  # 成功, 打破重试循环

            except requests.exceptions.RequestException as e:
                print(f"API request failed for {filename} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Max retries reached for {filename}. Skipping this file.")
                    message_content = ""  # 如果所有重试都失败，则设置为空
                    break  # 退出重试循环
            except Exception as e:  # 捕获其他潜在错误，如JSON解析
                print(f"An unexpected error occurred for {filename} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Max retries reached for {filename} due to unexpected error. Skipping this file.")
                    message_content = ""
                    break

        # 如果重试后message_content为空，则跳过保存
        if not message_content:
            continue

        # 保存处理结果
        message_content = message_content.lstrip()  # 关键修改：清除前导空格

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(message_content)  # 写入已清理的内容

        print(f"✓ {filename} 处理完成 → {output_filename}")

        # ---优化：引入延迟---
        time.sleep(API_DELAY)

print("\n所有患者病历处理完成！")