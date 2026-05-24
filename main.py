# main.py — YandexGPT версия (API-Key)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os

app = FastAPI()

# 🔥 CORS: разрешаем запросы с твоего сайта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://speedai-site.web.app", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# 🔑 Яндекс.Облако данные (из переменных окружения)
YC_API_KEY = os.getenv("YC_API_KEY", "")  # ← API-ключ (начинается на AQVN...)
YC_FOLDER_ID = os.getenv(" folder ID", "")  # ← Folder ID (начинается на b1g...)

if not YC_API_KEY or not YC_FOLDER_ID:
    raise RuntimeError("❌ YC_API_KEY или YC_FOLDER_ID не заданы в переменных окружения Render")

MY_CONTACT = "Telegram: https://t.me/FBK_MiniBusiness | VK: https://vk.ru/depnefef2323"

SYSTEM_PROMPT = f"""Ты ассистент компании SpeedAI. Основатель: Андрей.
Задача: отвечать об услугах (автоматизация, ИИ-боты, таблицы), выявлять потребность, вести к решению.
Правила:
1. Кратко, по-деловому, без воды.
2. Не называй цену сразу → спроси: "Какую задачу хотите решить?".
3. При завершении диалога выведи СТРОГО JSON: {{"handoff": true, "message": "Готов передать контакт."}}
4. Не выдумывай факты. Если не знаешь → предложи связаться с Андреем.
Контакт: {MY_CONTACT}
"""

# 🔗 Эндпоинт YandexGPT
YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

@app.post("/chat")
async def chat(req: dict):
    try:
        messages = req.get("messages", [])
        
        # Формируем промпт для YandexGPT (он любит простой текст)
        full_text = SYSTEM_PROMPT + "\n\nДиалог:\n"
        for msg in messages:
            role = "Пользователь" if msg["role"] == "user" else "Ассистент"
            full_text += f"{role}: {msg['content']}\n"
        full_text += "Ассистент:"
        
        # Запрос к YandexGPT
        payload = {
            "modelUri": f"gpt://{YC_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 800
            },
            "messages": [{"role": "user", "text": full_text}]
        }
        headers = {
            "Content-Type": "application/json",
            # 🔥 ВАЖНО: для API-ключа префикс "Api-Key", а не "Bearer"
            "Authorization": f"Api-Key {YC_API_KEY}"
        }
        
        print(f"🌐 Sending to YandexGPT...")
        r = requests.post(YANDEX_URL, json=payload, headers=headers, timeout=30)
        
        print(f"📡 YandexGPT response: {r.status_code} - {r.text[:200]}")
        
        if r.status_code != 200:
            if r.status_code == 401:
                print("❌ 401: Неверный API-ключ!")
            elif r.status_code == 403:
                print("❌ 403: Нет прав у сервисного аккаунта!")
            elif r.status_code == 400:
                print(f"❌ 400: Ошибка запроса: {r.text[:100]}")
            raise HTTPException(r.status_code, f"Ошибка YandexGPT: {r.text[:100]}")
        
        data = r.json()
        text = data["result"]["alternatives"][0]["message"]["text"]
        
        # Парсим handoff
        try:
            if text.strip().startswith("{"):
                parsed = json.loads(text.strip())
                if parsed.get("handoff"):
                    return {"text": parsed["message"], "handoff": True, "contacts": f"✅ {MY_CONTACT}"}
        except Exception as e:
            print(f"⚠️ Handoff parse error: {e}")
            pass
            
        return {"text": text, "handoff": False}
        
    except requests.exceptions.Timeout:
        raise HTTPException(504, "Таймаут: ИИ долго думает. Попробуйте ещё раз.")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Внутренняя ошибка: {str(e)[:100]}")

@app.get("/")
def root():
    return {"status": "SpeedAI Bot is running 🚀"}

@app.options("/chat")
async def options_chat():
    return {"status": "ok"}