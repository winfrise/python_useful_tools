import os
import re
import shutil


# ==================== 工具函数 ====================

def natural_sort_key(s):
    """自然排序 key：把字符串中的数字片段当作整数比较"""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r'(\d+)', str(s))]


def get_subfolders(folder_path):
    """获取 folder_path 下所有直接子文件夹，按自然排序返回"""
    subs = [f for f in os.listdir(folder_path)
            if os.path.isdir(os.path.join(folder_path, f))]
    subs.sort(key=natural_sort_key)
    return subs


def get_image_files(folder_path):
    """获取 folder_path 下所有图片文件名（不递归）"""
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp'}
    return [f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
            and os.path.splitext(f)[1].lower() in exts]


def validate_paths(folder1, folder2):
    """校验两个入参文件夹是否合法"""
    if not os.path.isdir(folder1):
        raise ValueError(f"文件夹1不存在或不是目录: {folder1}")
    if not os.path.isdir(folder2):
        raise ValueError(f"文件夹2不存在或不是目录: {folder2}")


# ==================== 核心步骤函数 ====================

def check_subfolder_count(subs1, subs2):
    """校验两个子文件夹列表数量是否一致"""
    print(f"文件夹1子文件夹数量: {len(subs1)}")
    print(f"文件夹2子文件夹数量: {len(subs2)}")
    if len(subs1) != len(subs2):
        raise ValueError("两个文件夹的子文件夹数量不一致，终止执行。")
    return True


def print_mapping(subs1, subs2):
    """打印两个文件夹子文件夹的对应关系"""
    print("\n========== 子文件夹对应关系 ==========")
    for i, (s1, s2) in enumerate(zip(subs1, subs2), 1):
        print(f"  {i:>3}. [{s1}]  <-->  [{s2}]")
    print("======================================\n")


def build_category_map(grandson_folders, path2):
    """
    构建 {图片名(不含扩展名): 类别名} 的映射
    类别名即孙文件夹名
    """
    mapping = {}
    for category in grandson_folders:
        category_path = os.path.join(path2, category)
        for img in get_image_files(category_path):
            name_no_ext = os.path.splitext(img)[0]
            mapping[name_no_ext] = category
    return mapping


def classify_one_subfolder(path1, path2, out_sub, sub_name):
    """
    处理一对对应的子文件夹：
      - 从 path2 的孙文件夹构建类别映射
      - 把 path1 中的图片按映射分类复制到 out_sub/<类别>/
      - 未匹配的放入 out_sub/_unmatched/
    返回 (匹配统计 dict, 未匹配图片列表)
    """
    grandson_folders = get_subfolders(path2)
    if not grandson_folders:
        print(f"    [警告] {sub_name} 下没有孙文件夹，跳过")
        return {}, []

    print(f"    分类类别（孙文件夹）: {grandson_folders}")

    category_map = build_category_map(grandson_folders, path2)
    images1 = get_image_files(path1)
    if not images1:
        print(f"    [警告] {sub_name} 下没有图片，跳过")
        return {}, []

    stats, unmatched = {}, []
    for img in images1:
        src = os.path.join(path1, img)
        name_no_ext = os.path.splitext(img)[0]

        if name_no_ext in category_map:
            category = category_map[name_no_ext]
            dst_dir = os.path.join(out_sub, category)
            stats[category] = stats.get(category, 0) + 1
        else:
            dst_dir = os.path.join(out_sub, "_unmatched")
            unmatched.append(img)

        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(dst_dir, img))

    return stats, unmatched


def print_subfolder_result(stats, unmatched):
    """打印单个子文件夹的分类结果"""
    total = sum(stats.values()) + len(unmatched)
    print(f"    图片总数: {total}")
    for cat, cnt in stats.items():
        print(f"      [{cat}] {cnt} 张")
    if unmatched:
        print(f"      [_unmatched] {len(unmatched)} 张 -> {unmatched}")


# ==================== 主流程函数 ====================

def classify_images(folder1, folder2, output_folder):
    """
    主函数：3 个参数
      folder1       : 子文件夹内是图片
      folder2       : 子文件夹内有孙文件夹，孙文件夹内是图片
      output_folder : 输出根目录
    """
    validate_paths(folder1, folder2)

    subs1 = get_subfolders(folder1)
    subs2 = get_subfolders(folder2)

    check_subfolder_count(subs1, subs2)
    print_mapping(subs1, subs2)

    os.makedirs(output_folder, exist_ok=True)

    for s1, s2 in zip(subs1, subs2):
        print(f"\n>>> 处理: {s1}  <-->  {s2}")
        path1 = os.path.join(folder1, s1)
        path2 = os.path.join(folder2, s2)
        out_sub = os.path.join(output_folder, s1)

        stats, unmatched = classify_one_subfolder(path1, path2, out_sub, s1)
        print_subfolder_result(stats, unmatched)

    print(f"\n✅ 全部完成，输出目录: {output_folder}")


# ==================== 入口 ====================

if __name__ == "__main__":

    source_dir = "/Volumes/西数4T外置/大量去水印/47组去水印完成"
    name_dir = "/Volumes/西数4T外置/大量去水印/7个为一组"
    output_dir = f"{source_dir}_恢复分组"
    classify_images(
        folder1=source_dir, 
        folder2=name_dir, 
        output_folder = output_dir
    )
