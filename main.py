# main.py — YandexGPT (Максимально просто, только текст)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, os

app = FastAPI()

# 🔥 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://speedai-site.web.app", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# 🔑 Ключи из переменных Render
YC_API_KEY = os.getenv("YC_API_KEY", "")
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")

# 📞 Контакт (просто текст)
MY_CONTACT = "Telegram: @FBK_MiniBusiness | Телефон: +7 904 958 42 82"

SYSTEM_PROMPT = f"""Ты ассистент компании SpeedAI. Основатель: Андрей.
Задача: отвечать об услугах (автоматизация, ИИ-боты, таблицы), выявлять потребность, вести к решению.
Правила:
1. Кратко, по-деловому, без воды.
2. Не называй цену сразу → спроси: "Какую задачу хотите решить?".
3. 3. Если пользователь готов к контакту — в конце ответа напиши: "Напишите в Telegram [https://t.me/FBK_MiniBusiness] или в ВК [https://vk.com/depnefef2323] — Андрей ответит лично."
4. Не выдумывай факты. Если не знаешь → предложи связаться с Андреем.
5. Пиши ОТВЕТЫ ОБЫЧНЫМ ТЕКСТОМ. Никакого JSON, кода, кавычек или специальных символов.
"""

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

@app.post("/chat")
async def chat(req: dict):
    if not YC_API_KEY or not YC_FOLDER_ID:
        raise HTTPException(500, "⚙️ Сервер работает, но ключи Yandex не найдены.")

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
            "Authorization": f"Api-Key {YC_API_KEY}"
        }
        
        r = requests.post(YANDEX_URL, json=payload, headers=headers, timeout=30)
        
        if r.status_code != 200:
            raise HTTPException(r.status_code, f"YandexGPT error: {r.text[:100]}")
        
        data = r.json()
        text = data["result"]["alternatives"][0]["message"]["text"]
        
        # 🔥 Просто возвращаем текст — ВСЕГДА
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