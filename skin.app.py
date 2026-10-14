import streamlit as st
import pandas as pd
from PIL import Image
import re

# EasyOCR 로드
try:
    import easyocr
    import numpy as np
    @st.cache_resource
    def load_ocr_reader():
        return easyocr.Reader(['ko', 'en'], gpu=False)
    ocr_reader = load_ocr_reader()
    HAS_OCR = True
except Exception:
    HAS_OCR = False

# 1. 엑셀(CSV) 파일에서 데이터 자동 로드
@st.cache_data
def load_data():
    products_df = pd.read_csv('products.csv')
    ingredients_df = pd.read_csv('ingredients.csv')
    
    products_list = []
    for _, row in products_df.iterrows():
        products_list.append({
            'id': int(row['id']),
            'name': str(row['name']),
            'category': str(row['category']),
            'keywords': [k.strip() for k in str(row['keywords']).split(',') if k.strip()],
            'ingredients': [i.strip() for i in str(row['ingredients']).split(',') if i.strip()]
        })
        
    ing_info_dict = {}
    for _, row in ingredients_df.iterrows():
        ing_info_dict[str(row['ingredient']).strip()] = {
            'category': str(row['category']),
            'info': str(row['info'])
        }
        
    return products_list, ing_info_dict

products, INGREDIENT_INFO = load_data()
COMMON_INGREDIENTS = {"정제수", "글리세린", "부틸렌글라이콜", "1,2-헥산다이올"}

# 2. OCR 스마트 매칭 함수
def match_product_from_image(img_file):
    if not HAS_OCR:
        return None, "OCR 라이브러리가 로드되지 않았습니다."
    try:
        image = Image.open(img_file)
        results = ocr_reader.readtext(np.array(image), detail=0)
        raw_text = " ".join(results)
        clean_extracted = re.sub(r'[^a-zA-Z0-9가-힣]', '', raw_text).lower()

        matched_product, max_score = None, 0
        for p in products:
            score = sum(1 for kw in p.get("keywords", []) if kw.lower().strip() in clean_extracted)
            if score > max_score and score >= 1:
                max_score = score
                matched_product = f"[{p['category']}] {p['name']}"
        return matched_product, raw_text
    except Exception as e:
        return None, f"오류: {str(e)}"

# 3. 웹 UI 구성
st.set_page_config(page_title="SkinTrace AI", page_icon="🧴", layout="centered")
st.title("🧴 SkinTrace AI : 개인 맞춤 부작용 추적 비서")
st.caption("다중 사진 인식(OCR)과 AI 원인 추적 분석을 통해 내 피부에 맞는 안전한 화장품을 찾아보세요.")
st.divider()

# 📸 이미지 다중 업로드
st.subheader("📸 1. 화장품 이미지 등록 (다중 스캔)")
tab1, tab2 = st.tabs(["🖼️ 갤러리/파일 다중 업로드", "📷 카메라 실시간 촬영"])
auto_detected_products = []

