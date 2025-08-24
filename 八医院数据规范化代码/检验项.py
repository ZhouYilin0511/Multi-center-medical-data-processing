import pandas as pd
import os
import re
import csv


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


def process_examination_records(file_path="E:\\PyCharm\\nlp\\八医院数据标准化代码\\八医院koa数据（314）\\检验项最终.xls", output_dir="检验项（259）"):
    """
    读取Excel文件，将每个患者的所有检查记录合并保存到一个文件中
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

        # 用于跟踪患者处理
        patients_processed = set()
        files_created = 0

        # 按住院号分组处理
        grouped = df.groupby('病案号')

        for patient_id, group in grouped:
            patient_id = str(patient_id)
            patients_processed.add(patient_id)

            # 创建患者目录
            patient_dir = os.path.join(output_dir, patient_id)
            if not os.path.exists(patient_dir):
                os.makedirs(patient_dir)

            # 为每个患者创建一个检查项文件
            output_file = os.path.join(patient_dir, "检验项.txt")
            files_created += 1

            # 写入所有检查记录
            with open(output_file, 'w', encoding='utf-8') as f:
                for idx, (_, row) in enumerate(group.iterrows(), start=1):
                    # 创建记录内容
                    record_lines = []
                    for col in ['参考范围', '报告时间', '检验结果', '单位', '检验套名称', '标本名称', '异常提示', '检验项名称', '接收时间']:
                        if col in row and pd.notna(row[col]):
                            cleaned_content = clean_content(str(row[col]))
                            record_lines.append(f"{col}: {cleaned_content}")

                    # 将当前记录的所有字段合并为一个字符串
                    record_content = "\n".join(record_lines)

                    # 写入当前记录，并在记录之间添加分隔符
                    if idx > 1:
                        f.write("\n\n")  # 记录之间的分隔符
                    f.write(record_content)

            print(f"已为患者 {patient_id} 创建检验项文件，包含 {len(group)} 条记录")

        print(f"\n处理完成。共处理 {len(patients_processed)} 位患者的记录，创建 {files_created} 个文件。")

    except FileNotFoundError:
        print(f"错误：文件 {file_path} 未找到。")
    except KeyError as e:
        print(f"列名错误：{e} 列不存在。请检查Excel文件结构。")
    except Exception as e:
        import traceback
        print(f"处理文件时发生错误：{e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    process_examination_records()