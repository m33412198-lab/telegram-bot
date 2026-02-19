import requests
import time
import uuid
import json

# 🔴 توکن رباتتو اینجا بزار
BOT_TOKEN = "BOT_TOKEN"
BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
s = requests.Session()

GIFTS = {
    "5170145012310081615": {"emoji": "💝", "price": 15},
    "5170233102089322756": {"emoji": "🧸", "price": 15},
    "5170250947678437525": {"emoji": "🎁", "price": 25},
    "5168103777563050263": {"emoji": "🌹", "price": 25},
    "5170144170496491616": {"emoji": "🎂", "price": 50},
    "5170314324215857265": {"emoji": "💐", "price": 50},
    "5170564780938756245": {"emoji": "🚀", "price": 50},
    "6028601630662853006": {"emoji": "🍾", "price": 50},
    "5168043875654172773": {"emoji": "🏆", "price": 100},
    "5170690322832818290": {"emoji": "💍", "price": 100},
    "5170521118301225164": {"emoji": "💎", "price": 100},
}

PENDING_PAYMENTS = {}

def api(method, **data):
    try:
        r = s.post(f"{BASE}/{method}", data=data, timeout=25)
        result = r.json()
        print("API:", method, result)
        return result
    except Exception as e:
        print("API Error:", e)
        return {}

def send_gift(user_id, gift_id):
    r = s.post(f"{BASE}/sendGift", json={
        "user_id": user_id,
        "gift_id": gift_id
    }, timeout=10)
    print("Gift result:", r.text)

print("Bot started...")

offset = 0

while True:
    updates = api("getUpdates", offset=offset, timeout=30)

    if not updates.get("ok"):
        time.sleep(1)
        continue

    for u in updates["result"]:
        offset = u["update_id"] + 1

        # ================= START =================
        if "message" in u and "text" in u["message"]:
            msg = u["message"]
            chat_id = msg["chat"]["id"]

            if msg["text"] == "/start":
                buttons = []
                for gid, info in GIFTS.items():
                    buttons.append([{
                        "text": f"{info['emoji']} - {info['price']} ⭐",
                        "callback_data": gid
                    }])

                api("sendMessage",
                    chat_id=chat_id,
                    text="🎁 یکی از گیفت‌ها رو انتخاب کن:",
                    reply_markup=json.dumps({"inline_keyboard": buttons})
                )

        # ================= انتخاب گیفت =================
        if "callback_query" in u:
            cq = u["callback_query"]
            gift_id = cq["data"]
            chat_id = cq["from"]["id"]

            # پاسخ به کلیک (خیلی مهم)
            api("answerCallbackQuery",
                callback_query_id=cq["id"],
                text="در حال ساخت فاکتور..."
            )

            if gift_id in GIFTS:
                price = GIFTS[gift_id]["price"]
                payload = "pay_" + uuid.uuid4().hex

                PENDING_PAYMENTS[payload] = {
                    "user_id": chat_id,
                    "gift_id": gift_id
                }

                prices = json.dumps([{
                    "label": "Stars",
                    "amount": price
                }])

                res = api("sendInvoice",
                    chat_id=chat_id,
                    title="پرداخت استار",
                    description=f"پرداخت {price} استار برای گیفت",
                    payload=payload,
                    provider_token="",
                    currency="XTR",
                    prices=prices
                )

                if not res.get("ok"):
                    api("sendMessage",
                        chat_id=chat_id,
                        text="❌ خطا در ساخت فاکتور:\n" + str(res)
                    )

        # ================= تایید پرداخت =================
        if "pre_checkout_query" in u:
            q = u["pre_checkout_query"]
            api("answerPreCheckoutQuery",
                pre_checkout_query_id=q["id"],
                ok=True
            )

        # ================= پرداخت موفق =================
        if "message" in u and "successful_payment" in u["message"]:
            msg = u["message"]
            payment = msg["successful_payment"]
            payload = payment["invoice_payload"]

            if payload in PENDING_PAYMENTS:
                data = PENDING_PAYMENTS[payload]
                send_gift(data["user_id"], data["gift_id"])

                api("sendMessage",
                    chat_id=data["user_id"],
                    text="✅ پرداخت انجام شد، گیفت ارسال شد 🎁"
                )

                del PENDING_PAYMENTS[payload]
