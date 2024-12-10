import os
import json
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

RESOURCE_URL = ""
CDN_BASE_URL = ""

# Configure logging
log_filename = "download_log.txt"
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def show_large_file_status(file_name, file_url):
    print(f"Downloading large file: {file_name}")
    print(f"URL: {file_url}")

def download_resources(resource_url, cdn_base_url, output_folder, chunk_size=1048576, max_workers=100):
    try:
        response = requests.get(resource_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching resource metadata: {e}")
        return

    resources = response.json().get('resource', [])
    total_files = len(resources)
    downloaded_files = []
    failed_files = []

    os.makedirs(output_folder, exist_ok=True)

    # Track download speed
    total_bytes_downloaded = 0
    last_bytes_downloaded = 0
    speed_last_updated = time.time()

    # Overall progress
    progress_bar = tqdm(total=total_files, desc="Overall download progress", unit="file", position=0)
    speed_desc = "Speed: 0.00 MB/s"
    speed_bar = tqdm(desc=speed_desc, position=1, bar_format="{desc}", total=0)

    def download_file_task(resource):
        nonlocal total_bytes_downloaded, last_bytes_downloaded, speed_last_updated

        file_url = cdn_base_url + resource['dest'].lstrip('/')
        dest_path = os.path.join(output_folder, resource['dest'].lstrip('/'))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Check if file is larger than 1GB and display its status
        if resource['size'] > 1 * 1024 * 1024 * 1024:  # 1GB in bytes
            show_large_file_status(resource['dest'], file_url)

        try:
            bytes_downloaded = download_file(file_url, dest_path, resource['size'], chunk_size)
            total_bytes_downloaded += bytes_downloaded
            downloaded_files.append(resource['dest'])
            logger.info(f"Downloaded {resource['dest']}")
        except Exception as e:
            failed_files.append(resource['dest'])
            logger.error(f"Failed to download {resource['dest']}: {e}")
        finally:
            progress_bar.update(1)
            # Update download speed
            current_time = time.time()
            elapsed_time = current_time - speed_last_updated
            if elapsed_time > 0.5:
                speed_mbps = (total_bytes_downloaded - last_bytes_downloaded) / (1024 * 1024 * elapsed_time)
                speed_desc = f"Speed: {speed_mbps:.2f} MB/s"
                speed_bar.set_description_str(speed_desc)
                speed_bar.refresh()
                last_bytes_downloaded = total_bytes_downloaded
                speed_last_updated = current_time

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_file_task, resource) for resource in resources]
        for future in as_completed(futures):
            pass  # Wait for each task to complete

    progress_bar.close()
    speed_bar.close()

    # Summary of the download process
    logger.info("\nDownload complete!")
    logger.info(f"Successfully downloaded: {len(downloaded_files)} file(s) out of {total_files}")
    logger.info(f"Failed downloads: {len(failed_files)} file(s)")

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
                logger.warning(f"Retrying ({attempt}/{max_retries}) for {url}...")
                time.sleep(5)
            else:
                logger.error(f"Failed after {max_retries} attempts. Error: {e}")
                raise Exception(f"Failed after {max_retries} attempts. Error: {e}")

def main():
    output_folder = "./downloads"
    os.makedirs(output_folder, exist_ok=True)
    download_resources(RESOURCE_URL, CDN_BASE_URL, output_folder)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nExiting...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
