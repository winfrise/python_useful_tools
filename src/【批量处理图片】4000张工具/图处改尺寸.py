import os
import re
from pathlib import Path
from PIL import Image


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}


def natural_key(text: str):
    """
    对单个字符串做自然排序键。
    例如：'img2' < 'img10'，'第2章' < '第10章'
    """
    parts = re.split(r"(\d+)", text)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part)))
        else:
            key.append((0, part.lower()))
    return key


def natural_sort_paths(paths):
    """
    对 Path 列表按完整路径逐段自然排序：
    先比父目录各段，再比文件名，保证目录层级和文件名都符合自然顺序。
    """
    def key(p: Path):
        result = []
        for part in p.parts:
            for sub in re.split(r"(\d+)", part):
                if sub.isdigit():
                    result.append((1, int(sub)))
                else:
                    result.append((0, sub.lower()))
        return result

    return sorted(paths, key=key)


def iter_images_natural(root: Path):
    """
    按自然顺序递归遍历目录：
    - 每一层的子目录按自然顺序进入
    - 每一层的文件按自然顺序处理
    只 yield 图片文件。
    """
    try:
        entries = list(root.iterdir())
    except PermissionError:
        return

    # 分开目录和文件
    dirs = [p for p in entries if p.is_dir()]
    files = [p for p in entries if p.is_file()]

    # 分别自然排序
    dirs = natural_sort_paths(dirs)
    files = natural_sort_paths(files)

    # 先处理当前层文件（按自然序）
    for f in files:
        if f.suffix.lower() in IMAGE_EXTS:
            yield f

    # 再按自然序递归进入子目录
    for d in dirs:
        yield from iter_images_natural(d)


def resize_images_by_reference(folder1: str, folder2: str, folder3: str):
    """
    遍历 folder1 中的图片，按 folder2 中同名图片的宽高进行缩放，结果保存到 folder3，
    并保持原有目录结构。文件夹与文件均按自然排序处理。

    :param folder1: 源图片文件夹（要修改尺寸的图片）
    :param folder2: 参考图片文件夹（提供目标宽高）
    :param folder3: 输出文件夹
    """
    folder1_path = Path(folder1)
    folder2_path = Path(folder2)
    folder3_path = Path(folder3)

    if not folder1_path.exists():
        raise FileNotFoundError(f"文件夹1不存在: {folder1}")

    # 按自然顺序递归遍历源图片
    for src_file in iter_images_natural(folder1_path):
        rel_path = src_file.relative_to(folder1_path)

        # 在 folder2 中查找同名文件
        ref_file = folder2_path / rel_path

        if not ref_file.exists():
            candidates = [
                p for p in folder2_path.rglob(src_file.name) if p.is_file()
            ]
            if not candidates:
                print(f"[跳过] 文件夹2中未找到对应文件: {rel_path}")
                continue
            # 多个同名候选也按自然顺序取第一个
            candidates = natural_sort_paths(candidates)
            ref_file = candidates[0]

        # 获取参考图片的宽高
        try:
            with Image.open(ref_file) as ref_img:
                target_size = ref_img.size  # (width, height)
        except Exception as e:
            print(f"[跳过] 无法读取参考图片 {ref_file}: {e}")
            continue

        # 打开源图片并调整尺寸
        try:
            with Image.open(src_file) as img:
                resized = img.resize(target_size, Image.LANCZOS)

                out_file = folder3_path / rel_path
                out_file.parent.mkdir(parents=True, exist_ok=True)

                save_kwargs = {}
                if out_file.suffix.lower() in {".jpg", ".jpeg"} and resized.mode in ("RGBA", "LA", "P"):
                    resized = resized.convert("RGB")

                fmt = img.format if img.format else None
                if fmt:
                    save_kwargs["format"] = fmt

                resized.save(out_file, **save_kwargs)
                print(f"[完成] {rel_path} -> {target_size}")
        except Exception as e:
            print(f"[失败] 处理 {src_file} 出错: {e}")


if __name__ == "__main__":
    folder1 = "/Users/teacher/Downloads/260张图片去水印_扁平化_还原目录/001"
    folder2 = "/Users/teacher/Downloads/260张图片去水印_扁平化_还原目录/002"
    folder3 = "/Users/teacher/Downloads/260张图片去水印_扁平化_还原目录/003"
    resize_images_by_reference(
        folder1=folder1,
        folder2=folder2,
        folder3=folder3
    )