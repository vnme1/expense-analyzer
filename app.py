"""
Expense Analyzer - 메인 앱 (리팩토링 버전)
탭별 모듈 분리 + 순환 import 해결 + 세션 저장
"""
import streamlit as st
from io import BytesIO
import os

# ✅ 유틸리티만 먼저 import
from utils.preprocess import load_data
from utils.ai_categorizer import CategoryClassifier
from utils.budget_manager import BudgetManager
from utils.theme_manager import ThemeManager
from utils.pdf_generator import PDFReportGenerator
from utils.category_manager import CategoryManager
from utils.data_validator import DataValidator
from utils.export_manager import ExportManager
from utils.savings_goal import SavingsGoalManager
from utils.recurring_transactions import RecurringTransactionManager
from utils.tag_manager import TagManager
from utils.comparison_analyzer import ComparisonAnalyzer
from utils.expense_predictor import ExpensePredictor

# 페이지 설정
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide"
)

# 세션 상태 초기화
if 'uploaded_file_data' not in st.session_state:
    st.session_state['uploaded_file_data'] = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state['uploaded_file_name'] = None
if 'use_sample' not in st.session_state:
    st.session_state['use_sample'] = False

# 싱글톤 초기화
@st.cache_resource
def get_managers():
    classifier = CategoryClassifier()
    classifier.load_model()
    
    return {
        'classifier': classifier,
        'budget_manager': BudgetManager(),
        'theme_manager': ThemeManager(),
        'pdf_generator': PDFReportGenerator(),
        'category_manager': CategoryManager(),
        'data_validator': DataValidator(),
        'export_manager': ExportManager(),
        'savings_goal_manager': SavingsGoalManager(),
        'recurring_manager': RecurringTransactionManager(),
        'tag_manager': TagManager(),
        'comparison_analyzer': ComparisonAnalyzer(),
        'expense_predictor': ExpensePredictor()
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
    st.markdown("### 🎨 테마")
    current_theme = theme_manager.get_theme_name()
    
    col_theme1, col_theme2 = st.columns([3, 1])
    with col_theme1:
        st.caption(f"현재: {'🌙 다크 모드' if current_theme == 'dark' else '☀️ 라이트 모드'}")
    with col_theme2:
        if st.button("🔄", help="테마 변경", use_container_width=True):
            theme_manager.toggle_theme()
            st.rerun()
    
    st.markdown("---")
    
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader(
        "CSV 또는 Excel 파일 선택",
        type=['csv', 'xlsx', 'xls']
    )
    
    # 🆕 파일 세션 저장 (테마 전환 시에도 유지)
    if uploaded_file is not None:
        st.session_state['uploaded_file_data'] = uploaded_file.getvalue()
        st.session_state['uploaded_file_name'] = uploaded_file.name
    
    st.markdown("---")
    
    st.header("🤖 AI 설정")
    use_ai = st.checkbox("AI 자동 분류 사용", value=False)

# 파일 없으면 종료
if uploaded_file is None and st.session_state['uploaded_file_data'] is None:
    st.info("👈 왼쪽 사이드바에서 파일을 업로드해주세요")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 샘플 데이터로 체험하기", type="primary", use_container_width=True):
            st.session_state['use_sample'] = True
            st.rerun()
    with col2:
        st.info("💡 샘플 데이터를 자동으로 로드하여 바로 기능을 체험해보세요!")
    
    st.stop()

# 데이터 로드
try:
    if st.session_state.get('use_sample') and uploaded_file is None:
        sample_path = os.path.join('data', 'sample.csv')
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8-sig') as f:
                df = load_data(f)
            st.success(f"✅ 샘플 데이터 로드 완료! ({len(df)}건)")
        else:
            st.error("샘플 데이터 파일을 찾을 수 없습니다")
            st.stop()
    else:
        # 세션에서 파일 복원
        if uploaded_file is not None:
            df = load_data(uploaded_file)
        elif st.session_state['uploaded_file_data'] is not None:
            file_data = BytesIO(st.session_state['uploaded_file_data'])
            file_data.name = st.session_state['uploaded_file_name']
            df = load_data(file_data)
        else:
            st.error("파일을 찾을 수 없습니다")
            st.stop()
    
    # AI 자동 분류
    if use_ai:
        if '분류' not in df.columns or df['분류'].isna().any():
            with st.spinner('🤖 AI가 카테고리를 분석 중입니다...'):
                df = managers['classifier'].auto_categorize_dataframe(df)
                if '분류' not in df.columns:
                    df['분류'] = df['분류_AI']
                else:
                    mask = df['분류'].isna() | (df['분류'] == '기타')
                    df.loc[mask, '분류'] = df.loc[mask, '분류_AI']
    
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

# 각 탭 렌더링 (싱글톤 전달)
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
    category_tab.render(df, managers['category_manager'])

with tabs_list[7]:
    validator.render(df, managers['data_validator'])

with tabs_list[8]:
    ai_learning.render(df, managers['classifier'])

with tabs_list[9]:
    savings_goal.render(df, managers['savings_goal_manager'])

with tabs_list[10]:
    recurring.render(df, managers['recurring_manager'], managers['category_manager'])

with tabs_list[11]:
    prediction.render(df, managers['budget_manager'])

# 푸터
st.markdown("---")
st.caption("💡 Expense Analyzer v2.5.0 | 리팩토링 완료 🚀")