import os
import shutil
from pathlib import Path
import re


def _natural_key(name: str):
    """自然排序 key：把字符串按数字片段拆分后比较，如 file2 < file10"""
    return [
        int(t) if t.isdigit() else t.lower()
        for t in re.split(r"(\d+)", name)
    ]


def _resolve_conflict(dst_file: Path) -> Path:
    """目标文件已存在时，自动追加 _1、_2 ... 后缀"""
    if not dst_file.exists():
        return dst_file
    stem, suffix = os.path.splitext(dst_file.name)
    i = 1
    while True:
        candidate = dst_file.parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def rename_files(src_dir, dst_dir, name_func, mode=1):
    """
    批量重命名文件并保存到目标文件夹。

    :param src_dir:  源文件夹路径
    :param dst_dir:  目标文件夹路径
    :param name_func: 自定义命名函数。
                      - mode=1 时签名: name_func(original_name, index) -> new_name
                      - mode=2 时签名: name_func(folder_name, folder_index,
                                                  original_name, file_index) -> new_name
                      返回值若为 None 或空串，则跳过该文件
    :param mode: 模式选择
                 - 1: 只遍历 src_dir 第一层的文件
                 - 2: 遍历 src_dir 下的子文件夹（自然排序），
                      再按顺序遍历每个子文件夹中的文件（自然排序）；
                      调用 name_func 时传入:
                        folder_name  - 当前文件所在子文件夹名称
                        folder_index - 子文件夹的自然排序索引（从 0 开始）
                        original_name- 原始文件名（含扩展名）
                        file_index   - 文件在**当前子文件夹内**的自然排序索引（从 0 开始）
    """
    if mode not in (1, 2):
        raise ValueError(f"mode 只能是 1 或 2，当前为: {mode}")

    src_path = Path(src_dir).resolve()
    dst_path = Path(dst_dir).resolve()

    if not src_path.is_dir():
        raise ValueError(f"源目录不存在或不是文件夹: {src_path}")

    dst_path.mkdir(parents=True, exist_ok=True)

    if mode == 1:
        _run_mode1(src_path, dst_path, name_func)
    else:
        _run_mode2(src_path, dst_path, name_func)


# ============================================================
# 模式 1：只遍历 src_dir 第一层的文件
# ============================================================
def _run_mode1(src_path: Path, dst_path: Path, name_func):
    files = [
        f for f in src_path.iterdir()
        if f.is_file() and not f.name.startswith(".")
    ]
    files.sort(key=lambda p: _natural_key(p.name))

    for idx, src_file in enumerate(files, start=0):
        original_name = src_file.name
        new_name = name_func("", "",original_name, idx)
        if not new_name:
            continue

        dst_file = _resolve_conflict(dst_path / new_name)
        shutil.copy2(src_file, dst_file)
        print(f"[{idx}] 原文件名: {original_name}  ->  新文件名: {dst_file.name}")


# ============================================================
# 模式 2：按子文件夹自然排序后，逐个遍历子文件夹里的文件
# ============================================================
def _run_mode2(src_path: Path, dst_path: Path, name_func):
    # 1. 收集并自然排序子文件夹（跳过以点开头的文件夹）
    subfolders = [
        d for d in src_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    subfolders.sort(key=lambda p: _natural_key(p.name))

    # 2. 按顺序遍历每个子文件夹里的文件
    for folder_index, subfolder in enumerate(subfolders, start=0):
        folder_name = subfolder.name

        files = [
            f for f in subfolder.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]
        files.sort(key=lambda p: _natural_key(p.name))

        # 目标子文件夹（保持子文件夹层级）
        dst_subfolder = dst_path / folder_name
        dst_subfolder.mkdir(parents=True, exist_ok=True)

        for file_index, src_file in enumerate(files, start=0):
            original_name = src_file.name
            new_name = name_func(folder_name, folder_index, original_name, file_index)

            if not new_name:
                continue

            dst_file = _resolve_conflict(dst_subfolder / new_name)
            shutil.copy2(src_file, dst_file)
            print(
                f"[folder={folder_index}][file={file_index}] "
                f"子文件夹: {folder_name} | "
                f"原文件名: {original_name}  ->  新文件名: {dst_file.name}"
            )


# ============================================================
# 使用示例
# ============================================================
if __name__ == "__main__":

    # ---------- 模式 1 的命名函数 ----------
    def seq_namer(folder_name, folder_index, original_name, index):
        ext = os.path.splitext(original_name)[1]
        return f"image_{30+index}{ext}"

    # ---------- 模式 2 的命名函数 ----------
    # 使用 文件夹索引 + 文件夹名 + 文件索引 构建新名称
    # 例如: 0001_20240101_0001.jpg
    def subfolder_namer(folder_name, folder_index, original_name, file_index):
        print(folder_name, folder_index)
        ext = os.path.splitext(original_name)[1]
        return f"{folder_index:04d}_{folder_name}_{file_index:04d}{ext}"

    # 只保留 文件夹名 + 文件夹索引 + 文件索引，丢弃原名
    def subfolder_compact_namer(folder_name, folder_index, original_name, file_index):
        ext = os.path.splitext(original_name)[1]
        new_index = (folder_index * 30) + file_index
        return f"IMAGE_{ new_index }{ext}"

    # ---------- 调用 ----------
    # 模式 1
    # rename_files("./source_folder", "./target_folder", seq_namer, mode=1)

    # 模式 2
    rename_files(
        src_dir="/Users/teacher/Downloads/test/test001",
        dst_dir="/Users/teacher/Downloads/test/test003",
        name_func=subfolder_compact_namer,
        mode=2,
    )