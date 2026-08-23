import re

def filter_and_extract_urls(input_txt_path, output_txt_path, pattern_str):
    """
    过滤并提取特定格式的URL片段，并进行去重。
    :param input_txt_path: 输入TXT文件路径
    :param output_txt_path: 输出TXT文件路径
    :param pattern_str: 用于匹配和提取的正则表达式字符串
    """
    # 1. 读取输入文件
    try:
        with open(input_txt_path, 'r', encoding='utf-8') as f:
            urls = f.readlines()
    except FileNotFoundError:
        print(f"错误：找不到文件 {input_txt_path}")
        return

    # 预处理：去空行、去首尾空格
    urls = [url.strip() for url in urls if url.strip()]
    print(f"正在处理，原始行数: {len(urls)}")

    # 2. 编译正则表达式
    try:
        # r"" 表示原始字符串，防止反斜杠转义问题
        pattern = re.compile(f"({pattern_str})")
    except re.error as e:
        print(f"正则表达式错误: {e}")
        return

    extracted_results = []
    seen = set()  # 【新增】用于存储已经出现过的URL，实现去重
    duplicate_count = 0 # 【新增】统计去重数量

    # 3. 遍历并提取
    for url in urls:
        match = pattern.search(url)
        if match:
            result_url = match.group(1)
            # 【修改】判断是否已存在
            if result_url not in seen:
                extracted_results.append(result_url)
                seen.add(result_url)
            else:
                duplicate_count += 1

    # 4. 打印统计信息
    print(f"原始数量: {len(urls)}")
    print(f"匹配提取数量 (去重前): {len(extracted_results) + duplicate_count}")
    print(f"重复数量: {duplicate_count}")
    print(f"最终保存数量 (去重后): {len(extracted_results)}")

    # 5. 写入结果到新文件
    if extracted_results:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            for item in extracted_results:
                f.write(item + '\n')
        print(f"成功！结果已保存至: {output_txt_path}")
    else:
        print("未匹配到任何内容，未生成新文件。")

# ================= 使用示例 =================
if __name__ == '__main__':
    # 输入文件路径
    input_txt_path = "/Users/teacher/Desktop/yunzhan/001.txt"
    output_text_path = input_txt_path.replace('.txt', '_output_filter.txt')
    
    # 定义核心匹配规则
    target_pattern = r'https://book\.yunzhan365\.com/dqfe/tbkc/files/large/[0-9a-f]{32}\.webp\?x-oss-process=image'
    
    # 执行函数
    filter_and_extract_urls(input_txt_path, output_text_path, target_pattern)