import asyncio
import datetime
import logging
import threading
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- НАЛАШТУВАННЯ ---
TELEGRAM_BOT_TOKEN = "8839088733:AAEaYe_0_dN0iMYrSy6Sncvd7PxMHQOwX20"
TELEGRAM_CHAT_ID = "395198925"
CHECK_INTERVAL_SECONDS = 600  # 10 хвилин

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Фейковий веб-сервер для вимог Render Free Web Service
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Privat24 Bond Bot is Running!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHTTPRequestHandler)
    server.serve_forever()


def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Помилка відправки в Telegram: {e}")


def get_target_months():
    today = datetime.date.today()
    first_target_month = today.month % 12 + 1
    first_target_year = today.year + (1 if today.month == 12 else 0)
    second_target_month = first_target_month % 12 + 1
    second_target_year = first_target_year + (1 if first_target_month == 12 else 0)
    return [
        (first_target_year, first_target_month),
        (second_target_year, second_target_month)
    ]


def check_bonds():
    target_months = get_target_months()
    logging.info(f"Шукаємо облігації з датами: {target_months}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get("https://next.privat24.ua/bonds/list", headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()

        found_bonds = []
        for year, month in target_months:
            date_str = f"{month:02d}.{year}"
            if date_str in page_text:
                found_bonds.append(f"Знайдено облігацію з датою погашення: <b>{date_str}</b>")

        if found_bonds:
            msg = "🔔 <b>Знайдено необхідні ОВДП в Privat24!</b>\n\n" + "\n".join(found_bonds)
            send_telegram_message(msg)
        else:
            logging.info("Потрібних облігацій не знайдено.")

    except Exception as e:
        logging.error(f"Помилка під час парсингу: {e}")


async def bot_loop():
    logging.info("Бот запущений і перевіряє ОВДП кожні 10 хвилин...")
    while True:
        check_bonds()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    asyncio.run(bot_loop())
