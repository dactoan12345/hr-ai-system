# db_manager.py
import mysql.connector
import config
from passlib.context import CryptContext # <-- Thêm thư viện
import json # <--- THÊM DÒNG NÀY

# --- Cấu hình băm mật khẩu ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    """Tạo và trả về một kết nối database."""
    try:
        conn = mysql.connector.connect(**config.DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối DB: {err}")
        return None

def verify_password(plain_password, hashed_password):
    """Xác thực mật khẩu thô với mật khẩu đã băm."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    """Băm mật khẩu."""
    return pwd_context.hash(password)

def create_user(email: str, password: str):
    """Tạo người dùng mới với mật khẩu đã được băm."""
    conn = get_db_connection()
    if not conn:
        return None, "Lỗi kết nối database."

    cursor = conn.cursor(dictionary=True)
    try:
        # Kiểm tra xem email đã tồn tại chưa
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return None, f"Email '{email}' đã được đăng ký."

        # Băm mật khẩu và tạo người dùng mới
        hashed_pass = hash_password(password)
        cursor.execute(
            "INSERT INTO users (email, fullname, hashed_password) VALUES (%s, %s, %s)",
            (email, email.split('@')[0], hashed_pass)
        )
        conn.commit()
        
        # Lấy lại thông tin user vừa tạo
        cursor.execute("SELECT id, email, fullname FROM users WHERE email = %s", (email,))
        new_user = cursor.fetchone()
        return new_user, "Đăng ký thành công!"

    except mysql.connector.Error as err:
        print(f"Lỗi DB khi tạo user: {err}")
        return None, "Đã có lỗi xảy ra từ phía server."
    finally:
        cursor.close()
        conn.close()

def authenticate_user(email: str, password: str):
    """Xác thực người dùng bằng email và mật khẩu."""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        # Nếu không tìm thấy user hoặc mật khẩu không khớp
        if not user or not verify_password(password, user["hashed_password"]):
            return None
            
        # Trả về thông tin user (không bao gồm mật khẩu)
        return {"id": user["id"], "email": user["email"], "fullname": user["fullname"]}
    
    except mysql.connector.Error as err:
        print(f"Lỗi DB khi xác thực: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


# --- CẬP NHẬT HÀM GHI LOG ---
def log_search_history(user_id: int, query: str, enhanced_query: str, intent: str, results_data: list):
    """Ghi lại lịch sử và KẾT QUẢ tìm kiếm vào DB."""
    conn = get_db_connection()
    if not conn:
        return
    
    # Chuyển đổi kết quả Python dict/list thành chuỗi JSON
    results_json = json.dumps(results_data)
        
    cursor = conn.cursor()
    try:
        query_data = (user_id, query, enhanced_query, intent, results_json)
        cursor.execute(
            "INSERT INTO search_history (user_id, query_text, enhanced_query, intent, search_results) VALUES (%s, %s, %s, %s, %s)",
            query_data
        )
        conn.commit()
        print(f"Đã ghi log tìm kiếm và kết quả cho user_id: {user_id}")
    except mysql.connector.Error as err:
        print(f"Lỗi DB khi ghi log: {err}")
    finally:
        cursor.close()
        conn.close()

# --- THÊM HÀM MỚI ĐỂ LẤY LỊCH SỬ ---
def get_search_history(user_id: int):
    """Lấy danh sách lịch sử tìm kiếm của người dùng."""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        # Sắp xếp để các tìm kiếm mới nhất hiện lên đầu
        cursor.execute(
            "SELECT id, query_text, search_timestamp FROM search_history WHERE user_id = %s ORDER BY search_timestamp DESC LIMIT 10",
            (user_id,)
        )
        history = cursor.fetchall()
        return history
    except mysql.connector.Error as err:
        print(f"Lỗi DB khi lấy lịch sử: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

# --- THÊM HÀM MỚI ĐỂ LẤY LẠI KẾT QUẢ CŨ ---
def get_past_search_result(search_id: int, user_id: int):
    """Lấy kết quả đã lưu của một lần tìm kiếm trong quá khứ."""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        # Thêm user_id để đảm bảo người dùng chỉ xem được lịch sử của chính mình
        cursor.execute(
            "SELECT search_results FROM search_history WHERE id = %s AND user_id = %s",
            (search_id, user_id)
        )
        result = cursor.fetchone()
        if result and result['search_results']:
            # Chuyển chuỗi JSON ngược lại thành Python dict/list
            return json.loads(result['search_results'])
        return None
    except (mysql.connector.Error, json.JSONDecodeError) as err:
        print(f"Lỗi khi lấy kết quả cũ: {err}")
        return None
    finally:
        cursor.close()
        conn.close()