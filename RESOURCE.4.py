import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# EX 
# RESOURCE_URL = "https://pcdownload-aliyun.aki-game.com/pcstarter/prod/game/G152/9.9.9/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/resource.json"
# CDN_BASE_URL = "https://pcdownload-huoshan.aki-game.com/pcstarter/prod/game/G152/9.9.9/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/zip/"

RESOURCE_URL = ""
CDN_BASE_URL = ""


class DownloadManager:
    def __init__(self):
        self.total_bytes_downloaded = 0
        self.last_bytes_downloaded = 0
        self.speed_last_updated = time.time()

    def download_resources(self, resource_url, cdn_base_url, output_folder, filters=None, chunk_size=8388608, max_workers=100):
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

        # Progress bars
        progress_bar = tqdm(total=total_files, desc="Overall download progress", unit="file", position=0)
        speed_desc = "Speed: 0.00 MB/s"
        speed_bar = tqdm(desc=speed_desc, position=1, bar_format="{desc}", total=0)
        time_bar = tqdm(desc="Elapsed Time: 0s", position=2, bar_format="{desc}", total=0)

        start_time = time.time()  # Start timer

        def update_elapsed_time():
            while not progress_bar.n == total_files:
                elapsed_time = time.time() - start_time
                time_bar.set_description(f"Elapsed Time: {int(elapsed_time)}s")
                time_bar.refresh()
                time.sleep(1)

        def download_file_task(resource):
            if filters and not any(f in resource['dest'] for f in filters):
                progress_bar.update(1)
                return

            file_url = cdn_base_url + resource['dest'].lstrip('/')
            dest_path = os.path.join(output_folder, resource['dest'].lstrip('/'))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            try:
                bytes_downloaded = self.download_file(file_url, dest_path, resource['size'], chunk_size)
                self.total_bytes_downloaded += bytes_downloaded
                downloaded_files.append(resource['dest'])
            except Exception as e:
                failed_files.append(resource['dest'])
                print(f"Failed to download {resource['dest']}: {e}")
            finally:
                progress_bar.update(1)
                self.update_speed(speed_bar)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Start elapsed time tracker
            from threading import Thread
            elapsed_time_thread = Thread(target=update_elapsed_time, daemon=True)
            elapsed_time_thread.start()

            futures = [executor.submit(download_file_task, resource) for resource in resources]
            for future in as_completed(futures):
                pass

        progress_bar.close()
        speed_bar.close()
        time_bar.close()

        end_time = time.time()  # End timer

        # Summary
        elapsed_time = end_time - start_time
        print("\nDownload complete!")
        print(f"Successfully downloaded: {len(downloaded_files)} file(s) out of {total_files}")
        print(f"Failed downloads: {len(failed_files)} file(s)")
        print(f"Total time: {elapsed_time:.2f} seconds")

    def download_file(self, url, dest, size, chunk_size=1048576, max_retries=3, timeout=30):
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

    def update_speed(self, speed_bar):
        current_time = time.time()
        elapsed_time = current_time - self.speed_last_updated
        if elapsed_time > 0.5:  # Update every 0.5 seconds
            speed_mbps = (self.total_bytes_downloaded - self.last_bytes_downloaded) / (1024 * 1024 * elapsed_time)
            speed_bar.set_description(f"Speed: {speed_mbps:.2f} MB/s")
            speed_bar.refresh()
            self.last_bytes_downloaded = self.total_bytes_downloaded
            self.speed_last_updated = current_time


def main():
    manager = DownloadManager()
    print("Welcome to the Resource Downloader!")
    output_folder = input("Name the file : ").strip()
    if not output_folder:
        print("Error: Output folder cannot be empty.")
        return
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filters = input("Enter to download all: ").strip()
    filters = [f.strip() for f in filters.split(',')] if filters else None

    max_workers = input("number of files to download (recommended 1,000): ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 1000

    manager.download_resources(RESOURCE_URL, CDN_BASE_URL, output_folder, filters=filters, max_workers=max_workers)


if __name__ == "__main__":
    main()
