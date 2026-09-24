import asyncio
import datetime
import logging
import requests
from playwright.async_api import async_playwright

# --- НАЛАШТУВАННЯ ---
TELEGRAM_BOT_TOKEN = "8839088733:AAEaYe_0_dN0iMYrSy6Sncvd7PxMHQOwX20"
TELEGRAM_CHAT_ID = "395198925"
CHECK_INTERVAL_SECONDS = 600  # 10 хвилин

# Налаштування логування
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def send_telegram_message(text: str):
    """Надсилає сповіщення у Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Помилка відправки в Telegram: {e}")


def get_target_months():
    """Визначає наступні два календарні місяці"""
    today = datetime.date.today()
    
    # Наступний місяць
    first_target_month = today.month % 12 + 1
    first_target_year = today.year + (1 if today.month == 12 else 0)
    
    # Другий місяць
    second_target_month = first_target_month % 12 + 1
    second_target_year = first_target_year + (1 if first_target_month == 12 else 0)
    
    return [
        (first_target_year, first_target_month),
        (second_target_year, second_target_month)
    ]


async def check_bonds():
    """Перевірка наявності облігацій на сторінці Privat24"""
    target_months = get_target_months()
    logging.info(f"Шукаємо облігації, що погашаються у місяцях: {target_months}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Перехід на сторінку
            await page.goto("https://next.privat24.ua/bonds/list", timeout=60000)
            await page.wait_for_timeout(5000)  # Чекаємо завантаження динамічного контенту

            page_content = await page.content()
            found_bonds = []

            for year, month in target_months:
                # Форматуємо місяць/рік для пошуку (наприклад, 10.2026 або 11.2026)
                date_str = f"{month:02d}.{year}"
                if date_str in page_content:
                    found_bonds.append(f"Знайдено облігацію з датою погашення: <b>{date_str}</b>")

            if found_bonds:
                msg = "🔔 <b>Знайдено необхідні ОВДП в Privat24!</b>\n\n" + "\n".join(found_bonds)
                logging.info("Знайдено потрібні облігації! Надсилаємо сповіщення...")
                send_telegram_message(msg)
            else:
                logging.info("Потрібних облігацій не знайдено.")

        except Exception as e:
            logging.error(f"Помилка під час парсингу: {e}")
        finally:
            await browser.close()


async def main():
    logging.info("Бот запущений і перевіряє ОВДП кожні 10 хвилин...")
    while True:
        await check_bonds()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
