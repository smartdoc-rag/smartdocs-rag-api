from pprint import pprint
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.retrievers import BaseRetriever
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import DistanceStrategy


class FileIngestionService:
    def faiss_ingest(
        self, documents: list[Document], embedding: HuggingFaceEmbeddings
    ) -> FAISS:
        vectorstore = FAISS.from_documents(
            documents=self.text_splitter(documents),
            embedding=embedding,
            distance_strategy=DistanceStrategy.COSINE,
        )
        return vectorstore

    def text_splitter(
        self, documents: list[Document], chunks: int = 1500, chunk_overlap: int = 200
    ) -> list[Document]:
        MARKDOWN_SEPARATORS = [
            "\n#{1,6}",  # Headings
            "```\n",  # Code blocks
            "\n\\*\\*\\*+\n",  # Horizontal rules
            "\n---+\n",  # Horizontal rules
            "\n\n",  # Paragraphs
            " ",
            "",
        ]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunks,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            strip_whitespace=True,
            separators=MARKDOWN_SEPARATORS,
        )
        return text_splitter.split_documents(documents)

    def get_retriever(
        self, vectorstore: FAISS, top_k: int = 3, fetch_k: int = 20
    ) -> BaseRetriever:
        return vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": top_k, "fetch_k": fetch_k}
        )
