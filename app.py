"""Expense Analyzer"""
import streamlit as st
from io import BytesIO
import os
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

st.set_page_config(page_title="Expense Analyzer", page_icon="💰", layout="wide")

if 'uploaded_file_data' not in st.session_state:
    st.session_state['uploaded_file_data'] = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state['uploaded_file_name'] = None
if 'use_sample' not in st.session_state:
    st.session_state['use_sample'] = False

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

if theme_manager.get_theme_name() == 'dark':
    theme_manager.apply_theme()

st.title("💰 개인 가계부 분석기")

with st.sidebar:
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader("CSV/Excel", type=['csv', 'xlsx', 'xls'])
    if uploaded_file:
        st.session_state['uploaded_file_data'] = uploaded_file.getvalue()
        st.session_state['uploaded_file_name'] = uploaded_file.name
    st.markdown("---")
    use_ai = st.checkbox("AI 자동 분류", value=False)

if uploaded_file is None and st.session_state['uploaded_file_data'] is None:
    st.info("파일을 업로드해주세요")
    if st.button("샘플 데이터로 체험"):
        st.session_state['use_sample'] = True
        st.rerun()
    st.stop()

try:
    if st.session_state.get('use_sample') and uploaded_file is None:
        with open('data/sample.csv', 'r', encoding='utf-8-sig') as f:
            df = load_data(f)
    else:
        if uploaded_file:
            df = load_data(uploaded_file)
        else:
            file_data = BytesIO(st.session_state['uploaded_file_data'])
            file_data.name = st.session_state['uploaded_file_name']
            df = load_data(file_data)
    
    # ✅ AI 자동 분류 (수정됨)
    if use_ai:
        with st.spinner('🤖 AI가 카테고리를 분석 중입니다...'):
            df = managers['classifier'].auto_categorize_dataframe(df)
            
            # AI 결과로 분류 컬럼 덮어쓰기
            if '분류_AI' in df.columns:
                df['분류'] = df['분류_AI']
                st.success(f"✅ {len(df)}건 로드 (AI 분류 완료)")
            else:
                st.warning("⚠️ AI 분류에 실패했습니다")
    else:
        st.success(f"✅ {len(df)}건 로드")
        
except Exception as e:
    st.error(f"오류: {e}")
    st.stop()

from tabs import dashboard, analysis, monthly_trend, budget, statistics, data_explorer, category_tab, validator, ai_learning, savings_goal, recurring, prediction

tabs = st.tabs(["📊 대시보드", "📈 분석", "📅 월별", "💰 예산", "📉 통계", "🔍 탐색", "📁 카테고리", "✅ 검증", "🤖 AI", "🎯 저축", "🔄 반복", "🔮 예측"])

with tabs[0]:
    dashboard.render(df, managers['budget_manager'])
with tabs[1]:
    analysis.render(df)
with tabs[2]:
    monthly_trend.render(df)
with tabs[3]:
    budget.render(df, managers['budget_manager'])
with tabs[4]:
    statistics.render(df)
with tabs[5]:
    data_explorer.render(df)
with tabs[6]:
    category_tab.render(df, managers['category_manager'])
with tabs[7]:
    validator.render(df, managers['data_validator'])
with tabs[8]:
    ai_learning.render(df, managers['classifier'])
with tabs[9]:
    savings_goal.render(df, managers['savings_goal_manager'])
with tabs[10]:
    recurring.render(df, managers['recurring_manager'], managers['category_manager'])
with tabs[11]:
    prediction.render(df, managers['budget_manager'])

st.caption("Expense Analyzer v2.5")