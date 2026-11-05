import os
import re
import json
from datetime import datetime


def natural_sort_key(name: str):
    """
    自然排序键：将字符串拆分为文本和数字片段，
    数字按数值大小比较，文本按字典序比较。
    例如：file2 < file10，img1_2 < img1_10
    """
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r'(\d+)', name)
    ]


def generate_directory_structure(folder_path: str, output_file: str = None) -> str:
    """
    生成指定文件夹的目录结构，并保存为JSON文件
    
    :param folder_path: 要扫描的文件夹路径
    :param output_file: 输出目录文件的路径（默认保存在folder_path下的 directory_structure.json）
    :return: 生成的目录文件路径
    """
    if not os.path.isdir(folder_path):
        raise ValueError(f"文件夹不存在或不是目录: {folder_path}")
    
    folder_path = os.path.abspath(folder_path)
    
    if output_file is None:
        output_file = os.path.join(folder_path, "directory_structure.json")
    else:
        output_file = os.path.abspath(output_file)
    
    structure = {
        "root": folder_path,
        "created_at": datetime.now().isoformat(),
        "type": "directory",
        "children": []
    }
    
    def scan_directory(path: str) -> dict:
        """递归扫描目录"""
        node = {
            "name": os.path.basename(path),
            "type": "directory",
            "children": []
        }
        try:
            entries = sorted(os.listdir(path), key=natural_sort_key)
        except PermissionError:
            node["error"] = "permission_denied"
            return node
        
        for entry in entries:
            # 跳过点开头的文件和目录
            if entry.startswith('.'):
                continue

            entry_path = os.path.join(path, entry)
            # 跳过输出文件自身
            if os.path.abspath(entry_path) == output_file:
                continue
            
            if os.path.isdir(entry_path):
                node["children"].append(scan_directory(entry_path))
            else:
                try:
                    size = os.path.getsize(entry_path)
                except OSError:
                    size = -1
                node["children"].append({
                    "name": entry,
                    "type": "file",
                    "size": size
                })
        return node
    
    # 扫描根目录下的所有条目
    try:
        entries = sorted(os.listdir(folder_path), key=natural_sort_key)
    except PermissionError as e:
        raise PermissionError(f"无权限读取文件夹: {folder_path}") from e
    
    for entry in entries:
        # 跳过点开头的文件和目录
        if entry.startswith('.'):
            continue

        entry_path = os.path.join(folder_path, entry)
        if os.path.abspath(entry_path) == output_file:
            continue
        if os.path.isdir(entry_path):
            structure["children"].append(scan_directory(entry_path))
        else:
            try:
                size = os.path.getsize(entry_path)
            except OSError:
                size = -1
            structure["children"].append({
                "name": entry,
                "type": "file",
                "size": size
            })
    
    # 写入JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    
    return output_file

if __name__ == "__main__":
    # 1. 生成目录结构文件
    folder_path = "/Volumes/西数4T外置/大量去水印/test"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17] 
    output_file = f"{folder_path}_{timestamp}.json"

    structure_file = generate_directory_structure(
        folder_path=folder_path,
        output_file=output_file,
    )
    print(f"目录结构已保存到: {structure_file}")
