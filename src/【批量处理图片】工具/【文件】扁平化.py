import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Union

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def flatten_files(
    source_dir: Union[str, Path],
    output_dir: Union[str, Path],
    action: str = "copy",
    naming: str = "original",
    separator: str = "__",
    overwrite: bool = False,
    recursive: bool = True,
    skip_hidden: bool = True,
) -> dict:
    """
    将 source_dir 下的所有文件扁平化到 output_dir。

    参数:
        source_dir: 源目录
        output_dir: 输出目录（不存在会自动创建）
        action: "copy" 复制 / "move" 移动
        naming: "original" 使用原文件名 / "prefixed" 目录前缀 + 原文件名
        separator: 生成前缀时的分隔符，默认为 "_"
        overwrite: 同名文件是否覆盖，False 时会自动加序号避免冲突
        recursive: 是否递归子目录
        skip_hidden: 是否跳过隐藏文件/目录

    返回:
        统计信息 dict: {"total": n, "success": n, "failed": n, "skipped": n, "details": [...]}
    """
    source_dir = Path(source_dir).resolve()
    output_dir = Path(output_dir).resolve()

    # 参数校验
    if not source_dir.is_dir():
        raise NotADirectoryError(f"源目录不存在或不是目录: {source_dir}")
    if action not in ("copy", "move"):
        raise ValueError(f"action 只能是 'copy' 或 'move'，当前值: {action}")
    if naming not in ("original", "prefixed"):
        raise ValueError(f"naming 只能是 'original' 或 'prefixed'，当前值: {naming}")
    if not separator:
        raise ValueError("separator 不能为空")
    if separator in ("/", "\\"):
        raise ValueError("separator 不能是路径分隔符")

    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "details": [],
    }

    # 遍历文件
    if recursive:
        walker = os.walk(source_dir)
    else:
        walker = [(str(source_dir), [], [f for f in os.listdir(source_dir)
                                          if (source_dir / f).is_file()])]

    for root, dirs, files in walker:
        root_path = Path(root)

        # 跳过隐藏目录（递归时需原地过滤 dirs）
        if skip_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in files:
            if skip_hidden and filename.startswith("."):
                continue

            src = root_path / filename
            stats["total"] += 1

            try:
                # 计算目标文件名
                if naming == "original":
                    new_name = filename
                else:  # prefixed
                    # 相对 source_dir 的父目录路径，用分隔符连接
                    rel_parent = root_path.relative_to(source_dir)
                    if str(rel_parent) == ".":
                        # 源目录根下的文件，无前缀
                        prefix = ""
                    else:
                        prefix = separator.join(rel_parent.parts) + separator
                    new_name = prefix + filename

                # 处理空文件名（极端情况）
                if not new_name:
                    raise ValueError("生成的目标文件名为空")

                dst = _resolve_target(output_dir / new_name, overwrite)

                # 执行操作
                if action == "copy":
                    shutil.copy2(src, dst)
                else:
                    shutil.move(str(src), str(dst))

                stats["success"] += 1
                stats["details"].append({
                    "status": "success",
                    "src": str(src),
                    "dst": str(dst),
                })
                logger.info(f"[{action.upper()}] {src} -> {dst}")

            except Exception as e:
                stats["failed"] += 1
                stats["details"].append({
                    "status": "failed",
                    "src": str(src),
                    "error": str(e),
                })
                logger.error(f"处理失败: {src}, 原因: {e}")

    return stats


def _resolve_target(dst: Path, overwrite: bool) -> Path:
    """当目标文件已存在且不允许覆盖时，自动在文件名后加 (1), (2)..."""
    if overwrite or not dst.exists():
        return dst

    stem, suffix = dst.stem, dst.suffix
    parent = dst.parent
    i = 1
    while True:
        candidate = parent / f"{stem}({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


if __name__ == "__main__":

    source_dir="/Volumes/西数4T外置/大量去水印/test"  # 源目录
    output_dir=f"{source_dir}_扁平化2"  # 输出目录
    action="copy"      # 复制(copy)或移动(move)（默认 copy）
    naming="prefixed" # 命名方式（默认 original） original, prefixed
    separator="__"     # 前缀分隔符（默认 '__'）
    overwrite=False  # 是否允许覆盖同名文件
    recursive=True   # 是否递归子目录
    skip_hidden=True # 包含隐藏文件

    result = flatten_files(
        source_dir=source_dir,
        output_dir=output_dir,
        action=action,
        naming=naming,
        separator=separator,
        overwrite=overwrite,
        recursive=recursive,
        skip_hidden=skip_hidden,
    )

    print("\n===== 完成 =====")
    print(f"总计: {result['total']}, 成功: {result['success']}, "
          f"失败: {result['failed']}")