import os
import re
import shutil

def organize_folders(source_dir, target_dir):
    """
    整理并重命名文件夹 (修复了带换行符文件名的问题)
    """
    
    if not os.path.exists(source_dir):
        print(f"错误：源文件夹 '{source_dir}' 不存在。")
        return

    all_items = os.listdir(source_dir)
    folders_to_process = []

    # 【关键修改】在正则表达式中加入 re.DOTALL 标志，或者在匹配前清理字符串
    # 这里我们选择在读取文件名时，把换行符替换为空，统一格式
    pattern = re.compile(r"[\(（](\d+)[\)）]")
    
    for item in all_items:
        item_path = os.path.join(source_dir, item)
        
        if os.path.isdir(item_path):
            # 清理掉名字里的换行符 \n 和 \r，变成单行纯文本
            clean_name = item.replace('\n', '').replace('\r', '')
            
            match = pattern.search(clean_name)
            if match:
                number = int(match.group(1))
                folders_to_process.append({
                    'old_name': item,  # 移动时仍使用原来的真实名字（带换行符的）
                    'old_path': item_path,
                    'number': number
                })

    if not folders_to_process:
        print("未找到符合格式的文件夹。")
        return

    # 自然排序
    folders_to_process.sort(key=lambda x: x['number'])

    print(f"共找到 {len(folders_to_process)} 个文件夹，开始处理...")

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    group_size = 7 
    
    for index, folder_info in enumerate(folders_to_process):
        group_num = (index // group_size) + 1
        group_name = f"组{group_num:03d}"
        group_path = os.path.join(target_dir, group_name)
        
        if not os.path.exists(group_path):
            os.makedirs(group_path)

        new_folder_name = str(folder_info['number'])
        new_folder_path = os.path.join(group_path, new_folder_name)

        try:
            # 如果在目标文件夹中已经存在同名文件夹（比如你之前运行过一次残留的），先删除或提示
            if os.path.exists(new_folder_path):
                print(f"[跳过] '{group_name}/{new_folder_name}' 已存在，请检查。")
                continue
                
            shutil.move(folder_info['old_path'], new_folder_path)
            print(f"[成功] '{folder_info['old_name']}' -> '{group_name}/{new_folder_name}'")
        except Exception as e:
            print(f"[失败] 无法处理 '{folder_info['old_name']}': {e}")

    print("\n所有操作完成！")

# ================= 使用示例 =================
if __name__ == "__main__":
    # 请将下面的路径替换为你电脑上实际的文件夹路径
    
    # 文件夹1 (源文件夹，包含那一堆副本)
    # 注意：Windows路径建议前面加 r，防止转义，例如 r"D:\Test\Folder1"
    source_path = r"/Volumes/西数4T外置/百度网盘默认下载/47个文件夹/47个" 
    
    # 文件夹2 (目标文件夹，整理后的结果放这里)
    target_path = f"{source_path}_分组"

    # 执行函数
    organize_folders(source_path, target_path)