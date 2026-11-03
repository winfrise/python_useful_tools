import os
import shutil


def flatten_directory(src_dir: str, dst_dir: str, separator: str = '-') -> None:
    """
    将源文件夹中的所有文件（包括子文件夹中的文件）扁平化复制到目标文件夹。
    文件名格式：相对路径（用分隔符分隔）- 原文件名
    
    Args:
        src_dir: 输入文件夹路径
        dst_dir: 输出文件夹路径
        separator: 自定义分隔符，默认为 '-'。不能包含路径分隔符 '/' 或 '\\'
    """
    # 参数校验
    if not os.path.isdir(src_dir):
        raise ValueError(f"源文件夹不存在或不是文件夹: {src_dir}")
    if not separator:
        raise ValueError("分隔符不能为空")
    if '/' in separator or '\\' in separator:
        raise ValueError(f"分隔符不能包含路径分隔符: {separator!r}")
    if separator in ('.', '..'):
        raise ValueError(f"分隔符不能是 '.' 或 '..'")
    
    # 创建目标文件夹（如果不存在）
    os.makedirs(dst_dir, exist_ok=True)
    
    # 获取源文件夹的绝对路径，用于计算相对路径
    src_dir_abs = os.path.abspath(src_dir)
    
    # 用于记录文件名冲突的情况
    name_conflicts = []
    
    # 遍历源文件夹下的所有文件
    for root, dirs, files in os.walk(src_dir_abs):
        for filename in files:
            # 文件的完整路径
            file_path = os.path.join(root, filename)
            
            # 计算相对于源文件夹的相对路径
            rel_path = os.path.relpath(file_path, src_dir_abs)
            
            # 将路径分隔符替换为自定义分隔符
            # 例如: "sub1/sub2/file.txt" -> "sub1-sub2-file.txt"（separator='-'）
            flat_name = rel_path.replace(os.sep, separator)
            
            # 处理 Windows 下可能的其他分隔符（防御性）
            flat_name = flat_name.replace('/', separator).replace('\\', separator)
            
            # 目标文件路径
            dst_path = os.path.join(dst_dir, flat_name)
            
            # 如果目标文件已存在，说明有冲突，追加序号
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(flat_name)
                counter = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(dst_dir, f"{base}_{counter}{ext}")
                    counter += 1
                name_conflicts.append((file_path, dst_path))
            
            # 复制文件（保留元数据）
            shutil.copy2(file_path, dst_path)
    
    # 输出处理结果
    print(f"文件扁平化完成！")
    print(f"  源文件夹: {src_dir_abs}")
    print(f"  目标文件夹: {os.path.abspath(dst_dir)}")
    print(f"  使用分隔符: {separator!r}")
    if name_conflicts:
        print(f"  有 {len(name_conflicts)} 个文件因重名被重命名：")
        for src, dst in name_conflicts:
            print(f"    {src} -> {os.path.basename(dst)}")


if __name__ == '__main__':
    # 使用示例
    src_dir = "/Users/teacher/Downloads/260张图片去水印"
    dst_dir = f"{src_dir}_扁平化"
    flatten_directory(
        src_dir=src_dir,
        dst_dir=dst_dir,
        separator='#',  # 可改为 '__'、'@' 等自定义分隔符
    )