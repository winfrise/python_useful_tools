import os
import hashlib
import json
from typing import List, Dict, Set, Optional, Tuple, Callable, Any

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


# ============ 1. 属性获取函数 ============

def get_file_size(filepath: str) -> int:
    """获取文件大小（字节）"""
    return os.path.getsize(filepath)


def get_file_md5(filepath: str) -> str:
    """获取文件 MD5"""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def get_image_dimensions(filepath: str) -> Optional[Tuple[int, int]]:
    """获取图片宽高，非图片返回 None"""
    if not _HAS_PIL:
        return None
    try:
        with Image.open(filepath) as img:
            return img.size
    except Exception:
        return None


# 内置属性注册表：名称 -> 获取函数
BUILTIN_ATTR_GETTERS: Dict[str, Callable[[str], Any]] = {
    "size": get_file_size,
    "md5": get_file_md5,
    "dimensions": get_image_dimensions,
}


# ============ 2. 目录遍历辅助函数 ============

def list_subdirs(folder: str) -> Set[str]:
    """获取文件夹下第一层子文件夹名"""
    return {e.name for e in os.scandir(folder) if e.is_dir()}


def list_files(folder: str) -> Set[str]:
    """获取文件夹下第一层文件名（不递归）"""
    return {e.name for e in os.scandir(folder) if e.is_file()}


# ============ 3. 属性批量获取 ============

def get_attributes(filepath: str,
                   attr_names: List[str],
                   attr_getters: Dict[str, Callable[[str], Any]]) -> Dict[str, Any]:
    """批量获取文件属性"""
    result = {}
    for name in attr_names:
        getter = attr_getters.get(name)
        if getter is None:
            result[name] = f"<未注册属性: {name}>"
            continue
        try:
            result[name] = getter(filepath)
        except Exception as e:
            result[name] = f"<获取失败: {e}>"
    return result


# ============ 4. 核心对比函数 ============

def compare_folders(folder_a: str,
                    folder_b: str,
                    attributes: Optional[List[str]] = None,
                    extra_getters: Optional[Dict[str, Callable[[str], Any]]] = None) -> Dict[str, Any]:
    """
    对比两个文件夹（只遍历到子文件夹这一层）

    :param folder_a: 文件夹 A 路径
    :param folder_b: 文件夹 B 路径
    :param attributes: 需要对比的文件属性列表，如 ["size", "md5", "dimensions"]
    :param extra_getters: 额外的自定义属性获取器 {名称: 函数}
    :return: 对比结果字典
    """
    attributes = attributes or ["size"]
    attr_getters = dict(BUILTIN_ATTR_GETTERS)
    if extra_getters:
        attr_getters.update(extra_getters)

    folder_a = os.path.abspath(folder_a)
    folder_b = os.path.abspath(folder_b)

    if not os.path.isdir(folder_a):
        raise NotADirectoryError(f"不是有效文件夹: {folder_a}")
    if not os.path.isdir(folder_b):
        raise NotADirectoryError(f"不是有效文件夹: {folder_b}")

    # --- 子文件夹对比 ---
    subdirs_a = list_subdirs(folder_a)
    subdirs_b = list_subdirs(folder_b)
    only_in_a_dirs = sorted(subdirs_a - subdirs_b)
    only_in_b_dirs = sorted(subdirs_b - subdirs_a)
    common_dirs = sorted(subdirs_a & subdirs_b)

    # --- 文件对比 ---
    files_a = list_files(folder_a)
    files_b = list_files(folder_b)
    only_in_a_files = sorted(files_a - files_b)
    only_in_b_files = sorted(files_b - files_a)
    common_files = sorted(files_a & files_b)

    # --- 共有文件属性对比 ---
    file_attr_diffs = []
    for fname in common_files:
        path_a = os.path.join(folder_a, fname)
        path_b = os.path.join(folder_b, fname)
        attrs_a = get_attributes(path_a, attributes, attr_getters)
        attrs_b = get_attributes(path_b, attributes, attr_getters)

        diffs = {}
        for attr in attributes:
            va, vb = attrs_a.get(attr), attrs_b.get(attr)
            # list 转 tuple 便于比较
            if isinstance(va, list):
                va = tuple(va)
            if isinstance(vb, list):
                vb = tuple(vb)
            if va != vb:
                diffs[attr] = {"A": va, "B": vb}

        if diffs:
            file_attr_diffs.append({
                "file": fname,
                "path_a": path_a,
                "path_b": path_b,
                "diffs": diffs,
            })

    is_consistent = not (
        only_in_a_dirs or only_in_b_dirs or
        only_in_a_files or only_in_b_files or
        file_attr_diffs
    )

    return {
        "folder_a": folder_a,
        "folder_b": folder_b,
        "compared_attributes": attributes,
        "is_consistent": is_consistent,
        "subdirs": {
            "only_in_a": only_in_a_dirs,
            "only_in_b": only_in_b_dirs,
            "common": common_dirs,
        },
        "files": {
            "only_in_a": only_in_a_files,
            "only_in_b": only_in_b_files,
            "common": common_files,
            "attr_diffs": file_attr_diffs,
        },
    }


