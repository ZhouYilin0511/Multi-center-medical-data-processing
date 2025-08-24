import os
import re
import unicodedata
from collections import defaultdict


def merge_patient_records(input_dir="step2-tojoint", output_dir="step3-merged"):
    """
    将每个患者文件夹中的零散TXT文件按病历顺序合并为一个整合病历文件
    新增功能：自动清理控制字符和"^"符号
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 定义大类及其包含的文件（按病历逻辑顺序）
    categories = [
        {
            "name": "入院记录",
            "files": [
                "入院记录-主诉_response.txt",
                "入院记录-现病史_response.txt",
                "入院记录-中医望诊_response.txt",
                "入院记录-专科检查_response.txt",
                "入院记录-辅助检查_response.txt"
            ]
        },
        {
            "name": "首次病程记录",
            "files": [
                "首次病程记录-病例特点_response.txt",
                "首次病程记录-首次病程-专科检查_response.txt",
                "首次病程记录-首次病程-中医诊断_response.txt",
                "首次病程记录-首次病程-西医诊断_response.txt",
                "首次病程记录-诊断依据_response.txt",
                "首次病程记录-诊疗计划_response.txt"
            ]
        },
        {
            "name": "日常病程记录",
            "is_daily": True  # 特殊标记为日常病程记录
        },
        {
            "name": "出院记录",
            "files": [
                "出院记录-入院情况_response.txt",
                "(合并)出院记录诊断_response.txt",
                "出院记录-诊疗经过_response.txt",
                "出院记录-出院情况_response.txt",
                "出院记录-出院医嘱_response.txt"
            ]
        },
        {
            "name": "其他记录",
            "files": ["其他记录_response.txt"]
        }
    ]

    # 遍历所有患者文件夹
    for patient_id in os.listdir(input_dir):
        patient_path = os.path.join(input_dir, patient_id)
        if not os.path.isdir(patient_path):
            continue

        print(f"处理患者: {patient_id}")

        # 收集该患者的所有文件
        patient_files = os.listdir(patient_path)

        # 创建合并后的文件
        merged_content = []
        merged_filename = f"整合病历_{patient_id}.txt"
        output_path = os.path.join(output_dir, merged_filename)

        # 特殊处理：收集日常病程记录并按序号排序
        daily_records = []
        for filename in patient_files:
            if re.match(r'(\(拆分\))?日常病程记录(\d+)?_response\.txt', filename):
                # 提取序号用于排序
                match = re.search(r'(\d+)', filename)
                index = int(match.group(1)) if match else 0
                daily_records.append((index, filename))

        # 按序号排序日常病程记录
        daily_records.sort(key=lambda x: x[0])
        sorted_daily = [filename for _, filename in daily_records]

        # 按类别顺序处理文件
        for category in categories:
            category_content = []

            if "is_daily" in category and category["is_daily"]:
                # 处理日常病程记录
                for filename in sorted_daily:
                    file_path = os.path.join(patient_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            # 清理内容：去除所有换行符和多余空格
                            content = re.sub(r'\s+', ' ', content)

                            # 清理控制字符和特殊符号
                            content = ''.join([c for c in content if unicodedata.category(c)[0] != 'C'])
                            content = content.replace('^', '')  # 删除^符号

                            # 获取标题（去掉_response.txt）
                            title = filename.replace('_response.txt', '')

                            # 添加标题和内容
                            category_content.append(f"{title}：{content}\n")

                    except Exception as e:
                        print(f"  读取文件失败: {filename} - {str(e)}")

                if category_content:
                    # 添加日常病程记录标题
                    merged_content.append("\n【日常病程记录】\n")
                    merged_content.extend(category_content)

            else:
                # 处理其他类别
                for pattern in category["files"]:
                    if pattern in patient_files:
                        file_path = os.path.join(patient_path, pattern)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                # 清理内容：去除所有换行符和多余空格
                                content = re.sub(r'\s+', ' ', content)

                                # 清理控制字符和特殊符号
                                content = ''.join([c for c in content if unicodedata.category(c)[0] != 'C'])
                                content = content.replace('^', '')  # 删除^符号

                                # 获取标题（去掉_response.txt）
                                title = pattern.replace('_response.txt', '')

                                # 简化标题
                                if "(合并)" in title:
                                    title = title.replace("(合并)", "")
                                else:
                                    # 其他标题去掉前缀中的"首次病程记录-"
                                    title = re.sub(r'^首次病程记录-', '', title)

                                # 添加标题和内容
                                category_content.append(f"{title}：{content}\n")

                        except Exception as e:
                            print(f"  读取文件失败: {pattern} - {str(e)}")

                if category_content:
                    # 添加类别标题
                    merged_content.append(f"\n【{category['name']}】\n")
                    merged_content.extend(category_content)

        # 写入合并后的文件
        with open(output_path, 'w', encoding='utf-8') as out_file:
            # 将列表内容合并为字符串
            final_content = ''.join(merged_content)

            # 清理多余的空行
            final_content = re.sub(r'\n{3,}', '\n\n', final_content)

            # 写入文件
            out_file.write(final_content.strip())

        print(f"  已创建整合病历: {merged_filename}")

    print("\n所有患者病历整合完成!")


if __name__ == "__main__":
    merge_patient_records()
