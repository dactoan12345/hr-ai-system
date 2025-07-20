# app.py
import streamlit as st
import json # <-- Thêm import
import pandas as pd
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

import config
import ai_services
import db_manager
from resume_manager import ResumeManager

# --- Cấu hình trang và khởi tạo hệ thống (giữ nguyên) ---
st.set_page_config(page_title="Nhà Tư vấn Nhân sự AI", page_icon="🤖", layout="wide")

@st.cache_resource
def initialize_system():
    print("--- KHỞI TẠO HỆ THỐNG (Chạy một lần) ---")
    genai.configure(api_key=config.GEMINI_API_KEY)
    llm_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
    embedding_model = SentenceTransformer(config.SENTENCE_MODEL_NAME)
    resume_mgr = ResumeManager(embedding_model)
    resume_mgr.load_resumes_from_db()
    print("--- ✅ HỆ THỐNG ĐÃ SẴN SÀNG ---")
    return llm_model, embedding_model, resume_mgr

llm_model, embedding_model, resume_manager = initialize_system()

# --- Quản lý session state (giữ nguyên) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.search_results = None

# --- Giao diện Login / Register (giữ nguyên) ---
if not st.session_state.logged_in:
    st.title("Chào mừng đến với Nhà Tư vấn Nhân sự AI 🤖")
    login_tab, register_tab = st.tabs(["Đăng nhập", "Đăng ký"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Mật khẩu", type="password", key="login_pass")
            submitted = st.form_submit_button("Đăng nhập")
            if submitted:
                with st.spinner("Đang xác thực..."):
                    user_info = db_manager.authenticate_user(email, password)
                if user_info:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_info
                    st.rerun()
                else:
                    st.error("Email hoặc mật khẩu không chính xác.")
    with register_tab:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Mật khẩu", type="password", key="reg_pass")
            reg_confirm_password = st.text_input("Xác nhận mật khẩu", type="password", key="reg_confirm")
            reg_submitted = st.form_submit_button("Đăng ký")
            if reg_submitted:
                if reg_password != reg_confirm_password: st.error("Mật khẩu xác nhận không khớp.")
                elif len(reg_password) < 6: st.error("Mật khẩu phải có ít nhất 6 ký tự.")
                else:
                    with st.spinner("Đang tạo tài khoản..."):
                        new_user, message = db_manager.create_user(reg_email, reg_password)
                    if new_user: st.success(f"{message} Vui lòng chuyển qua tab 'Đăng nhập' để vào hệ thống.")
                    else: st.error(message)
else:
    # --- GIAO DIỆN CHÍNH CỦA ỨNG DỤNG ---
    
    # --- THAY ĐỔI 1: HIỂN THỊ LỊCH SỬ TRÊN SIDEBAR ---
    st.sidebar.header(f"Xin chào, {st.session_state.user_info['email']}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Lịch sử tìm kiếm")
    
    history_items = db_manager.get_search_history(st.session_state.user_info['id'])

    def load_past_results(search_id):
        user_id = st.session_state.user_info['id']
        past_results = db_manager.get_past_search_result(search_id, user_id)
        if past_results:
            st.session_state.search_results = past_results
        else:
            st.error("Không thể tải kết quả cũ.")

    if not history_items:
        st.sidebar.info("Chưa có lịch sử tìm kiếm.")
    else:
        for item in history_items:
            # Dùng on_click để gọi hàm khi nút được nhấn
            st.sidebar.button(
                label=f"'{item['query_text'][:30]}...'",
                key=f"history_{item['id']}",
                on_click=load_past_results,
                args=(item['id'],),
                help=f"Tìm lúc: {item['search_timestamp']}",
                use_container_width=True
            )

    st.sidebar.markdown("---")
    if st.sidebar.button("Đăng xuất"):
        # ... (logic đăng xuất giữ nguyên)
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.search_results = None
        st.rerun()

    st.title("🤖 Nhà Tư vấn Nhân sự AI")
    st.write("Mô tả yêu cầu tuyển dụng của bạn, hoặc chọn một tìm kiếm cũ từ lịch sử bên trái.")

    user_query = st.text_area("Nhập mô tả công việc hoặc dự án tại đây:", height=150)

    if st.button("Tìm kiếm ứng viên mới", type="primary"):
        if not user_query:
            st.warning("Vui lòng nhập yêu cầu tuyển dụng.")
        else:
            with st.spinner("AI đang phân tích yêu cầu và tìm kiếm..."):
                # --- Toàn bộ logic tìm kiếm giữ nguyên ---
                enhanced_query = ai_services.enhance_query(llm_model, user_query)
                intent = ai_services.classify_intent(llm_model, enhanced_query)
                dynamic_weights = ai_services.get_dynamic_weights(llm_model, enhanced_query)
                plan = ai_services.get_ai_plan(llm_model, enhanced_query, intent)
                roles_to_find = plan.get('team_composition', []) if intent == 'project_description' else plan
                
                all_results = []
                # ... (Vòng lặp for role in roles_to_find giữ nguyên) ...
                for role in roles_to_find:
                    role_title = role.get('position_title', 'KHÔNG XÁC ĐỊNH').upper()
                    detailed_query = f"{role.get('position_title','')} with {role.get('experience_level','')} skills in {', '.join(role.get('hard_skills',[]))}"
                    candidate_ids, relevance_scores = resume_manager.query_pinecone(detailed_query, top_k=config.SHORTLIST_SIZE)
                    if not candidate_ids:
                        continue
                    shortlisted_resumes_df = resume_manager.get_resumes_by_ids(candidate_ids)
                    candidate_results = []
                    for i, (idx, candidate_row) in enumerate(shortlisted_resumes_df.iterrows()):
                        relevance_score = relevance_scores.get(str(idx), 0)
                        parsed_scores = ai_services.get_on_demand_quality_scores(candidate_row.to_dict(), llm_model)
                        if not parsed_scores: continue
                        quality_score = ai_services.calculate_quality_score(parsed_scores, dynamic_weights, role, candidate_row)
                        normalized_quality_score = quality_score / 300.0
                        final_score = (config.WEIGHT_RELEVANCE * relevance_score) + (config.WEIGHT_QUALITY * normalized_quality_score)
                        candidate_results.append({
                            "final_score": final_score, "relevance_score": relevance_score,
                            "quality_score": quality_score, "data": candidate_row.to_dict(),
                            "parsed_scores": parsed_scores, "id": idx
                        })
                    ranked_candidates = sorted(candidate_results, key=lambda x: x['final_score'], reverse=True)
                    all_results.append({"role": role_title, "candidates": ranked_candidates})
                
                st.session_state.search_results = all_results
                
                # --- THAY ĐỔI 2: GỬI KẾT QUẢ ĐỂ LƯU VÀO DB ---
                db_manager.log_search_history(
                    user_id=st.session_state.user_info['id'],
                    query=user_query,
                    enhanced_query=enhanced_query,
                    intent=intent,
                    results_data=all_results # <-- Gửi kết quả đi
                )

    # --- HIỂN THỊ KẾT QUẢ (giữ nguyên)---
    if st.session_state.search_results:
        st.markdown("---")
        st.subheader("Kết quả đề xuất")
        for result_group in st.session_state.search_results:
            st.markdown(f"#### 🏆 Top ứng viên cho vị trí: **{result_group['role']}**")
            # ... (toàn bộ logic hiển thị kết quả giữ nguyên) ...
            if not result_group['candidates']:
                st.info("Không tìm thấy ứng viên nào phù hợp.")
                continue
            for i, result in enumerate(result_group['candidates'][:config.TOP_K_RESULTS]):
                candidate = result['data']
                parsed = result['parsed_scores']
                with st.expander(f"**#{i+1}: {str(candidate.get('fullname', 'N/A')).title()}** | Điểm: {result['final_score']:.2f}", expanded= i < 2):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"- **ID Hồ sơ:** `{result['id']}`\n- **Email:** `{candidate.get('email', 'N/A')}`\n- **Điện thoại:** `{candidate.get('phonenumber', 'N/A')}`")
                    with col2:
                        st.metric("Điểm Liên quan (Semantic)", f"{result['relevance_score']:.3f}")
                        st.metric("Điểm Chất lượng (LLM)", f"{result['quality_score']:.0f}")
                    st.markdown("---")
                    st.markdown("**Các chỉ số chính do AI phân tích:**")
                    key_metrics_cols = st.columns(4)
                    key_metrics_cols[0].metric("Số năm KN", f"{parsed.get('parsed_exp_years', 'N/A')}")
                    key_metrics_cols[1].metric("Kỹ năng Cứng (Nâng cao)", f"{parsed.get('parsed_prof_skill_advanced', 'N/A')}")
                    key_metrics_cols[2].metric("Chứng chỉ giá trị", f"{parsed.get('parsed_certs_high_value', 'N/A')}")
                    key_metrics_cols[3].metric("Điểm Ngoại ngữ", f"{parsed.get('parsed_lang_score', 'N/A')}")