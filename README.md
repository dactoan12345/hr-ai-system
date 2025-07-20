# Hệ thống Tư vấn Nhân sự AI 🤖

Hệ thống này là một trợ lý nhân sự thông minh, được xây dựng để giúp các nhà tuyển dụng và quản lý dự án nhanh chóng tìm ra những ứng viên phù hợp nhất từ một cơ sở dữ liệu hồ sơ (CV).

Ứng dụng sử dụng các mô hình ngôn ngữ lớn (LLM) để phân tích yêu cầu tuyển dụng, hiểu ý định người dùng, và đánh giá sâu sắc chất lượng của từng ứng viên dựa trên nhiều tiêu chí, thay vì chỉ tìm kiếm theo từ khóa đơn thuần.

## ✨ Các tính năng chính

  * **Phân tích Yêu cầu Động:** Tự động phân loại yêu cầu của người dùng là mô tả một dự án lớn (cần nhiều vị trí) hay một vai trò cụ thể.
  * **Tìm kiếm Ngữ nghĩa:** Sử dụng vector embedding để tìm kiếm các hồ sơ liên quan nhất về mặt ngữ nghĩa, thay vì chỉ khớp từ khóa.
  * **Đánh giá Chuyên sâu bằng AI:** Dùng mô hình Gemini để chấm điểm chi tiết chất lượng của ứng viên dựa trên kinh nghiệm, kỹ năng, chứng chỉ, thành tích, v.v.
  * **Hệ thống Trọng số Động:** Tự động điều chỉnh độ quan trọng của các tiêu chí xếp hạng (kinh nghiệm, kỹ năng mềm,...) dựa trên yêu cầu cụ thể của mỗi lần tìm kiếm.
  * **Xác thực Người dùng:** Hệ thống đăng ký, đăng nhập an toàn bằng email và mật khẩu (sử dụng hashing).
  * **Lịch sử Tìm kiếm:** Lưu lại các phiên tìm kiếm và kết quả, cho phép người dùng xem lại một cách dễ dàng.
  * **Giao diện Tương tác:** Giao diện web trực quan được xây dựng bằng Streamlit.

-----

## 🏗️ Kiến trúc Hệ thống

Hệ thống bao gồm các thành phần chính:

1.  **Giao diện người dùng (Streamlit):** Nơi người dùng tương tác, đăng nhập, nhập truy vấn và xem kết quả.
2.  **Logic Backend (Python):** Bao gồm các dịch vụ AI, quản lý cơ sở dữ liệu, và logic nghiệp vụ.
3.  **Vector Database (Pinecone):** Lưu trữ và truy vấn các vector embedding của hồ sơ để tìm kiếm ngữ nghĩa tốc độ cao.
4.  **Relational Database (TiDB Cloud):** Lưu trữ dữ liệu gốc của hồ sơ, thông tin người dùng, và lịch sử tìm kiếm.
5.  **AI Models (Google Gemini & Sentence Transformers):** Bộ não của hệ thống, dùng để hiểu ngôn ngữ, đánh giá và xếp hạng.

-----

## 🛠️ Công nghệ sử dụng

  * **Giao diện & Backend:** Streamlit
  * **Ngôn ngữ:** Python 3.9+
  * **Cơ sở dữ liệu:** TiDB Cloud, Pinecone
  * **Mô hình AI:** Google Gemini 1.5 Flash, `paraphrase-multilingual-MiniLM-L12-v2`
  * **Thư viện chính:** `google-generativeai`, `sentence-transformers`, `pandas`, `passlib[bcrypt]`, `mysql-connector-python`

-----

## 🚀 Hướng dẫn Cài đặt và Chạy

### 1\. Chuẩn bị Môi trường

Đầu tiên, hãy sao chép (clone) mã nguồn của dự án về máy của bạn:

```bash
git clone [<URL_repository_cua_ban>](https://github.com/dactoan12345/hr-ai-system.git)
cd hr_ai_system
```

Tạo một môi trường ảo để quản lý các thư viện. Đây là một bước thực hành tốt.

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo:

  * Trên Windows:
    ```bash
    .venv\Scripts\activate
    ```
  * Trên macOS/Linux:
    ```bash
    source .venv/bin/activate
    ```

### 2\. Cài đặt Thư viện

Cài đặt tất cả các thư viện cần thiết từ file `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3\. Cấu hình Biến môi trường

Tạo một file mới tên là **`.env`** trong thư mục gốc của dự án. Sao chép nội dung dưới đây và điền các thông tin của bạn vào.

```text
# .env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
DB_PASSWORD="YOUR_DATABASE_PASSWORD_HERE"
SSL_CERT_PATH="/path/to/your/isrgrootx1.pem"
PINECONE_API_KEY="YOUR_PINECONE_API_KEY_HERE"
```

### 4\. Sử dụng

Hệ thống cần được chạy theo 2 bước:

**Bước 1: Đồng bộ dữ liệu lên Pinecone (Chỉ chạy lần đầu hoặc khi có CV mới)**

Chạy script sau để đọc dữ liệu hồ sơ từ TiDB, tạo vector embedding và đẩy lên Pinecone. Script này cũng sẽ tự động tạo index trên Pinecone nếu nó chưa tồn tại.

```bash
python sync_pinecone.py
```

*(Quá trình này có thể mất một lúc tùy thuộc vào số lượng hồ sơ).*

**Bước 2: Chạy ứng dụng web**

Sau khi đồng bộ xong, khởi chạy ứng dụng Streamlit:

```bash
streamlit run app.py
```

Một tab mới trên trình duyệt sẽ tự động mở ra, hiển thị giao diện ứng dụng. Bạn có thể bắt đầu bằng việc đăng ký tài khoản và sau đó đăng nhập để sử dụng.
