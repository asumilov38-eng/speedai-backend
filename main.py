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
        messages = req.get("messages", [])
        
        payload = {
            "model": "meta-llama/llama-3-8b-instruct:free",
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
        
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if r.status_code != 200:
            print(f"❌ OpenRouter error: {r.status_code} - {r.text}")
            raise HTTPException(502, f"Ошибка ИИ: {r.status_code}")
        
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        
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
        raise HTTPException(504, "Таймаут: ИИ долго думает. Попробуйте ещё раз.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        raise HTTPException(502, f"Ошибка соединения с ИИ: {str(e)}")
    except Exception as e:
        print(f"❌ Internal error: {e}")
        raise HTTPException(500, f"Внутренняя ошибка: {str(e)}")

@app.get("/")
def root():
    return {"status": "SpeedAI Bot is running 🚀"}

# 🔥 Обработка OPTIONS для CORS preflight
@app.options("/chat")
async def options_chat():
    return {"status": "ok"}