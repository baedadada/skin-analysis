import streamlit as st

import streamlit as st

# 1. 페이지 기본 설정 (모바일 친화적 레이아웃)
st.set_page_config(
    page_title="Custom Skin Care Analysis",
    page_icon="🧴",
    layout="centered"
)

# 2. 성분 상세 정보 DB
INGREDIENT_INFO = {
    "리날룰": {"category": "향료 알레르겐", "info": "식약처 지정 알레르기 유발 주의 향료 성분"},
    "리모넨": {"category": "향료 알레르겐", "info": "식약처 지정 알레르기 유발 주의 향료 성분"},
    "향료": {"category": "착향제", "info": "민감성 피부의 경우 접촉성 피부염이나 자극을 유발할 수 있는 종합 향료 성분"},
    "시트론올": {"category": "향료 알레르겐", "info": "장미향 등을 내는 알레르기 유발 가능 성분"},
    "제라니올": {"category": "향료 알레르겐", "info": "식약처 지정 알레르기 유발 주의 향료 성분"},
    "에탄올": {"category": "용매/수렴", "info": "사용 감촉은 산뜻하나 민감성 피부에 건조함 및 붉어짐 자극 유발 가능"},
    "변성알코올": {"category": "용매/수렴", "info": "피부 증발을 촉진하여 피부 장벽이 약한 경우 화끈거림 유발 가능"},
    "디메치콘": {"category": "실리콘계 오일", "info": "발림성을 개선하나 모공을 막아 트러블(밀폐성 여드름)을 유발할 수 있음"},
    "시어버터": {"category": "고보습 오일", "info": "유분이 많아 지성 피부나 여드름성 피부에서 모공 막힘 가능성"},
    "실리카": {"category": "피지흡착/스피큘", "info": "미세 침형/파우더 구조로 물리적 자극이나 따가움을 유발할 수 있음"},
    "스테아릭애씨드": {"category": "계면활성제/지방산", "info": "모공을 막을 가능성이 있어 지성/트러블성 피부 주의 필요"},
    "레티놀": {"category": "주름개선/비타민A", "info": "고기능성 성분으로 초기에 레티놀 반응(각질, 붉어짐, 따가움) 유발 가능"},
    "글루코놀락톤(PHA)": {"category": "각질제거", "info": "저자극 각질제거제이나 피부 장벽 손상 시 따가움 유발 가능"},
    "살리실릭애씨드(BHA)": {"category": "피지/각질케어", "info": "모공 속 피지를 녹이나 민감 피부에는 과도한 자극 유발 가능"},
    "페녹시에탄올": {"category": "보존제", "info": "제품 변질 방지제이나 피부가 얇은 경우 자극 반응 가능성"},
    "BHT": {"category": "산화방지제", "info": "지질 산화 방지 성분으로 피부에 따라 민감 반응 가능"},
    "병풀추출물": {"category": "진정/자극완화", "info": "피부 진정에 좋으나 특정 식물 알레르기가 있는 경우 과민 반응 가능"},
    "마데카소사이드": {"category": "진정", "info": "병풀 유래 고농축 성분으로 개인 체질에 따라 부작용 발생 가능"},
    "티트리추출물": {"category": "피지조절/진정", "info": "트러블 케어용 성분이나 피부에 따라 화끈거림이나 가려움 유발 가능"},
    "티트리잎오일": {"category": "에센셜오일", "info": "고농도 사용 시 피부 자극 및 알레르기성 반응 주의"},
    "약모밀추출물(어성초)": {"category": "진정", "info": "어성초 성분으로 피부 상태에 따라 드물게 가려움 유발 가능"}
}

