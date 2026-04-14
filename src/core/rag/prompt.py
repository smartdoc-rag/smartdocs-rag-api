VIETNAMESE_CHARS = set(
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
)


def _is_vietnamese(text: str) -> bool:
    return any(char in VIETNAMESE_CHARS for char in text.lower())


PROMPT_VI = """Sử dụng ngữ cảnh sau để trả lời câu hỏi.
Nếu bạn không biết, hãy nói là bạn không biết.
Trả lời ngắn gọn (3-4 câu), BẮT BUỘC bằng tiếng Việt.

Lịch sử hội thoại:
{history}

Ngữ cảnh:
{context}

Câu hỏi: {user_input}
Trả lời:
"""

PROMPT_EN = """Use the following context to answer the question.
If you don't know the answer, just say you don't know.
Keep the answer concise (3-4 sentences).

Conversation history:
{history}

Context:
{context}

Question: {user_input}
Answer:
"""
