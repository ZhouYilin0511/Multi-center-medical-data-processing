import os
import re

def is_chinese_name(name):
    """检查是否为2-3个中文字符的名字"""
    pattern = r'^[\u4e00-\u9fa5]{2,3}$'
    return bool(re.fullmatch(pattern, name))


def is_chinese_title(line):
    # 检查是否包含“记录”或“查房”或“术”
    if "记录" not in line and "查房" not in line and "术" not in line:
        return False

    # 检查是否仅包含中文
    if re.fullmatch(r'[\u4e00-\u9fa5]+', line):
        # 仅包含中文，检查长度是否为4-15
        return 4 <= len(line) <= 15
    # 检查仅包含中文及中文字符
    elif re.fullmatch(r'[\u4e00-\u9fa5，、.（）]+', line):
        # 包含中文字符，检查长度是否不超过20
        return 4 <= len(line) <= 20
    return False

def de_privacy_admission(content):
    """针对入院记录的去隐私化处理"""
    # 1. 删除开头的隐私信息块（姓名到发病节气）
    content = re.sub(r'姓\s*名：.*?发病节气：.*?\n\n', '', content, flags=re.DOTALL)

    # 2. 删除开头的隐私信息块（患者姓名到住院天数） - 出院记录
    # 修改为匹配英文冒号和单个换行符
    content = re.sub(r'患者姓名[:：].*?住院天数[:：].*?\n', '', content, flags=re.DOTALL)

    # 预处理：将连续多个空格替换为换行符，便于行处理
    normalized_text = re.sub(r'(?<!\n)\s{4,}', '\n', content)
    lines = normalized_text.splitlines()

    # 存储结果行
    result_lines = []
    # 记录已知的医生名字

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line:
            continue
        # 检查是否日期行（匹配yyyy-mm-dd格式）
        elif re.match(r'^\d{4}[-./年]\d{1,2}[-./月]\d{1,2}(?:日)?(?: \d{1,2}:\d{2})?$', stripped_line):
            if len(lines) > i + 1 and is_chinese_title(lines[i+1].strip()):
                lines[i + 1] = '    '.join([line, lines[i + 1].strip()])
            else:
                result_lines.append("DATE")
        # 如果检测到日期行，则跳过紧随其后的姓名行
        # 跳过姓名行（假设日期行后的第一行是姓名）
        elif is_chinese_name(stripped_line):
            names.add(stripped_line)
            result_lines.append("NAME")
        else:
            result_lines.append(line)

    # 恢复原始格式：将换行符替换为原始空格
    # 注意：这里保留单空格，因为原始多个空格已转为换行符
    content = '\n'.join(result_lines)

    for name in names:
        content = content.replace(name, 'NAME')

    # ====== 新增的后处理步骤 ======
    # 1. 删除所有NAME和DATE标签
    content = content.replace('NAME', '').replace('DATE', '')

    # 2.1 清理多余空格
    # 处理连续空格/制表符 (不包含换行符)
    content = re.sub(r'[ \t]{2,}', ' ', content)
    # 2.2 专门处理换行符周围的空格
    content = re.sub(r'\n\s+', '\n', content)  # 行首空格
    content = re.sub(r'\s+\n', '\n', content)  # 行尾空格

    # 3. 额外修正：处理连续换行符
    content = re.sub(r'\n{3,}', '\n\n', content)  # 保留最多两个连续换行

    return content


def process_admission_files(input_root, output_root):
    """处理所有患者文件夹下的入院记录文件"""
    # 遍历输入目录下的所有患者文件夹

    for patient_id in os.listdir(input_root):

        patient_folder = os.path.join(input_root, patient_id)

        # 确保是目录
        if not os.path.isdir(patient_folder):
            continue

        # 构建入院文件路径
        global names
        files = ['入院.txt', '出院.txt', '首程.txt', '病程.txt']
        names = set()
        pattern1 = r'.*[姓签]\s*名：\s*([^ \n]+)[ \n]'

        for file in files:
            # admission_file = os.path.join(patient_folder, '入院.txt')
            admission_file = os.path.join(patient_folder, file)

            # 检查文件是否存在
            if not os.path.exists(admission_file):
                print(f'未找到文件: {admission_file}')
                continue

            try:
                # 尝试多种编码读取文件
                encodings = ['utf-8', 'gbk', 'gb18030', 'latin1']
                content = None
                for encoding in encodings:
                    try:
                        with open(admission_file, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue

                if content is None:
                    print(f'无法解码文件: {admission_file}')
                    continue

                # 去隐私化处理

                matches = re.findall(pattern1, content)
                names.update(matches)

                processed_content = de_privacy_admission(content)

                # 创建输出目录
                output_folder = os.path.join(output_root, patient_id)
                os.makedirs(output_folder, exist_ok=True)

                # 写入处理后的内容
                output_file = os.path.join(output_folder, file)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(processed_content)

                print(f'处理完成: {patient_id}/{file}')
            except Exception as e:
                print(f'处理失败: {admission_file}, 错误: {str(e)}')


if __name__ == "__main__":
    # 设置路径
    input_root = 'E:\\PyCharm\\nlp\\附二数据标准化代码\\附二导出数据'  # 替换为您的原始数据目录
    output_root = 'step1-De_privacy'  # 输出目录

    # 确保输出目录存在
    os.makedirs(output_root, exist_ok=True)
    names = set()

    # 处理所有入院记录文件
    process_admission_files(input_root, output_root)
    print('所有入院记录处理完成！')