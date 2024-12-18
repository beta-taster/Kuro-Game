import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # ใช้แสดง Progress Bar

RESOURCE_URL = ""
CDN_BASE_URL = ""

# ใช้ session เพื่อประหยัด TCP connections
session = requests.Session()

def download_file(url, dest, size, session, progress_bar, max_retries=3, timeout=30, chunk_size=65536):
    attempt = 0
    while attempt < max_retries:
        try:
            with session.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                # ตรวจสอบว่ามีไฟล์อยู่แล้วหรือไม่ และขนาดตรงกันหรือเปล่า
                if os.path.exists(dest) and os.path.getsize(dest) == size:
                    progress_bar.update(size)  # ข้ามไปที่ Progress Bar ทันที
                    return
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))  # อัปเดต Progress Bar
            return
        except requests.RequestException as e:
            attempt += 1
            if attempt >= max_retries:
                print(f"Failed to download {url} after {max_retries} attempts")
                return

def download_resources(resource_url, cdn_base_url, output_folder, max_workers=16):
    response = session.get(resource_url)
    response.raise_for_status()
    resources = response.json().get('resource', [])

    # คำนวณขนาดรวมทั้งหมดของไฟล์
    total_size = sum([res['size'] for res in resources])
    
    # สร้าง Progress Bar
    with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, ncols=100, desc="Downloaded files") as progress_bar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for resource in resources:
                file_url = cdn_base_url + resource['dest'].lstrip('/')
                dest_path = os.path.join(output_folder, resource['dest'].lstrip('/'))
                futures.append(executor.submit(download_file, file_url, dest_path, resource['size'], session, progress_bar))

            for future in as_completed(futures):
                future.result()  # Raise exception ถ้าการดาวน์โหลดล้มเหลว

def main():
    output_folder = input("Enter the folder path to download files to: ").strip()
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    start_time = time.time()
    download_resources(RESOURCE_URL, CDN_BASE_URL, output_folder)
    elapsed_time = time.time() - start_time
    print(f"\nAll downloads completed in {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
