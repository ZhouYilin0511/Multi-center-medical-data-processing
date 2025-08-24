import os
import re
from datetime import datetime


def split_daily_course(content):
    """根据时间戳拆分病程记录"""
    # 匹配时间戳模式，例如：2021.10.10 08:11 主治医师查房记录
    pattern = re.compile(r'\d{4}\.\d{2}\.\d{2} \d{2}:\d{2} .+')
    matches = list(pattern.finditer(content))

    records = []
    for i in range(len(matches)):
        start = matches[i].start()
        if i < len(matches) - 1:
            end = matches[i + 1].start()
        else:
            end = len(content)
        record = content[start:end].strip()
        records.append(record)

    return records


def process_course_records(content, patient_dir):
    """处理病程记录并保存为文件"""
    records = split_daily_course(content)
    files_created = 0

    if len(records) == 0:
        # 空记录
        pass
    elif len(records) == 1:
        # 单个记录
        file_path = os.path.join(patient_dir, "病程记录.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(records[0])
        files_created += 1
    else:
        # 多个记录
        for i, record in enumerate(records, 1):
            file_path = os.path.join(patient_dir, f"(拆分)病程记录{i}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(record)
            files_created += 1

    return files_created


def extract_sections_from_file(input_file, output_dir, excludes):
    """提取文件内容并处理病程记录"""
    try:
        # 读取原始文件内容
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 如果是病程记录文件，直接处理并返回
        if os.path.basename(input_file) == "病程.txt":
            files_created = process_course_records(content, output_dir)
            print(f"成功处理病程记录，生成 {files_created} 个文件")
            return True

        lines = content.split('\n')
        # 提取所需内容
        extracted_contents = []
        allow = True

        # 遍历所有内容，寻找冒号
        for line in lines:
            idx1 = line.find('：')
            idx2 = line.find(':')
            if idx1 != -1 and idx2 != -1:
                idx = min(idx1, idx2)
            elif idx1 == -1:
                idx = idx2
            elif idx2 == -1:
                idx = idx1
            else:
                idx = -1

            if idx != -1:
                title = re.sub(r'[^\u4e00-\u9fff]', '', line[:idx])

                allow = True
                for exclude in excludes:
                    if exclude in title:
                        allow = False
                        break

                if '病史' in title:
                    tail_idx = line.find('既往')
                    if tail_idx != -1:
                        line = line[:tail_idx]

                if '体格检查' in title:
                    tail_idx = line.find('专科检查')
                    if tail_idx != -1:
                        extracted_contents.append(line[tail_idx:])

                if '入院情况' in title:
                    # 先尝试查找"体格检查"
                    s = max(line.find('体格检查'), line.find('体查'))
                    e = line.find('专科检查')

                    if s != -1:
                        # 如果有"体格检查"，按原逻辑处理
                        line = line[:s] + line[e:] if e > s else line[:s]
                    else:
                        # 如果没有"体格检查"，尝试查找"T: "
                        t_pos = line.find('T:')
                        if t_pos != -1:
                            # 如果找到"T: "，删除从"T: "开始到"专科检查"之前的内容
                            line = line[:t_pos] + line[e:] if e > t_pos else line[:t_pos]

                if '入院情况' in title:
                    tail_idx = line.find('既往')
                    if tail_idx != -1:
                        line = line[:tail_idx]

                if '出院情况' in title:         # 出院情况中可能也有体格检查
                    s = max(line.find('体格检查'), line.find('体查'))
                    e = line.find('专科检查')
                    if s != -1:
                        line = line[:s] + line[e:] if e > s else line[:s]

            if allow:
                extracted_contents.append(line)

        # 合并所有提取的内容
        result = '\n'.join(extracted_contents)

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        # 写入输出文件
        output_file = os.path.join(output_dir, os.path.basename(input_file))
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)

        print(f"成功处理: {input_file}")
        return True

    except Exception as e:
        print(f"处理文件 {input_file} 时出错: {str(e)}")
        return False


def process_directory(input_dir, output_dir):
    """处理目录中的所有文本文件"""
    # 确保输入目录存在
    if not os.path.isdir(input_dir):
        print(f"错误: 输入目录不存在 {input_dir}")
        return

    exclude_sections = {
        '入院': [
            '问诊', "既往史", '个人史', '婚育史', '月经史', '家族史', '体格检查'
        ],
        '首程': [
            '体格检查', '中医鉴别诊断', '西医鉴别诊断', '病例分型'
        ],
        '出院': ['医师签名']
    }

    # 遍历目录中的所有文件
    for dir_name in os.listdir(input_dir):
        input_dir_path = os.path.join(input_dir, dir_name)
        output_dir_path = os.path.join(output_dir, dir_name)

        # 确保输出子目录存在
        os.makedirs(output_dir_path, exist_ok=True)

        # 首先处理病程.txt文件
        course_file = os.path.join(input_dir_path, '病程.txt')
        if os.path.exists(course_file):
            extract_sections_from_file(course_file, output_dir_path, [])

        # 处理其他文件
        for filename, excludes in exclude_sections.items():
            input_path = os.path.join(input_dir_path, f'{filename}.txt')
            if os.path.exists(input_path):
                extract_sections_from_file(input_path, output_dir_path, excludes)


# 使用示例
if __name__ == "__main__":
    input_dir = "E:\\PyCharm\\nlp\\附二数据标准化代码\\step1-De_privacy"  # 输入目录
    output_dir = "E:\\PyCharm\\nlp\\附二数据标准化代码\\step2-Extracted"  # 输出目录

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 处理整个目录
    process_directory(input_dir, output_dir)
    print("处理完成！所有文件已保存到:", output_dir)