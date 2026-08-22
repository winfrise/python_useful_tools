import re

def filter_urls(input_txt_path, output_txt_path, filter_type, filter_value):
    """
    从输入TXT文件中过滤URL，输出到新TXT文件。

    :param input_txt_path: 输入TXT文件路径（每行一个URL）
    :param output_txt_path: 输出TXT文件路径
    :param filter_type: 过滤类型，'regex'（正则）或 'keyword'（关键字）
    :param filter_value: 过滤规则（正则表达式字符串 或 关键字字符串）
    """
    # 1. 读取输入文件所有URL
    with open(input_txt_path, 'r', encoding='utf-8') as f:
        urls = f.readlines()
    # 去除每行首尾空白符（如换行符、空格）
    urls = [url.strip() for url in urls if url.strip()]

    # 2. 根据过滤类型处理URL
    filtered_urls = []
    if filter_type == 'regex':
        # 正则匹配：编译正则后逐行匹配
        pattern = re.compile(filter_value)
        filtered_urls = [url for url in urls if pattern.search(url)]
    elif filter_type == 'keyword':
        # 关键字包含：判断URL是否包含关键字
        filtered_urls = [url for url in urls if filter_value in url]
    else:
        raise ValueError("filter_type 必须是 'regex' 或 'keyword'")

    # 3. 写入过滤后的URL到输出文件
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_urls) + '\n')  # 每个URL换行，末尾加换行保证格式

    print(f"原始 URL 数量: {len(urls)}")
    print(f"过滤后结果数量: {len(filtered_urls)}")
    print(f"处理完成，文件已保存至: {output_txt_path}")


# ------------------- 示例调用 -------------------
if __name__ == "__main__":
    # 示例1：正则过滤（匹配含 "yunzhan365" 的URL）
    input_txt_path = "/Users/teacher/Desktop/yunzhan/001.txt"
    output_text_path = input_txt_path.replace('.txt', '_output_filter.txt')
    filter_value = r'https://book\.yunzhan365\.com/dqfe/tbkc/files/large/[0-9a-f]{32}\.webp\?x-oss-process=image/resize,h_\d+,w_\d+/sharpen,\d+&\d+'
    filter_urls(
        input_txt_path=input_txt_path,
        output_txt_path=output_text_path,
        filter_type="regex",
        filter_value=filter_value  # 正则表达式，可根据需求调整（如 r"https?://.*\.webp" 匹配webp图片URL）
    )

    # 示例2：关键字过滤（匹配含 "yunzhan365" 的URL）
    # filter_urls(
    #     input_txt_path="input.txt",
    #     output_txt_path="output_keyword.txt",
    #     filter_type="keyword",
    #     filter_value="yunzhan365"  # 关键字，直接判断URL是否包含该字符串
    # )