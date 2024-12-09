import requests
import time
import json

# กำหนด Webhook URLs
webhook_urls = {
    "Teat": '',
    "Teat": '',
    "Teat": ''
}

# ตัวแปรสำหรับเก็บข้อมูลล่าสุด
last_data_1 = None
last_data_2 = None

# ฟังก์ชันในการตรวจสอบและส่งข้อความไปยัง Discord Webhook
def check_for_updates():
    global last_data_1, last_data_2

    url_1 = "https://prod-cn-alicdn-gamestarter.kurogame.com/pcstarter/prod/starter/10008_Pa0Q0EMFxukjEqX33pF9Uyvdc8MaGPSz/G152/index.json"
    url_2 = "https://prod-cn-alicdn-gamestarter.kurogame.com/pcstarter/prod/game/G152/10008_Pa0Q0EMFxukjEqX33pF9Uyvdc8MaGPSz/index.json"

    # ตรวจสอบข้อมูลจาก URL ที่ 1
    response_1 = requests.get(url_1)
    if response_1.status_code == 200:
        data_1 = response_1.json()
        if data_1 != last_data_1:
            send_webhooks(data_1, url_1, "Wuthering Waves BETA CN (Starter)", last_data_1)
            last_data_1 = data_1
    else:
        print(f"ไม่สามารถดึงข้อมูลจาก URL 1: {response_1.status_code}, {response_1.text}")

    # ตรวจสอบข้อมูลจาก URL ที่ 2
    response_2 = requests.get(url_2)
    if response_2.status_code == 200:
        data_2 = response_2.json()
        if data_2 != last_data_2:
            send_webhooks(data_2, url_2, "Wuthering Waves BETA CN (Game)", last_data_2)
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

    # คำนวณการเปลี่ยนแปลงของ "p"
    current_p = data["default"].get("p", None)
    last_p = last_data["default"].get("p", None) if last_data else None

    # แสดง diff ถ้ามีการเปลี่ยนแปลง
    if current_p and current_p != last_p:
        embed_fields.append({
            "name": "Diff:",
            "value": f"```diff\n- P: {last_p}\n+ P: {current_p}\n```" if last_p else f"```diff\n+ P: {current_p}\n```",
            "inline": False
        })

    # ข้อมูลเพิ่มเติม
    embed_fields.extend([
        {
            "name": "Version",
            "value": data["default"].get("version", "No data"),
            "inline": True
        },
        {
            "name": "Installer",
            "value": json.dumps(data["default"].get("installer", "No data"), ensure_ascii=False),
            "inline": False
        },
        {
            "name": "Resources",
            "value": json.dumps(data["default"].get("resources", "No data"), ensure_ascii=False),
            "inline": False
        }
    ])

    # ส่งข้อมูลไปยัง Webhook
    webhook_data = {
        "embeds": [
            {
                "title": title,
                "description": f"{url}",  # แสดงลิงก์เท่านั้น
                "color": 16771840,  # https://convertingcolors.com/decimal-color-16711680.html?search=Decimal(16711680)
                "fields": embed_fields,
                "image": {
                    "url": ""  # เพิ่มรูปภาพที่ด้านล่าง
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
    time.sleep(1)
