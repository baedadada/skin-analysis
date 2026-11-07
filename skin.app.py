화장품 뒷면 전성분 라벨 사진(3번 탭)을 찍어 분석할 때 결과가 **지나치게 늦게 나오는 이유**는 딥러닝 모델의 특성과 API 처리 구조 때문입니다. 원인과 해결 방법을 알기 쉽게 정리해 드리고, 속도를 최적화한 코드를 안내해 드릴게요!

---

### 🔍 왜 결과가 늦게 나올까요? (원인 분석)

1. **고해상도 이미지 전송 대기 시간 (Network & Payload):**
* 스마트폰이나 카메라로 촬영한 화장품 뒷면 사진은 보통 용량이 매우 큽니다(수 메가바이트 이상). 이 큰 이미지 파일을 인터넷을 통해 구글의 Gemini 서버로 전송하는 데만 상당한 시간이 소요됩니다.


2. **멀티모달 Vision AI의 텍스트 밀도 높은 분석:**
* 화장품 뒷면은 글씨가 아주 작고 빽빽하게 적혀 있습니다. Gemini 비전 모델이 이 수많은 글자를 하나하나 시각적으로 해독(OCR + 자연어 분석)하고 전성분 목록을 정리하는 과정은 일반 텍스트 대화보다 계산량이 훨씬 많아 처리 시간이 수 초~십여 초 이상 걸립니다.


3. **불필요한 고성능 모델 파라미터 호출:**
* 가벼운 성분 매칭이나 텍스트 분석에 비해 이미지 분석 요청은 네트워크 환경에 따라 응답 지연이 눈에 띄게 체감됩니다.



---

### 🛠️ 어떻게 해결했나요? (속도 최적화 코드 적용 포인트)

이미지 분석 속도를 대폭 개선하기 위해 코드에 아래와 같은 **최적화 조치**를 적용했습니다.

1. **이미지 자동 압축 및 리사이징 (`PIL` 활용):**
* 업로드된 무거운 사진을 서버로 보내기 전에 **최대 가로/세로 800픽셀 크기로 자동 압축**시킵니다. 전송 용량이 수십 배 줄어들기 때문에 서버로 업로드되고 응답을 받는 속도가 눈에 띄게 빨라집니다.


2. **프롬프트 경량화:**
* AI가 불필요한 수식어 없이 전성분 이름만 빠르게 쉼표로 뱉어내도록 프롬프트를 간결하게 수정하여 연산 시간을 단축했습니다.



---

### 💻 속도가 최적화된 최종 `app.py` 전체 코드

프로젝트 폴더 내의 **`app.py`** 파일을 아래 코드로 완전히 덮어씌워 주시면 훨씬 쾌적하고 빠른 속도로 비전 분석을 이용하실 수 있습니다.

