from typing import Optional, List

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

    def chat_flow(self, user_input: str, context_docs: Optional[List[Document]] = None):
        # Nếu có context_docs thì dùng, không thì dùng retriever
        if context_docs is not None:
            context_text = "\n\n".join([doc.page_content for doc in context_docs])
        elif self.retriever:
            retrieved = self.retriever.invoke(user_input)
            context_text = "\n\n".join([doc.page_content for doc in retrieved])
        else:
            context_text = ""

        prompt = ChatPromptTemplate.from_template(
            PROMPT_VI if _is_vietnamese(user_input) else PROMPT_EN
        )
        rag_chain = (
            {
                "context": RunnableLambda(lambda _: context_text),
                "history": RunnableLambda(lambda _: ""),
                "user_input": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return rag_chain.invoke(user_input)