with tab1:
    uploaded_files = st.file_uploader("과거 부작용 제품 사진을 여러 장 선택하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files:
        st.write(f"📷 총 {len(uploaded_files)}장의 사진이 업로드되었습니다.")
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, file in enumerate(uploaded_files):
            cols[idx % 4].image(file, caption=f"사진 {idx+1}", use_container_width=True)
            matched, raw_text = match_product_from_image(file)
            if matched and matched not in auto_detected_products:
                auto_detected_products.append(matched)

with tab2:
    captured_image = st.camera_input("화장품 정면 촬영")
    if captured_image:
        st.image(captured_image, width=220)
        matched, raw_text = match_product_from_image(captured_image)
        if matched and matched not in auto_detected_products:
            auto_detected_products.append(matched)

if auto_detected_products:
    st.success(f"🎉 총 {len(auto_detected_products)}개 제품이 자동으로 인식되었습니다!")
    for prod in auto_detected_products:
        st.markdown(f"- ✅ **{prod}**")

st.divider()

# ⚠️ 제품 및 증상 설정
st.subheader("⚠️ 2. 부작용 이력 및 구매 검토 제품 설정")
product_dict = {f"[{p['category']}] {p['name']}": p['id'] for p in products}
default_selected = [p for p in auto_detected_products if p in product_dict]

selected_problem_names = st.multiselect("과거 부작용/트러블이 있었던 제품 (자동 선택됨 / 직접 추가 가능):", options=list(product_dict.keys()), default=default_selected)
selected_symptoms = st.multiselect("📌 과거 경험한 주요 부작용 증상:", options=['따가움/화끈거림', '붉어짐/홍조', '트러블/모공막힘/좁쌀', '가려움', '건조함/각질/당김', '눈시림'])
selected_new_name = st.selectbox("🛒 구매 검토 중인 새 제품 (총 90종 중 선택):", options=list(product_dict.keys()))

# 📊 분석 실행
analysis_triggered = st.button("🔍 AI 성분 위험도 및 원인 분석 실행", type="primary", use_container_width=True)

if analysis_triggered:
    if not selected_problem_names:
        st.error("과거 부작용을 경험했던 제품을 최소 1개 이상 선택해 주세요!")
    else:
        problem_ids = [product_dict[name] for name in selected_problem_names]
        new_id = product_dict[selected_new_name]

        problem_ings = [set(p['ingredients']) - COMMON_INGREDIENTS for p in products if p['id'] in problem_ids]
        all_ings = [ing for sub in problem_ings for ing in sub]
        
        caution_ings = set(all_ings) if len(problem_ids) == 1 else {ing for ing in set(all_ings) if all_ings.count(ing) >= 2} or set(all_ings)
        new_product_ings = set(next(p for p in products if p['id'] == new_id)['ingredients'])
        matched = new_product_ings.intersection(caution_ings)

        st.divider()
        st.subheader("📊 AI 맞춤 성분 분석 리포트")
        st.write(f"**분석 대상 문제 제품 ({len(selected_problem_names)}개):** {', '.join(selected_problem_names)}")
        if selected_symptoms:
            st.write(f"**등록된 사용자 증상:** `{', '.join(selected_symptoms)}`")

        if matched:
            st.warning(f"⚠️ **[주의] 과거 문제 제품과 겹치는 위험/특이 성분 {len(matched)}개가 발견되었습니다!**")
            for ing in matched:
                info = INGREDIENT_INFO.get(ing, {"category": "주의 성분", "info": "과거 부작용 유발 제품 포함 성분"})
                st.markdown(f"- **{ing}** (`{info['category']}`) : {info['info']}")
        else:
            st.success("✅ **[안전] 과거 부작용 유발 제품의 주요 특이/위험 성분이 새 제품에서 발견되지 않았습니다.**")

        st.session_state['last_analysis'] = {
            "problem_products": selected_problem_names,
            "symptoms": selected_symptoms,
            "new_product": selected_new_name,
            "matched_ingredients": list(matched)
        }

# --- 🤖 AI 원인 추적 상담사 챗봇 UI ---
st.divider()
st.subheader("💬 AI 피부 전문 상담 에이전트")
st.caption("분석된 결과나 성분에 대해 궁금한 점을 AI 코디네이터에게 자유롭게 물어보세요.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 피부 부작용 원인 분석 AI 코디네이터입니다. 화장품 사진을 등록하고 분석을 실행한 뒤 궁금한 점을 물어보세요."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("예: 이 제품을 쓰고 왜 트러블이 날까? 대체할 성분 추천해줘"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("사용자의 부작용 이력과 성분 데이터를 기반으로 AI가 추론 중입니다..."):
            last_data = st.session_state.get('last_analysis', None)
            if last_data and last_data['matched_ingredients']:
                matched_str = ", ".join(last_data['matched_ingredients'])
                symptom_str = ", ".join(last_data['symptoms']) if last_data['symptoms'] else "불편함"
                ai_response = f"질문하신 내용과 기록을 대조해 보았을 때, 고객님이 겪으신 **'{symptom_str}'** 증상은 선택하신 문제 제품들과 구매 검토 중인 제품에 공통으로 포함된 **[{matched_str}]** 성분 때문일 가능성이 매우 높습니다. 해당 성분은 피부 장벽을 자극하거나 모공을 밀폐할 수 있으므로, 사용을 자제하시고 진정 성분 위주의 제품을 선택하시는 것을 추천합니다!"
            elif last_data:
                ai_response = f"선택하신 새 제품에는 과거 부작용을 일으킨 주요 특이 성분이 겹치지 않아 비교적 안전합니다. 다만 개인 체질이나 컨디션에 따라 다를 수 있으니 소량 테스트 후 사용하시는 것을 권장합니다."
            else:
                ai_response = "먼저 상단에서 화장품 사진을 등록하시고 [AI 성분 위험도 및 원인 분석 실행] 버튼을 눌러주시면, 데이터를 바탕으로 더 정확한 원인 추적 답변을 드릴 수 있습니다!"
            
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
