import streamlit as st
from PIL import Image
import re

# EasyOCR 라이브러리 예외 처리 및 로드
try:
    import easyocr
    import numpy as np
    @st.cache_resource
    def load_ocr_reader():
        # 한글(ko)과 영어(en) 인식 모델 동시 로드
        return easyocr.Reader(['ko', 'en'], gpu=False)
    ocr_reader = load_ocr_reader()
    HAS_OCR = True
except Exception:
    HAS_OCR = False

# 1. 페이지 기본 설정 (모바일 친화적)
st.set_page_config(
    page_title="Custom Skin Care Analysis",
    page_icon="🧴",
    layout="centered"
)

# 2. 고도화된 위험/주의 성분 상세 DB
INGREDIENT_INFO = {
    # 향료 및 알레르겐
    "리날룰": {"category": "향료 알레르겐", "info": "식약처 지정 알레르기 유발 주의 향료 성분"},
    "리모넨": {"category": "향료 알레르겐", "info": "식약처 지정 알레르기 유발 주의 향료 성분"},
    "향료": {"category": "착향제", "info": "민감성 피부 접촉성 피부염, 자극 유발 가능"},
    "시트론올": {"category": "향료 알레르겐", "info": "장미향 유발 성분, 알레르기 반응 주의"},
    "제라니올": {"category": "향료 알레르겐", "info": "식약처 지정 알레르기 유발 주의 성분"},
    "시트랄": {"category": "향료 알레르겐", "info": "시트러스계 향료, 피부 접촉성 알레르기 유발 가능"},
    "벤질알코올": {"category": "향료/보존제", "info": "고농도 시 피부 자극 및 알레르기 유발 가능"},

    # 알코올/용매류
    "에탄올": {"category": "용매/수렴", "info": "피부 수분 증발 촉진, 민감성 피부 붉어짐 및 건조 유발"},
    "변성알코올": {"category": "용매/수렴", "info": "장벽이 약한 피부에 화끈거림 및 따가움 유발"},
    "아이소프로필알코올": {"category": "용매", "info": "피부 탈수 및 강한 자극 반응 가능성"},

    # 모공 막힘 (코메도제닉) 및 실리콘계
    "디메치콘": {"category": "실리콘계 오일", "info": "발림성을 높이나 모공 밀폐로 인한 트러블 유발 가능"},
    "시어버터": {"category": "고보습 오일", "info": "지성/여드름성 피부에서 모공 막힘 가능성 높음"},
    "스테아릭애씨드": {"category": "지방산", "info": "모공을 막아 좁쌀 여드름 유발 가능성"},
    "코코넛야자오일": {"category": "고보습 오일", "info": "코메도제닉 지수가 높아 트러블 유발 위험"},
    "미리스틱애씨드": {"category": "지방산/세정", "info": "지성 피부 모공 자극 및 트러블 유발 위험"},
    "팔미틱애씨드": {"category": "지방산", "info": "모공 자극 및 밀폐성 트러블 유발 가능성"},

    # 특수 케어/물리적 자극 성분
    "실리카": {"category": "스피큘/피지흡착", "info": "미세 입자 자극으로 따가움 및 붉어짐 유발"},
    "레티놀": {"category": "비타민A계열", "info": "초기 각질 탈락, 따가움, 붉어짐(레티놀 반응) 유발"},
    "글루코놀락톤(PHA)": {"category": "각질제거", "info": "약산성 각질제거제나 장벽 손상 시 따가움 유발"},
    "살리실릭애씨드(BHA)": {"category": "피지/각질케어", "info": "모공 케어 성분이나 민감 피부 과도한 건조 및 자극"},
    "글리콜릭애씨드(AHA)": {"category": "각질제거", "info": "산성도가 높아 민감성 피부에 강한 자극/따가움 유발"},
    "락틱애씨드(AHA)": {"category": "각질제거", "info": "피부 각질을 용해하며 화끈거림 유발 가능"},

    # 보존제 및 자외선 차단 성분
    "페녹시에탄올": {"category": "보존제", "info": "피부 민감도에 따라 유착성 자극 유발"},
    "메틸파라벤": {"category": "보존제", "info": "파라벤계 보존제로 피부 알레르기 유발 가능성"},
    "프로필파라벤": {"category": "보존제", "info": "피부 자극 및 알레르기 반응 유발 가능성"},
    "BHT": {"category": "산화방지제", "info": "지질 산화 방지제로 민감 피부 반응 주의"},
    "벤조페논-3": {"category": "자외선차단", "info": "유기 자차 성분으로 눈시림 및 피부 자극 유발"},
    "에칠헥실메톡시신나메이트": {"category": "자외선차단", "info": "민감성 피부 접촉성 피부염 유발 가능"},

    # 진정/천연 오일류
    "병풀추출물": {"category": "진정", "info": "식물 추출물 특성상 특정 체질에 알레르기 유발 가능"},
    "마데카소사이드": {"category": "진정", "info": "고농축 진정 성분이나 체질별 과민 반응 가능"},
    "티트리추출물": {"category": "피지케어", "info": "트러블 케어 성분이나 화끈거림 유발 가능"},
    "티트리잎오일": {"category": "에센셜오일", "info": "고농도 자극 및 알레르기성 반응 주의"},
    "라벤더오일": {"category": "에센셜오일", "info": "천연 향료 성분으로 접촉성 피부염 유발 가능"},
    "약모밀추출물(어성초)": {"category": "진정", "info": "피부 상태에 따라 드물게 가려움 유발 가능"}
}