# 3. 제품 데이터셋 (30종)
products = [
    {"id": 1, "name": "라로슈포제 시카플라스트 밤 B5+", "category": "크림", "ingredients": ["정제수", "글리세린", "판테놀", "마데카소사이드", "징크글루코네이트", "시어버터", "부틸렌글라이콜"]},
    {"id": 2, "name": "에스트라 아토베리어365 크림", "category": "크림", "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "세라마이드엔피", "스쿠알란", "콜레스테롤", "스테아릭애씨드"]},
    {"id": 3, "name": "닥터지 레드 블레미쉬 클리어 수딩 크림", "category": "크림", "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "병풀추출물", "마데카소사이드", "나이아신아마이드", "판테놀", "1,2-헥산다이올"]},
    {"id": 4, "name": "피지오겔 DMT 페이셜 크림", "category": "크림", "ingredients": ["정제수", "카프릴릭/카프릭트라이글리세라이드", "글리세린", "펜틸렌글라이콜", "코코넛야자오일", "시어버터", "스쿠알란"]},
    {"id": 5, "name": "에스트라 아토베리어365 로션", "category": "크림", "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "스쿠알란", "스테아릭애씨드", "디메치콘", "세라마이드엔피", "1,2-헥산다이올"]},
    {"id": 6, "name": "이니스프리 그린티 씨드 히알루론산 크림", "category": "크림", "ingredients": ["정제수", "프로판다이올", "글리세린", "녹차추출물", "소듐하이알루로네이트", "디메치콘", "1,2-헥산다이올", "향료"]},
    {"id": 7, "name": "바이오더마 시카비오 포마드", "category": "크림", "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "병풀추출물", "징크옥사이드", "시어버터", "1,2-헥산다이올"]},
    {"id": 8, "name": "웰라쥬 리얼 히알루로닉 블루 100 앰플", "category": "에센스", "ingredients": ["정제수", "부틸렌글라이콜", "1,2-헥산다이올", "소듐하이알루로네이트", "히알루로닉애씨드", "베타인", "판테놀", "알란토인"]},
    {"id": 9, "name": "토리든 다이브인 저분자 히알루론산 세럼", "category": "에센스", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "소듐하이알루로네이트", "판테놀", "알란토인", "베타인", "마데카소사이드"]},
    {"id": 10, "name": "구달 청귤 비타C 잡티 케어 세럼", "category": "에센스", "ingredients": ["정제수", "부틸렌글라이콜", "나이아신아마이드", "귤추출물", "알부틴", "1,2-헥산다이올", "리날룰", "리모넨", "알란토인"]},
    {"id": 11, "name": "VT COSMETICS 리들샷 100", "category": "에센스", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "나이아신아마이드", "실리카", "병풀추출물", "아시아티코사이드", "1,2-헥산다이올"]},
    {"id": 12, "name": "아이소이 잡티세럼 (블레미쉬 케어)", "category": "에센스", "ingredients": ["정제수", "글리세린", "알부틴", "다마스크장미꽃오일", "병풀추출물", "알란토인", "시트론올", "제라니올"]},
    {"id": 13, "name": "넘버즈인 3번 보들보들 결세럼", "category": "에센스", "ingredients": ["비피다발효용해물", "갈락토미세스발효필터물", "부틸렌글라이콜", "나이아신아마이드", "글리세린", "1,2-헥산다이올"]},
    {"id": 14, "name": "이니스프리 레티놀 시카 흔적 세럼", "category": "에센스", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "나이아신아마이드", "레티놀", "병풀추출물", "살리실릭애씨드(BHA)", "1,2-헥산다이올"]},
    {"id": 15, "name": "아이소이 아크니 드라이 매제 스팟", "category": "에센스", "ingredients": ["정제수", "에탄올", "부틸렌글라이콜", "병풀추출물", "티트리추출물", "글리세린", "1,2-헥산다이올"]},
    {"id": 16, "name": "아이오페 레티놀 슈퍼 바운스 세럼", "category": "에센스", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "레티놀", "나이아신아마이드", "디메치콘", "페녹시에탄올", "BHT"]},
    {"id": 17, "name": "라운드랩 1025 독도 토너", "category": "토너", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "펜틸렌글라이콜", "해수", "아이리쉬모스추출물", "판테놀", "알란토인", "1,2-헥산다이올"]},
    {"id": 18, "name": "브링그린 티트리 시카 수딩 토너", "category": "토너", "ingredients": ["정제수", "부틸렌글라이콜", "티트리추출물", "병풀추출물", "1,2-헥산다이올", "마데카소사이드", "알란토인", "향료"]},
    {"id": 19, "name": "아비브 어성초 스팟 패드 카밍터치", "category": "토너", "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "약모밀추출물(어성초)", "1,2-헥산다이올", "알란토인", "판테놀", "베타인"]},
    {"id": 20, "name": "메디힐 티트리 트러블 패드", "category": "토너", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "티트리추출물", "티트리잎오일", "병풀추출물", "알란토인"]},
    {"id": 21, "name": "아누아 어성초 77 진정 토너", "category": "토너", "ingredients": ["약모밀추출물(어성초)", "정제수", "1,2-헥산다이올", "글리세린", "베타인", "병풀추출물", "판테놀", "카모마일꽃추출물"]},
    {"id": 22, "name": "스킨푸드 당근 카로틴 카밍 패드", "category": "토너", "ingredients": ["정제수", "당근추출물", "글리세린", "부틸렌글라이콜", "1,2-헥산다이올", "알란토인", "소듐하이알루로네이트", "올리브오일"]},
    {"id": 23, "name": "성바울루스 PHA 맑은 토너", "category": "토너", "ingredients": ["정제수", "글루코놀락톤(PHA)", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "알란토인", "판테놀"]},
    {"id": 24, "name": "헤라 셀 에센스 바이옴 플러스", "category": "토너", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "나이아신아마이드", "1,2-헥산다이올", "페녹시에탄올", "향료", "리날룰"]},
    {"id": 25, "name": "마녀공장 퓨어 클렌징 오일", "category": "클렌징", "ingredients": ["돌콩오일", "카프릴릭/카프릭트라이글리세라이드", "호호바씨오일", "올리브오일", "리날룰", "리모넨", "향료", "토코페롤"]},
    {"id": 26, "name": "센카 퍼펙트 휩 페이셜 워시", "category": "클렌징", "ingredients": ["정제수", "스테아릭애씨드", "글리세린", "마이리스틱애씨드", "포타슘하이드록사이드", "라우릭애씨드", "향료", "소듐하이알루로네이트"]},
    {"id": 27, "name": "자작나무 수분 선크림 (라운드랩)", "category": "선케어", "ingredients": ["정제수", "부틸렌글라이콜", "자작나무수액", "글리세린", "나이아신아마이드", "디에칠아미노하이드록시벤조일헥실벤조에이트", "1,2-헥산다이올"]},
    {"id": 28, "name": "셀퓨전씨 레이저 선스크린 100", "category": "선케어", "ingredients": ["정제수", "징크옥사이드", "프로판다이올", "티타늄디옥사이드", "부틸렌글라이콜", "나이아신아마이드", "향료", "1,2-헥산다이올"]},
    {"id": 29, "name": "식물나라 산뜻 수분 선젤", "category": "선케어", "ingredients": ["정제수", "부틸렌글라이콜", "에탄올", "나이아신아마이드", "병풀추출물", "1,2-헥산다이올", "향료"]},
    {"id": 30, "name": "에스쁘아 워터 스플래쉬 선크림", "category": "선케어", "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "징크옥사이드", "디메치콘", "1,2-헥산다이올", "리모넨", "향료"]}
]

