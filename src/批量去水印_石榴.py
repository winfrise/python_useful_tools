
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

# 接口统一返回结构: {"code": 0, "msg": "success", "data": {...}, "success": true}
# code == 0 (或 success == true) 表示成功, 非 0 为错误, msg 为具体错误原因(以接口返回为准)
# 下列含义仅作为常见约定的辅助说明, 实际仍以接口返回的 msg 优先
CODE_MEANINGS = {
    0:   "成功",
    400: "请求参数错误(如 image_base64 为空或格式非法)",
    401: "APIKEY 无效或未授权",
    403: "无访问权限 / 免费额度耗尽或欠费",
    404: "接口地址或目标资源不存在",
    413: "图片体积过大(单张建议不超过 20MB)",
    429: "请求过于频繁, 已触发限流",
    500: "服务端内部错误",
    502: "网关错误",
    503: "服务暂时不可用",
    504: "网关超时",
}
# 临时性错误(可重试); 其余错误码视为硬错误, 重试无意义直接失败
RETRYABLE_CODES = {429, 500, 502, 503, 504}

# ================= 核心工具函数 =================

def describe_code(code):
    """返回错误码的中文含义说明"""
    return CODE_MEANINGS.get(code, "未知错误码(详见接口返回的 msg)")

def encode_image_to_base64(image_path):
    """将本地图片读取并编码为 Base64 字符串"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_image_bytes(response_data):
    """
    从 data 字段(或顶层)中提取图片二进制数据。
    兼容多种可能的返回字段(result_base64 / image_base64 / url / image_id)。
    """
    # 优先在 data 子对象中查找, 找不到再回退到顶层
    scopes = []
    if isinstance(response_data.get("data"), dict):
        scopes.append(response_data["data"])
    scopes.append(response_data)

    for obj in scopes:
        # 1. 优先尝试 Base64 字段(石榴接口常见为 result_base64)
        for key in ("result_base64", "image_base64", "base64"):
            if obj.get(key):
                try:
                    b64 = obj[key]
                    # 去掉可能的 data:image/...;base64, 前缀
                    if isinstance(b64, str) and "," in b64 and b64.strip().startswith("data:"):
                        b64 = b64.split(",", 1)[1]
                    return base64.b64decode(b64)
                except Exception as e:
                    logger.warning(f"Base64 字段[{key}]解码失败: {e}")

        # 2. 尝试直接下载 URL
        for key in ("url", "image_url"):
            if obj.get(key):
                try:
                    resp = requests.get(obj[key], timeout=30)
                    resp.raise_for_status()
                    return resp.content
                except Exception as e:
                    logger.warning(f"URL[{key}]下载失败: {e}")

    return None

def handle_api_response(resp, image_path):
    """
    校验并解析单次 HTTP 响应, 做 code 判断。
    返回 (img_bytes, retryable):
        - img_bytes 非 None: 成功拿到结果图
        - img_bytes 为 None: 失败, 已打印 code + msg; retryable 决定是否值得重试
    """
    # --- HTTP 层状态码判断 ---
    if resp.status_code != 200:
        retryable = resp.status_code in RETRYABLE_CODES
        msg = ""
        try:
            j = resp.json()
            msg = j.get("msg") or j.get("message") or ""
        except Exception:
            msg = resp.text[:200]
        logger.error(
            f"[HTTP错误] {os.path.basename(image_path)} "
            f"status={resp.status_code}({describe_code(resp.status_code)})"
            + (f" | msg: {msg}" if msg else "")
        )
        return None, retryable

    # --- 解析 JSON 业务体 ---
    try:
        data = resp.json()
    except Exception as e:
        logger.error(f"[解析失败] {os.path.basename(image_path)}: 返回非合法JSON - {e}")
        return None, False

    # --- 业务 code 判断(核心) ---
    code = data.get("code")
    success = data.get("success")
    msg = data.get("msg") or data.get("message") or ""
    # 成功条件: code == 0 或 success == True
    is_ok = (code == 0) or (success is True)

    if not is_ok:
        code_show = code if code is not None else "N/A"
        retryable = (code in RETRYABLE_CODES) if code is not None else False
        logger.error(
            f"[接口返回错误] {os.path.basename(image_path)} "
            f"code={code_show}({describe_code(code) if code is not None else '缺少code字段'})"
            + (f" | msg: {msg}" if msg else " | msg: 无")
            + " | 可重试" if retryable else
            f"[接口返回错误] {os.path.basename(image_path)} "
            f"code={code_show}({describe_code(code) if code is not None else '缺少code字段'})"
            + (f" | msg: {msg}" if msg else " | msg: 无")
            + " | 不可重试"
        )
        return None, retryable

    # --- code 正常, 提取图片 ---
    img_bytes = extract_image_bytes(data)
    if img_bytes is None:
        if "image_id" in (data.get("data") if isinstance(data.get("data"), dict) else data):
            logger.warning(
                f"[无结果图] {os.path.basename(image_path)}: 接口仅返回 image_id, "
                f"需二次请求获取结果, 当前版本未实现自动二次获取"
            )
        else:
            logger.error(
                f"[解析失败] {os.path.basename(image_path)}: code正常但未找到结果图字段"
                f" | 原始返回: {str(data)[:200]}"
            )
        return None, False

    return img_bytes, False

# ================= 单图处理函数 =================
def process_single_image(image_path, output_dir, api_key, overwrite=False):
    """
    处理单张图片的去水印逻辑。
    包含: 检查跳过、API请求、code判断、失败重试、结果保存。
    """
    output_path = os.path.join(output_dir, f"no_wm_{Path(image_path).name}")

    # 断点续跑: 如果文件已存在且不需要覆盖, 直接跳过
    if os.path.exists(output_path) and not overwrite:
        logger.info(f"[跳过] 已存在: {output_path}")
        return "skipped"

    # 读取并编码图片
    try:
        img_base64 = encode_image_to_base64(image_path)
    except Exception as e:
        logger.error(f"[读取失败] {image_path}: {e}")
        return "failed"

    headers = {"APIKEY": api_key, "Content-Type": "application/json"}
    payload = {"image_base64": img_base64}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            img_bytes, retryable = handle_api_response(resp, image_path)

            if img_bytes is not None:
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                logger.info(f"[成功] {image_path} -> {output_path}")
                return "success"

            # code 层失败: 不可重试则立即结束, 不再空耗
            if not retryable:
                return "failed"
            # 可重试的临时错误 -> 退避后继续
            wait_time = 2 ** attempt
            logger.warning(
                f"[可重试错误] {os.path.basename(image_path)} "
                f"(尝试 {attempt + 1}/{max_retries}), {wait_time}秒后重试..."
            )
            time.sleep(wait_time)

        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt
            logger.warning(
                f"[请求异常] {image_path} (尝试 {attempt + 1}/{max_retries}): {e}。"
                f"{wait_time}秒后重试..."
            )
            time.sleep(wait_time)

    logger.error(f"[最终失败] {image_path} 达到最大重试次数或遇到不可重试错误。")
    return "failed"

# ================= 批量处理主函数 =================
def batch_remove_watermark(input_path, output_dir, api_key, max_workers=4, overwrite=False):
    """
    批量去水印入口函数。
    自动判断输入是单文件还是目录, 并使用线程池并发处理。
    """
    os.makedirs(output_dir, exist_ok=True)

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

    logger.info(f"共发现 {len(tasks)} 张图片, 启动 {max_workers} 个线程处理...")

    stats = {"success": 0, "skipped": 0, "failed": 0}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(process_single_image, path, output_dir, api_key, overwrite): path
            for path in tasks
        }
        for future in as_completed(future_to_path):
            result = future.result()
            stats[result] = stats.get(result, 0) + 1

    logger.info("=" * 40)
    logger.info("批量处理完成!")
    logger.info(f"成功: {stats['success']} | 跳过: {stats['skipped']} | 失败: {stats['failed']}")
    logger.info("=" * 40)

# ================= 命令行入口 =================
if __name__ == "__main__":

    input_path = "/Users/teacher/Desktop/111/001_output_bottom"

    base_name, ext = os.path.splitext(input_path)
    output_dir = f"{base_name}_去水印"
    print(output_dir)

    api_key = "nNPvHZ5njU7tvrkLUfCkAiptORViipO4"
    max_workers = 4
    overwrite = False
    batch_remove_watermark(
        input_path = input_path,
        output_dir = output_dir,
        api_key = api_key,  # SHILIUAI_API_KEY
        max_workers = max_workers,  # 并发线程数
        overwrite = overwrite,  # 强制覆盖已存在的输出文件
    )