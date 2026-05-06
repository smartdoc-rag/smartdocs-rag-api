from sentence_transformers import CrossEncoder
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self):
        if self._model is None:
            model_name = getattr(settings, 'CROSS_ENCODER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
            try:
                self._model = CrossEncoder(model_name)
                logger.info(f"Loaded cross-encoder model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load cross-encoder: {e}")
                self._model = None
        return self._model

    def rerank(self, query: str, documents: list, top_k: int = 5, keep_scores: bool = True):
        """
        Re-rank documents using cross-encoder.
        Returns top_k documents sorted by relevance.
        """
        model = self.get_model()
        if not model or not documents:
            return documents[:top_k]

        # Tạo pairs (query, doc_text)
        pairs = [(query, doc.page_content) for doc in documents]
        # Dự đoán scores (thường là similarity, càng cao càng tốt)
        scores = model.predict(pairs)

        # Gắn score vào metadata và sắp xếp
        for doc, score in zip(documents, scores):
            doc.metadata['cross_encoder_score'] = float(score)

        sorted_docs = sorted(documents, key=lambda d: d.metadata.get('cross_encoder_score', 0), reverse=True)
        return sorted_docs[:top_k]