import os
import re
import shutil
import argparse
from pathlib import Path


def is_hidden(path: Path) -> bool:
    """判断文件或文件夹是否为隐藏（以 . 开头，或 Windows 隐藏属性）"""
    name = path.name
    if name.startswith('.'):
        return True
    # Windows 隐藏属性
    if os.name == 'nt':
        try:
            attrs = os.stat(path).st_file_attributes
            if attrs & 0x2:  # FILE_ATTRIBUTE_HIDDEN
                return True
        except (AttributeError, OSError):
            pass
    return False


def natural_sort_key(name: str):
    """
    自然排序的 key 函数。
    将字符串拆分为数字和非数字部分，数字部分转为 int 比较。
    例如: "folder2" -> ['folder', 2, '']
          "folder10" -> ['folder', 10, '']
    """
    parts = re.split(r'(\d+)', name)
    result = []
    for part in parts:
        if part.isdigit():
            result.append(int(part))
        else:
            # 转小写以忽略大小写差异（可选，如需区分大小写可去掉 .lower()）
            result.append(part.lower())
    return result


def get_subfolders(input_dir: Path):
    """获取输入文件夹下所有非隐藏的一级子文件夹，并按自然顺序排序"""
    subfolders = []
    for entry in input_dir.iterdir():
        if entry.is_dir() and not is_hidden(entry):
            subfolders.append(entry)
    # 自然排序
    subfolders.sort(key=lambda p: natural_sort_key(p.name))
    return subfolders


def copy_or_move(src: Path, dst: Path, mode: str, skip_hidden: bool = True):
    """
    复制或移动文件/文件夹，跳过隐藏文件。
    src: 源路径
    dst: 目标路径（父目录下的完整目标路径）
    mode: 'copy' 或 'move'
    """
    if src.is_dir():
        # 创建目标文件夹
        dst.mkdir(parents=True, exist_ok=True)
        # 递归处理内部内容
        for item in src.iterdir():
            if skip_hidden and is_hidden(item):
                continue
            copy_or_move(item, dst / item.name, mode, skip_hidden)
        # 如果是移动，删除空源文件夹
        if mode == 'move':
            try:
                src.rmdir()
            except OSError:
                pass
    else:
        # 是文件
        if skip_hidden and is_hidden(src):
            return
        if mode == 'copy':
            shutil.copy2(src, dst)
        elif mode == 'move':
            # 确保目标父目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        else:
            raise ValueError(f"未知模式: {mode}")


def group_folders(input_dir: str, output_dir: str, mode: str, count: int):
    """
    主函数：分组子文件夹
    input_dir: 输入文件夹
    output_dir: 输出文件夹
    mode: 'copy' 或 'move'
    count: 每组数量
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"输入文件夹不存在或不是文件夹: {input_dir}")
    if mode not in ('copy', 'move'):
        raise ValueError(f"模式必须是 'copy' 或 'move'，当前: {mode}")
    if count <= 0:
        raise ValueError(f"数量必须大于 0，当前: {count}")

    # 创建输出文件夹
    output_path.mkdir(parents=True, exist_ok=True)

    # 获取所有非隐藏子文件夹（已按自然顺序排序）
    subfolders = get_subfolders(input_path)
    total = len(subfolders)

    if total == 0:
        print("输入文件夹下没有可处理的子文件夹（已跳过隐藏文件夹）。")
        return

    print(f"共找到 {total} 个子文件夹，每组 {count} 个，模式: {mode}")
    print("排序顺序（自然排序）:")
    for idx, f in enumerate(subfolders, 1):
        print(f"  {idx:3d}. {f.name}")
    print()

    # 分组并处理
    for i in range(0, total, count):
        group_index = i // count + 1
        group_name = f"group_{group_index:03d}"
        group_dir = output_path / group_name
        group_dir.mkdir(parents=True, exist_ok=True)

        batch = subfolders[i:i + count]
        for folder in batch:
            target = group_dir / folder.name
            try:
                copy_or_move(folder, target, mode)
                print(f"[{mode}] {folder.name} -> {group_name}/")
            except Exception as e:
                print(f"处理 {folder} 时出错: {e}")

        print(f"分组 {group_name} 完成，共 {len(batch)} 个文件夹")

    print("全部处理完成。")


if __name__ == "__main__":
    input_dir = "/Volumes/西数4T外置/大量去水印/20261105-2/第四批截图"
    output_dir = f"{input_dir}_分组"
    mode = "copy" # copy 或 move
    folder_count = 6

    group_folders(
        input_dir=input_dir,
        output_dir = output_dir,
        mode = mode,
        count = folder_count
    )