```python
import streamlit as st
import pandas as pd
from PIL import Image
import re
import google.generativeai as genai
import time

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

# 1. 데이터 로드 (products.csv 및 ingredients.csv - 세미콜론 ; 구분 파싱)
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
            'ingredients': [i.strip() for i in str(row['ingredients']).split(';') if i.strip()]
        })
        
    ing_info_dict = {}
    for _, row in ingredients_df.iterrows():
        ing_name = str(row['ingredient']).strip()
        ing_info_dict[ing_name] = {
            'category': str(row.get('category', '주요 성분')),
            'purpose': str(row.get('purpose', '피부 케어 및 제형 유지')),
            'benefits': str(row.get('benefits', '피부 상태 개선')),
            'side_effects': str(row.get('side_effects', '개인 컨디션 및 체질에 따른 민감 자극 가능성'))
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

# 3. 페이지 설정 및 짙은 네이비 톤 CSS
st.set_page_config(page_title="DermaSafe Rx | AI 피부 맞춤 처방전", page_icon="🩺", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 상단 히어로 배너 */
    .hero-container {
        background: linear-gradient(135deg, #0F2C59 0%, #1E3A8A 100%);
        color: white;
        padding: 32px 25px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(15, 44, 89, 0.2);
    }
    
    /* 🩺 처방전 메인 카드 스타일 */
    .prescription-medical-card {
        background-color: #FFFFFF;
        border: 2px solid #2563EB;
        border-radius: 20px;
        padding: 35px;
        box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.1);
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    /* 처방전 헤더 라인 */
    .rx-header {
        border-bottom: 2px dashed #CBD5E1;
        padding-bottom: 15px;
        margin-bottom: 20px;
    }

    /* 구매 판정 배너 */
    .verdict-badge-danger {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FCA5A5;
        padding: 14px 20px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 15px;
        text-align: center;
        margin-bottom: 24px;
    }
    .verdict-badge-safe {
        background-color: #F0FDF4;
        color: #16A34A;
        border: 1px solid #86EFAC;
        padding: 14px 20px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 15px;
        text-align: center;
        margin-bottom: 24px;
    }

    /* 성분 세부 분석 카드 */
    .ingredient-detail-card {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    .ing-title {
        color: #0F2C59;
        font-size: 16px;
        font-weight: 800;
    }
    .ing-badge {
        background-color: #E0F2FE;
        color: #0284C7;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        margin-left: 6px;
    }
    .ing-row {
        margin-top: 6px;
        font-size: 14px;
        line-height: 1.6;
        color: #334155;
    }

    /* 초록색 세이프 가이드 박스 */
    .guide-box {
        background-color: #F0FDF4;
        border: 1px solid #86EFAC;
        border-radius: 12px;
        padding: 18px 20px;
        margin-top: 24px;
        font-size: 14px;
        color: #166534;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# 헤더 배너
st.markdown("""
    <div class="hero-container">
        <h1 style="margin:0; font-size:28px; font-weight:800; color:#FFFFFF;">🩺 DermaSafe Rx</h1>
        <p style="margin:6px 0 0 0; color:#93C5FD; font-size:14px;">개인 부작용 이력 기반 AI 피부 자극 예측 & 정밀 성분 처방 솔루션</p>
    </div>
""", unsafe_allow_html=True)

# 공통 제품 딕셔너리
product_dict = {f"[{p['category']}] {p['name']}": p['id'] for p in products}

# 🎛️ 상단 탭
st.subheader("🔍 피부 진단 조건 설정")
st.caption("원하시는 방식을 선택하여 제품을 지정해 주세요.")

main_tab1, main_tab2, main_tab3 = st.tabs([
    "📸 1. 제품 사진/카메라 등록", 
    "🛒 2. 목록에서 직접 선택", 
    "🏷️ 3. 화장품 뒷면 전성분 라벨 스캔 (AI Vision)"
])

detected_from_cam = None

with main_tab1:
    st.markdown("##### 🖼️ 과거 자극을 주었던 제품의 사진을 업로드하거나 촬영해 주세요.")
    cam_sub1, cam_sub2 = st.tabs(["파일 업로드", "실시간 카메라"])
    
    with cam_sub1:
        up_file = st.file_uploader("사진 파일 선택", type=["jpg", "jpeg", "png"], key="uploader_cam")
        if up_file:
            st.image(up_file, width=220, caption="등록된 제품 사진")
            matched, _ = match_product_from_image(up_file)
            if matched:
                detected_from_cam = matched
                st.success(f"🎉 자동 인식된 제품: **{matched}**")
            else:
                st.warning("사진에서 일치하는 제품을 찾지 못했습니다.")

    with cam_sub2:
        cap_img = st.camera_input("제품 정면 촬영", key="camera_cam")
        if cap_img:
            matched, _ = match_product_from_image(cap_img)
            if matched:
                detected_from_cam = matched
                st.success(f"🎉 자동 인식된 제품: **{matched}**")
            else:
                st.warning("촬영된 이미지에서 제품을 인식하지 못했습니다.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📋 진단 세부 조건 입력")
    cam_symptoms = st.multiselect(
        "📌 과거 경험한 주요 증상:",
        options=['따가움/화끈거림', '붉어짐/홍조', '트러블/모공막힘/좁쌀', '가려움', '건조함/각질/당김', '눈시림'],
        key="cam_sym"
    )
    cam_new_name = st.selectbox(
        "🛒 구매 검토 중인 새 제품 선택:",
        options=list(product_dict.keys()),
        key="cam_new"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    cam_triggered = st.button("🩺 정밀 처방전 카드 발급받기", type="primary", use_container_width=True, key="btn_cam")

with main_tab2:
    st.markdown("##### 📝 데이터베이스 목록에서 문제 제품과 새 제품을 직접 지정합니다.")
    
    dir_problem_names = st.multiselect(
        "⚠️ 과거 트러블 유발 제품 선택:",
        options=list(product_dict.keys()),
        key="dir_prob"
    )
    dir_symptoms = st.multiselect(
        "📌 과거 경험한 주요 증상:",
        options=['따가움/화끈거림', '붉어짐/홍조', '트러블/모공막힘/좁쌀', '가려움', '건조함/각질/당김', '눈시림'],
        key="dir_sym"
    )
    dir_new_name = st.selectbox(
        "🛒 구매 검토 중인 새 제품 선택:",
        options=list(product_dict.keys()),
        key="dir_new"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    dir_triggered = st.button("🩺 정밀 처방전 카드 발급받기", type="primary", use_container_width=True, key="btn_dir")

with main_tab3:
    st.markdown("##### 🏷️ 데이터베이스에 없는 신제품도 화장품 뒷면 '전성분 표기 라벨'을 찍어 올리면 AI가 즉시 분석합니다!")
    vision_file = st.file_uploader("화장품 뒷면 전성분 라벨 사진 업로드", type=["jpg", "jpeg", "png"], key="vision_uploader")
    
    v_col1, v_col2 = st.columns(2, gap="medium")
    with v_col1:
        vision_problem_names = st.multiselect(
            "⚠️ 과거 트러블 유발 제품 선택:",
            options=list(product_dict.keys()),
            key="vision_prob"
        )
        vision_symptoms = st.multiselect(
            "📌 과거 경험한 주요 증상:",
            options=['따가움/화끈거림', '붉어짐/홍조', '트러블/모공막힘/좁쌀', '가려움', '건조함/각질/당김', '눈시림'],
            key="vision_sym"
        )
    with v_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        vision_triggered = st.button("✨ AI 멀티모달 비전 라벨 정밀 분석", type="primary", use_container_width=True, key="btn_vision")

# 어떤 탭이 실행되었는지 판정
is_cam = cam_triggered
is_dir = 'dir_triggered' in locals() and dir_triggered
is_vision = 'vision_triggered' in locals() and vision_triggered

analysis_triggered = is_cam or is_dir or is_vision

if is_cam:
    used_problem_names = [detected_from_cam] if detected_from_cam and detected_from_cam in product_dict else []
    used_symptoms = cam_symptoms
    used_new_name = cam_new_name
    analysis_mode = "db"
elif is_dir:
    used_problem_names = dir_problem_names
    used_symptoms = dir_symptoms
    used_new_name = dir_new_name
    analysis_mode = "db"
elif is_vision:
    used_problem_names = vision_problem_names
    used_symptoms = vision_symptoms
    used_new_name = "AI 비전 라벨 스캔 제품 (신규)"
    analysis_mode = "vision"
else:
    analysis_triggered = False

# 📋 진단서 / 처방전 카드 형태 출력
if analysis_triggered:
    if is_cam and not detected_from_cam:
        st.error("먼저 카메라나 사진 업로드를 통해 제품을 인식시켜 주세요!")
    elif (is_dir or is_vision) and not used_problem_names:
        st.error("과거 부작용을 경험했던 제품을 최소 1개 이상 지정해 주세요!")
    elif is_vision and not vision_file:
        st.error("분석할 화장품 뒷면 전성분 라벨 사진을 업로드해 주세요!")
    else:
        problem_ids = [product_dict[name] for name in used_problem_names]
        problem_ings = [set(p['ingredients']) - COMMON_INGREDIENTS for p in products if p['id'] in problem_ids]
        all_ings = [ing for sub in problem_ings for ing in sub]
        caution_ings = set(all_ings) if len(problem_ids) == 1 else {ing for ing in set(all_ings) if all_ings.count(ing) >= 2} or set(all_ings)

        if analysis_mode == "db":
            new_id = product_dict[used_new_name]
            new_product_ings = set(next(p for p in products if p['id'] == new_id)['ingredients'])
            matched = new_product_ings.intersection(caution_ings)
            scanned_ingredients_text = "기존 데이터베이스 매칭 완료"
        else:
            # 🚀 [속도 최적화 적용] Gemini Vision API 호출 전 이미지 압축 및 리사이징
            with st.spinner("🤖 AI가 전성분 라벨을 고속 스캔 및 대조 중입니다... (잠시만 기다려주세요)"):
                try:
                    api_key = st.secrets.get("GEMINI_API_KEY", None)
                    if not api_key:
                        st.error("⚠️ API Key가 필요합니다.")
                        st.stop()
                    genai.configure(api_key=api_key)
                    vision_model = genai.GenerativeModel('gemini-3.8-flash')
                    
                    # 이미지 열기 및 리사이징 (최대 800픽셀로 줄여서 업로드 속도 극대화)
                    img = Image.open(vision_file)
                    img.thumbnail((800, 800))
                    
                    prompt = "화장품 뒷면 전성분 라벨 사진입니다. 포함된 성분 이름들을 쉼표(,)로 구분해서 빠르게 나열해 줘."
                    response = vision_model.generate_content([prompt, img])
                    extracted_text = response.text
                    
                    extracted_list = [s.strip() for s in extracted_text.replace('\n', ',').split(',') if s.strip()]
                    scanned_ingredients_text = ", ".join(extracted_list[:15]) + (" 외 다수" if len(extracted_list) > 15 else "")
                    
                    new_product_ings = set(extracted_list)
                    matched = new_product_ings.intersection(caution_ings)
                except Exception as e:
                    st.error(f"비전 분석 중 오류 발생: {str(e)}")
                    st.stop()

        st.markdown("---")
        
        symptoms_str = ', '.join(used_symptoms) if used_symptoms else '지정 없음'
        
        if matched:
            verdict_html = '<div class="verdict-badge-danger">🚨 [구매 신중 권장] 과거 자극 경험 성분과 교집합이 확인되었습니다. 패치 테스트 후 사용을 권합니다.</div>'
            verdict_text = "[구매 신중 권장] 과거 자극 경험 성분과 교집합이 확인되었습니다."
        else:
            verdict_html = '<div class="verdict-badge-safe">✨ [구매 적합 판정] 과거 부작용 유발 성분이 포함되어 있지 않아 비교적 안심하고 사용 가능합니다.</div>'
            verdict_text = "[구매 적합 판정] 과거 부작용 유발 성분이 포함되어 있지 않습니다."

        ingredients_html = ""
        ingredients_text_list = []
        if matched:
            ingredients_html += "<h4 style='color:#0F2C59; margin-top:15px;'>🔬 감지된 공통 성분별 정밀 분석 리포트</h4>"
            for ing in matched:
                info = INGREDIENT_INFO.get(ing, {
                    'category': '기능성 성분',
                    'purpose': '피부 케어 및 제형 유지',
                    'benefits': '피부 유효 성분 전달',
                    'side_effects': '⚠️ 개인 컨디션 및 체질에 따른 민감 자극 가능성'
                })
                ingredients_html += (
                    f'<div class="ingredient-detail-card">'
                    f'<div><span class="ing-title">🧪 {ing}</span> <span class="ing-badge">{info["category"]}</span></div>'
                    f'<div class="ing-row">🎯 <b>배합 목적:</b> {info["purpose"]}</div>'
                    f'<div class="ing-row" style="color: #047857;">✨ <b>주요 효능:</b> {info["benefits"]}</div>'
                    f'<div class="ing-row" style="color: #B91C1C; font-weight: 600;">⚠️ <b>주의점 및 부작용:</b> {info["side_effects"]}</div>'
                    f'</div>'
                )
                ingredients_text_list.append(f"- {ing} ({info['category']}): 목적({info['purpose']}) / 주의점({info['side_effects']})")
        else:
            ingredients_html += "<p style='color:#64748B;'>💡 과거 자극 유발 제품의 주요 성분이 새 제품에서 발견되지 않았습니다.</p>"

        alternative_html = ""
        if matched:
            alternative_html = (
                '<div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 18px 20px; margin-top: 20px; font-size: 14px; color: #1E3A8A; line-height: 1.6;">'
                '<b style="color: #1D4ED8; font-size: 15px;">💡 AI 맞춤형 대체 성분 & 케어 솔루션</b><br><br>'
                f'위험 성분으로 감지된 <b>{", ".join(matched)}</b> 성분 대신, 피부 진정과 보습에 도움을 주는 <b>판테놀, 알란토인, 히알루론산</b> 등이 함유된 순한 대체 제품군(예: 시카 밤, 무향 진정 토너)을 선택하시는 것을 추천해 드립니다.'
                '</div>'
            )

        guide_html = (
            '<div class="guide-box">'
            '<b style="color: #15803D; font-size: 15px;">🌿 세이프가드 마일드 케어 처방 가이드</b><br><br>'
            '1. <b>부드러운 휴식 권장:</b> 피부에 일시적인 불편함이나 자극이 느껴지신다면, 의심되는 제품의 사용을 잠시 멈추고 피부가 숨을 고를 수 있도록 여유를 주시는 것을 권해드립니다.<br><br>'
            '2. <b>진정 중심 루틴:</b> 장벽이 편안해질 때까지 자극적인 기능성 제품을 피하고 순한 보습 위주로 케어해 보세요.<br><br>'
            '3. <b>전문가 상담:</b> 불편함이 가라앉지 않고 지속될 경우 피부과 전문의와 정밀한 상담을 받아보시는 것을 조심스럽게 권장합니다.'
            '</div>'
        )

        final_card_html = (
            f'<div class="prescription-medical-card">'
            f'<div class="rx-header">'
            f'<h2 style="color:#0F2C59; margin:0; font-size:20px; font-weight:800;">📋 DERMASAFE MEDICAL PRESCRIPTION REPORT</h2>'
            f'<p style="color:#64748B; margin:4px 0 0 0; font-size:13px;">발급 기관: AI Clinical Preventive Skin Safeguard System</p>'
            f'</div>'
            f'<p style="margin:5px 0;"><b>검토 대상 제품:</b> {used_new_name}</p>'
            f'<p style="margin:5px 0 0 0;"><b>호소 이력 증상:</b> {symptoms_str}</p>'
            f'<p style="margin:5px 0 0 0; color:#475569; font-size:13px;"><b>전성분 분석 정보:</b> {scanned_ingredients_text}</p><br>'
            f'{verdict_html}'
            f'{ingredients_html}'
            f'{alternative_html}'
            f'{guide_html}'
            f'</div>'
        )
        
        st.markdown(final_card_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        report_txt = f"""==================================================
 [DERMASAFE Rx] MEDICAL SKIN PRESCRIPTION REPORT
==================================================
- 발급 기관: AI Clinical Preventive Skin Safeguard System
- 검토 대상 제품: {used_new_name}
- 호소 이력 증상: {symptoms_str}
- 구매 판정 결과: {verdict_text}

[감지된 주의 성분 분석]
{"\n".join(ingredients_text_list) if ingredients_text_list else "감지된 위험 성분 없음 (안심 사용 가능)"}

[AI 맞춤형 대체 성분 추천 가이드]
- 자극 성분 회피 및 판테놀, 알란토인, 히알루론산 중심의 순한 진정/보습 제품 선택 권장

[세이프가드 마일드 케어 가이드]
1. 부드러운 휴식 권장: 의심되는 제품 사용 중단 및 피부 휴식
2. 진정 중심 루틴: 자극적인 기능성 제품 피하고 순한 보습 케어
3. 전문가 상담: 지속적인 불편함 시 피부과 전문의 상담 권장
=================================================="""

        st.download_button(
            label="📥 메디컬 처방전 리포트 문서 다운로드 (TXT)",
            data=report_txt,
            file_name="DermaSafe_Rx_Prescription_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.session_state['last_analysis'] = {
            "problem_products": used_problem_names,
            "symptoms": used_symptoms,
            "new_product": used_new_name,
            "matched_ingredients": list(matched)
        }

# 💬 AI 상담 챗봇
st.markdown("<br><hr><br>", unsafe_allow_html=True)
st.subheader("💬 AI 피부 전문 코디네이터 상담")
st.caption("처방전 결과나 성분에 대해 궁금한 점을 자유롭게 물어보세요.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! DermaSafe Rx AI 코디네이터입니다. 처방전 발급 후 궁금하신 점을 말씀해 주세요."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("예: 이 성분 대신 쓸 수 있는 자극 없는 성분 추천해줘"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("AI가 처방 데이터와 성분 프로필을 분석 중입니다..."):
            api_key = st.secrets.get("GEMINI_API_KEY", None)
            if not api_key:
                ai_response = "⚠️ **[API Key 필요]** Secrets에 `GEMINI_API_KEY`를 설정해 주세요."
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3.8-flash')
                    last_data = st.session_state.get('last_analysis', {})
                    
                    context_prompt = (
                        "너는 DermaSafe Rx의 전문 피부과 AI 코디네이터야.\n"
                        f"- 문제 제품: {last_data.get('problem_products', '없음')}\n"
                        f"- 증상: {last_data.get('symptoms', '없음')}\n"
                        f"- 새 제품: {last_data.get('new_product', '없음')}\n"
                        f"- 겹치는 성분: {last_data.get('matched_ingredients', '없음')}\n\n"
                        f"사용자 질문: \"{user_input}\"\n"
                        "⚠️ 지침: 무조건 성분 탓으로 단정하지 말고 부드럽고 객관적으로 설명해 줘. "
                        "단호하게 지시하기보다 '사용을 잠시 멈추고 피부에 휴식을 주시는 것을 권해드립니다'와 같이 정중한 어조로 조언해 줘."
                    )
                    response = model.generate_content(context_prompt)
                    ai_response = response.text
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "Quota exceeded" in err_msg:
                        ai_response = "⚠️ **[요청 한도 초과 안내]** 무료 API 사용량(분당 5회 요청 제한)을 초과했습니다. 약 50초 정도 잠시 숨을 고르신 후 다시 질문해 주세요! ☕"
                    else:
                        ai_response = f"⚠️ AI 응답 중 오류가 발생했습니다: {err_msg}"
            
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})

# 하단 푸터
st.markdown("""
    <br><br>
    <div style="text-align: center; color: #94A3B8; font-size: 12px; padding: 20px 0; border-top: 1px solid #E2E8F0;">
        © 2026 DermaSafe Rx. All rights reserved. | AI-Powered Preventive Skin Safeguard Platform
    </div>
""", unsafe_allow_html=True)

```