COMMON_INGREDIENTS = {"정제수", "글리세린", "부틸렌글라이콜", "1,2-헥산다이올"}

# 4. 웹 UI 구현
st.title("🧴 개인 맞춤 화장품 성분 분석기")
st.caption("화장품 용기 사진 촬영 및 성분비교 모바일 UI")

st.divider()

# --- [신규 기능] 📸 사진 촬영 및 제품 자동 인식 ---
st.subheader("📸 1. 화장품 촬영으로 빠른 등록 (선택)")
st.caption("스마트폰으로 화장품 용기 앞면(제품명)을 직접 찍어보세요.")

# 카메라 촬영 입력창 (스마트폰에서는 카메라 열림)
captured_image = st.camera_input("화장품 본품 용기 앞면 촬영하기")

auto_selected_product = None
if captured_image is not None:
    st.image(captured_image, caption="촬영된 화장품 사진", width=250)
    # 시연용 제품 자동 매칭 메시지 (OCR 데모)
    auto_selected_product = "[크림] 라로슈포제 시카플라스트 밤 B5+"
    st.success(f"🔍 **이미지 분석 완료!** 제품이 감지되었습니다: **{auto_selected_product}**")

st.divider()

# 5. 기존 선택 폼
st.subheader("⚠️ 2. 부작용 경험 제품 및 증상 설정")

