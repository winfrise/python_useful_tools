import os
import shutil

def compare_folders(folder1, folder2):
    """
    对比两个文件夹中的文件，找出各自独有的文件，并提供交互式复制功能。
    """
    # 1. 获取两个文件夹中的文件名集合
    files1 = {f for f in os.listdir(folder1) if not f.startswith('.')}
    files2 = {f for f in os.listdir(folder2) if not f.startswith('.')}
    
    # 2. 利用集合运算找出差异
    # 文件夹1有，文件夹2没有
    only_in_folder1 = files1 - files2
    # 文件夹2有，文件夹1没有
    only_in_folder2 = files2 - files1
    
    # 3. 在控制台展示对比结果
    print("\n" + "="*50)
    print("📊 文件夹对比结果：")
    print("="*50)
    
    if not only_in_folder1 and not only_in_folder2:
        print("✅ 两个文件夹中的文件完全一致！")
        return
    
    if only_in_folder1:
        print(f"\n📁 仅在 [{folder1}] 中存在的文件 ({len(only_in_folder1)} 个):")
        for file in sorted(only_in_folder1):
            print(f"   - {file}")
            
    if only_in_folder2:
        print(f"\n📂 仅在 [{folder2}] 中存在的文件 ({len(only_in_folder2)} 个):")
        for file in sorted(only_in_folder2):
            print(f"   - {file}")
            
    print("="*50)
    
    # 4. 交互式操作
    print("\n请选择要执行的操作：")
    print("1. 将【文件夹1独有】的文件复制到【文件夹2】")
    print("2. 将【文件夹2独有】的文件复制到【文件夹1】")
    print("3. 退出")
    
    choice = input("请输入选项 (1/2/3): ").strip()
    
    if choice == '1':
        copy_files(only_in_folder1, folder1, folder2)
    elif choice == '2':
        copy_files(only_in_folder2, folder2, folder1)
    elif choice == '3':
        print("已退出。")
    else:
        print("⚠️ 无效的输入，请重新运行程序。")

def copy_files(files_set, source_dir, target_dir):
    """
    将指定的文件集合从源目录复制到目标目录。
    """
    if not files_set:
        print("没有需要复制的文件。")
        return
        
    print(f"\n⏳ 正在将 {len(files_set)} 个文件从 [{source_dir}] 复制到 [{target_dir}]...")
    success_count = 0
    for file in files_set:
        source_path = os.path.join(source_dir, file)
        target_path = os.path.join(target_dir, file)
        try:
            # 仅复制文件，跳过子文件夹（如需递归处理子文件夹可修改此处逻辑）
            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
                print(f"   ✔️ 成功: {file}")
                success_count += 1
            else:
                print(f"   ⚠️ 跳过文件夹: {file}")
        except Exception as e:
            print(f"   ❌ 失败: {file} | 错误: {e}")
            
    print(f"\n✅ 复制完成！成功复制 {success_count}/{len(files_set)} 个文件。")

# ================= 测试运行 =================
if __name__ == "__main__":
    # 替换为你实际要对比的文件夹路径
    dir1 = "/Volumes/西数4T外置/百度网盘默认下载/3、【政治】人教【选择性必修12合订】必刷题26/政治-人教-选修一二-主书__提取的图片_output_滑块去水印"
    dir2 = "/Volumes/西数4T外置/百度网盘默认下载/3、【政治】人教【选择性必修12合订】必刷题26/政治-人教-选修一二-主书__提取的图片_output_滑块去水印_output_图片覆盖"
    
    # 简单的路径存在性检查
    if not os.path.exists(dir1) or not os.path.exists(dir2):
        print(f"⚠️ 请确保文件夹 '{dir1}' 和 '{dir2}' 存在！")
    else:
        compare_folders(dir1, dir2)