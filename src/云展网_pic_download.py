import os
import requests
from urllib.parse import urlparse
from datetime import datetime


def download_images(txt_file_path):
    """
    从txt文件读取图片URL并批量下载，保存到txt同目录下的download_pic文件夹。

    参数：
        txt_file_path (str): txt文件的路径（需包含文件名，如 "urls.txt"）
    """
    # 1. 确定txt文件的目录和输出文件夹路径
    txt_dir = os.path.dirname(os.path.abspath(txt_file_path))  # txt所在目录的绝对路径
    timestamp = datetime.now().strftime("%Y年%m月%d日%H时%M分%S秒")
    output_dir = os.path.join(txt_dir, f"download_pic_{timestamp}")         # 输出文件夹路径（txt目录下）

    # 2. 创建输出文件夹（若不存在）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出文件夹：{output_dir}")
    else:
        print(f"输出文件夹已存在：{output_dir}")

    # 3. 读取txt文件中的URL列表
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]  # 过滤空行

    print(f"共读取到 {len(urls)} 个图片URL")

    # 4. 逐个下载图片
    for idx, url in enumerate(urls, 1):
        try:

            filename = f"image_{idx}.webp"

            # 构造本地保存路径
            save_path = os.path.join(output_dir, filename)

            # 发送GET请求下载图片（设置超时避免长时间等待）
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 检查HTTP状态码（非200则抛异常）

            # 写入本地文件
            with open(save_path, 'wb') as img_file:
                img_file.write(response.content)

            print(f"第 {idx} 张下载成功：{filename}")

        except requests.exceptions.RequestException as e:
            print(f"第 {idx} 张下载失败（URL：{url}），错误：{e}")
        except Exception as e:
            print(f"第 {idx} 张保存失败（URL：{url}），错误：{e}")

    print("所有图片下载完成！")


if __name__ == "__main__":
    # 替换为你的txt文件路径（示例："urls.txt" 表示当前目录下的urls.txt）
    txt_path = "/Users/teacher/Desktop/yunzhan/001_output_filter.txt"
    download_images(txt_path)