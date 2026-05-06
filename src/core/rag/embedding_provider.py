import threading
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

_lock = threading.Lock()
_embedding = None


def get_embedding() -> HuggingFaceEmbeddings:
    global _embedding
    if _embedding is None:  # Nếu instance = None
        with _lock:
            if _embedding is None:  # Nếu chưa có instance = None sau khi đã gỡ khóa
                _embedding = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                    model_kwargs={"device": "cpu", "token": settings.HF_TOKEN},
                    encode_kwargs={"normalize_embeddings": False},
                    multi_process=True,
                    show_progress=True,
                )
    return _embedding
