# main.py — ПОЛНЫЙ ГОТОВЫЙ КОД (скопируй и замени весь файл)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os  # ← os добавлен сюда

app = FastAPI()

# 🔥 CORS: разрешаем запросы с твоего сайта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://speedai-site.web.app", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# 🔑 API-ключ из переменной окружения (безопасно!)
API_KEY = os.getenv("OPENROUTER_KEY", "")
if not API_KEY:
    raise RuntimeError("❌ OPENROUTER_KEY не задан в переменных окружения Render")

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

@app.post("/chat")
async def chat(req: dict):
    try:
        print(f"🔑 API_KEY starts with: {API_KEY[:10] if API_KEY else 'EMPTY'}...")  # Лог ключа
        print(f"📦 Request: {req.get('messages', [])[-1].get('content', '')[:50]}...")  # Лог запроса
        
        messages = req.get("messages", [])
        
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "temperature": 0.3,
            "max_tokens": 800
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://speedai-site.web.app/",
            "X-Title": "SpeedAI Chat"
        }
        
        print(f"🌐 Sending to OpenRouter...")
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📡 OpenRouter response: {r.status_code} - {r.text[:200]}")  # Лог ответа
        
        if r.status_code != 200:
            if r.status_code == 401:
                print("❌ 401: Неверный API-ключ!")
            elif r.status_code == 429:
                print("❌ 429: Лимит запросов исчерпан!")
            elif r.status_code == 404:
                print("❌ 404: Модель не найдена!")
            raise HTTPException(r.status_code, f"OpenRouter error: {r.text[:100]}")
        
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        
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
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Internal error: {str(e)[:100]}")

@app.get("/")
def root():
    return {"status": "SpeedAI Bot is running 🚀"}

# 🔥 Обработка OPTIONS для CORS preflight
@app.options("/chat")
async def options_chat():
    return {"status": "ok"}