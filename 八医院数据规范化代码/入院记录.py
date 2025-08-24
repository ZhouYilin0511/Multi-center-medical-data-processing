import pandas as pd
import os
import re
from datetime import datetime

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

def summarize_medical_records(file_path="E:\\PyCharm\\nlp\\八医院数据标准化代码\\八医院koa数据（314）\\入院记录.xls", output_dir="入院记录（311）"):
    """
    读取Excel文件，将第三行作为标题，从第二行开始读取数据，
    并将每个患者的病历信息的每个部分单独保存到对应的文件中。
    """
    try:
        # 读取Excel文件，第一行作为列名
        df = pd.read_excel(file_path, header=0)

        if df.empty:
            print(f"文件 {file_path} 的第二行之后没有找到数据。")
            return

        # 创建输出目录（如果不存在）
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建目录: {output_dir}")

        print(f"从文件 {file_path} 读取到数据，开始处理并将结果保存到 '{output_dir}' 目录中：\n")

        # 定义各个部分的列名
        admission_cols = ['主诉', '辅助检查项目', '现病史', '中医四诊', '专科检查']  # 入院记录

        # 计数器
        patients_count = 0
        files_created = 0

        for index, row in df.iterrows():
            # 获取住院号作为患者ID
            patient_id = row['住院号']
            if pd.isna(patient_id) or str(patient_id).strip() == "":
                print(f"跳过第 {index + 1} 行: 未找到有效的住院号")
                continue

            # 创建患者目录
            patient_dir = os.path.join(output_dir, str(patient_id))
            if not os.path.exists(patient_dir):
                os.makedirs(patient_dir)

            # 1. 入院记录 - 每个部分单独保存
            for col in admission_cols:
                if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
                    safe_col = clean_filename(col)
                    file_path = os.path.join(patient_dir, f"入院记录-{safe_col}.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(clean_content(str(row[col])))  # Apply clean_content
                    files_created += 1

            patients_count += 1
            print(f"已处理患者 {patient_id} 的记录")

        print(f"\n处理完成。共处理 {patients_count} 位患者的记录，创建 {files_created} 个文件。")

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