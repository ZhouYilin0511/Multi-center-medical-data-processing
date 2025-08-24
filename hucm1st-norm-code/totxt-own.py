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


def split_daily_course(content):
    """
    拆分日常病程记录为多个独立记录
    使用正则表达式匹配日期时间格式（如：2022-07-09 09:12）
    """
    if pd.isna(content) or not content.strip():
        return []

    # 匹配日期时间模式（YYYY-MM-DD HH:MM）
    pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}'
    matches = list(re.finditer(pattern, content))

    if not matches:
        # Before returning, clean the single content block
        return [clean_content(content)]

    # 根据匹配位置拆分内容
    records = []
    start_index = 0

    for i, match in enumerate(matches):
        record_start = match.start()
        if i > 0:
            # 获取上一个匹配结束到当前匹配开始之间的内容
            record_content = content[start_index:record_start].strip()
            if record_content:
                records.append(clean_content(record_content)) # Apply clean_content here
        start_index = record_start

    # 添加最后一个记录
    last_record = content[start_index:].strip()
    if last_record:
        records.append(clean_content(last_record)) # Apply clean_content here

    return records


def summarize_medical_records(file_path="KOA精确导出v1.xlsx", output_dir="step1-totxt"):
    """
    读取Excel文件，将第三行作为标题，从第四行开始读取数据，
    并将每个患者的病历信息的每个部分单独保存到对应的文件中。
    """
    try:
        # 读取Excel文件，第三行作为列名
        df = pd.read_excel(file_path, header=2)

        if df.empty:
            print(f"文件 {file_path} 的第四行之后没有找到数据。")
            return

        # 创建输出目录（如果不存在）
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建目录: {output_dir}")

        print(f"从文件 {file_path} 读取到数据，开始处理并将结果保存到 '{output_dir}' 目录中：\n")

        # 定义各个部分的列名
        admission_cols = ['主诉', '辅助检查', '现病史', '中医望诊', '专科检查']  # 入院记录
        discharge_cols = ['诊疗经过', '入院情况', '出院医嘱', '出院情况']  # 出院记录（不包含诊断部分）
        discharge_diagnosis_cols = ['出院记录-入院诊断', '出院诊断']  # 出院诊断（合并）
        first_course_cols = ['首次病程-中医诊断', '诊疗计划', '诊断依据', '首次病程-专科检查',
                             '首次病程-西医诊断', '病例特点']  # 首次病程记录
        daily_course_col = '日常病程'  # 日常病程记录
        # 其他记录列（排除已处理的列和regno_admno）
        other_records_cols = [col for col in df.columns
                              if col not in admission_cols + discharge_cols + discharge_diagnosis_cols +
                              first_course_cols + [daily_course_col, 'regno_admno']]

        # 计数器
        patients_count = 0
        files_created = 0

        for index, row in df.iterrows():
            # 获取登记号就诊号（regno_admno）作为患者ID
            patient_id = row['regno_admno']
            if pd.isna(patient_id) or str(patient_id).strip() == "":
                print(f"跳过第 {index + 1} 行: 未找到有效的登记号就诊号")
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
                        f.write(clean_content(str(row[col]))) # Apply clean_content
                    files_created += 1

            # 2. 出院记录
            # 2.1 合并诊断部分
            diagnosis_content = []
            for col in discharge_diagnosis_cols:
                if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
                    diagnosis_content.append(clean_content(str(row[col]))) # Apply clean_content

            if diagnosis_content:
                file_path = os.path.join(patient_dir, "(合并)出院记录诊断.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(diagnosis_content))
                files_created += 1

            # 2.2 其他出院记录部分单独保存
            for col in discharge_cols:
                if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
                    safe_col = clean_filename(col)
                    file_path = os.path.join(patient_dir, f"出院记录-{safe_col}.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(clean_content(str(row[col]))) # Apply clean_content
                    files_created += 1

            # 3. 首次病程记录 - 每个部分单独保存
            for col in first_course_cols:
                if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
                    safe_col = clean_filename(col)
                    file_path = os.path.join(patient_dir, f"首次病程记录-{safe_col}.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(clean_content(str(row[col]))) # Apply clean_content
                    files_created += 1

            # 4. 日常病程记录 - 拆分处理
            if daily_course_col in row and pd.notna(row[daily_course_col]) and str(row[daily_course_col]).strip() != "":
                content = str(row[daily_course_col])
                records = split_daily_course(content) # clean_content is applied within split_daily_course

                if len(records) == 0:
                    # 空记录
                    pass
                elif len(records) == 1:
                    # 单个记录
                    file_path = os.path.join(patient_dir, "日常病程记录.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(records[0])
                    files_created += 1
                else:
                    # 多个记录
                    for i, record in enumerate(records, 1):
                        file_path = os.path.join(patient_dir, f"(拆分)日常病程记录{i}.txt")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(record)
                        files_created += 1

            # 5. 其他记录（病案首页+影像+实验室检查）
            other_records_content = []
            for col in other_records_cols:
                if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
                     # Apply clean_content to the value before adding to the list
                     other_records_content.append(f"{col}: {clean_content(str(row[col]))}")
            if other_records_content:
                with open(os.path.join(patient_dir, "其他记录.txt"), "w", encoding="utf-8") as f:
                    # Joining with a single newline to avoid excessive blank lines if content is already clean
                    f.write("\n".join(other_records_content))
                files_created += 1 # Increment files_created for "其他记录.txt"

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