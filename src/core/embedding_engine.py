import warnings

from config import config

warnings.filterwarnings(
    'ignore',
    message=r'`resume_download` is deprecated.*',
    category=FutureWarning,
    module=r'huggingface_hub\.file_download',
)


class EmbeddingEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.embeddings = None
        self._initialized = True

    def _load(self):
        if self.embeddings is None:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL,
                model_kwargs={
                    'device': 'cpu',
                    'local_files_only': config.MODEL_LOCAL_FILES_ONLY,
                },
                encode_kwargs={'normalize_embeddings': True},
            )
        return self.embeddings

    def get_embeddings(self):
        return self._load()

    def embed_query(self, text: str):
        return self._load().embed_query(text)

    def embed_documents(self, texts: list):
        return self._load().embed_documents(texts)
