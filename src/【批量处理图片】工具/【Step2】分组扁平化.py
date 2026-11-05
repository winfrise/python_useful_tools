import os
import shutil
from pathlib import Path


def flatten_folders(input_dir, output_dir, mode='copy'):
    """
    遍历输入文件夹下的子文件夹，将子文件夹中嵌套文件夹里的文件扁平化到子文件夹层级，
    然后放入输出文件夹。
    
    结构示例:
        输入/子文件夹A/嵌套文件夹1/file1.txt
        输入/子文件夹A/嵌套文件夹2/file2.txt
        =>
        输出/子文件夹A/file1.txt
        输出/子文件夹A/file2.txt
    
    :param input_dir:  输入文件夹路径
    :param output_dir: 输出文件夹路径
    :param mode:       'copy' 或 'move'
    """
    if mode not in ('copy', 'move'):
        raise ValueError("mode 参数只能是 'copy' 或 'move'")

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.is_dir():
        raise NotADirectoryError(f"输入文件夹不存在: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    stats = {'copied': 0, 'moved': 0, 'skipped': 0, 'renamed': 0}

    # 遍历输入文件夹下的每个子文件夹
    for sub_dir in input_path.iterdir():
        if not sub_dir.is_dir():
            continue
        # 跳过隐藏子文件夹
        if sub_dir.name.startswith('.'):
            stats['skipped'] += 1
            continue

        # 目标子文件夹（与输入子文件夹同名）
        target_sub_dir = output_path / sub_dir.name
        target_sub_dir.mkdir(parents=True, exist_ok=True)

        # 遍历子文件夹下所有层级中的文件
        for root, dirs, files in os.walk(sub_dir):
            # 过滤隐藏文件夹（原地修改 dirs 可阻止 os.walk 深入）
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file_name in files:
                # 跳过隐藏文件
                if file_name.startswith('.'):
                    stats['skipped'] += 1
                    continue

                src_file = Path(root) / file_name
                dst_file = target_sub_dir / file_name

                # 处理同名文件：自动重命名以避免覆盖
                if dst_file.exists():
                    base = dst_file.stem
                    ext = dst_file.suffix
                    idx = 1
                    while dst_file.exists():
                        dst_file = target_sub_dir / f"{base}_{idx}{ext}"
                        idx += 1
                    stats['renamed'] += 1

                try:
                    if mode == 'copy':
                        shutil.copy2(src_file, dst_file)
                        stats['copied'] += 1
                    else:  # move
                        shutil.move(str(src_file), str(dst_file))
                        stats['moved'] += 1
                    print(f"[{mode}] {src_file}  ->  {dst_file}")
                except Exception as e:
                    print(f"[错误] 处理 {src_file} 失败: {e}")
                    stats['skipped'] += 1

        # move 模式下，删除空的嵌套文件夹（保留子文件夹本身）
        if mode == 'move':
            _remove_empty_dirs(sub_dir, keep_root=True)

    # 输出统计
    print("\n===== 完成 =====")
    print(f"复制: {stats['copied']}  移动: {stats['moved']}  "
          f"重命名避免冲突: {stats['renamed']}  跳过: {stats['skipped']}")
    return stats


def _remove_empty_dirs(root_dir, keep_root=True):
    """递归删除空文件夹"""
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for d in dirs:
            dir_path = Path(root) / d
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except OSError:
                pass


if __name__ == '__main__':
    input_dir = "/Volumes/西数4T外置/大量去水印/20261105-2/第四批截图_分组"
    output_dir = f"{input_dir}_组扁平化"
    mode = "copy" # copy 或 move
    flatten_folders(
        input_dir=input_dir,
        output_dir=output_dir,
        mode = mode
    )