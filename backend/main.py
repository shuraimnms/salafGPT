from fastapi import FastAPI, HTTPException

from backend.guard.salaf_guard import (
    detect_language,
    refusal_message,
    should_refuse_output,
)
from backend.llm.openrouter import OpenRouterClient
from backend.schemas import ChatRequest, ChatResponse
from backend.utils import load_system_prompt

app = FastAPI(title="Salaf GPT")
client = OpenRouterClient()
BASE_PROMPT = load_system_prompt()


def build_language_directive(language: str, allow_arabic: bool) -> str:
    if language == "urdu":
        return "جواب صرف اردو میں دیں۔ عربی استعمال نہ کریں جب تک واضح طور پر نہ کہا جائے۔"
    if language == "roman_urdu":
        return "Jawab sirf Roman Urdu mein dein. Arabic use na karein jab tak wazeh tor par na kaha jaye."
    if language == "arabic":
        if allow_arabic:
            return "أجب باللغة العربية فقط كما طلب المستخدم."
        return "لا تستخدم العربية إلا إذا طُلب ذلك صراحة."
    return "Reply only in English. Do not use Arabic unless explicitly requested."


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    decision = detect_language(request.message)
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    system_prompt = f"{BASE_PROMPT}\n\nLanguage directive: {build_language_directive(decision.language, decision.allow_arabic)}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message.strip()},
    ]

    llm_response = await client.chat(messages)
    if llm_response.error:
        return ChatResponse(reply=refusal_message(decision.language))

    reply = (llm_response.content or "").strip()
    refuse, _reason = should_refuse_output(reply, decision.allow_arabic)
    if refuse or not reply:
        return ChatResponse(reply=refusal_message(decision.language))

    return ChatResponse(reply=reply)
