import os
from pathlib import Path
from typing import Optional, Union, List, Dict

# ========== 常量定义 ==========

# 所有格式的通配符
ALL_FORMATS = "*"

# 图片格式常量
IMAGE_FORMATS: List[str] = [".jpg", ".jpeg", ".png"]


# ========== 主函数 ==========

def count_files(
    folder_path: Union[str, Path],
    formats: Union[str, List[str]] = IMAGE_FORMATS,
    recursive: bool = True,
    return_detail: bool = False,
) -> Union[int, Dict[str, int]]:
    """
    统计指定文件夹下的文件数量（包括所有子文件夹中的文件）。
    
    参数:
        folder_path (str | Path): 要统计的文件夹路径
        formats (str | List[str]): 文件格式过滤，支持:
            - "*"                    统计所有格式（默认常量为 ALL_FORMATS）
            - 单个格式，如 ".jpg" 或 "jpg"
            - 多个格式的列表，如 [".jpg", ".png"]
            - 默认值为图片的所有格式（DEFAULT_FORMATS）
        recursive (bool): 是否递归统计子文件夹，默认 True
        return_detail (bool): 是否返回按扩展名分组的详细统计，默认 False
    
    返回:
        int: 文件总数（return_detail=False）
        dict: {扩展名: 数量, ...} 及总数（return_detail=True）
    
    示例:
        >>> count_files("./photos")                        # 默认统计所有图片
        123
        >>> count_files("./photos", ALL_FORMATS)           # 统计所有文件
        456
        >>> count_files("./photos", [".jpg", ".png"])      # 统计 jpg 和 png
        78
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"文件夹不存在: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"路径不是文件夹: {folder}")

    # ---- 规范化 formats 参数 ----
    # 判断是否为 "统计所有格式"
    match_all = False

    if formats is None:
        match_all = False  # None 视为不匹配任何格式? 这里按"全部"处理更合理，见下方
    if isinstance(formats, str):
        if formats == ALL_FORMATS:
            match_all = True
        else:
            formats = [formats]
    else:
        # 列表/元组中如果包含 "*"，也视为匹配所有格式
        if ALL_FORMATS in formats:
            match_all = True

    # 构建统一小写、带点前缀的扩展名集合
    ext_set: Optional[set] = None
    if not match_all:
        if formats is None:
            ext_set = set()  # 空集合 => 不统计任何文件
        else:
            ext_set = {
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in formats
            }

    total = 0
    detail: Dict[str, int] = {}

    # ---- 遍历策略 ----
    if recursive:
        walker = os.walk(folder)
    else:
        walker = [(str(folder), [], os.listdir(folder))]

    for root, _, files in walker:
        for filename in files:
            ext = Path(filename).suffix.lower()

            # 格式过滤：match_all 为 True 时不过滤
            if not match_all and ext not in ext_set:
                continue

            total += 1
            if return_detail:
                key = ext if ext else "(无扩展名)"
                detail[key] = detail.get(key, 0) + 1

    if return_detail:
        detail["total"] = total
        return detail

    return total


if __name__ == "__main__":
    path = "."


    folder_path = "/Users/teacher/Downloads/260张图片去水印/001"
    formats = ['.jpg', '.png']
    recursive = True # 是否递归
    return_detail = True # 是否返回详细

    total = count_files(
        folder_path=folder_path,
        formats=formats,
        recursive=recursive,
        return_detail=return_detail
    )

    print(total)

