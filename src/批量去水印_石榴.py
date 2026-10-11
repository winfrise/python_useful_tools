import os
import sys
import time
import base64
import logging
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# ================= 配置与日志设置 =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

API_URL = "https://api.shiliuai.com/api/auto_inpaint/v1"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# ================= 核心工具函数 =================

def encode_image_to_base64(image_path):
    """将本地图片读取并编码为 Base64 字符串"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_image_bytes(response_data):
    """
    从API返回的JSON中提取图片二进制数据。
    兼容多种可能的返回字段（base64、url、image_id）。
    """
    # 1. 优先尝试 Base64
    if "image_base64" in response_data and response_data["image_base64"]:
        try:
            return base64.b64decode(response_data["image_base64"])
        except Exception as e:
            logger.warning(f"Base64 解码失败: {e}")

    # 2. 尝试直接下载 URL
    if "url" in response_data and response_data["url"]:
        try:
            resp = requests.get(response_data["url"], timeout=30)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.warning(f"URL 下载失败: {e}")

    # 3. 兜底：如果只返回了 image_id，可能需要二次请求（此处仅做记录）
    if "image_id" in response_data:
        logger.warning("API仅返回 image_id，暂不支持自动二次获取，请检查API文档。")
        
    return None

# ================= 单图处理函数 =================
def process_single_image(image_path, output_dir, api_key, overwrite=False):
    """
    处理单张图片的去水印逻辑。
    包含：检查跳过、API请求、失败重试、结果保存。
    """
    output_path = os.path.join(output_dir, f"no_wm_{Path(image_path).name}")
    
    # 断点续跑：如果文件已存在且不需要覆盖，直接跳过
    if os.path.exists(output_path) and not overwrite:
        logger.info(f"[跳过] 已存在: {output_path}")
        return "skipped"

    # 读取并编码图片
    try:
        img_base64 = encode_image_to_base64(image_path)
    except Exception as e:
        logger.error(f"[读取失败] {image_path}: {e}")
        return "failed"

    # 请求API（带指数退避重试）
    headers = {"APIKEY": api_key, "Content-Type": "application/json"}
    payload = {"image_base64": img_base64}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            # 提取结果
            img_bytes = extract_image_bytes(data)
            if img_bytes:
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                logger.info(f"[成功] {image_path} -> {output_path}")
                return "success"
            else:
                logger.error(f"[解析失败] {image_path}，返回数据: {data}")
                return "failed"
                
        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt
            logger.warning(f"[请求异常] {image_path} (尝试 {attempt+1}/{max_retries}): {e}。{wait_time}秒后重试...")
            time.sleep(wait_time)
            
    logger.error(f"[最终失败] {image_path} 达到最大重试次数。")
    return "failed"

# ================= 批量处理主函数 =================
def batch_remove_watermark(input_path, output_dir, api_key, max_workers=4, overwrite=False):
    """
    批量去水印入口函数。
    自动判断输入是单文件还是目录，并使用线程池并发处理。
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 收集所有待处理的图片路径
    tasks = []
    input_p = Path(input_path)
    if input_p.is_file() and input_p.suffix.lower() in SUPPORTED_EXTENSIONS:
        tasks.append(str(input_p))
    elif input_p.is_dir():
        for ext in SUPPORTED_EXTENSIONS:
            tasks.extend([str(p) for p in input_p.rglob(f"*{ext}")])
            tasks.extend([str(p) for p in input_p.rglob(f"*{ext.upper()}")])
    else:
        logger.error(f"输入路径无效或格式不支持: {input_path}")
        return

    logger.info(f"🚀 共发现 {len(tasks)} 张图片，启动 {max_workers} 个线程处理...")
    
    # 统计结果
    stats = {"success": 0, "skipped": 0, "failed": 0}
    
    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(process_single_image, path, output_dir, api_key, overwrite): path 
            for path in tasks
        }
        
        for future in as_completed(future_to_path):
            result = future.result()
            stats[result] = stats.get(result, 0) + 1

    # 打印汇总报告
    logger.info("="*40)
    logger.info("🎉 批量处理完成！")
    logger.info(f"✅ 成功: {stats['success']} | ⏭️ 跳过: {stats['skipped']} | ❌ 失败: {stats['failed']}")
    logger.info("="*40)


# ================= 命令行入口 =================
if __name__ == "__main__":


    input_path = ""
    output_dir = ""
    api_key = "nNPvHZ5njU7tvrkLUfCkAiptORViipO4"
    max_workers = 4
    overwrite = False
    batch_remove_watermark(
        input_path = input_path,
        output_dir = output_dir,
        api_key = api_key,  # SHILIUAI_API_KEY
        max_workers = max_workers, # 并发线程数
        overwrite = overwrite, # 强制覆盖已存在的输出文件
    )