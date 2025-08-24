import pandas as pd
import os
import re
from collections import defaultdict


def clean_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def clean_content(content):
    """
    清理文本内容：
    1. 移除星号 (*)
    2. 将多个连续的空格替换为单个空格
    3. 将多个连续的换行符替换为单个换行符，并去除首尾空格
    """
    if pd.isna(content) or not isinstance(content, str):
        return ""
    # 移除星号
    content = content.replace('*', '')
    # 将多个连续的空格替换为单个空格
    content = re.sub(r'\s+', ' ', content)
    # 将多个连续的换行符替换为单个换行符，并去除首尾空格
    content = re.sub(r'\n+', '\n', content).strip()
    return content


def summarize_medical_records(file_path="E:\\PyCharm\\nlp\\八医院数据标准化代码\\八医院koa数据（314）\\日常病程最终.xls", output_dir="日常病程记录（314）"):
    """
    读取Excel文件，将每个患者的每条病程记录单独保存为编号的txt文件
    """
    try:
        # 读取Excel文件，第一行作为列名
        df = pd.read_excel(file_path, header=0)

        if df.empty:
            print(f"文件 {file_path} 没有找到数据。")
            return

        # 创建输出目录（如果不存在）
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建目录: {output_dir}")

        print(f"从文件 {file_path} 读取到数据，开始处理并将结果保存到 '{output_dir}' 目录中：\n")

        # 用于跟踪每个患者的记录计数
        patient_record_count = defaultdict(int)
        total_files_created = 0
        patients_processed = set()

        # 按住院号分组处理
        grouped = df.groupby('住院号')

        for patient_id, group in grouped:
            patient_id = str(patient_id)
            patients_processed.add(patient_id)

            # 创建患者目录
            patient_dir = os.path.join(output_dir, patient_id)
            if not os.path.exists(patient_dir):
                os.makedirs(patient_dir)

            # 按时间排序（如果需要按时间顺序编号）
            # group = group.sort_values(by='病程记录时间')

            # 为每条记录创建单独的文件
            for idx, (_, row) in enumerate(group.iterrows(), start=1):
                # 更新记录计数
                patient_record_count[patient_id] += 1
                record_num = patient_record_count[patient_id]

                # 创建文件内容
                content_lines = []
                for col in ['病程记录时间', '标题', '病程记录内容']:
                    if col in row and pd.notna(row[col]):
                        cleaned_content = clean_content(str(row[col]))
                        content_lines.append(f"{col}: {cleaned_content}")

                if content_lines:
                    # 创建文件名
                    filename = f"(拆分)日常病程记录{record_num}.txt"
                    file_path = os.path.join(patient_dir, filename)

                    # 写入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(content_lines))
                    total_files_created += 1

        print(f"处理完成。共处理 {len(patients_processed)} 位患者的记录，创建 {total_files_created} 个文件。")

    except FileNotFoundError:
        print(f"错误：文件 {file_path} 未找到。")
    except KeyError as e:
        print(f"列名错误：{e} 列不存在。请检查Excel文件结构。")
    except Exception as e:
        import traceback
        print(f"处理文件时发生错误：{e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    summarize_medical_records()