import requests
import time
import json

# กำหนด Webhook URLs
webhook_urls = {
    "Teat": ''
    "Teat": ''
    "Teat": ''
}

# ตัวแปรสำหรับเก็บข้อมูลล่าสุด
last_data_1 = None
last_data_2 = None

# ฟังก์ชันในการตรวจสอบและส่งข้อความไปยัง Discord Webhook
def check_for_updates():
    global last_data_1, last_data_2

    url_1 = "https://prod-cn-alicdn-gamestarter.kurogame.com/pcstarter/prod/starter/10003_Y8xXrXk65DqFHEDgApn3cpK5lfczpFx5/G152/index.json"
    url_2 = "https://prod-cn-alicdn-gamestarter.kurogame.com/pcstarter/prod/game/G152/10003_Y8xXrXk65DqFHEDgApn3cpK5lfczpFx5/index.json"

    # ตรวจสอบข้อมูลจาก URL ที่ 1
    response_1 = requests.get(url_1)
    if response_1.status_code == 200:
        data_1 = response_1.json()
        if data_1 != last_data_1:
            send_webhooks(data_1, url_1, "Wuthering Waves CN (Starter)", last_data_1)
            last_data_1 = data_1
    else:
        print(f"ไม่สามารถดึงข้อมูลจาก URL 1: {response_1.status_code}, {response_1.text}")

    # ตรวจสอบข้อมูลจาก URL ที่ 2
    response_2 = requests.get(url_2)
    if response_2.status_code == 200:
        data_2 = response_2.json()
        if data_2 != last_data_2:
            send_webhooks(data_2, url_2, "Wuthering Waves CN (Game)", last_data_2)
            last_data_2 = data_2
    else:
        print(f"ไม่สามารถดึงข้อมูลจาก URL 2: {response_2.status_code}, {response_2.text}")

# ฟังก์ชันในการส่งข้อมูลไปยัง Discord Webhook หลายอัน
def send_webhooks(data, url, title, last_data):
    for webhook_key in webhook_urls:
        send_webhook(data, url, title, webhook_key, last_data)

# ฟังก์ชันในการส่งข้อมูลไปยัง Discord Webhook หนึ่งอัน
def send_webhook(data, url, title, webhook_key, last_data):
    embed_fields = []

    # ข้อมูลเพิ่มเติมจาก URL
    current_version = data["default"].get("version", "No data")
    current_installer = data["default"].get("installer", "No data")
    current_resources = data["default"].get("resources", "No data")


    # ข้อมูลเพิ่มเติมสำหรับ "resourceChunk"


    # ตรวจสอบว่า "predownload" มีอยู่ในข้อมูลหรือไม่
    predownload = data["predownload"] if "predownload" in data else {}


    predownload_resources = predownload.get("resources", "No data")


    # เพิ่มข้อมูลลงใน embed_fields
    embed_fields.extend([
        {
            "name": "Version",
            "value": current_version,
            "inline": True
        },
        {
            "name": "Installer",
            "value": json.dumps(current_installer, ensure_ascii=False),
            "inline": False
        },
        {
            "name": "Resources",
            "value": current_resources,  # Display the resources path as a string
            "inline": False
        },

        {
            "name": "Predownload Resources",
            "value": predownload_resources,
            "inline": False
        }

    ])

    # ส่งข้อมูลไปยัง Webhook
    webhook_data = {
        "embeds": [
            {
                "title": title,
                "description": f"{url}",  # แสดงลิงก์เท่านั้น
                "color": 16711680,  # สีแดง
                "fields": embed_fields,
                "image": {
                    "url": "https://cdn.oneesports.gg/cdn-data/2024/03/WutheringWaves_Game_Rover_Wallpaper-1024x576.jpg"  # เพิ่มรูปภาพที่ด้านล่าง
                }
            }
        ]
    }

    # เพิ่มรูปภาพที่ด้านบนขวา
    webhook_data["embeds"][0]["thumbnail"] = {
        "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQkmsLi-PweF4K3vppsBMmbrQ2zFikTpYHdNg&s"  # เพิ่มลิงก์รูปภาพที่ด้านบนขวา
    }

    webhook_url = webhook_urls.get(webhook_key)
    if webhook_url:
        response = requests.post(webhook_url, json=webhook_data)
        if response.status_code == 204:
            print(f"ส่งข้อความ {title} ไปยัง Discord ({webhook_key}) เรียบร้อยแล้ว!")
        else:
            print(f"ไม่สามารถส่งข้อความ {title} ได้ที่ Webhook {webhook_key}: {response.status_code}, {response.text}")

# ตรวจสอบข้อมูลทุก 60 วินาที
while True:
    check_for_updates()
    time.sleep(60)
