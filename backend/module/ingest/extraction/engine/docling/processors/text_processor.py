# app/utils/document_engine/processors/text_processor.py
import unicodedata

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Chuyển đổi mã Unicode từ NFD sang NFC (Chuẩn tiếng Việt)
    return unicodedata.normalize("NFC", text).strip()