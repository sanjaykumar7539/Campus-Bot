import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


class Config:
    BASE_DIR = str(ROOT_DIR)
    DATA_DIR = str(Path(os.getenv('DATA_DIR', ROOT_DIR / 'data')).resolve())
    VECTOR_DB_PATH = str(Path(os.getenv('VECTOR_DB_PATH', ROOT_DIR / 'vector_db')).resolve())
    MODEL_PATH = str(Path(os.getenv('SLM_MODEL_PATH', ROOT_DIR / 'models/phi3-mini')).resolve())
    EMBEDDING_MODEL = os.getenv(
        'EMBEDDING_MODEL',
        'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    )
    # Runtime inference must use the models downloaded during setup. This avoids
    # Hugging Face network checks/retries delaying the first student question.
    MODEL_LOCAL_FILES_ONLY = _bool('MODEL_LOCAL_FILES_ONLY', True)
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 500))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))
    TOP_K = int(os.getenv('TOP_K_RETRIEVAL', 3))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.55))
    ENABLE_HYBRID_SEARCH = _bool('ENABLE_HYBRID_SEARCH', True)
    VECTOR_WEIGHT = float(os.getenv('VECTOR_WEIGHT', 0.70))
    KEYWORD_WEIGHT = float(os.getenv('KEYWORD_WEIGHT', 0.30))
    HYBRID_CANDIDATE_K = int(os.getenv('HYBRID_CANDIDATE_K', 12))
    HYBRID_THRESHOLD = float(os.getenv('HYBRID_THRESHOLD', 0.45))
    ENABLE_RERANKER = _bool('ENABLE_RERANKER', True)
    RERANKER_MODEL = os.getenv('RERANKER_MODEL', 'BAAI/bge-reranker-base')
    RERANKER_CANDIDATE_K = int(os.getenv('RERANKER_CANDIDATE_K', 12))
    RERANKER_WEIGHT = float(os.getenv('RERANKER_WEIGHT', 0.70))
    ENABLE_LANGGRAPH = _bool('ENABLE_LANGGRAPH', True)
    LETTUCEDETECT_ENABLED = _bool('LETTUCEDETECT_ENABLED', True)
    LETTUCEDETECT_MODEL = os.getenv('LETTUCEDETECT_MODEL', 'KRLabsOrg/lettucedect-base-modernbert-en-v1')
    LETTUCEDETECT_MIN_CONFIDENCE = float(os.getenv('LETTUCEDETECT_MIN_CONFIDENCE', 0.80))
    VECTOR_BACKEND = os.getenv('VECTOR_BACKEND', 'chroma').lower()
    PGVECTOR_URL = os.getenv('PGVECTOR_URL', '').strip()
    PGVECTOR_COLLECTION = os.getenv('PGVECTOR_COLLECTION', 'campusmind_knowledge')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{ROOT_DIR / 'college_chatbot.db'}")
    # Product identity and tenant/institute identity are intentionally separate.
    PRODUCT_NAME = os.getenv('PRODUCT_NAME', 'CampusMind AI')
    PRODUCT_VERSION = os.getenv('PRODUCT_VERSION', '2.0.0')
    PRODUCT_EDITION = os.getenv('PRODUCT_EDITION', 'Institutional')
    APP_ENV = os.getenv('APP_ENV', 'development')
    SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', '')
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '').strip()
    INSTITUTE_NAME = os.getenv('INSTITUTE_NAME', 'EGS Pillay Engineering College')
    INSTITUTE_SHORT_NAME = os.getenv('INSTITUTE_SHORT_NAME', 'EGSPEC')
    STRICT_MODE = _bool('STRICT_MODE', True)
    CORS_ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', '').split(',') if x.strip()]
    AUTO_OPEN_BROWSER = _bool('AUTO_OPEN_BROWSER', True)
    REQUEST_TIMEOUT_SECONDS = int(os.getenv('REQUEST_TIMEOUT_SECONDS', 20))

    # Secure network-resilience layer for institute source synchronization.
    # CampusMind can answer from the local knowledge base even when these sources
    # are temporarily unreachable. Network settings affect synchronization only.
    NETWORK_MODE = os.getenv('NETWORK_MODE', 'auto').strip().lower()
    NETWORK_CONNECT_TIMEOUT = float(os.getenv('NETWORK_CONNECT_TIMEOUT', 10))
    NETWORK_READ_TIMEOUT = float(os.getenv('NETWORK_READ_TIMEOUT', REQUEST_TIMEOUT_SECONDS))
    NETWORK_MAX_RETRIES = int(os.getenv('NETWORK_MAX_RETRIES', 4))
    NETWORK_BACKOFF_FACTOR = float(os.getenv('NETWORK_BACKOFF_FACTOR', 0.8))
    NETWORK_CIRCUIT_FAILURES = int(os.getenv('NETWORK_CIRCUIT_FAILURES', 5))
    NETWORK_CIRCUIT_RESET_SECONDS = int(os.getenv('NETWORK_CIRCUIT_RESET_SECONDS', 60))
    NETWORK_POOL_CONNECTIONS = int(os.getenv('NETWORK_POOL_CONNECTIONS', 10))
    NETWORK_POOL_MAXSIZE = int(os.getenv('NETWORK_POOL_MAXSIZE', 20))
    NETWORK_JITTER_MS = int(os.getenv('NETWORK_JITTER_MS', 120))
    NETWORK_USER_AGENT = os.getenv('NETWORK_USER_AGENT', 'Mozilla/5.0 (compatible; CampusMind-EGSPEC/4.0)')
    NETWORK_HTTP_PROXY = os.getenv('NETWORK_HTTP_PROXY', '').strip() or os.getenv('HTTP_PROXY', '').strip()
    NETWORK_HTTPS_PROXY = os.getenv('NETWORK_HTTPS_PROXY', '').strip() or os.getenv('HTTPS_PROXY', '').strip()
    NETWORK_CA_BUNDLE = os.getenv('NETWORK_CA_BUNDLE', '').strip() or os.getenv('REQUESTS_CA_BUNDLE', '').strip()
    NETWORK_BASIC_AUTH_USER = os.getenv('NETWORK_BASIC_AUTH_USER', '').strip()
    NETWORK_BASIC_AUTH_PASSWORD = os.getenv('NETWORK_BASIC_AUTH_PASSWORD', '').strip()
    NETWORK_ALLOWED_DOMAINS = [x.strip().lower() for x in os.getenv(
        'NETWORK_ALLOWED_DOMAINS',
        'egspec.org,coe.egspec.org,egspgroup.in,admissions.egspgroup.in'
    ).split(',') if x.strip()]
    MAX_SESSION_MESSAGES = int(os.getenv('MAX_SESSION_MESSAGES', 20))
    CHAT_RATE_LIMIT = int(os.getenv('CHAT_RATE_LIMIT', 20))
    CHAT_RATE_WINDOW_SECONDS = int(os.getenv('CHAT_RATE_WINDOW_SECONDS', 60))
    RESPONSE_CACHE_ENABLED = _bool('RESPONSE_CACHE_ENABLED', True)
    RESPONSE_CACHE_TTL_SECONDS = int(os.getenv('RESPONSE_CACHE_TTL_SECONDS', 900))
    RESPONSE_CACHE_MAX_ENTRIES = int(os.getenv('RESPONSE_CACHE_MAX_ENTRIES', 500))
    # Protect CPU/local-LLM inference from traffic spikes. Cache hits bypass this queue.
    LLM_MAX_CONCURRENT = int(os.getenv('LLM_MAX_CONCURRENT', 2))
    LLM_MAX_QUEUE = int(os.getenv('LLM_MAX_QUEUE', 64))
    LLM_QUEUE_TIMEOUT_SECONDS = float(os.getenv('LLM_QUEUE_TIMEOUT_SECONDS', 12))
    ESCALATION_EMAIL = os.getenv('ESCALATION_EMAIL', '').strip()
    ESCALATION_PHONE = os.getenv('ESCALATION_PHONE', '').strip()
    ADMISSIONS_CONTACT_URL = os.getenv(
        'ADMISSIONS_CONTACT_URL',
        'https://admissions.egspgroup.in/',
    ).strip()
    JWT_SECRET = os.getenv('JWT_SECRET', '').strip()
    JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', 60))
    FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY', '').strip()
    AUTH_REQUIRED = _bool('AUTH_REQUIRED', False)
    LOGIN_MAX_FAILURES = int(os.getenv('LOGIN_MAX_FAILURES', 5))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv('LOGIN_LOCKOUT_MINUTES', 15))
    VOICE_STREAMING_ENABLED = _bool('VOICE_STREAMING_ENABLED', True)
    VOICE_STT_MODEL = os.getenv('VOICE_STT_MODEL', 'small')
    VOICE_STT_DEVICE = os.getenv('VOICE_STT_DEVICE', 'cpu')
    VOICE_STT_COMPUTE_TYPE = os.getenv('VOICE_STT_COMPUTE_TYPE', 'int8')
    VOICE_STT_CPU_THREADS = int(os.getenv('VOICE_STT_CPU_THREADS', 4))
    VOICE_PARTIAL_INTERVAL_SECONDS = float(os.getenv('VOICE_PARTIAL_INTERVAL_SECONDS', 1.5))
    VOICE_MIN_UTTERANCE_SECONDS = float(os.getenv('VOICE_MIN_UTTERANCE_SECONDS', 0.35))
    VOICE_MAX_AUDIO_BYTES = int(os.getenv('VOICE_MAX_AUDIO_BYTES', 640000))
    VOICE_VAD_THRESHOLD = float(os.getenv('VOICE_VAD_THRESHOLD', 0.5))
    VOICE_MIN_RMS_ENERGY = float(os.getenv('VOICE_MIN_RMS_ENERGY', 0.012))
    VOICE_TTS_ENABLED = _bool('VOICE_TTS_ENABLED', True)
    VOICE_TTS_ENGINE = os.getenv('VOICE_TTS_ENGINE', 'edge').lower()
    PIPER_EXECUTABLE = os.getenv('PIPER_EXECUTABLE', 'piper')
    PIPER_MODEL_PATH = os.getenv('PIPER_MODEL_PATH', '').strip()
    PIPER_SAMPLE_RATE = int(os.getenv('PIPER_SAMPLE_RATE', 22050))

    # Automatic website/PDF knowledge synchronization
    MONITOR_ENABLED = _bool('MONITOR_ENABLED', True)
    MONITOR_BASE_URL = os.getenv('MONITOR_BASE_URL', 'https://egspec.org/')
    # Trusted public institute sources. A normal website sync now combines all of them.
    # Override with OFFICIAL_SOURCE_ROOTS as a comma-separated list when needed.
    OFFICIAL_SOURCE_ROOTS = [u.strip() for u in os.getenv(
        'OFFICIAL_SOURCE_ROOTS',
        'https://egspec.org/,https://coe.egspec.org/,https://admissions.egspgroup.in/'
    ).split(',') if u.strip()]
    MONITOR_INTERVAL_SECONDS = int(os.getenv('MONITOR_INTERVAL_SECONDS', 3600))
    MONITOR_MAX_PAGES = int(os.getenv('MONITOR_MAX_PAGES', 5000))
    MONITOR_RETRIES = int(os.getenv('MONITOR_RETRIES', 3))
    MONITOR_MIN_TEXT_LENGTH = int(os.getenv('MONITOR_MIN_TEXT_LENGTH', 40))
    # Optional multi-stage extraction fallback for difficult/JavaScript-heavy pages.
    ADVANCED_WEB_INGESTION = _bool('ADVANCED_WEB_INGESTION', True)
    ADVANCED_WEB_MIN_TEXT = int(os.getenv('ADVANCED_WEB_MIN_TEXT', 180))
    CRAWL4AI_ENABLED = _bool('CRAWL4AI_ENABLED', True)
    ANAKIN_ENABLED = _bool('ANAKIN_ENABLED', False)
    ANAKIN_BASE_URL = os.getenv('ANAKIN_BASE_URL', 'http://127.0.0.1:8080').strip()
    ANAKIN_ALLOW_REMOTE = _bool('ANAKIN_ALLOW_REMOTE', False)
    PLAYWRIGHT_FALLBACK_ENABLED = _bool('PLAYWRIGHT_FALLBACK_ENABLED', True)
    PLAYWRIGHT_TIMEOUT_MS = int(os.getenv('PLAYWRIGHT_TIMEOUT_MS', 30000))
    PLAYWRIGHT_SETTLE_MS = int(os.getenv('PLAYWRIGHT_SETTLE_MS', 1200))
    MONITOR_PAGES = [p.strip() for p in os.getenv(
        'MONITOR_PAGES',
        ',about/,admissions/,academics/,departments/,examinations/,placement/,hostel/,fee-structure/,faculty/,news/,events/,contact/'
    ).split(',')]

    # Compound retrieval / high-accuracy knowledge controls
    CONTEXTUAL_RETRIEVAL_ENABLED = _bool('CONTEXTUAL_RETRIEVAL_ENABLED', True)
    CHUNK_DEDUP_ENABLED = _bool('CHUNK_DEDUP_ENABLED', True)
    ENABLE_KAG = _bool('ENABLE_KAG', True)
    KAG_GRAPH_PATH = os.getenv('KAG_GRAPH_PATH', str(Path(DATA_DIR) / 'knowledge_graph.json'))
    KAG_TOP_K = int(os.getenv('KAG_TOP_K', 5))
    ENABLE_CAG = _bool('ENABLE_CAG', True)
    CAG_CONTEXT_TTL_SECONDS = int(os.getenv('CAG_CONTEXT_TTL_SECONDS', 1800))
    CAG_CONTEXT_MAX_ENTRIES = int(os.getenv('CAG_CONTEXT_MAX_ENTRIES', 500))

    AUTO_DETECT_LANGUAGE = _bool('AUTO_DETECT_LANGUAGE', True)
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
    SUPPORTED_LANGUAGES = {
        'en': 'English', 'ta': 'Tamil', 'tanglish': 'Thanglish', 'hi': 'Hindi',
        'te': 'Telugu', 'ml': 'Malayalam', 'kn': 'Kannada',
    }

    FALLBACK_MESSAGE = (
        'I do not have verified information about that in the institute records.'
    )
    SYSTEM_PROMPT = (
        f'You are the official AI assistant for {INSTITUTE_NAME}.\n'
        'You MUST ONLY answer based on the provided institute context.\n'
        f"If the answer is not found in the context, reply exactly: '{FALLBACK_MESSAGE}'\n"
        'Never treat conversation history as an authoritative factual source.\n'
        'DO NOT use outside knowledge. DO NOT hallucinate.\n'
        'Keep names, dates, fees, codes and numbers exactly as shown in the context.\n'
        'Cite the source document when possible. Keep answers concise and helpful.'
    )

    @classmethod
    def validate(cls):
        errors = []
        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            errors.append('CHUNK_OVERLAP must be smaller than CHUNK_SIZE')
        if cls.TOP_K < 1:
            errors.append('TOP_K_RETRIEVAL must be >= 1')
        if cls.CHAT_RATE_LIMIT < 1 or cls.CHAT_RATE_WINDOW_SECONDS < 1:
            errors.append('Chat rate-limit values must be >= 1')
        if cls.LLM_MAX_CONCURRENT < 1 or cls.LLM_MAX_QUEUE < 0 or cls.LLM_QUEUE_TIMEOUT_SECONDS <= 0:
            errors.append('LLM traffic protection values are invalid')
        if not 0 <= cls.VECTOR_WEIGHT <= 1 or not 0 <= cls.KEYWORD_WEIGHT <= 1:
            errors.append('Hybrid weights must be between 0 and 1')
        if abs((cls.VECTOR_WEIGHT + cls.KEYWORD_WEIGHT) - 1.0) > 0.001:
            errors.append('VECTOR_WEIGHT + KEYWORD_WEIGHT must equal 1.0')
        if not 0 <= cls.RERANKER_WEIGHT <= 1:
            errors.append('RERANKER_WEIGHT must be between 0 and 1')
        if cls.VECTOR_BACKEND not in {'chroma', 'pgvector'}:
            errors.append('VECTOR_BACKEND must be chroma or pgvector')
        if cls.VECTOR_BACKEND == 'pgvector' and not cls.PGVECTOR_URL:
            errors.append('PGVECTOR_URL is required when VECTOR_BACKEND=pgvector')
        if cls.AUTH_REQUIRED and len(cls.JWT_SECRET) < 32:
            errors.append('JWT_SECRET must contain at least 32 characters when AUTH_REQUIRED=true')
        if cls.VOICE_TTS_ENGINE not in {'edge','piper'}:
            errors.append('VOICE_TTS_ENGINE must be edge or piper')
        if cls.NETWORK_MODE not in {'auto', 'direct', 'proxy', 'offline'}:
            errors.append('NETWORK_MODE must be auto, direct, proxy or offline')
        if cls.NETWORK_CONNECT_TIMEOUT <= 0 or cls.NETWORK_READ_TIMEOUT <= 0:
            errors.append('Network timeout values must be > 0')
        if cls.NETWORK_MAX_RETRIES < 0 or cls.NETWORK_CIRCUIT_FAILURES < 1:
            errors.append('Network retry/circuit-breaker values are invalid')
        if not cls.NETWORK_ALLOWED_DOMAINS:
            errors.append('NETWORK_ALLOWED_DOMAINS must contain at least one trusted domain')
        if cls.ADVANCED_WEB_MIN_TEXT < cls.MONITOR_MIN_TEXT_LENGTH:
            errors.append('ADVANCED_WEB_MIN_TEXT must be >= MONITOR_MIN_TEXT_LENGTH')
        if cls.PLAYWRIGHT_TIMEOUT_MS < 1000 or cls.PLAYWRIGHT_SETTLE_MS < 0:
            errors.append('Playwright timing values are invalid')
        if errors:
            raise ValueError('; '.join(errors))
        return True


config = Config()
config.validate()
