from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, json

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# 1. ВСТАВЬ СВОЙ КЛЮЧ OPENROUTER:
API_KEY = "sk-or-v1-ЗДЕСЬ_ТВОЙ_КЛЮЧ"

# 2. ВСТАВЬ СВОЙ КОНТАКТ:
MY_CONTACT = "Telegram: @shumilov_andrey | WhatsApp: +79990000000"

SYSTEM_PROMPT = f"""Ты ассистент SpeedAI. Основатель: Андрей.
Задача: отвечать об услугах (ИИ-боты, автоматизация, таблицы), выявлять потребность, вести к решению.
Правила:
1. Кратко, по-деловому.
2. Не называй цену сразу → спроси: "Какую задачу хотите решить?".
3. При завершении диалога выведи СТРОГО JSON: {{"handoff": true, "message": "Готов передать контакт."}}
4. Не выдумывай факты. Если не знаешь → предложи связаться с Андреем.
Контакт: {MY_CONTACT}
"""

@app.post("/chat")
async def chat(req: dict):
    messages = req.get("messages", [])
    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "temperature": 0.3
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://speedai-site.web.app/",
        "X-Title": "SpeedAI Chat"
    }
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        try:
            if text.strip().startswith("{"):
                data = json.loads(text.strip())
                if data.get("handoff"):
                    return {"text": data["message"], "handoff": True, "contacts": f"✅ {MY_CONTACT}"}
        except: pass
        return {"text": text, "handoff": False}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/")
def root(): return {"status": "SpeedAI Bot is running 🚀"}