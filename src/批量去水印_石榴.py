import os
import base64
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== 配置区 ==========
API_KEY = "你的石榴智能APIKey"
API_URL = "https://api.shiliuai.com/api/auto_inpaint/v1"
INPUT_DIR = "./input_shiliu"
OUTPUT_DIR = "./output_shiliu"
MAX_WORKERS = 10  # 并发线程数
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
# ==========================

def process_shiliu(image_path: str):
    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
        
        headers = {
            "APIKEY": API_KEY,
            "Content-Type": "application/json"
        }
        payload = {"image_base64": image_b64}
        
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200: return f"[失败] {image_path} status={resp.status_code}"
        
        data = resp.json()
        # 石榴智能通常返回处理后的 base64 字符串或 URL
        result_base64 = data.get("result_base64")
        result_url = data.get("image_url")
        
        out_path = Path(OUTPUT_DIR) / f"{Path(image_path).stem}_no_wm{Path(image_path).suffix}"
        
        if result_base64:
            out_path.write_bytes(base64.b64decode(result_base64))
            return f"[成功] {image_path}"
        elif result_url:
            img_resp = requests.get(result_url, timeout=30)
            if img_resp.status_code == 200:
                out_path.write_bytes(img_resp.content)
                return f"[成功] {image_path}"
                
        return f"[失败] {image_path} 解析结果异常"
    except Exception as e:
        return f"[异常] {image_path} {e}"

def batch_shiliu():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    files = [str(f) for f in Path(INPUT_DIR).iterdir() if f.suffix.lower() in ALLOWED_EXTS]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_shiliu, f): f for f in files}
        for future in as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    batch_shiliu()