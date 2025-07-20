# sync_pinecone.py
import pandas as pd
import mysql.connector
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec  # <-- THAY ĐỔI 1: Import ServerlessSpec
import config
import torch
import time

def sync_data_to_pinecone():
    """
    Đọc tất cả hồ sơ từ TiDB, tạo embedding, và đẩy lên Pinecone.
    Tự động tạo index nếu chưa có.
    """
    print("--- BẮT ĐẦU QUÁ TRÌNH ĐỒNG BỘ ---")
    
    # 1. & 2. Tải dữ liệu và model (giữ nguyên)
    print("1. Đang kết nối TiDB và tải dữ liệu...")
    conn = mysql.connector.connect(**config.DB_CONFIG)
    df = pd.read_sql(f"SELECT id, full_text FROM {config.TABLE_NAME}", conn)
    conn.close()
    print(f"   -> Tải thành công {len(df)} hồ sơ.")

    print("2. Đang tải model embedding...")
    model = SentenceTransformer(config.SENTENCE_MODEL_NAME, device='cuda' if torch.cuda.is_available() else 'cpu')
    print("   -> Tải model thành công.")

    # 3. Kết nối Pinecone và kiểm tra/tạo index
    print("3. Đang kết nối tới Pinecone...")
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index_name = config.PINECONE_INDEX_NAME

    if index_name not in pc.list_indexes().names():
        print(f"   -> Index '{index_name}' không tồn tại. Đang tạo index mới (Serverless)...")
        # --- THAY ĐỔI 2: Sử dụng ServerlessSpec với giá trị cố định ---
        pc.create_index(
            name=index_name,
            dimension=384,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        # -----------------------------------------------------------
        print("   -> Đã gửi yêu cầu tạo index. Chờ index khởi tạo...")
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(10)
    else:
        print(f"   -> Đã tìm thấy index '{index_name}'.")

    index = pc.Index(index_name)
    print("   -> Kết nối Pinecone thành công.")

    # 4. Tạo embedding và upsert (giữ nguyên)
    print(f"4. Đang tạo embedding và upsert lên Pinecone (batch_size=100)...")
    batch_size = 100
    for i in tqdm(range(0, len(df), batch_size)):
        i_end = min(i + batch_size, len(df))
        batch = df.iloc[i:i_end]
        texts = batch['full_text'].fillna('').tolist()
        ids = batch['id'].astype(str).tolist()
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        vectors_to_upsert = list(zip(ids, embeddings))
        index.upsert(vectors=vectors_to_upsert)

    print("\n--- ✅ QUÁ TRÌNH ĐỒNG BỘ HOÀN TẤT! ---")
    print(f"   -> Tổng số vector trong index: {index.describe_index_stats()['total_vector_count']}")

if __name__ == "__main__":
    sync_data_to_pinecone()