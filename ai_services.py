# ai_services.py
import json
import time
import google.api_core.exceptions
import pandas as pd
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import prompts
import config

def get_api_response_resilient(prompt, model):
    """Hàm gọi API Gemini bền bỉ, có cơ chế retry."""
    max_retries = 3
    initial_wait_time = 5
    for attempt in range(max_retries):
        try:
            safety_settings_config = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            response = model.generate_content(
                prompt,
                request_options={'timeout': 100},
                safety_settings=safety_settings_config
            )
            return response
        except google.api_core.exceptions.ResourceExhausted as e:
            wait_time = initial_wait_time * (2 ** attempt)
            print(f"⚠️ Rate limit hit. Đang chờ {wait_time} giây... (lần {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"🔥 Lỗi không xác định khi gọi API: {e}")
            return None
    print(f"🔥 Đã thử lại {max_retries} lần nhưng vẫn thất bại.")
    return None

def enhance_query(model, query):
    """Sử dụng LLM để sửa lỗi và làm rõ query của người dùng."""
    try:
        prompt = prompts.PROMPT_QUERY_ENHANCER.format(user_query=query)
        response = get_api_response_resilient(prompt, model)
        if response:
            return response.text.strip()
        return query
    except Exception:
        return query

def classify_intent(model, query):
    """Phân loại ý định người dùng."""
    prompt = prompts.PROMPT_INTENT_CLASSIFIER.format(user_query=query)
    response = get_api_response_resilient(prompt, model)
    return response.text.strip() if response else None

def get_dynamic_weights(model, query):
    """Lấy trọng số động dựa trên query."""
    prompt = prompts.PROMPT_WEIGHT_ADJUSTER.format(user_query=query)
    response = get_api_response_resilient(prompt, model)
    if response:
        try:
            # Dọn dẹp output từ LLM để đảm bảo là JSON hợp lệ
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print("⚠️ Không thể parse JSON từ trọng số động, sử dụng trọng số mặc định.")
            return config.DEFAULT_DYNAMIC_WEIGHTS
    return config.DEFAULT_DYNAMIC_WEIGHTS

def get_ai_plan(model, query, intent):
    """Lấy kế hoạch tuyển dụng từ AI."""
    prompt_template = prompts.PROMPT_PROJECT_DECOMPOSER if intent == 'project_description' else prompts.PROMPT_ROLE_EXTRACTOR
    prompt = prompt_template.format(user_query=query)
    response = get_api_response_resilient(prompt, model)
    if response:
        try:
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print(f"⚠️ Lỗi parse JSON từ kế hoạch của AI. Output thô: {response.text}")
            return None
    return None

def get_on_demand_quality_scores(candidate_row, model):
    """Đánh giá chất lượng chi tiết của một ứng viên."""
    full_text_block = ""
    columns_to_consolidate = [
        "experience", "language_skill", "certificate", "achievement",
        "project", "activity", "professional_skill", "soft_skill", "education"
    ]
    for col in columns_to_consolidate:
        content = candidate_row.get(col, "")
        if pd.notna(content) and str(content).strip() != "":
            full_text_block += f"### {col.upper()}\n{content}\n\n"

    if not full_text_block.strip():
        print(f"⚠️ Bỏ qua ứng viên ID {candidate_row.get('id')} vì không có nội dung để đánh giá.")
        return {}

    prompt = prompts.PROMPT_HYBRID_EVALUATION.format(text_input=full_text_block)
    response = get_api_response_resilient(prompt, model)
    if response:
        try:
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print(f"⚠️ Lỗi parse JSON điểm chất lượng cho ID {candidate_row.get('id')}. Output thô: {response.text}")
            return {}
    return {}

def calculate_quality_score(parsed_scores, dynamic_weights, role_info, candidate_row):
    """Tính điểm chất lượng dựa trên điểm đã phân tích và trọng số."""
    score = 0
    weights = dynamic_weights
    
    # Tính điểm từ các thành phần được LLM phân tích
    score += parsed_scores.get('parsed_exp_years', 0) * weights.get('experience', 7)
    score += parsed_scores.get('parsed_prof_skill_advanced', 0) * weights.get('professional_skill', 8)
    score += parsed_scores.get('parsed_lang_score', 0) * weights.get('language', 5)
    score += parsed_scores.get('parsed_certs_high_value', 0) * weights.get('certificate', 4)
    score += parsed_scores.get('parsed_achievements_high_impact', 0) * weights.get('achievement', 4)
    score += parsed_scores.get('parsed_projects_high_impact', 0) * weights.get('project', 5)
    score += parsed_scores.get('parsed_soft_skill_count', 0) * weights.get('soft_skill', 3)
    score += parsed_scores.get('parsed_activities_high_impact', 0) * weights.get('activity', 2)
    
    # Cộng điểm thưởng cho kỹ năng cứng khớp chính xác
    required_skills = set([s.lower().strip() for s in role_info.get('hard_skills', [])])
    candidate_skills_text = str(candidate_row.get('professional_skill', ''))
    if pd.notna(candidate_skills_text):
        candidate_skills = set([s.strip().lower() for s in candidate_skills_text.split(',')])
        matched_skills_count = len(required_skills.intersection(candidate_skills))
        # Mỗi kỹ năng khớp được thưởng 15 điểm
        score += matched_skills_count * 15
        
    return score