# ============ 5. 报告打印函数 ============

def print_report(result: Dict[str, Any]) -> None:
    print("=" * 70)
    print(f"文件夹 A: {result['folder_a']}")
    print(f"文件夹 B: {result['folder_b']}")
    print(f"对比属性: {result['compared_attributes']}")
    print("=" * 70)
    print(f"\n[总体一致]: {'✅ 是' if result['is_consistent'] else '❌ 否'}")

    print("\n--- 子文件夹对比 ---")
    sd = result["subdirs"]
    print(f"仅 A 存在: {sd['only_in_a'] or '无'}")
    print(f"仅 B 存在: {sd['only_in_b'] or '无'}")
    print(f"共有 {len(sd['common'])} 个")

    print("\n--- 文件对比 ---")
    f = result["files"]
    print(f"仅 A 存在: {f['only_in_a'] or '无'}")
    print(f"仅 B 存在: {f['only_in_b'] or '无'}")
    print(f"共有 {len(f['common'])} 个")

    if f["attr_diffs"]:
        print("\n--- 属性差异文件 ---")
        for item in f["attr_diffs"]:
            print(f"\n  文件: {item['file']}")
            for attr, val in item["diffs"].items():
                print(f"    {attr}: A={val['A']}  |  B={val['B']}")
    else:
        print("\n共有文件属性全部一致 ✅")
    print("\n" + "=" * 70)


# ============ 6. 使用示例 ============

if __name__ == "__main__":
    # 示例 1：基础对比（文件大小 + 图片宽高 + MD5）
    folder_a = "/Users/teacher/Downloads/260张图片去水印_扁平化_还原目录"
    folder_b = "/Users/teacher/Downloads/260张图片去水印"
    attributes=["size", "dimensions", "md5"]
    custom_attributes = {}

    # custom_attributes = {
    #     "mtime": lambda p: os.path.getmtime(p),
    #     "ext": lambda p: os.path.splitext(p)[1].lower(),
    # }

    result = compare_folders(
        folder_a=folder_a,
        folder_b=folder_b,
        attributes=attributes,
        extra_getters = custom_attributes
    )
    print_report(result)

    # 示例 2：注册并使用自定义属性（如修改时间）
    # custom = {
    #     "mtime": lambda p: os.path.getmtime(p),
    #     "ext": lambda p: os.path.splitext(p)[1].lower(),
    # }
    # result2 = compare_folders(
    #     folder_a="./folderA",
    #     folder_b="./folderB",
    #     attributes=["mtime", "ext"],
    #     extra_getters=custom,
    # )
    # print_report(result2)

    # 保存 JSON 报告
    # with open("compare_report.json", "w", encoding="utf-8") as fp:
    #     json.dump(result, fp, ensure_ascii=False, indent=2, default=str)
    # print("报告已保存到 compare_report.json")