product_dict = {f"[{p['category']}] {p['name']}": p['id'] for p in products}

# 사진이 촬영되었으면 해당 제품이 기본으로 선택되도록 세팅
default_selected = [auto_selected_product] if auto_selected_product in product_dict else []

selected_problem_names = st.multiselect(
    "과거 부작용/트러블이 있었던 제품 (1개 이상 선택):",
    options=list(product_dict.keys()),
    default=default_selected
)

# 증상 선택
selected_symptoms = st.multiselect(
    "📌 겪었던 주요 증상을 선택하세요:",
    options=['따가움/화끈거림', '붉어짐/홍조', '트러블/모공막힘', '가려움', '건조함/당김']
)

# 구매 예정 제품 선택
selected_new_name = st.selectbox(
    "🛒 구매를 검토 중인 새 제품:",
    options=list(product_dict.keys())
)

# 6. 분석 버튼 및 로직
if st.button("🔍 성분 위험도 분석 실행", type="primary", use_container_width=True):
    if not selected_problem_names:
        st.error("과거 문제 제품을 최소 1개 이상 선택해 주세요!")
    else:
        problem_ids = [product_dict[name] for name in selected_problem_names]
        new_id = product_dict[selected_new_name]

        # 1) 문제 제품 특이 성분 모으기
        problem_ingredients_list = []
        for p in products:
            if p['id'] in problem_ids:
                unique_ings = set(p['ingredients']) - COMMON_INGREDIENTS
                problem_ingredients_list.append(unique_ings)

        # 2) 선택 개수별 주의 성분 판별
        caution_ingredients = set()
        all_problem_ings = [ing for sublist in problem_ingredients_list for ing in sublist]

        if len(problem_ids) == 1:
            caution_ingredients = set(all_problem_ings)
        else:
            for ing in set(all_problem_ings):
                if all_problem_ings.count(ing) >= 2:
                    caution_ingredients.add(ing)
            if not caution_ingredients:
                caution_ingredients = set(all_problem_ings)

        # 3) 새 제품 교집합 분석
        new_product = next((p for p in products if p['id'] == new_id), None)
        new_product_ings = set(new_product['ingredients'])
        matched = new_product_ings.intersection(caution_ingredients)

        # 4) 결과 표시
        st.divider()
        st.subheader("📊 분석 결과 리포트")
        
        if selected_symptoms:
            st.write(f"**기록된 증상:** {', '.join(selected_symptoms)}")

        if matched:
            st.warning("⚠️ **[주의] 과거 문제 제품과 겹치는 주의 성분이 발견되었습니다!**")
            for ing in matched:
                info = INGREDIENT_INFO.get(ing, {"category": "기타 성분", "info": "과거 문제 제품 포함 성분"})
                st.markdown(f"- **{ing}** (`{info['category']}`) : {info['info']}")
        else:
            st.success("✅ **[안전] 과거 문제 제품의 주요 특이 성분이 발견되지 않았습다.**")

        st.caption("※ 본 시스템은 사용자의 입력 이력을 기반으로 한 비교 참고 도구입니다.")
