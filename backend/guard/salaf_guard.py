import re
from dataclasses import dataclass
from typing import Tuple


ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
URDU_CHAR_RE = re.compile(r"[ٹڈڑںےھ]")
ROMAN_URDU_HINTS = {
    "hai",
    "nahi",
    "kya",
    "kyun",
    "kyu",
    "ka",
    "ke",
    "ki",
    "mein",
    "mera",
    "meri",
    "ap",
    "aap",
    "bhai",
    "salaam",
    "salam",
    "namaz",
}
QURAN_MENTION_RE = re.compile(r"qur['’]?an|quran|koran", re.IGNORECASE)


@dataclass(frozen=True)
class LanguageDecision:
    language: str
    allow_arabic: bool


def detect_language(message: str) -> LanguageDecision:
    normalized = message.strip()
    if not normalized:
        return LanguageDecision(language="english", allow_arabic=False)

    contains_arabic = bool(ARABIC_CHAR_RE.search(normalized))
    if contains_arabic:
        if URDU_CHAR_RE.search(normalized):
            return LanguageDecision(language="urdu", allow_arabic=True)
        if re.search(r"\b(arabic|عربي|العربية)\b", normalized, re.IGNORECASE):
            return LanguageDecision(language="arabic", allow_arabic=True)
        return LanguageDecision(language="english", allow_arabic=False)

    tokens = re.findall(r"[a-zA-Z']+", normalized.lower())
    roman_hits = sum(1 for token in tokens if token in ROMAN_URDU_HINTS)
    if roman_hits >= 2:
        return LanguageDecision(language="roman_urdu", allow_arabic=False)

    return LanguageDecision(language="english", allow_arabic=False)


def refusal_message(language: str) -> str:
    if language == "urdu":
        return (
            "معذرت، میں اس سوال کا محفوظ اور مستند جواب فراہم نہیں کر سکتا۔ "
            "براہ کرم سوال واضح کریں یا مستند حوالہ فراہم کریں۔"
        )
    if language == "roman_urdu":
        return (
            "Maaf kijiye, main is sawal ka mehfooz aur mustanad jawab nahin de sakta. "
            "Barah-e-karam sawal wazeh karein ya mustanad hawala dein."
        )
    if language == "arabic":
        return (
            "عذرًا، لا أستطيع تقديم إجابة موثوقة وآمنة لهذا السؤال. "
            "يرجى توضيح السؤال أو تقديم مصدر موثوق."
        )
    return (
        "Sorry, I cannot provide a safe and verified answer to this question. "
        "Please clarify the question or provide a reliable reference."
    )


def should_refuse_output(reply: str, allow_arabic: bool) -> Tuple[bool, str]:
    arabic_chars = ARABIC_CHAR_RE.findall(reply)
    total_chars = max(len(reply), 1)
    arabic_ratio = len(arabic_chars) / total_chars
    if arabic_ratio > 0.25 or len(arabic_chars) > 120:
        if not allow_arabic:
            return True, "Excessive Arabic content"

    quran_mentions = len(QURAN_MENTION_RE.findall(reply))
    if quran_mentions > 3:
        return True, "Excessive Quran mentions"

    return False, ""
