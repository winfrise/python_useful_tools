import os
import sys
import shutil


def copy_jpg_as_jpeg(src_dir: str, dst_dir: str) -> None:
    """
    递归遍历 src_dir，把所有 .jpg 文件复制到 dst_dir，
    扩展名改为 .jpeg，文件名主体和相对目录层级保持不变。
    不修改 src_dir 中的任何原文件。
    """
    if not os.path.isdir(src_dir):
        print(f"[错误] 源文件夹无效: {src_dir}")
        return

    # 目标根目录不存在则创建
    os.makedirs(dst_dir, exist_ok=True)

    copied_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(src_dir):
        for filename in files:
            name, ext = os.path.splitext(filename)
            # 只处理 .jpg（大小写不敏感）
            if ext.lower() != ".jpg":
                continue

            # 计算相对路径，保持层级
            rel_dir = os.path.relpath(root, src_dir)
            # 目标子目录
            target_dir = os.path.join(dst_dir, rel_dir) if rel_dir != "." else dst_dir
            os.makedirs(target_dir, exist_ok=True)

            src_path = os.path.join(root, filename)
            dst_path = os.path.join(target_dir, name + ".jpeg")

            # 防覆盖：目标已存在则跳过
            if os.path.exists(dst_path):
                print(f"[跳过] 目标已存在: {dst_path}")
                skipped_count += 1
                continue

            try:
                shutil.copy2(src_path, dst_path)  # copy2 保留元数据
                print(f"[复制] {src_path}  ->  {dst_path}")
                copied_count += 1
            except OSError as e:
                print(f"[失败] {src_path}: {e}")
                skipped_count += 1

    print(f"\n完成：复制 {copied_count} 个，跳过/失败 {skipped_count} 个。")


if __name__ == "__main__":

    folder1 = "/Users/teacher/Downloads/260张图片去水印/001_重命名"
    folder2 = f"{folder1}_改后缀"

    copy_jpg_as_jpeg(folder1, folder2)