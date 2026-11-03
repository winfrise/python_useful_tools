import os
from pathlib import Path
from PIL import Image


def resize_images_by_reference(folder1: str, folder2: str, folder3: str):
    """
    遍历 folder1 中的图片，按 folder2 中同名图片的宽高进行缩放，结果保存到 folder3，
    并保持原有目录结构。

    :param folder1: 源图片文件夹（要修改尺寸的图片）
    :param folder2: 参考图片文件夹（提供目标宽高）
    :param folder3: 输出文件夹
    """
    folder1_path = Path(folder1)
    folder2_path = Path(folder2)
    folder3_path = Path(folder3)

    if not folder1_path.exists():
        raise FileNotFoundError(f"文件夹1不存在: {folder1}")

    # 支持常见图片格式，可自行扩展
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}

    for src_file in folder1_path.rglob("*"):
        if not src_file.is_file():
            continue
        if src_file.suffix.lower() not in image_exts:
            continue

        # 计算相对路径（保持目录结构）
        rel_path = src_file.relative_to(folder1_path)

        # 在 folder2 中查找同名文件
        ref_file = folder2_path / rel_path

        if not ref_file.exists():
            # 如果按相对路径找不到，尝试在 folder2 中按文件名查找（递归）
            candidates = [
                p for p in folder2_path.rglob(src_file.name) if p.is_file()
            ]
            if not candidates:
                print(f"[跳过] 文件夹2中未找到对应文件: {rel_path}")
                continue
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
                # 保留原图模式，resize 会默认用 bicubic 插值
                resized = img.resize(target_size, Image.LANCZOS)

                # 构造输出路径，保持目录结构
                out_file = folder3_path / rel_path
                out_file.parent.mkdir(parents=True, exist_ok=True)

                # 保存（注意：对于 JPEG 需转 RGB，避免带 alpha 保存失败）
                save_kwargs = {}
                if out_file.suffix.lower() in {".jpg", ".jpeg"} and resized.mode in ("RGBA", "LA", "P"):
                    resized = resized.convert("RGB")

                # 尽量沿用原图格式
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