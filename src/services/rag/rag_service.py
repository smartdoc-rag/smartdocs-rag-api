from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from src.core.rag.llm_model import LLMModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever

from src.core.rag.prompt import PROMPT_VI, PROMPT_EN
from src.core.rag.prompt import _is_vietnamese


class RAGService:
    def __init__(self, vectorStoreRetriever: BaseRetriever):
        self.llm = LLMModel().get_ollama()
        self.retriever = vectorStoreRetriever

    def chat_flow(self, user_input: str):
        prompt = ChatPromptTemplate.from_template(
            PROMPT_VI if _is_vietnamese(user_input) else PROMPT_EN
        )
        print("--- Đang suy nghĩ ---")

        rag_chain = (
            {
                "context": self.retriever,
                "history": RunnableLambda(lambda _: ""),
                "user_input": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain.invoke(user_input)
