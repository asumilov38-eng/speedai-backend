# main.py — YandexGPT (Чистый код, ключи только в Render)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os

app = FastAPI()

# 🔥 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://speedai-site.web.app", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# 🔑 Читаем переменные (НЕ ломаем запуск, если их нет)
YC_API_KEY = os.getenv("YC_API_KEY", "")
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")

MY_CONTACT = "Telegram: @shumilov_andrey | WhatsApp: +79990000000"

SYSTEM_PROMPT = f"""Ты ассистент компании SpeedAI. Основатель: Андрей.
Задача: отвечать об услугах (автоматизация, ИИ-боты, таблицы), выявлять потребность, вести к решению.
Правила:
1. Кратко, по-деловому, без воды.
2. Не называй цену сразу → спроси: "Какую задачу хотите решить?".
3. При завершении диалога выведи СТРОГО JSON: {{"handoff": true, "message": "Готов передать контакт."}}
4. Не выдумывай факты. Если не знаешь → предложи связаться с Андреем.
Контакт: {MY_CONTACT}
"""

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

@app.post("/chat")
async def chat(req: dict):
    # 🔍 ПРОВЕРКА КЛЮЧЕЙ ПРЯМО ЗДЕСЬ (чтобы не блокировать запуск сервера)
    if not YC_API_KEY or not YC_FOLDER_ID:
        raise HTTPException(500, "⚙️ Сервер работает, но ключи Yandex не найдены. Проверь переменные в Render.")

    try:
        messages = req.get("messages", [])
        
        # Формируем промпт
        full_text = SYSTEM_PROMPT + "\n\nДиалог:\n"
        for msg in messages:
            role = "Пользователь" if msg["role"] == "user" else "Ассистент"
            full_text += f"{role}: {msg['content']}\n"
        full_text += "Ассистент:"
        
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
            "Authorization": f"Api-Key {YC_API_KEY}"  # 🔥 Api-Key, не Bearer!
        }
        
        print(f"🌐 Sending to YandexGPT...")
        r = requests.post(YANDEX_URL, json=payload, headers=headers, timeout=30)
        print(f"📡 YandexGPT response: {r.status_code} - {r.text[:200]}")
        
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"YandexGPT error: {r.text[:100]}")
        
        data = r.json()
        result = data.get("result", {})
        alternatives = result.get("alternatives", [])
        
        if not alternatives:
            raise HTTPException(500, "Пустой ответ от ИИ")
            
        text = alternatives[0].get("message", {}).get("text", "")
        if not text:
            raise HTTPException(500, "Нет текста в ответе ИИ")
        
        # Парсим handoff
        try:
            if text.strip().startswith("{"):
                parsed = json.loads(text.strip())
                if parsed.get("handoff"):
                    return {"text": parsed["message"], "handoff": True, "contacts": f"✅ {MY_CONTACT}"}
        except:
            pass
            
        return {"text": text, "handoff": False}
        
    except requests.exceptions.Timeout:
        raise HTTPException(504, "Таймаут: ИИ долго думает.")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(500, f"Error: {str(e)[:100]}")

@app.get("/")
def root():
    return {"status": "SpeedAI Bot is running 🚀"}

@app.options("/chat")
async def options_chat():
    return {"status": "ok"}