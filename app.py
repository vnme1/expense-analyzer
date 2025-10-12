"""
Expense Analyzer - 메인 앱 (리팩토링 버전)
탭별 모듈 분리로 코드 간결화
"""
import streamlit as st

# ✅ 순환 import 방지를 위해 필요할 때만 import
from utils.preprocess import load_data
from utils.ai_categorizer import CategoryClassifier
from utils.budget_manager import BudgetManager
from utils.theme_manager import ThemeManager

# 페이지 설정
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide"
)

# 싱글톤 초기화
@st.cache_resource
def get_managers():
    return {
        'classifier': CategoryClassifier(),
        'budget_manager': BudgetManager(),
        'theme_manager': ThemeManager()
    }

managers = get_managers()
theme_manager = managers['theme_manager']

# 테마 적용
if theme_manager.get_theme_name() == 'dark':
    theme_manager.apply_theme()

# 타이틀
st.title("💰 개인 가계부 분석기")
st.markdown("**CSV/Excel 파일을 업로드하여 수입/지출을 분석하세요 + AI 자동 분류 🤖**")

# 사이드바
with st.sidebar:
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader(
        "CSV 또는 Excel 파일 선택",
        type=['csv', 'xlsx', 'xls']
    )
    
    st.markdown("---")
    
    st.header("🤖 AI 설정")
    use_ai = st.checkbox("AI 자동 분류 사용", value=False)
    
    st.markdown("---")
    st.markdown("### 🎨 테마")
    if st.button("🌓 테마 변경"):
        theme_manager.toggle_theme()
        st.rerun()

# 파일 없으면 종료
if uploaded_file is None:
    st.info("👈 왼쪽 사이드바에서 파일을 업로드해주세요")
    st.stop()

# 데이터 로드
try:
    df = load_data(uploaded_file)
    
    if use_ai:
        df = managers['classifier'].auto_categorize_dataframe(df)
    
    st.success(f"✅ {len(df)}건의 거래 내역을 불러왔습니다")
except Exception as e:
    st.error(f"❌ 파일 로드 오류: {str(e)}")
    st.stop()

# ✅ 탭 import는 여기서! (데이터 로드 후)
from tabs import (
    dashboard,
    analysis,
    monthly_trend,
    budget,
    statistics,
    data_explorer,
    category_tab,
    validator,
    ai_learning,
    savings_goal,
    recurring,
    prediction
)

# 탭 구성
tabs_list = st.tabs([
    "📊 대시보드", "📈 상세 분석", "📅 월별 추이", "💰 예산 관리",
    "📉 통계", "🔍 데이터 탐색", "📁 카테고리 관리", "✅ 데이터 검증",
    "🤖 AI 학습", "🎯 저축 목표", "🔄 반복 거래", "🔮 예측 & 비교"
])

# 각 탭 렌더링
with tabs_list[0]:
    dashboard.render(df, managers['budget_manager'])

with tabs_list[1]:
    analysis.render(df)

with tabs_list[2]:
    monthly_trend.render(df)

with tabs_list[3]:
    budget.render(df, managers['budget_manager'])

with tabs_list[4]:
    statistics.render(df)

with tabs_list[5]:
    data_explorer.render(df)

with tabs_list[6]:
    category_tab.render(df)

with tabs_list[7]:
    validator.render(df)

with tabs_list[8]:
    ai_learning.render(df, managers['classifier'])

with tabs_list[9]:
    savings_goal.render(df)

with tabs_list[10]:
    recurring.render(df)

with tabs_list[11]:
    prediction.render(df, managers['budget_manager'])

# 푸터
st.markdown("---")
st.caption("💡 Expense Analyzer v2.5.0 | 리팩토링 완료 🚀")