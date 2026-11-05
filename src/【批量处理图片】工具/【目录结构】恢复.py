import os
import json
import shutil


def restore_directory_structure(source_folder: str,
                                structure_file: str,
                                output_folder: str,
                                mode: str = "copy") -> None:
    """
    根据目录结构文件，把 source_folder 下的文件按结构整理到 output_folder

    :param source_folder:  源文件夹（文件实际所在的目录，扁平或任意组织都行）
    :param structure_file: 目录结构JSON文件路径
    :param output_folder:  输出文件夹（按结构组织后的存放目录）
    :param mode:           "copy"=复制, "move"=移动
    """
    if mode not in ("copy", "move"):
        raise ValueError(f"mode 只能是 'copy' 或 'move'，收到: {mode}")

    if not os.path.isdir(source_folder):
        raise ValueError(f"源文件夹不存在: {source_folder}")

    if not os.path.isfile(structure_file):
        raise ValueError(f"目录结构文件不存在: {structure_file}")

    with open(structure_file, "r", encoding="utf-8") as f:
        structure = json.load(f)

    source_folder = os.path.abspath(source_folder)
    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # 建立源文件夹下所有文件的索引：文件名 -> 完整路径（只索引文件名，用于扁平查找）
    # 若存在同名文件，保留第一个（或你可以改成按相对路径匹配）
    file_index = {}
    for root, _, files in os.walk(source_folder):
        for fname in files:
            file_index.setdefault(fname, os.path.join(root, fname))

    stats = {"copied": 0, "moved": 0, "missing": 0, "skipped": 0}
    missing_files = []

    def do_action(src: str, dst: str):
        """执行复制或移动"""
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if mode == "copy":
            shutil.copy2(src, dst)
            stats["copied"] += 1
        else:  # move
            shutil.move(src, dst)
            stats["moved"] += 1

    def restore_node(node: dict, parent_path: str):
        node_type = node.get("type")
        name = node.get("name", "")
        if not name:
            return

        if node_type == "directory":
            dir_path = os.path.join(parent_path, name)
            os.makedirs(dir_path, exist_ok=True)
            for child in node.get("children", []):
                restore_node(child, dir_path)

        elif node_type == "file":
            dst_path = os.path.join(parent_path, name)

            # 从源文件夹中找到该文件
            src_path = file_index.get(name)
            if not src_path:
                stats["missing"] += 1
                missing_files.append(name)
                print(f"警告：源文件夹中找不到文件 {name}，跳过")
                return

            # 目标已存在则跳过（避免覆盖）
            if os.path.exists(dst_path):
                stats["skipped"] += 1
                print(f"跳过已存在文件: {dst_path}")
                return

            try:
                do_action(src_path, dst_path)
            except OSError as e:
                print(f"警告：处理失败 {src_path} -> {dst_path}: {e}")

    for child in structure.get("children", []):
        restore_node(child, output_folder)

    print(f"\n整理完成 -> {output_folder}")
    print(f"  复制: {stats['copied']}  移动: {stats['moved']}  "
          f"跳过(已存在): {stats['skipped']}  缺失: {stats['missing']}")
    if missing_files:
        print(f"  缺失文件: {missing_files}")

if __name__ == "__main__":

    source_folder="/Volumes/西数4T外置/大量去水印/test_扁平化2"
    structure_file="/Volumes/西数4T外置/大量去水印/test_20261105103527552.json"
    output_folder=f"{source_folder}_恢复目录33"
    mode="copy"  # 可选值: copy | move

    restore_directory_structure(
        source_folder=source_folder,
        structure_file=structure_file,
        output_folder=output_folder,
        mode=mode
    )