import os
import shutil
import sys


def organize_patient_files(source_folders, target_root):
    """
    按照患者编号整理文件，不修改原始文件名
    :param source_folders: 包含患者文件夹的源文件夹列表
    :param target_root: 整理后的目标根目录
    """
    # 确保目标目录存在
    os.makedirs(target_root, exist_ok=True)

    # 遍历所有源文件夹
    for source_folder in source_folders:
        if not os.path.exists(source_folder):
            print(f"警告: 源文件夹 '{source_folder}' 不存在，跳过")
            continue

        # 遍历源文件夹中的患者文件夹
        for patient_id in os.listdir(source_folder):
            patient_source_path = os.path.join(source_folder, patient_id)

            # 确保是目录
            if not os.path.isdir(patient_source_path):
                continue

            # 创建目标患者文件夹
            patient_target_path = os.path.join(target_root, patient_id)
            os.makedirs(patient_target_path, exist_ok=True)

            # 复制所有txt文件到目标文件夹
            for filename in os.listdir(patient_source_path):
                if filename.endswith('.txt'):
                    src_file = os.path.join(patient_source_path, filename)
                    dest_file = os.path.join(patient_target_path, filename)

                    # 检查目标文件是否已存在（虽然您说不会存在同名文件，但添加检查更安全）
                    if os.path.exists(dest_file):
                        print(f"警告: 目标文件已存在，跳过复制: {dest_file}")
                        continue

                    # 复制文件
                    shutil.copy2(src_file, dest_file)
                    print(f"已复制: {src_file} -> {dest_file}")


if __name__ == "__main__":
    # 配置参数
    SOURCE_FOLDERS = [
        "E:\\PyCharm\\nlp\\八医院数据标准化代码\\入院记录（311）",  # 入院记录
        "E:\\PyCharm\\nlp\\八医院数据标准化代码\\出院记录（314）",  # 出院记录
        "E:\\PyCharm\\nlp\\八医院数据标准化代码\\首次病程（314）",  # 首次病程
        "E:\\PyCharm\\nlp\\八医院数据标准化代码\\日常病程记录（314）",  # 日常病程记录
        "E:\\PyCharm\\nlp\\八医院数据标准化代码\\检查项（221）",  # 检查项
        "E:\\PyCharm\\nlp\\八医院数据标准化代码\\检验项（259）"  # 检验项
    ]
    TARGET_ROOT = "E:\\PyCharm\\nlp\\八医院数据标准化代码\\step1-totxt_integration"  # 替换为您想要的目标根目录

    # 执行整理
    organize_patient_files(SOURCE_FOLDERS, TARGET_ROOT)
    print("\n文件整理完成！")