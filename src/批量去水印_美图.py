import os
import base64
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== 配置区 ==========
APP_CODE = "你的阿里云AppCode"
API_URL = "https://market.aliyuncs.com/app/xxxx"  # 替换为实际购买后的接口地址
INPUT_DIR = "./input_meitu"
OUTPUT_DIR = "./output_meitu"
MAX_WORKERS = 10  # 并发线程数
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
# ==========================

def process_meitu(image_path: str):
    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
        
        headers = {
            "Authorization": f"APPCODE {APP_CODE}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {"image": image_b64}
        
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200: return f"[失败] {image_path} status={resp.status_code}"
        
        data = resp.json()
        result_url = data.get("image_url") or data.get("imageUrl")
        if not result_url: return f"[失败] {image_path} 未返回结果图"
        
        img_resp = requests.get(result_url, timeout=30)
        if img_resp.status_code == 200:
            out_path = Path(OUTPUT_DIR) / f"{Path(image_path).stem}_no_wm{Path(image_path).suffix}"
            out_path.write_bytes(img_resp.content)
            return f"[成功] {image_path}"
        return f"[失败] {image_path} 下载结果图失败"
    except Exception as e:
        return f"[异常] {image_path} {e}"

def batch_meitu():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    files = [str(f) for f in Path(INPUT_DIR).iterdir() if f.suffix.lower() in ALLOWED_EXTS]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_meitu, f): f for f in files}
        for future in as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    batch_meitu()