# 3. 제품 데이터셋 (50종 확장 + 영문/한글 검색 키워드 포함)
products = [
    {"id": 1, "name": "라로슈포제 시카플라스트 밤 B5+", "category": "크림", "keywords": ["larocheposay", "laroche", "cicaplast", "baume", "b5", "라로슈포제", "시카플라스트"], "ingredients": ["정제수", "글리세린", "판테놀", "마데카소사이드", "징크글루코네이트", "시어버터", "부틸렌글라이콜"]},
    {"id": 2, "name": "에스트라 아토베리어365 크림", "category": "크림", "keywords": ["aestura", "atobarrier", "365", "cream", "에스트라", "아토베리어"], "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "세라마이드엔피", "스쿠알란", "콜레스테롤", "스테아릭애씨드"]},
    {"id": 3, "name": "닥터지 레드 블레미쉬 클리어 수딩 크림", "category": "크림", "keywords": ["drg", "dr.g", "red", "blemish", "clear", "soothing", "닥터지", "블레미쉬"], "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "병풀추출물", "마데카소사이드", "나이아신아마이드", "판테놀", "1,2-헥산다이올"]},
    {"id": 4, "name": "피지오겔 DMT 페이셜 크림", "category": "크림", "keywords": ["physiogel", "dmt", "facial", "cream", "피지오겔"], "ingredients": ["정제수", "카프릴릭/카프릭트라이글리세라이드", "글리세린", "펜틸렌글라이콜", "코코넛야자오일", "시어버터", "스쿠알란"]},
    {"id": 5, "name": "에스트라 아토베리어365 로션", "category": "크림", "keywords": ["aestura", "atobarrier", "365", "lotion", "에스트라", "로션"], "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "스쿠알란", "스테아릭애씨드", "디메치콘", "세라마이드엔피", "1,2-헥산다이올"]},
    {"id": 6, "name": "이니스프리 그린티 씨드 히알루론산 크림", "category": "크림", "keywords": ["innisfree", "greentea", "seed", "hyaluronic", "이니스프리", "그린티"], "ingredients": ["정제수", "프로판다이올", "글리세린", "녹차추출물", "소듐하이알루로네이트", "디메치콘", "1,2-헥산다이올", "향료"]},
    {"id": 7, "name": "바이오더마 시카비오 포마드", "category": "크림", "keywords": ["bioderma", "cicabio", "pommade", "바이오더마", "시카비오"], "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "병풀추출물", "징크옥사이드", "시어버터", "1,2-헥산다이올"]},
    {"id": 8, "name": "웰라쥬 리얼 히알루로닉 블루 100 앰플", "category": "에센스", "keywords": ["wellage", "real", "hyaluronic", "blue", "100", "ampoule", "웰라쥬"], "ingredients": ["정제수", "부틸렌글라이콜", "1,2-헥산다이올", "소듐하이알루로네이트", "히알루로닉애씨드", "베타인", "판테놀", "알란토인"]},
    {"id": 9, "name": "토리든 다이브인 저분자 히알루론산 세럼", "category": "에센스", "keywords": ["torriden", "divein", "serum", "토리든", "다이브인"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "소듐하이알루로네이트", "판테놀", "알란토인", "베타인", "마데카소사이드"]},
    {"id": 10, "name": "구달 청귤 비타C 잡티 케어 세럼", "category": "에센스", "keywords": ["goodal", "green", "tangerine", "vitac", "serum", "구달", "청귤"], "ingredients": ["정제수", "부틸렌글라이콜", "나이아신아마이드", "귤추출물", "알부틴", "1,2-헥산다이올", "리날룰", "리모넨", "알란토인"]},
    {"id": 11, "name": "VT COSMETICS 리들샷 100", "category": "에센스", "keywords": ["vt", "reedle", "shot", "100", "리들샷"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "나이아신아마이드", "실리카", "병풀추출물", "아시아티코사이드", "1,2-헥산다이올"]},
    {"id": 12, "name": "아이소이 잡티세럼 (블레미쉬 케어)", "category": "에센스", "keywords": ["isoi", "blemish", "care", "serum", "아이소이", "잡티세럼"], "ingredients": ["정제수", "글리세린", "알부틴", "다마스크장미꽃오일", "병풀추출물", "알란토인", "시트론올", "제라니올"]},
    {"id": 13, "name": "넘버즈인 3번 보들보들 결세럼", "category": "에센스", "keywords": ["numbuzin", "no3", "number3", "serum", "넘버즈인", "결세럼"], "ingredients": ["비피다발효용해물", "갈락토미세스발효필터물", "부틸렌글라이콜", "나이아신아마이드", "글리세린", "1,2-헥산다이올"]},
    {"id": 14, "name": "이니스프리 레티놀 시카 흔적 세럼", "category": "에센스", "keywords": ["innisfree", "retinol", "cica", "serum", "이니스프리", "레티놀"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "나이아신아마이드", "레티놀", "병풀추출물", "살리실릭애씨드(BHA)", "1,2-헥산다이올"]},
    {"id": 15, "name": "아이소이 아크니 드라이 매제 스팟", "category": "에센스", "keywords": ["isoi", "acni", "spot", "아이소이", "아크니"], "ingredients": ["정제수", "에탄올", "부틸렌글라이콜", "병풀추출물", "티트리추출물", "글리세린", "1,2-헥산다이올"]},
    {"id": 16, "name": "아이오페 레티놀 슈퍼 바운스 세럼", "category": "에센스", "keywords": ["iope", "retinol", "super", "bounce", "serum", "아이오페"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "레티놀", "나이아신아마이드", "디메치콘", "페녹시에탄올", "BHT"]},
    {"id": 17, "name": "라운드랩 1025 독도 토너", "category": "토너", "keywords": ["roundlab", "1025", "dokdo", "toner", "라운드랩", "독도"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "펜틸렌글라이콜", "해수", "아이리쉬모스추출물", "판테놀", "알란토인", "1,2-헥산다이올"]},
    {"id": 18, "name": "브링그린 티트리 시카 수딩 토너", "category": "토너", "keywords": ["bringgreen", "teatree", "cica", "toner", "브링그린"], "ingredients": ["정제수", "부틸렌글라이콜", "티트리추출물", "병풀추출물", "1,2-헥산다이올", "마데카소사이드", "알란토인", "향료"]},
    {"id": 19, "name": "아비브 어성초 스팟 패드 카밍터치", "category": "토너", "keywords": ["abib", "heartleaf", "spot", "pad", "아비브", "어성초"], "ingredients": ["정제수", "글리세린", "부틸렌글라이콜", "약모밀추출물(어성초)", "1,2-헥산다이올", "알란토인", "판테놀", "베타인"]},
    {"id": 20, "name": "메디힐 티트리 트러블 패드", "category": "토너", "keywords": ["mediheal", "teatree", "trouble", "pad", "메디힐"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "티트리추출물", "티트리잎오일", "병풀추출물", "알란토인"]},
    {"id": 21, "name": "아누아 어성초 77 진정 토너", "category": "토너", "keywords": ["anua", "heartleaf", "77", "toner", "아누아", "어성초"], "ingredients": ["약모밀추출물(어성초)", "정제수", "1,2-헥산다이올", "글리세린", "베타인", "병풀추출물", "판테놀", "카모마일꽃추출물"]},
    {"id": 22, "name": "스킨푸드 당근 카로틴 카밍 패드", "category": "토너", "keywords": ["skinfood", "carrot", "carotene", "pad", "스킨푸드", "당근패드"], "ingredients": ["정제수", "당근추출물", "글리세린", "부틸렌글라이콜", "1,2-헥산다이올", "알란토인", "소듐하이알루로네이트", "올리브오일"]},
    {"id": 23, "name": "성바울루스 PHA 맑은 토너", "category": "토너", "keywords": ["stpaulus", "pha", "toner", "성바울루스"], "ingredients": ["정제수", "글루코놀락톤(PHA)", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "알란토인", "판테놀"]},
    {"id": 24, "name": "헤라 셀 에센스 바이옴 플러스", "category": "토너", "keywords": ["hera", "cell", "essence", "biome", "헤라"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "나이아신아마이드", "1,2-헥산다이올", "페녹시에탄올", "향료", "리날룰"]},
    {"id": 25, "name": "마녀공장 퓨어 클렌징 오일", "category": "클렌징", "keywords": ["manyo", "pure", "cleansing", "oil", "마녀공장", "클렌징오일"], "ingredients": ["돌콩오일", "카프릴릭/카프릭트라이글리세라이드", "호호바씨오일", "올리브오일", "리날룰", "리모넨", "향료", "토코페롤"]},
    {"id": 26, "name": "센카 퍼펙트 휩 페이셜 워시", "category": "클렌징", "keywords": ["senka", "perfect", "whip", "wash", "센카", "퍼펙트휩"], "ingredients": ["정제수", "스테아릭애씨드", "글리세린", "마이리스틱애씨드", "포타슘하이드록사이드", "라우릭애씨드", "향료", "소듐하이알루로네이트"]},
    {"id": 27, "name": "자작나무 수분 선크림 (라운드랩)", "category": "선케어", "keywords": ["roundlab", "birch", "juice", "sunscreen", "라운드랩", "자작나무", "선크림"], "ingredients": ["정제수", "부틸렌글라이콜", "자작나무수액", "글리세린", "나이아신아마이드", "디에칠아미노하이드록시벤조일헥실벤조에이트", "1,2-헥산다이올"]},
    {"id": 28, "name": "셀퓨전씨 레이저 선스크린 100", "category": "선케어", "keywords": ["cellfusionc", "laser", "sunscreen", "100", "셀퓨전씨", "선스크린"], "ingredients": ["정제수", "징크옥사이드", "프로판다이올", "티타늄디옥사이드", "부틸렌글라이콜", "나이아신아마이드", "향료", "1,2-헥산다이올"]},
    {"id": 29, "name": "식물나라 산뜻 수분 선젤", "category": "선케어", "keywords": ["shigmullnara", "sun", "gel", "식물나라", "선젤"], "ingredients": ["정제수", "부틸렌글라이콜", "에탄올", "나이아신아마이드", "병풀추출물", "1,2-헥산다이올", "향료"]},
    {"id": 30, "name": "에스쁘아 워터 스플래쉬 선크림", "category": "선케어", "keywords": ["espoir", "water", "splash", "suncream", "에스쁘아"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "징크옥사이드", "디메치콘", "1,2-헥산다이올", "리모넨", "향료"]},
    {"id": 31, "name": "닥터자르트 시카페어 크림", "category": "크림", "keywords": ["drjart", "dr.jart", "cicapair", "cream", "닥터자르트", "시카페어"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "병풀추출물", "마데카소사이드", "라벤더오일", "시어버터", "페녹시에탄올"]},
    {"id": 32, "name": "키엘 수분 크림 (울트라 페이셜)", "category": "크림", "keywords": ["kiehl", "kiehls", "ultra", "facial", "cream", "키엘", "수분크림"], "ingredients": ["정제수", "글리세린", "시클로헥사실록산", "스쿠알란", "스테아릭애씨드", "팔미틱애씨드", "페녹시에탄올"]},
    {"id": 33, "name": "설화수 자음생크림", "category": "크림", "keywords": ["sulwhasoo", "concentrated", "ginseng", "설화수", "자음생"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "인삼추출물", "디메치콘", "향료", "리날룰", "메틸파라벤"]},
    {"id": 34, "name": "제로이드 피디아덤 크림", "category": "크림", "keywords": ["zeroid", "pidederm", "cream", "제로이드"], "ingredients": ["정제수", "글리세린", "카프릴릭/카프릭트라이글리세라이드", "세라마이드엔피", "스쿠알란", "1,2-헥산다이올"]},
    {"id": 35, "name": "에스트라 테라크네365 스팟 트리트먼트", "category": "에센스", "keywords": ["aestura", "theracne", "spot", "에스트라", "테라크네"], "ingredients": ["정제수", "부틸렌글라이콜", "살리실릭애씨드(BHA)", "에탄올", "나이아신아마이드", "1,2-헥산다이올"]},
    {"id": 36, "name": "폴라초이스 스킨 퍼펙팅 2% BHA 리퀴드", "category": "토너", "keywords": ["paula", "paulaschoice", "bha", "liquid", "폴라초이스"], "ingredients": ["정제수", "메틸프로판다이올", "살리실릭애씨드(BHA)", "녹차추출물", "부틸렌글라이콜"]},
    {"id": 37, "name": "디오디너리 나이아신아마이드 10% + 징크 1%", "category": "에센스", "keywords": ["deordinary", "ordinary", "niacinamide", "zinc", "디오디너리"], "ingredients": ["정제수", "나이아신아마이드", "펜틸렌글라이콜", "징크피씨에이", "디메칠이소소바이드", "페녹시에탄올"]},
    {"id": 38, "name": "디오디너리 AHA 30% + BHA 2% 필링 솔루션", "category": "에센스", "keywords": ["ordinary", "aha", "bha", "peeling", "디오디너리", "필링"], "ingredients": ["정제수", "글리콜릭애씨드(AHA)", "락틱애씨드(AHA)", "살리실릭애씨드(BHA)", "알로에베라잎수", "프로판다이올"]},
    {"id": 39, "name": "코스알엑스 원스텝 원래Clear 패드", "category": "토너", "keywords": ["cosrx", "onestep", "clear", "pad", "코스알엑스"], "ingredients": ["정제수", "부틸렌글라이콜", "글리세린", "살리실릭애씨드(BHA)", "티트리잎오일", "1,2-헥산다이올"]},
    {"id": 40, "name": "한율 어린쑥 수분진정 크림", "category": "크림", "keywords": ["hanyul", "artemisia", "cream", "한율", "어린쑥"], "ingredients": ["정제수", "프로판다이올", "글리세린", "어린쑥추출물", "1,2-헥산다이올", "향료", "시트랄"]},
    {"id": 41, "name": "넘버즈인 5번 글루타치온 C 흔적 앰플", "category": "에센스", "keywords": ["numbuzin", "no5", "glutathione", "ampoule", "넘버즈인", "글루타치온"], "ingredients": ["글루타치온", "나이아신아마이드", "부틸렌글라이콜", "1,2-헥산다이올", "소듐하이알루로네이트", "알란토인"]},
    {"id": 42, "name": "바닐라코 클린잇제로 클렌징 밤", "category": "클렌징", "keywords": ["banilaco", "cleanitzero", "balm", "바닐라코", "클린잇제로"], "ingredients": ["에칠헥실팔미테이트", "합성왁스", "부틸렌글라이콜", "아세로라추출물", "향료", "프로필파라벤"]},
    {"id": 43, "name": "비오템 옴므 아쿠아파워 올인원", "category": "에센스", "keywords": ["biotherm", "aquapower", "homme", "비오템", "아쿠아파워"], "ingredients": ["정제수", "에탄올", "글리세린", "디메치콘", "변성알코올", "향료", "리모넨", "리날룰"]},
    {"id": 44, "name": "닥터지 그린 밀드 업 선 플러스", "category": "선케어", "keywords": ["drg", "green", "mild", "sun", "닥터지", "그린밀드"], "ingredients": ["정제수", "징크옥사이드", "프로판다이올", "부틸렌글라이콜", "병풀추출물", "1,2-헥산다이올"]},
    {"id": 45, "name": "헤라 UV 프로텍터 멀티디펜스", "category": "선케어", "keywords": ["hera", "uv", "protector", "defense", "헤라", "선크림"], "ingredients": ["정제수", "에칠헥실메톡시신나메이트", "부틸렌글라이콜", "에탄올", "벤조페논-3", "향료", "페녹시에탄올"]},
    {"id": 46, "name": "에뛰드 순정 2x 베리어 수분 크림", "category": "크림", "keywords": ["etude", "soonjung", "barrier", "cream", "에뛰드", "순정"], "ingredients": ["정제수", "프로판다이올", "글리세린", "판테놀", "마데카소사이드", "1,2-헥산다이올"]},
    {"id": 47, "name": "식물나라 티트리 시카 수딩 젤", "category": "크림", "keywords": ["shigmullnara", "teatree", "cica", "gel", "식물나라", "티트리"], "ingredients": ["정제수", "티트리추출물", "병풀추출물", "글리세린", "에탄올", "1,2-헥산다이올"]},
    {"id": 48, "name": "이소솝 파슬리 시드 안티 오시던트 세럼", "category": "에센스", "keywords": ["aesop", "parsley", "seed", "serum", "이솝", "파슬리"], "ingredients": ["알로에베라잎즙", "정제수", "부틸렌글라이콜", "라벤더오일", "벤질알코올", "리날룰"]},
    {"id": 49, "name": "더랩바이블랑두 올리고 히알루론산 토너", "category": "토너", "keywords": ["thelab", "blancdoux", "oligo", "hyaluronic", "toner", "더랩바이블랑두"], "ingredients": ["정제수", "부틸렌글라이콜", "1,2-헥산다이올", "소듐하이알루로네이트", "하이드롤라이즈드히알루로닉애씨드", "알란토인"]},
    {"id": 50, "name": "차앤박(CNP) 프로폴리스 에너시 Active 앰플", "category": "에센스", "keywords": ["cnp", "propolis", "energy", "ampoule", "차앤박", "프로폴리스"], "ingredients": ["정제수", "프로폴리스추출물", "부틸렌글라이콜", "글리세린", "1,2-헥산다이올", "소듐하이알루로네이트", "베타인"]}
]

COMMON_INGREDIENTS = {"정제수", "글리세린", "부틸렌글라이콜", "1,2-헥산다이올"}

# --- 🔍 영문/한글 키워드 기반 스마트 OCR 매칭 함수 ---
def match_product_from_image(img_file):
    if not HAS_OCR:
        return None, "OCR 라이브러리(easyocr)가 설치되어 있지 않거나 로드되지 않았습니다."
    
    try:
        image = Image.open(img_file)
        img_np = np.array(image)
        
        # EasyOCR 글자 추출 (한글, 영문 통합)
        results = ocr_reader.readtext(img_np, detail=0)
        
        # 인식된 텍스트 합치기 및 특수문자 제거 후 소문자 변환
        raw_text = " ".join(results)
        clean_extracted = re.sub(r'[^a-zA-Z0-9가-힣]', '', raw_text).lower()

        matched_product = None
        max_score = 0

        # 키워드 기반 매칭 탐색
        for p in products:
            score = 0
            keywords = p.get("keywords", [])
            for kw in keywords:
                kw_clean = kw.lower().strip()
                if kw_clean and kw_clean in clean_extracted:
                    score += 1

            if score > max_score and score >= 1:
                max_score = score
                matched_product = f"[{p['category']}] {p['name']}"

        return matched_product, raw_text
    except Exception as e:
        return None, f"이미지 인식 중 오류 발생: {str(e)}"

# 4. 웹 UI 구현
st.title("🧴 개인 맞춤 화장품 성분 분석기")
st.caption("영문/한글 OCR 스마트 사진 인식 및 성분 위험도 정밀 비교")

st.divider()

st.subheader("📸 1. 화장품 이미지 등록")
st.caption("제품명(브랜드명)이 잘 보이도록 촬영하거나 올리면 자동으로 제품을 찾아줍니다.")

tab1, tab2 = st.tabs(["📷 실시간 카메라 촬영", "🖼️ 갤러리/파일 업로드"])

auto_selected_product = None
ocr_debug_text = ""

with tab1:
    captured_image = st.camera_input("화장품 정면 촬영")
    if captured_image is not None:
        st.image(captured_image, width=220)
        with st.spinner("🔍 사진 속 영문/한글 제품명을 읽는 중..."):
            auto_selected_product, ocr_debug_text = match_product_from_image(captured_image)

with tab2:
    uploaded_file = st.file_uploader("스마트폰 갤러리에서 사진 선택", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, width=220)
        with st.spinner("🔍 사진 속 영문/한글 제품명을 읽는 중..."):
            auto_selected_product, ocr_debug_text = match_product_from_image(uploaded_file)

# OCR 결과 안내
if auto_selected_product:
    st.success(f"🎉 **제품 자동 인식 성공!** -> **{auto_selected_product}**")
elif (captured_image or uploaded_file) and not auto_selected_product:
    st.info("💡 **사진에서 제품명을 완벽히 매칭하지 못했습니다.** 아래 목록에서 직접 선택해 주세요.")
    with st.expander("🔍 사진에서 읽어낸 텍스트 확인 (디버깅)"):
        st.write(ocr_debug_text if ocr_debug_text else "인식된 글자가 없습니다.")

st.divider()

# 5. 제품 및 증상 선택
st.subheader("⚠️ 2. 과거 부작용 경험 및 구매 예정 제품 선택")

product_dict = {f"[{p['category']}] {p['name']}": p['id'] for p in products}

# 이미지 인식 결과 자동 선택
default_selected = [auto_selected_product] if auto_selected_product in product_dict else []

selected_problem_names = st.multiselect(
    "과거 부작용/트러블이 있었던 제품 (1개 이상 선택):",
    options=list(product_dict.keys()),
    default=default_selected
)

selected_symptoms = st.multiselect(
    "📌 과거 경험한 주요 부작용 증상:",
    options=['따가움/화끈거림', '붉어짐/홍조', '트러블/모공막힘/좁쌀', '가려움', '건조함/각질/당김', '눈시림']
)

selected_new_name = st.selectbox(
    "🛒 구매 검토 중인 새 제품:",
    options=list(product_dict.keys())
)

# 6. 성분 분석 실행
if st.button("🔍 성분 위험도 및 부작용 분석 실행", type="primary", use_container_width=True):
    if not selected_problem_names:
        st.error("과거 부작용을 경험했던 제품을 최소 1개 이상 선택해 주세요!")
    else:
        problem_ids = [product_dict[name] for name in selected_problem_names]
        new_id = product_dict[selected_new_name]

        problem_ingredients_list = []
        for p in products:
            if p['id'] in problem_ids:
                unique_ings = set(p['ingredients']) - COMMON_INGREDIENTS
                problem_ingredients_list.append(unique_ings)

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

        new_product = next((p for p in products if p['id'] == new_id), None)
        new_product_ings = set(new_product['ingredients'])
        matched = new_product_ings.intersection(caution_ingredients)

        st.divider()
        st.subheader("📊 맞춤 성분 분석 리포트")
        
        if selected_symptoms:
            st.write(f"**등록된 사용자 증상:** `{', '.join(selected_symptoms)}`")

        if matched:
            st.warning(f"⚠️ **[주의] 과거 문제 제품의 위험/특이 성분 {len(matched)}개가 새 제품에 포함되어 있습니다!**")
            for ing in matched:
                info = INGREDIENT_INFO.get(ing, {"category": "주의 성분", "info": "과거 부작용 유발 제품에 포함된 성분"})
                st.markdown(f"- **{ing}** (`{info['category']}`) : {info['info']}")
        else:
            st.success("✅ **[안전] 과거 부작용 유발 제품의 주요 특이/위험 성분이 발견되지 않았습니다.**")

        st.caption("※ 본 분석 시스템은 입력 데이터를 기반으로 한 참고용 가이드입니다.")
