# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- CẤU HÌNH MODEL ---
GEMINI_MODEL_NAME = 'gemini-1.5-flash'
SENTENCE_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- CẤU HÌNH DATABASE ---
TABLE_NAME = 'cleaned_resumes'
DB_PASSWORD = os.getenv("DB_PASSWORD")
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")
DB_CONFIG = {
    "host": "gateway01.us-west-2.prod.aws.tidbcloud.com",
    "port": 4000,
    "user": "ftBrFWJ25fJoKjx.root",
    "password": DB_PASSWORD,
    "database": "SEG301",
    "ssl_ca": SSL_CERT_PATH,
    "ssl_verify_cert": True,
    "ssl_verify_identity": True
}

# --- CẤU HÌNH PINECONE ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = "hr-ai-system" # Đặt tên index của bạn ở đây

# --- CẤU HÌNH LOGIC XẾP HẠNG ---
WEIGHT_RELEVANCE = 0.4
WEIGHT_QUALITY = 0.6
DEFAULT_DYNAMIC_WEIGHTS = {
    'experience': 7, 'professional_skill': 8, 'language': 5,
    'certificate': 4, 'achievement': 4, 'project': 5,
    'soft_skill': 3, 'activity': 2
}
SHORTLIST_SIZE = 10 # Tăng shortlist cho Pinecone
TOP_K_RESULTS = 5