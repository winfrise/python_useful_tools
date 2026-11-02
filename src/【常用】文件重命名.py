import os
import shutil
from pathlib import Path
import re


def rename_files(src_dir, dst_dir, name_func):
    """
    遍历源文件夹第一层中的所有文件（不递归子文件夹），
    使用自定义函数生成新文件名后保存到目标文件夹。

    :param src_dir:  源文件夹路径
    :param dst_dir:  目标文件夹路径
    :param name_func: 自定义命名函数，签名为 name_func(original_name, index) -> new_name
                       - original_name: 原始文件名（含扩展名）
                       - index: 自然排序后的索引
                       - 返回值: 新的文件名（含扩展名），返回 None 或空串则跳过
    """
    src_path = Path(src_dir).resolve()
    dst_path = Path(dst_dir).resolve()

    if not src_path.is_dir():
        raise ValueError(f"源目录不存在或不是文件夹: {src_path}")

    dst_path.mkdir(parents=True, exist_ok=True)

    # ---------- 1. 收集 src_dir 第一层的文件（跳过以点开头的文件） ----------
    all_files = [
        f for f in src_path.iterdir()
        if f.is_file() and not f.name.startswith(".")
    ]

    # ---------- 2. 自然排序 ----------
    def natural_key(path: Path):
        # 只对文件名做自然排序
        return [
            int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", path.name)
        ]

    all_files.sort(key=natural_key)

    # ---------- 3. 逐个重命名并保存 ----------
    for idx, src_file in enumerate(all_files, start=0):
        original_name = src_file.name
        new_name = name_func(original_name, idx)

        # 命名函数返回 None 或空串 -> 跳过
        if not new_name:
            continue

        dst_file = dst_path / new_name

        # 处理同名冲突（自动加数字后缀）
        if dst_file.exists():
            stem, suffix = os.path.splitext(new_name)
            i = 1
            while True:
                candidate = dst_path / f"{stem}_{i}{suffix}"
                if not candidate.exists():
                    dst_file = candidate
                    break
                i += 1

        shutil.copy2(src_file, dst_file)

        print(f"[{idx}] 原文件名: {original_name}  ->  新文件名: {dst_file.name}")


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":

    # 示例 1: 顺序命名 image_0.jpg, image_1.jpg ...
    def seq_namer(original_name, index):
        ext = os.path.splitext(original_name)[1]
        return f"image_{index}{ext}"

    # 示例 2: 保留原名加后缀
    def prefix_namer(original_name, index):
        stem, ext = os.path.splitext(original_name)
        return f"{stem}_renamed_{index}{ext}"

    # 示例 3: 统一加前缀
    def simple_prefix(original_name, index):
        return f"NEW_{original_name}"

    rename_files(
        src_dir="/Users/teacher/Downloads/test/test001",
        dst_dir="/Users/teacher/Downloads/test/test002",
        name_func=seq_namer,
    )