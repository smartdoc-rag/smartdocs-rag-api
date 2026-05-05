from typing import Optional, List, Tuple

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from src.core.rag.llm_model import LLMModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever

from src.core.rag.prompt import PROMPT_VI, PROMPT_EN
from src.core.rag.prompt import _is_vietnamese


class RAGService:
    def __init__(self, vectorStoreRetriever: Optional[BaseRetriever] = None):
        self.llm = LLMModel().get_ollama()
        self.retriever = vectorStoreRetriever

    def chat_flow(
        self,
        user_input: str,
        context_docs: Optional[List[Document]] = None,
        chat_history: Optional[List[Tuple[str, str]]] = None,
    ):
        # Context đưa cho LLM — kèm metadata (file_name, page) để LLM biết nguồn
        if context_docs is not None:
            context_parts = []
            for doc in context_docs:
                meta = doc.metadata or {}
                source = meta.get("file_name", meta.get("source", ""))
                page = meta.get("page", meta.get("page_label", ""))
                header = ""
                if source:
                    header += f"[Tài liệu: {source}"
                if page:
                    header += f" | Trang: {page}" if header else f"[Trang: {page}"
                if header:
                    header += "]\n"
                context_parts.append(f"{header}{doc.page_content}")
            context_text = "\n\n".join(context_parts)
        elif self.retriever:
            retrieved = self.retriever.invoke(user_input)
            context_text = "\n\n".join([doc.page_content for doc in retrieved])
        else:
            context_text = ""

        # Xử lý lịch sử hội thoại (chỉ lấy 5 cặp gần nhất)
        history_text = ""
        if chat_history:
            for user_msg, assistant_msg in chat_history[-5:]:
                history_text += f"Người dùng: {user_msg}\nTrợ lý: {assistant_msg}\n"

        prompt = ChatPromptTemplate.from_template(
            PROMPT_VI if _is_vietnamese(user_input) else PROMPT_EN
        )
        rag_chain = (
            {
                "context": RunnableLambda(lambda _: context_text),
                "history": RunnableLambda(lambda _: history_text),
                "user_input": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return rag_chain.invoke(user_input)

    def rewrite_query(
        self, original_query: str, chat_history: List[Tuple[str, str]] = None
    ) -> str:
        if not chat_history:
            return original_query
        history_text = "\n".join(
            [f"Người dùng: {u}\nTrợ lý: {a}" for u, a in chat_history[-3:]]
        )
        prompt = f"""Viết lại câu hỏi sau thành một câu hỏi độc lập, rõ ràng, bao gồm đầy đủ ngữ cảnh từ lịch sử hội thoại. Chỉ trả về câu hỏi đã viết lại, không giải thích.

    Lịch sử:
    {history_text}

    Câu hỏi gốc: {original_query}

    Câu hỏi viết lại:"""
        return self.llm.invoke(prompt)

    def evaluate_answer(self, question: str, answer: str, context: str) -> dict:
        prompt = f"""Đánh giá câu trả lời dựa trên ngữ cảnh. Trả về JSON:
    {{
        "confidence": 0-100,
        "is_relevant": true/false,
        "missing_info": "nội dung còn thiếu hoặc null"
    }}

    Câu hỏi: {question}
    Ngữ cảnh: {context}
    Câu trả lời: {answer}

    Đánh giá:"""
        response = self.llm.invoke(prompt)
        try:
            import json

            return json.loads(response)
        except:
            return {"confidence": 50, "is_relevant": True, "missing_info": None}

    def needs_more_info(self, question: str, answer: str, confidence: int) -> bool:
        return confidence < 60  # ngưỡng thấp
