import os
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# EX 
# RESOURCE_URL = "https://pcdownload-aliyun.aki-game.com/pcstarter/prod/game/G152/9.9.9/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/resource.json"
# CDN_BASE_URL = "https://pcdownload-huoshan.aki-game.com/pcstarter/prod/game/G152/9.9.9/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/zip/"

RESOURCE_URL = ""
CDN_BASE_URL = ""

def download_resources(resource_url, cdn_base_url, output_folder, filters=None, chunk_size=1048576, max_workers=100):
    try:
        response = requests.get(resource_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching resource metadata: {e}")
        return

    resources = response.json().get('resource', [])
    total_files = len(resources)
    downloaded_files = []
    failed_files = []

    os.makedirs(output_folder, exist_ok=True)

    # ตัวแปรสำหรับคำนวณความเร็ว
    total_bytes_downloaded = 0
    last_bytes_downloaded = 0
    speed_last_updated = time.time()

    # แสดงความคืบหน้าแบบรวม
    progress_bar = tqdm(total=total_files, desc="Overall download progress", unit="file", position=0)
    speed_desc = "Speed: 0.00 MB/s"
    speed_bar = tqdm(desc=speed_desc, position=1, bar_format="{desc}", total=0)

    def download_file_task(resource):
        nonlocal total_bytes_downloaded, last_bytes_downloaded, speed_last_updated
        if filters and not any(f in resource['dest'] for f in filters):
            progress_bar.update(1)
            return  # ข้ามไฟล์ที่ไม่ตรงกับตัวกรอง

        file_url = cdn_base_url + resource['dest'].lstrip('/')
        dest_path = os.path.join(output_folder, resource['dest'].lstrip('/'))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        try:
            bytes_downloaded = download_file(file_url, dest_path, resource['size'], chunk_size)
            total_bytes_downloaded += bytes_downloaded
            downloaded_files.append(resource['dest'])
        except Exception as e:
            failed_files.append(resource['dest'])
            print(f"Failed to download {resource['dest']}: {e}")
        finally:
            progress_bar.update(1)
            # อัปเดตความเร็ว
            current_time = time.time()
            elapsed_time = current_time - speed_last_updated
            if elapsed_time > 0.5:  # อัปเดตทุก 0.5 วินาที
                speed_mbps = (total_bytes_downloaded - last_bytes_downloaded) / (1024 * 1024 * elapsed_time)
                speed_desc = f"Speed: {speed_mbps:.2f} MB/s"
                speed_bar.set_description_str(speed_desc)
                speed_bar.refresh()
                last_bytes_downloaded = total_bytes_downloaded
                speed_last_updated = current_time

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_file_task, resource) for resource in resources]
        for future in as_completed(futures):
            pass  # รอให้แต่ละงานเสร็จสิ้น

    progress_bar.close()
    speed_bar.close()

    # สรุปผล
    print("\nDownload complete!")
    print(f"Successfully downloaded: {len(downloaded_files)} file(s) out of {total_files}")
    print(f"Failed downloads: {len(failed_files)} file(s)")

def download_file(url, dest, size, chunk_size=1048576, max_retries=3, timeout=30):
    bytes_downloaded = 0
    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
            return bytes_downloaded
        except requests.RequestException as e:
            if attempt < max_retries:
                print(f"Retrying ({attempt}/{max_retries}) for {url}...")
                time.sleep(5)
            else:
                raise Exception(f"Failed after {max_retries} attempts. Error: {e}")

def main():
    print("Welcome to the Resource Downloader!")
    output_folder = input("Enter the folder path to download the file. Enter the desired folder name.: ").strip()
    if not output_folder:
        print("Error: Output folder cannot be empty.")
        return
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filters = input("Enter file filters (e.g., '.zip,.png'), or press Enter to download all: ").strip()
    filters = [f.strip() for f in filters.split(',')] if filters else None

    max_workers = input("Enter the number of concurrent downloads (default: 100) (recommended: 10,000): ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 100

    download_resources(RESOURCE_URL, CDN_BASE_URL, output_folder, filters=filters, max_workers=max_workers)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
