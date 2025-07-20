# resume_manager.py
import mysql.connector
import pandas as pd
from pinecone import Pinecone, ServerlessSpec  # <-- THAY ĐỔI 1: Import ServerlessSpec
import config

class ResumeManager:
    """Quản lý dữ liệu hồ sơ từ TiDB và đồng bộ vector với Pinecone."""

    def __init__(self, embedding_model):
        print("Khởi tạo ResumeManager...")
        self.db_config = config.DB_CONFIG
        self.table_name = config.TABLE_NAME
        self.embedding_model = embedding_model
        self.df_resumes = pd.DataFrame()

        self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
        self.index_name = config.PINECONE_INDEX_NAME

        if self.index_name not in self.pc.list_indexes().names():
            print(f"CẢNH BÁO: Index '{self.index_name}' không tồn tại. Đang tạo tạm thời (Serverless).")
            print("Vui lòng chạy script sync_pinecone.py để đồng bộ dữ liệu.")
            # --- THAY ĐỔI 2: Sử dụng ServerlessSpec với giá trị cố định ---
            self.pc.create_index(
                name=self.index_name,
                dimension=384,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            # -----------------------------------------------------------

        self.index = self.pc.Index(self.index_name)
        print(f"✅ Kết nối tới Pinecone index '{self.index_name}' thành công.")

    # ... các hàm còn lại giữ nguyên ...
    def load_resumes_from_db(self):
        print("\n--- Đang tải dữ liệu hồ sơ từ TiDB... ---")
        try:
            conn = mysql.connector.connect(**self.db_config)
            query = f"SELECT * FROM {self.table_name}"
            self.df_resumes = pd.read_sql(query, conn)
            self.df_resumes['id'] = self.df_resumes['id'].astype(str)
            self.df_resumes.set_index('id', inplace=True)
            print(f"✅ Tải thành công {len(self.df_resumes)} hồ sơ vào bộ nhớ.")
            return True
        except Exception as e:
            print(f"❌ LỖI KHI TẢI DỮ LIỆU TỪ DB: {e}")
            return False
        finally:
            if 'conn' in locals() and conn.is_connected():
                conn.close()

    def get_resumes_by_ids(self, ids: list):
        if self.df_resumes.empty:
            self.load_resumes_from_db()
        str_ids = [str(i) for i in ids]
        valid_ids = [id for id in str_ids if id in self.df_resumes.index]
        return self.df_resumes.loc[valid_ids]

    def query_pinecone(self, query_text: str, top_k: int):
        print(f"--- Đang truy vấn Pinecone với top_k={top_k}... ---")
        query_embedding = self.embedding_model.encode(query_text).tolist()
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=False
        )
        candidate_ids = [match['id'] for match in results['matches']]
        relevance_scores = {match['id']: match['score'] for match in results['matches']}
        print(f"✅ Pinecone trả về {len(candidate_ids)} kết quả.")
        return candidate_ids, relevance_scores