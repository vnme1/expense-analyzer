"""
Expense Analyzer - 개인 가계부 분석 대시보드
Streamlit 기반 인터랙티브 재무 분석 도구
v2.5 - 빠른 입력 + 요약 카드 + 즐겨찾기 필터 + 편집 모드
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
from datetime import datetime
from utils.preprocess import (
    load_data, 
    summarize_by_category, 
    summarize_by_month, 
    get_summary_metrics,
    filter_by_date_range,
    get_statistics
)
from utils.ai_categorizer import CategoryClassifier
from utils.budget_manager import BudgetManager
from utils.pdf_generator import PDFReportGenerator
from utils.category_manager import CategoryManager
from utils.data_validator import DataValidator
from utils.export_manager import ExportManager
#  Phase 1&2 모듈
from utils.theme_manager import ThemeManager
from utils.savings_goal import SavingsGoalManager
from utils.recurring_transactions import RecurringTransactionManager
from utils.tag_manager import TagManager
from utils.comparison_analyzer import ComparisonAnalyzer
from utils.expense_predictor import ExpensePredictor

st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide"
)

# 세션 상태 초기화
if 'show_budget_settings' not in st.session_state:
    st.session_state['show_budget_settings'] = False

if 'use_sample' not in st.session_state:
    st.session_state['use_sample'] = False

if 'suggested_budgets' not in st.session_state:
    st.session_state['suggested_budgets'] = None

if 'quick_filter' not in st.session_state:
    st.session_state['quick_filter'] = None

@st.cache_resource
def get_classifier():
    """AI 분류기 싱글톤"""
    classifier = CategoryClassifier()
    classifier.load_model()
    return classifier

@st.cache_resource
def get_budget_manager():
    """예산 관리자 싱글톤"""
    return BudgetManager()

@st.cache_resource
def get_pdf_generator():
    """PDF 생성기 싱글톤"""
    return PDFReportGenerator()

@st.cache_resource
def get_category_manager():
    """카테고리 관리자 싱글톤"""
    return CategoryManager()

@st.cache_resource
def get_data_validator():
    """데이터 검증기 싱글톤"""
    return DataValidator()

@st.cache_resource
def get_export_manager():
    """내보내기 관리자 싱글톤"""
    return ExportManager()

@st.cache_resource
def get_theme_manager():
    return ThemeManager()

@st.cache_resource
def get_savings_goal_manager():
    return SavingsGoalManager()

@st.cache_resource
def get_recurring_manager():
    return RecurringTransactionManager()

@st.cache_resource
def get_tag_manager():
    return TagManager()

@st.cache_resource
def get_comparison_analyzer():
    return ComparisonAnalyzer()

@st.cache_resource
def get_expense_predictor():
    return ExpensePredictor()

classifier = get_classifier()
budget_manager = get_budget_manager()
pdf_generator = get_pdf_generator()
category_manager = get_category_manager()
data_validator = get_data_validator()
export_manager = get_export_manager()
theme_manager = get_theme_manager()
savings_goal_manager = get_savings_goal_manager()
recurring_manager = get_recurring_manager()
tag_manager = get_tag_manager()
comparison_analyzer = get_comparison_analyzer()
expense_predictor = get_expense_predictor()

# 🎨 테마 적용
theme_manager.apply_theme()

st.title("💰 개인 가계부 분석기")
st.markdown("**CSV/Excel 파일을 업로드하여 수입/지출을 분석하세요 + AI 자동 분류 🤖**")

# 사이드바
with st.sidebar:
    # 🌓 다크 모드 토글
    st.markdown("### 🎨 테마")
    current_theme = theme_manager.get_theme_name()
    
    col_theme1, col_theme2 = st.columns([3, 1])
    with col_theme1:
        st.caption(f"현재: {'🌙 다크 모드' if current_theme == 'dark' else '☀️ 라이트 모드'}")
    with col_theme2:
        if st.button("🔄", help="테마 변경", use_container_width=True):
            new_theme = theme_manager.toggle_theme()
            st.rerun()
    
    st.markdown("---")
    
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader(
        "CSV 또는 Excel 파일 선택",
        type=['csv', 'xlsx', 'xls'],
        help="날짜, 금액, 분류 컬럼이 포함된 파일"
    )
    
    st.markdown("---")
    
    st.header("🤖 AI 설정")
    use_ai = st.checkbox("AI 자동 분류 사용", value=False, 
                         help="'분류' 컬럼이 없어도 자동으로 카테고리를 예측합니다")
    
    if use_ai:
        st.info("💡 AI가 '적요' 내용을 분석하여 자동으로 카테고리를 분류합니다")
    
    st.markdown("---")
    st.markdown("### 📋 파일 형식 안내")
    
    tab_csv, tab_excel = st.tabs(["CSV", "Excel"])
    
    with tab_csv:
        st.code("""날짜,적요,금액,분류,메모
2025-01-02,스타벅스,-4500,카페,아메리카노
2025-01-03,월급,2500000,급여,1월 급여""")
    
    with tab_excel:
        st.markdown("""
**Excel 파일 형식**
- `.xlsx` 또는 `.xls` 확장자
- 첫 번째 시트의 데이터를 읽음
- 컬럼명은 CSV와 동일
        """)
    
    #  빠른 거래 입력
    st.markdown("---")
    st.markdown("### ⚡ 빠른 거래 입력")
    
    with st.expander("➕ 새 거래 추가", expanded=False):
        with st.form("quick_add_transaction", clear_on_submit=True):
            add_date = st.date_input(
                "날짜",
                value=datetime.now(),
                help="거래 날짜를 선택하세요"
            )
            
            add_desc = st.text_input(
                "적요",
                placeholder="예: 스타벅스",
                help="거래 내역 설명"
            )
            
            col_amount, col_type = st.columns([2, 1])
            
            with col_amount:
                add_amount = st.number_input(
                    "금액",
                    min_value=0,
                    step=1000,
                    help="거래 금액 (양수로 입력)"
                )
            
            with col_type:
                add_type = st.selectbox(
                    "구분",
                    options=["지출", "수입"]
                )
            
            # AI 자동 분류 사용 시
            if use_ai and add_desc:
                predicted_cat = classifier.predict(add_desc)
                add_category = st.text_input("카테고리", value=predicted_cat)
            else:
                categories = category_manager.get_all_categories()
                add_category = st.selectbox("카테고리", options=categories)
            
            add_memo = st.text_input(
                "메모 (선택)",
                placeholder="추가 메모",
                help="선택사항"
            )
            
            submitted = st.form_submit_button("💾 거래 추가", use_container_width=True)
            
            if submitted:
                if not add_desc or add_amount == 0:
                    st.error("❌ 적요와 금액을 입력해주세요")
                else:
                    try:
                        import os
                        
                        # CSV 파일 경로
                        csv_path = 'data/user_expenses.csv'
                        
                        # 금액 부호 조정
                        final_amount = -add_amount if add_type == "지출" else add_amount
                        
                        # 새 행 생성
                        new_row = pd.DataFrame({
                            '날짜': [add_date],
                            '적요': [add_desc],
                            '금액': [final_amount],
                            '분류': [add_category],
                            '메모': [add_memo]
                        })
                        
                        # 기존 데이터에 추가
                        if os.path.exists(csv_path):
                            existing_df = pd.read_csv(csv_path, encoding='utf-8-sig')
                            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                        else:
                            # 폴더 생성
                            os.makedirs('data', exist_ok=True)
                            updated_df = new_row
                        
                        # 저장
                        updated_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        
                        st.success(f"✅ 거래가 추가되었습니다!")
                        st.info("💡 페이지를 새로고침하여 변경사항을 확인하세요")
                        
                    except Exception as e:
                        st.error(f"❌ 저장 실패: {str(e)}")

if uploaded_file is None:
    st.info("👈 왼쪽 사이드바에서 CSV 또는 Excel 파일을 업로드해주세요")
    
    st.markdown("---")
    st.subheader("🎯 빠른 시작")
    
    col_demo1, col_demo2 = st.columns([1, 2])
    with col_demo1:
        if st.button("🚀 샘플 데이터로 체험하기", type="primary", use_container_width=True):
            st.session_state['use_sample'] = True
            st.rerun()
    with col_demo2:
        st.info("💡 샘플 데이터를 자동으로 로드하여 바로 기능을 체험해보세요!")
    
    st.markdown("---")
    st.subheader("📥 샘플 데이터 다운로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1. 카테고리 포함 버전 (CSV)**")
        sample_data = """날짜,적요,금액,분류,메모
2025-01-02,스타벅스,-4500,카페,아메리카노
2025-01-03,월급,2500000,급여,1월 급여
2025-01-04,이마트,-75000,식비,장보기
2025-01-05,넷플릭스,-14500,구독,월구독료
2025-01-10,CGV,-32000,여가,영화관람"""
        st.download_button(
            label="샘플 CSV 다운로드",
            data=sample_data.encode('utf-8-sig'),
            file_name="sample_expense.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("**2. AI 자동 분류용 (CSV)**")
        sample_data_ai = """날짜,적요,금액,메모
2025-01-02,스타벅스,-4500,아메리카노
2025-01-03,월급,2500000,1월 급여
2025-01-04,이마트,-75000,장보기
2025-01-05,넷플릭스,-14500,월구독료
2025-01-10,CGV,-32000,영화관람"""
        st.download_button(
            label="AI용 샘플 다운로드",
            data=sample_data_ai.encode('utf-8-sig'),
            file_name="sample_expense_ai.csv",
            mime="text/csv"
        )
    
    st.stop()

# 데이터 로드
try:
    if 'use_sample' in st.session_state and st.session_state['use_sample'] and uploaded_file is None:
        import os
        sample_path = os.path.join('data', 'sample.csv')
        if os.path.exists(sample_path):
            with open(sample_path, 'r', encoding='utf-8-sig') as f:
                df = load_data(f)
            st.success(f"✅ 샘플 데이터 로드 완료! ({len(df)}건)")
            st.info("💡 사이드바에서 직접 CSV/Excel 파일을 업로드하면 자신의 데이터를 분석할 수 있습니다")
        else:
            st.error("샘플 데이터 파일을 찾을 수 없습니다")
            st.session_state['use_sample'] = False
            st.stop()
    else:
        df = load_data(uploaded_file)
    
    if use_ai:
        if '분류' not in df.columns or df['분류'].isna().any() or (df['분류'] == '기타').any():
            with st.spinner('🤖 AI가 카테고리를 분석 중입니다...'):
                df = classifier.auto_categorize_dataframe(df)
                
                if '분류' not in df.columns:
                    df['분류'] = df['분류_AI']
                else:
                    mask = df['분류'].isna() | (df['분류'] == '기타')
                    df.loc[mask, '분류'] = df.loc[mask, '분류_AI']
                
            st.success(f"✅ {len(df)}건의 거래 내역을 불러왔습니다 (AI 자동 분류 적용)")
            
            if '분류_AI' in df.columns:
                ai_count = df['분류_AI'].notna().sum()
                st.info(f"🤖 AI가 {ai_count}건의 카테고리를 자동으로 분류했습니다")
        else:
            st.success(f"✅ {len(df)}건의 거래 내역을 불러왔습니다")
    else:
        st.success(f"✅ {len(df)}건의 거래 내역을 불러왔습니다")
        
except Exception as e:
    st.error(f"❌ 파일 로드 오류: {str(e)}")
    st.stop()

# 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "📊 대시보드", 
    "📈 상세 분석", 
    "📅 월별 추이", 
    "💰 예산 관리",
    "📉 통계",
    "🔍 데이터 탐색",
    "📁 카테고리 관리",
    "✅ 데이터 검증",
    "🤖 AI 학습",
    "🎯 저축 목표",      # 
    "🔄 반복 거래",       # 
    "🔮 예측 & 비교"     # 
])

# 탭1: 대시보드
with tab1:
    #  이번 달 요약 카드
    st.markdown("### 📊 이번 달 요약")
    
    # 이번 달 데이터 필터링
    current_month = pd.Timestamp.now().strftime('%Y-%m')
    this_month_df = df[df['년월'] == current_month]
    
    # 지난 달 데이터
    last_month = (pd.Timestamp.now() - pd.DateOffset(months=1)).strftime('%Y-%m')
    last_month_df = df[df['년월'] == last_month]
    
    # 계산
    this_month_expense = this_month_df[this_month_df['구분'] == '지출']['금액_절대값'].sum()
    last_month_expense = last_month_df[last_month_df['구분'] == '지출']['금액_절대값'].sum()
    expense_change = this_month_expense - last_month_expense
    
    this_month_income = this_month_df[this_month_df['구분'] == '수입']['금액_절대값'].sum()
    
    # 가장 많이 쓴 카테고리
    if len(this_month_df[this_month_df['구분'] == '지출']) > 0:
        top_category = this_month_df[this_month_df['구분'] == '지출'].groupby('분류')['금액_절대값'].sum().idxmax()
        top_category_amount = this_month_df[this_month_df['구분'] == '지출'].groupby('분류')['금액_절대값'].sum().max()
    else:
        top_category = "-"
        top_category_amount = 0
    
    # 예산 달성률
    if budget_manager.budgets['default'] or (current_month in budget_manager.budgets.get('monthly', {})):
        budget_summary = budget_manager.get_monthly_summary(this_month_df, current_month)
        budget_usage = budget_summary['전체_사용률']
    else:
        budget_usage = 0
    
    # 카드 표시
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💸 이번 달 지출", 
            f"{this_month_expense:,.0f}원",
            delta=f"{expense_change:,.0f}원" if last_month_expense > 0 else None,
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "💵 이번 달 수입",
            f"{this_month_income:,.0f}원"
        )
    
    with col3:
        st.metric(
            "🏆 최다 지출",
            top_category,
            f"{top_category_amount:,.0f}원"
        )
    
    with col4:
        savings_rate = ((this_month_income - this_month_expense) / this_month_income * 100) if this_month_income > 0 else 0
        st.metric(
            "💰 저축률",
            f"{savings_rate:.1f}%",
            delta="✨ 달성!" if savings_rate >= 30 else "목표: 30%",
            delta_color="normal" if savings_rate >= 30 else "off"
        )
    
    with col5:
        if budget_usage > 0:
            st.metric(
                "📊 예산 사용",
                f"{budget_usage:.0f}%",
                delta="위험" if budget_usage >= 80 else "양호",
                delta_color="inverse" if budget_usage >= 80 else "normal"
            )
        else:
            st.metric(
                "📊 예산 사용",
                "미설정",
                "예산을 설정하세요"
            )
    
    st.markdown("---")
    
    metrics = get_summary_metrics(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💵 총 수입", f"{metrics['총_수입']:,.0f}원")
    with col2:
        st.metric("💸 총 지출", f"{metrics['총_지출']:,.0f}원")
    with col3:
        st.metric("💰 잔액", f"{metrics['잔액']:,.0f}원")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 카테고리별 지출 비율")
        category_summary = summarize_by_category(df)
        
        if not category_summary.empty:
            fig_pie = px.pie(
                values=category_summary.values,
                names=category_summary.index,
                title="지출 카테고리 분포",
                hole=0.4
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>금액: %{value:,.0f}원<br>비율: %{percent}<extra></extra>'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("지출 데이터가 없습니다")
    
    with col_right:
        st.subheader("📈 월별 수입/지출")
        monthly_summary = summarize_by_month(df)
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=monthly_summary.index,
            y=monthly_summary['수입'],
            name='수입',
            marker_color='#4CAF50'
        ))
        fig_bar.add_trace(go.Bar(
            x=monthly_summary.index,
            y=monthly_summary['지출'],
            name='지출',
            marker_color='#FF5252'
        ))
        fig_bar.update_layout(
            barmode='group',
            xaxis_title="월",
            yaxis_title="금액 (원)",
            legend=dict(orientation="h", y=1.1),
            xaxis=dict(type='category')
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # PDF 리포트 생성
    st.markdown("---")
    st.subheader("📄 월간 리포트 생성")
    
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input(
            "시작 날짜",
            value=df['날짜'].min(),
            min_value=df['날짜'].min(),
            max_value=df['날짜'].max(),
            help="PDF에 포함할 시작 날짜를 선택하세요"
        )
    
    with col_date2:
        end_date = st.date_input(
            "종료 날짜",
            value=df['날짜'].max(),
            min_value=df['날짜'].min(),
            max_value=df['날짜'].max(),
            help="PDF에 포함할 종료 날짜를 선택하세요"
        )
    
    if start_date > end_date:
        st.error("⚠️ 시작 날짜는 종료 날짜보다 이전이어야 합니다")
    else:
        filtered_df = filter_by_date_range(df, start_date, end_date)
        
        st.info(f"📅 선택 기간: {start_date} ~ {end_date} ({len(filtered_df)}건)")
        
        if st.button("📄 PDF 리포트 생성", type="primary", use_container_width=True):
            with st.spinner("📝 리포트 생성 중... (10-20초 소요)"):
                try:
                    pdf_buffer = pdf_generator.generate_report(filtered_df, budget_manager)
                    st.success("✅ 리포트 생성 완료!")
                    
                    st.markdown("### 📋 PDF 미리보기")
                    pdf_buffer.seek(0)
                    base64_pdf = base64.b64encode(pdf_buffer.read()).decode('utf-8')
                    
                    pdf_display = f'''
                        <div style="width: 100%; height: 1000px; border: 2px solid #e0e0e0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <iframe src="data:application/pdf;base64,{base64_pdf}" 
                                    width="100%" 
                                    height="100%" 
                                    type="application/pdf"
                                    style="border: none;">
                            </iframe>
                        </div>
                    '''
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    
                    st.markdown("")
                    
                    pdf_buffer.seek(0)
                    col_center = st.columns([1, 2, 1])[1]
                    with col_center:
                        st.download_button(
                            label="📥 PDF 다운로드",
                            data=pdf_buffer,
                            file_name=f"expense_report_{start_date}_{end_date}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"❌ PDF 생성 실패: {str(e)}")
                    st.info("💡 kaleido 라이브러리 설치가 필요할 수 있습니다: pip install kaleido")

# 탭2: 상세 분석
with tab2:
    st.subheader("🔍 카테고리별 상세 분석")
    
    category_summary = summarize_by_category(df)
    
    if not category_summary.empty:
        fig_detail = px.bar(
            x=category_summary.index,
            y=category_summary.values,
            labels={'x': '카테고리', 'y': '지출액 (원)'},
            title="카테고리별 지출 상세",
            color=category_summary.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_detail, use_container_width=True)
        
        st.markdown("### 📋 카테고리별 지출 내역")
        detail_df = pd.DataFrame({
            '카테고리': category_summary.index,
            '지출액': category_summary.values,
            '비율(%)': (category_summary.values / category_summary.sum() * 100).round(1)
        })
        st.dataframe(
            detail_df.style.format({'지출액': '{:,.0f}원', '비율(%)': '{:.1f}%'}),
            use_container_width=True
        )
    else:
        st.info("지출 데이터가 없습니다")

# 탭3: 월별 추이
with tab3:
    st.subheader("📅 월별 수입/지출 추이")
    
    monthly_summary = summarize_by_month(df)
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['수입'],
        mode='lines+markers',
        name='수입',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=10)
    ))
    fig_line.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['지출'],
        mode='lines+markers',
        name='지출',
        line=dict(color='#FF5252', width=3),
        marker=dict(size=10)
    ))
    fig_line.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['잔액'],
        mode='lines+markers',
        name='잔액',
        line=dict(color='#2196F3', width=3, dash='dot'),
        marker=dict(size=10)
    ))
    fig_line.update_layout(
        xaxis_title="월",
        yaxis_title="금액 (원)",
        legend=dict(orientation="h", y=1.1),
        xaxis=dict(type='category')
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("### 📊 월별 상세 내역")
    monthly_display = monthly_summary.copy()
    monthly_display.columns = ['수입', '지출', '잔액']
    st.dataframe(
        monthly_display.style.format('{:,.0f}원'),
        use_container_width=True
    )

# 탭4: 예산 관리 (기존 코드 유지)
with tab4:
    st.subheader("💰 예산 관리")
    
    available_months = budget_manager.get_available_months(df)
    if available_months:
        current_month = available_months[-1]
        if budget_manager.check_and_reset_if_needed(current_month):
            st.success(f"✅ {current_month} 예산이 자동으로 생성되었습니다!")
    
    col_mode, col_month, col_settings = st.columns([1, 2, 1])
    
    with col_mode:
        analysis_mode = st.radio(
            "분석 모드",
            options=["📅 전체 기간", "📆 월별"],
            horizontal=True
        )
    
    target_month = None
    
    with col_month:
        if analysis_mode == "📆 월별":
            if available_months:
                target_month = st.selectbox(
                    "분석할 월 선택",
                    options=available_months,
                    index=len(available_months) - 1
                )
                st.info(f"💡 {target_month} 기준으로 예산을 분석합니다")
            else:
                st.warning("⚠️ 데이터가 없습니다")
        else:
            st.info(f"💡 전체 기간 ({df['날짜'].min().strftime('%Y-%m-%d')} ~ {df['날짜'].max().strftime('%Y-%m-%d')}) 기준")
    
    with col_settings:
        if st.button("⚙️ 설정", use_container_width=True):
            st.session_state['show_budget_settings'] = not st.session_state.get('show_budget_settings', False)
    
    if st.session_state.get('show_budget_settings', False):
        with st.expander("⚙️ 예산 설정", expanded=True):
            st.markdown("### 🔄 자동 갱신")
            
            auto_reset = st.checkbox(
                "매월 자동으로 기본 예산 적용",
                value=budget_manager.is_auto_reset_enabled(),
                help="활성화 시 새로운 월에 자동으로 기본 예산이 복사됩니다"
            )
            
            if auto_reset != budget_manager.is_auto_reset_enabled():
                budget_manager.set_auto_reset(auto_reset)
                st.success("✅ 자동 갱신 설정이 변경되었습니다")
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 예산 템플릿")
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown("**기본 예산 → 특정 월로 복사**")
                
                if budget_manager.budgets['default']:
                    copy_to_month = st.text_input(
                        "대상 월 (예: 2025-02)",
                        placeholder="2025-02"
                    )
                    
                    if st.button("📋 복사 실행", use_container_width=True):
                        if copy_to_month and len(copy_to_month) == 7:
                            budget_manager.copy_default_to_month(copy_to_month)
                            st.success(f"✅ 기본 예산이 {copy_to_month}로 복사되었습니다")
                            st.rerun()
                        else:
                            st.error("⚠️ 올바른 형식으로 입력하세요 (예: 2025-02)")
                else:
                    st.info("기본 예산을 먼저 설정해주세요")
            
            with col_t2:
                st.markdown("**월별 예산 삭제**")
                
                monthly_budgets = budget_manager.get_monthly_budgets_list()
                
                if monthly_budgets:
                    delete_month = st.selectbox(
                        "삭제할 월 선택",
                        options=monthly_budgets
                    )
                    
                    if st.button("🗑️ 삭제 실행", use_container_width=True):
                        budget_manager.delete_monthly_budget(delete_month)
                        st.success(f"✅ {delete_month} 예산이 삭제되었습니다")
                        st.rerun()
                else:
                    st.info("설정된 월별 예산이 없습니다")
    
    st.markdown("---")
    
    alerts = budget_manager.get_alerts(df, target_month)
    if alerts:
        st.markdown("### 🔔 알림")
        for alert in alerts:
            if alert['level'] == 'error':
                st.error(alert['message'])
            elif alert['level'] == 'warning':
                st.warning(alert['message'])
            else:
                st.info(alert['message'])
        st.markdown("---")
    
    summary = budget_manager.get_monthly_summary(df, target_month)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💵 총 예산", f"{summary['총_예산']:,.0f}원")
    with col2:
        st.metric("💸 총 지출", f"{summary['총_지출']:,.0f}원")
    with col3:
        st.metric("💰 총 잔여", f"{summary['총_잔여']:,.0f}원")
    with col4:
        st.metric("📊 전체 사용률", f"{summary['전체_사용률']:.1f}%")
    
    st.markdown("---")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("### ⚙️ 예산 설정")
        
        if target_month and target_month in budget_manager.budgets['monthly']:
            st.info(f"📆 **{target_month} 전용 예산**을 설정합니다")
        else:
            st.info("📅 **기본 예산** (모든 월에 적용)")
        
        categories = df['분류'].unique().tolist()
        selected_category = st.selectbox("카테고리 선택", categories)
        
        current_budget = budget_manager.get_budget(selected_category, target_month)
        st.info(f"현재 예산: {current_budget:,.0f}원")
        
        new_budget = st.number_input(
            "새 예산 설정 (원)",
            min_value=0,
            value=int(current_budget) if current_budget > 0 else 100000,
            step=10000
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 예산 저장", type="primary"):
                budget_manager.set_budget(selected_category, new_budget, target_month)
                st.success(f"✅ {selected_category} 예산이 {new_budget:,.0f}원으로 설정되었습니다!")
                st.rerun()
        
        with col_btn2:
            if st.button("🗑️ 예산 삭제"):
                budget_manager.delete_budget(selected_category, target_month)
                st.success(f"✅ {selected_category} 예산이 삭제되었습니다!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 💡 AI 예산 추천")
        st.caption("과거 지출 평균 + 20% 여유분")
        
        if 'suggested_budgets' not in st.session_state:
            st.session_state['suggested_budgets'] = None
        
        if st.button("🔮 예산 추천 받기", key="suggest_budget_btn"):
            suggested = budget_manager.suggest_budget(df)
            st.session_state['suggested_budgets'] = suggested
        
        if st.session_state['suggested_budgets']:
            st.markdown("**추천 예산:**")
            
            for cat, amount in st.session_state['suggested_budgets'].items():
                st.write(f"- **{cat}**: {amount:,.0f}원")
            
            st.markdown("")
            
            col_apply1, col_apply2 = st.columns([1, 1])
            
            with col_apply1:
                if st.button("📥 추천 예산 일괄 적용", type="primary", use_container_width=True, key="apply_all_btn"):
                    for cat, amount in st.session_state['suggested_budgets'].items():
                        budget_manager.set_budget(cat, amount, target_month)
                    
                    st.success("✅ 추천 예산이 일괄 적용되었습니다!")
                    st.session_state['suggested_budgets'] = None
                    st.rerun()
            
            with col_apply2:
                if st.button("❌ 추천 취소", use_container_width=True, key="cancel_suggest_btn"):
                    st.session_state['suggested_budgets'] = None
                    st.rerun()
    
    with col_right:
        st.markdown("### 📊 예산 현황")
        
        analysis = budget_manager.analyze_spending(df, target_month)
        
        if not analysis.empty:
            st.dataframe(
                analysis.style.format({
                    '예산': '{:,.0f}원',
                    '지출': '{:,.0f}원',
                    '잔여': '{:,.0f}원',
                    '사용률(%)': '{:.1f}%'
                }),
                use_container_width=True
            )
            
            st.markdown("### 📈 카테고리별 사용률")
            
            fig_budget = go.Figure()
            
            for _, row in analysis.iterrows():
                color = '#EF4444' if row['사용률(%)'] >= 100 else \
                        '#F59E0B' if row['사용률(%)'] >= 80 else \
                        '#10B981'
                
                fig_budget.add_trace(go.Bar(
                    x=[min(row['사용률(%)'], 100)],
                    y=[row['카테고리']],
                    orientation='h',
                    name=row['카테고리'],
                    marker_color=color,
                    text=f"{row['사용률(%)']:.1f}%",
                    textposition='inside',
                    showlegend=False
                ))
            
            fig_budget.update_layout(
                xaxis_title="사용률 (%)",
                xaxis_range=[0, 100],
                height=300,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_budget, use_container_width=True)
        else:
            st.info("예산이 설정된 카테고리가 없습니다. 왼쪽에서 예산을 설정해주세요.")
    
    if len(available_months) > 1:
        st.markdown("---")
        st.markdown("### 📊 월별 예산 사용률 추이")
        
        comparison_df = budget_manager.get_monthly_comparison(df)
        
        if not comparison_df.empty:
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Scatter(
                x=comparison_df['월'],
                y=comparison_df['예산'],
                mode='lines+markers',
                name='예산',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=10)
            ))
            
            fig_comparison.add_trace(go.Scatter(
                x=comparison_df['월'],
                y=comparison_df['지출'],
                mode='lines+markers',
                name='지출',
                line=dict(color='#EF4444', width=3),
                marker=dict(size=10)
            ))
            
            fig_comparison.update_layout(
                xaxis_title="월",
                yaxis_title="금액 (원)",
                legend=dict(orientation="h", y=1.1),
                height=400
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            fig_usage = go.Figure()
            
            fig_usage.add_trace(go.Scatter(
                x=comparison_df['월'],
                y=comparison_df['사용률(%)'],
                mode='lines+markers',
                name='사용률',
                line=dict(color='#F59E0B', width=3),
                marker=dict(size=12),
                fill='tozeroy',
                fillcolor='rgba(245, 158, 11, 0.1)'
            ))
            
            fig_usage.add_hline(y=80, line_dash="dash", line_color="red", 
                               annotation_text="위험 (80%)")
            fig_usage.add_hline(y=60, line_dash="dash", line_color="orange", 
                               annotation_text="주의 (60%)")
            
            fig_usage.update_layout(
                xaxis_title="월",
                yaxis_title="사용률 (%)",
                yaxis_range=[0, max(comparison_df['사용률(%)'].max() + 10, 110)],
                height=300
            )
            
            st.plotly_chart(fig_usage, use_container_width=True)
            
            st.markdown("### 📋 월별 상세 내역")
            st.dataframe(
                comparison_df.style.format({
                    '예산': '{:,.0f}원',
                    '지출': '{:,.0f}원',
                    '잔여': '{:,.0f}원',
                    '사용률(%)': '{:.1f}%'
                }),
                use_container_width=True
            )

# 탭5: 통계 대시보드
with tab5:
    st.subheader("📉 고급 통계 분석")
    
    stats = get_statistics(df)
    
    st.markdown("### 💡 핵심 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "월평균 지출",
            f"{stats['월평균_지출']:,.0f}원",
            help="전체 기간의 월별 평균 지출액"
        )
    
    with col2:
        st.metric(
            "평균 거래 금액",
            f"{stats['평균_지출']:,.0f}원",
            help="지출 건당 평균 금액"
        )
    
    with col3:
        st.metric(
            "저축률",
            f"{stats['저축률']:.1f}%",
            help="(수입 - 지출) / 수입 × 100"
        )
    
    with col4:
        st.metric(
            "카테고리 수",
            f"{stats['카테고리_수']}개",
            help="사용 중인 카테고리 개수"
        )
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 💸 지출 통계")
        
        expense_stats = pd.DataFrame({
            '항목': [
                '총 지출',
                '월평균 지출',
                '건당 평균 지출',
                '최대 단건 지출',
                '최소 단건 지출',
                '지출 건수'
            ],
            '값': [
                f"{stats['총_지출']:,.0f}원",
                f"{stats['월평균_지출']:,.0f}원",
                f"{stats['평균_지출']:,.0f}원",
                f"{stats['최대_지출']:,.0f}원",
                f"{stats['최소_지출']:,.0f}원",
                f"{stats['지출_건수']}건"
            ]
        })
        
        st.dataframe(
            expense_stats,
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"💡 **최대 지출 항목**: {stats['최대_지출_항목']}")
    
    with col_right:
        st.markdown("### 💵 수입 & 카테고리")
        
        income_stats = pd.DataFrame({
            '항목': [
                '총 수입',
                '월평균 수입',
                '순수익 (수입-지출)',
                '저축률',
                '수입 건수',
                '최다 지출 카테고리'
            ],
            '값': [
                f"{stats['총_수입']:,.0f}원",
                f"{stats['월평균_수입']:,.0f}원",
                f"{stats['순수익']:,.0f}원",
                f"{stats['저축률']:.1f}%",
                f"{stats['수입_건수']}건",
                stats['최다_지출_카테고리']
            ]
        })
        
        st.dataframe(
            income_stats,
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")
    
    st.markdown("### 📊 지출 금액 분포")
    
    expense_df = df[df['구분'] == '지출']
    
    if len(expense_df) > 0:
        fig_hist = px.histogram(
            expense_df,
            x='금액_절대값',
            nbins=20,
            labels={'금액_절대값': '지출 금액 (원)', 'count': '거래 건수'},
            title='지출 금액 분포 히스토그램',
            color_discrete_sequence=['#FF5252']
        )
        
        fig_hist.update_layout(
            xaxis_title="지출 금액 (원)",
            yaxis_title="거래 건수",
            showlegend=False
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("지출 데이터가 없습니다")
    
    st.markdown("---")
    
    st.markdown("### 📅 요일별 지출 패턴")
    
    expense_df_copy = expense_df.copy()
    expense_df_copy['요일'] = expense_df_copy['날짜'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_map = {
        'Monday': '월', 'Tuesday': '화', 'Wednesday': '수',
        'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'
    }
    
    weekday_spending = expense_df_copy.groupby('요일')['금액_절대값'].sum().reindex(weekday_order, fill_value=0)
    weekday_spending.index = [weekday_map[day] for day in weekday_spending.index]
    
    fig_weekday = px.bar(
        x=weekday_spending.index,
        y=weekday_spending.values,
        labels={'x': '요일', 'y': '총 지출 (원)'},
        title='요일별 지출 금액',
        color=weekday_spending.values,
        color_continuous_scale='Reds'
    )
    
    fig_weekday.update_layout(showlegend=False)
    st.plotly_chart(fig_weekday, use_container_width=True)
    
    weekday_avg = expense_df_copy.groupby('요일')['금액_절대값'].mean().reindex(weekday_order, fill_value=0)
    weekday_avg.index = [weekday_map[day] for day in weekday_avg.index]
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        max_day = weekday_avg.idxmax()
        st.info(f"📈 **가장 많이 쓰는 요일**: {max_day} ({weekday_avg.max():,.0f}원/건)")
    
    with col_w2:
        min_day = weekday_avg.idxmin()
        st.success(f"📉 **가장 적게 쓰는 요일**: {min_day} ({weekday_avg.min():,.0f}원/건)")
    
    st.markdown("---")
    st.markdown("### 📥 통계 데이터 내보내기")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        if st.button("📊 통계 Excel 다운로드", use_container_width=True):
            with st.spinner("Excel 생성 중..."):
                excel_buffer = export_manager.export_statistics_to_excel(df, stats)
                
                filename = export_manager.get_filename_with_timestamp('statistics')
                
                st.download_button(
                    label="📥 Excel 파일 다운로드",
                    data=excel_buffer,
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with col_export2:
        st.info("💡 모든 통계 데이터가 여러 시트로 구성된 Excel 파일로 저장됩니다")

# 탭6: 데이터 탐색
with tab6:
    st.subheader("🔍 원본 데이터 탐색")
    
    #  즐겨찾기 필터
    st.markdown("### ⭐ 빠른 필터")
    
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        if st.button("📅 이번 달", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'month',
                'value': pd.Timestamp.now().strftime('%Y-%m')
            }
    
    with col_f2:
        if st.button("☕ 카페 지출", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'category',
                'value': '카페'
            }
    
    with col_f3:
        if st.button("🍔 식비 전체", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'category',
                'value': '식비'
            }
    
    with col_f4:
        if st.button("💳 고액 거래", use_container_width=True):
            st.session_state['quick_filter'] = {
                'type': 'amount',
                'value': 100000
            }
    
    with col_f5:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state['quick_filter'] = None
    
    # 빠른 필터 적용
    if 'quick_filter' in st.session_state and st.session_state['quick_filter']:
        filter_info = st.session_state['quick_filter']
        
        if filter_info['type'] == 'month':
            filtered_df_quick = df[df['년월'] == filter_info['value']]
            st.info(f"📅 필터 적용: {filter_info['value']} ({len(filtered_df_quick)}건)")
        elif filter_info['type'] == 'category':
            filtered_df_quick = df[df['분류'] == filter_info['value']]
            st.info(f"📂 필터 적용: {filter_info['value']} ({len(filtered_df_quick)}건)")
        elif filter_info['type'] == 'amount':
            filtered_df_quick = df[df['금액_절대값'] >= filter_info['value']]
            st.info(f"💰 필터 적용: {filter_info['value']:,}원 이상 ({len(filtered_df_quick)}건)")
    else:
        filtered_df_quick = df
    
    st.markdown("---")
    
    st.markdown("### 🔧 상세 필터")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        available_categories = filtered_df_quick['분류'].unique()
        filter_category = st.multiselect(
            "카테고리 필터",
            options=available_categories,
            default=available_categories
        )
    
    with col_f2:
        filter_type = st.multiselect(
            "구분 필터",
            options=['수입', '지출'],
            default=['수입', '지출']
        )
    
    filtered_df = filtered_df_quick[
        (filtered_df_quick['분류'].isin(filter_category)) & 
        (filtered_df_quick['구분'].isin(filter_type))
    ]
    
    sort_column = st.selectbox(
        "정렬 기준",
        options=['날짜', '금액_절대값', '분류'],
        index=0
    )
    sort_order = st.radio("정렬 순서", ['내림차순', '오름차순'], horizontal=True)
    ascending = (sort_order == '오름차순')
    
    display_df = filtered_df.sort_values(sort_column, ascending=ascending)
    
    st.markdown(f"**{len(display_df)}건의 거래 내역**")
    
    #  편집 모드 토글
    col_edit1, col_edit2 = st.columns([1, 4])
    
    with col_edit1:
        edit_mode = st.checkbox("✏️ 편집 모드", help="메모를 직접 수정할 수 있습니다")
    
    with col_edit2:
        if edit_mode:
            st.info("💡 메모 칸을 더블클릭하여 수정한 후 엔터를 누르세요")
    
    display_cols = ['날짜', '적요', '금액', '분류', '구분']
    if '분류_AI' in display_df.columns:
        display_cols.append('분류_AI')
    if '메모' in display_df.columns:
        display_cols.append('메모')
    
    if edit_mode and '메모' in display_df.columns:
        edited_df = st.data_editor(
            display_df[display_cols],
            use_container_width=True,
            num_rows="fixed",
            disabled=(['날짜', '적요', '금액', '분류', '구분', '분류_AI'] if '분류_AI' in display_cols else ['날짜', '적요', '금액', '분류', '구분']),
            column_config={
                "날짜": st.column_config.DateColumn(
                    "날짜",
                    format="YYYY-MM-DD",
                ),
                "금액": st.column_config.NumberColumn(
                    "금액",
                    format="%d원",
                ),
                "메모": st.column_config.TextColumn(
                    "메모",
                    help="더블클릭하여 수정",
                    max_chars=100,
                )
            },
            key="editable_table"
        )
        
        col_save1, col_save2 = st.columns([1, 4])
        
        with col_save1:
            if st.button("💾 변경사항 저장", type="primary", use_container_width=True):
                try:
                    import os
                    csv_path = 'data/user_expenses.csv'
                    os.makedirs('data', exist_ok=True)
                    edited_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    st.success("✅ 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 저장 실패: {str(e)}")
        
        with col_save2:
            st.caption("⚠️ 저장하지 않으면 변경사항이 사라집니다")
    
    else:
        st.dataframe(
            display_df[display_cols].style.format({'금액': '{:,.0f}원'}),
            use_container_width=True
        )
    
    csv = display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 필터링된 데이터 다운로드 (CSV)",
        data=csv,
        file_name="filtered_expense.csv",
        mime="text/csv"
    )

# 탭7: 카테고리 관리
with tab7:
    st.subheader("📁 카테고리 관리")
    
    st.markdown("""
    카테고리를 추가, 수정, 삭제하거나 여러 카테고리를 하나로 병합할 수 있습니다.
    """)
    
    st.markdown("---")
    
    # 현재 카테고리 목록
    st.markdown("### 📋 현재 카테고리")
    
    categories = category_manager.get_all_categories()
    cat_stats = category_manager.get_category_statistics(df)
    
    # 사용 현황 표시
    category_usage = []
    for cat in categories:
        usage = cat_stats.get(cat, {'count': 0, 'exists': False})
        category_usage.append({
            '카테고리': cat,
            '사용 건수': usage['count'],
            '상태': '✅ 사용중' if usage['exists'] else '⚪ 미사용'
        })
    
    usage_df = pd.DataFrame(category_usage)
    st.dataframe(usage_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 기능 선택
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### ➕ 카테고리 추가")
        new_category = st.text_input("새 카테고리 이름", key="new_cat")
        
        if st.button("추가", type="primary", use_container_width=True):
            result = category_manager.add_category(new_category)
            if result['success']:
                st.success(result['message'])
                st.rerun()
            else:
                st.error(result['message'])
    
    with col2:
        st.markdown("### ✏️ 카테고리 이름 변경")
        old_cat = st.selectbox("변경할 카테고리", categories, key="old_cat")
        new_cat_name = st.text_input("새 이름", key="rename_cat")
        
        if st.button("변경", use_container_width=True):
            result = category_manager.rename_category(old_cat, new_cat_name)
            if result['success']:
                st.success(result['message'])
                st.rerun()
            else:
                st.error(result['message'])
    
    with col3:
        st.markdown("### 🗑️ 카테고리 삭제")
        del_cat = st.selectbox("삭제할 카테고리", categories, key="del_cat")
        
        if st.button("삭제", use_container_width=True):
            result = category_manager.delete_category(del_cat)
            if result['success']:
                st.success(result['message'])
                st.warning(f"⚠️ 기존 '{del_cat}' 데이터는 '기타'로 변경됩니다")
                st.rerun()
            else:
                st.error(result['message'])
    
    st.markdown("---")
    
    # 카테고리 병합
    st.markdown("### 🔀 카테고리 병합")
    st.caption("여러 카테고리를 하나로 합칠 수 있습니다 (예: '외식', '식당' → '식비')")
    
    col_merge1, col_merge2 = st.columns([2, 1])
    
    with col_merge1:
        merge_sources = st.multiselect(
            "병합할 카테고리 (여러 개 선택)",
            categories,
            key="merge_sources"
        )
    
    with col_merge2:
        merge_target = st.text_input("→ 통합될 카테고리", key="merge_target")
    
    if st.button("🔀 병합 실행", type="primary"):
        if merge_sources and merge_target:
            result = category_manager.merge_categories(merge_sources, merge_target)
            if result['success']:
                st.success(result['message'])
                st.rerun()
            else:
                st.error(result['message'])
        else:
            st.warning("병합할 카테고리와 대상 카테고리를 모두 입력해주세요")
    
    st.markdown("---")
    
    # 초기화
    st.markdown("### 🔄 기본 카테고리로 초기화")
    st.warning("⚠️ 모든 사용자 정의 카테고리가 삭제되고 기본 카테고리로 복원됩니다")
    
    if st.button("기본값으로 초기화", use_container_width=True):
        result = category_manager.reset_to_default()
        st.success(result['message'])
        st.rerun()

# 탭8: 데이터 검증
with tab8:
    st.subheader("✅ 데이터 검증 및 품질 체크")
    
    st.markdown("""
    업로드된 데이터의 오류, 이상치, 개선 사항을 자동으로 검사합니다.
    """)
    
    st.markdown("---")
    
    # 검증 실행 버튼
    if st.button("🔍 데이터 검증 시작", type="primary", use_container_width=True):
        with st.spinner("검증 중..."):
            validation_results = data_validator.validate(df)
            summary = data_validator.get_summary()
            
            # 요약 표시
            if summary['status'] == 'excellent':
                st.success(summary['message'])
            elif summary['status'] == 'error':
                st.error(summary['message'])
            elif summary['status'] == 'warning':
                st.warning(summary['message'])
            else:
                st.info(summary['message'])
            
            st.markdown("---")
            
            # 오류 표시
            if validation_results['errors']:
                st.markdown("### ❌ 오류 (즉시 수정 필요)")
                
                for error in validation_results['errors']:
                    with st.expander(f"🔴 {error['message']}", expanded=True):
                        st.error(f"**심각도:** {error['severity']}")
                        if 'details' in error:
                            st.json(error['details'])
            
            # 경고 표시
            if validation_results['warnings']:
                st.markdown("### ⚠️ 경고 (확인 권장)")
                
                for warning in validation_results['warnings']:
                    with st.expander(f"🟡 {warning['message']}"):
                        st.warning(f"**심각도:** {warning['severity']}")
                        
                        if 'details' in warning:
                            st.markdown("**상세 내역:**")
                            details_df = pd.DataFrame(warning['details'])
                            st.dataframe(details_df, use_container_width=True)
                        
                        if 'suggestion' in warning:
                            st.info(f"💡 **제안:** {warning['suggestion']}")
                        
                        if 'threshold' in warning:
                            st.caption(f"기준값: {warning['threshold']}")
            
            # 개선 제안 표시
            if validation_results['suggestions']:
                st.markdown("### 💡 개선 제안")
                
                for suggestion in validation_results['suggestions']:
                    with st.expander(f"💡 {suggestion['message']}"):
                        if 'suggestion' in suggestion:
                            st.info(suggestion['suggestion'])
                        
                        if 'details' in suggestion:
                            st.markdown("**상세 내역:**")
                            if isinstance(suggestion['details'], list):
                                details_df = pd.DataFrame(suggestion['details'])
                                st.dataframe(details_df, use_container_width=True)
                            else:
                                st.json(suggestion['details'])
            
            st.markdown("---")
            
            # 통계 요약
            st.markdown("### 📊 검증 통계")
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            with col_s1:
                st.metric("총 검사 항목", summary['total_issues'])
            with col_s2:
                st.metric("오류", len(validation_results['errors']))
            with col_s3:
                st.metric("경고", len(validation_results['warnings']))
            with col_s4:
                st.metric("개선 제안", len(validation_results['suggestions']))
    
    else:
        st.info("👆 위의 버튼을 클릭하여 데이터 검증을 시작하세요")
        
        st.markdown("---")
        st.markdown("### 📋 검증 항목")
        
        checks = [
            "✅ 필수 컬럼 확인 (날짜, 금액)",
            "✅ 날짜 유효성 검사 (미래 날짜, 이상 범위)",
            "✅ 금액 검사 (0원 거래, 비정상적 큰 금액)",
            "✅ 중복 거래 탐지",
            "✅ 통계적 이상치 탐지 (IQR 방법)",
            "✅ 누락 항목 확인 (적요, 카테고리)",
            "✅ 카테고리 일관성 검사",
            "✅ 비슷한 카테고리 탐지"
        ]
        
        for check in checks:
            st.markdown(f"- {check}")

# 탭9: AI 학습
with tab9:
    st.subheader("🤖 AI 모델 학습 및 평가")
    
    st.markdown("""
    ### AI 자동 분류란?
    - '적요' (거래 내역 설명)를 분석하여 자동으로 카테고리를 예측합니다
    - 예: "스타벅스" → 카페, "이마트" → 식비, "CGV" → 여가
    
    ### 학습 방법
    1. 카테고리가 포함된 CSV/Excel 파일 업로드
    2. 아래 '모델 학습' 버튼 클릭
    3. 이후 카테고리 없는 데이터도 자동 분류 가능!
    
    ⚠️ **주의:** 정확한 학습을 위해 최소 100건 이상의 데이터를 권장합니다.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 현재 모델 상태")
        if classifier.pipeline is None:
            st.warning("⚠️ 학습된 모델이 없습니다")
        else:
            st.success("✅ 모델 로드 완료")
            
            if st.button("🎯 모델 정확도 평가"):
                if '분류' in df.columns and len(df) > 0:
                    with st.spinner('평가 중...'):
                        result = classifier.evaluate(df)
                        st.metric("정확도", f"{result['accuracy']*100:.1f}%")
                        st.caption(f"{result['correct']}건 정확 / 전체 {result['total']}건")
                else:
                    st.error("'분류' 컬럼이 있는 데이터가 필요합니다")
    
    with col2:
        st.markdown("### 🎓 모델 학습")
        
        if '분류' in df.columns and '적요' in df.columns:
            st.info(f"현재 데이터: {len(df)}건")
            
            if len(df) < 50:
                st.warning("⚠️ 데이터가 너무 적습니다. 최소 50건 이상 권장합니다.")
            
            if st.button("🚀 모델 학습 시작", type="primary"):
                with st.spinner('학습 중... (수십 초 소요)'):
                    try:
                        classifier.train(df)
                        st.success("✅ 학습 완료!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"학습 실패: {str(e)}")
        else:
            st.warning("학습을 위해서는 '적요'와 '분류' 컬럼이 필요합니다")
    
    st.markdown("---")
    
    st.markdown("### 🧪 실시간 예측 테스트")
    test_text = st.text_input(
        "적요 입력",
        placeholder="예: 스타벅스, 이마트, CGV 등",
        help="거래 내역 설명을 입력하면 AI가 카테고리를 예측합니다"
    )
    
    if test_text:
        predicted_category = classifier.predict(test_text)
        st.success(f"🎯 예측 카테고리: **{predicted_category}**")

# 🆕 탭10: 저축 목표
with tab10:
    st.subheader("🎯 저축 목표 관리")
    
    st.markdown("""
    장기적인 재무 목표를 설정하고 진행 상황을 추적하세요.
    - 여행 자금, 비상금, 자동차 구매 등 다양한 목표 설정 가능
    - 실시간 진행률 및 달성 가능성 분석
    - 일일/월별 저축 권장액 자동 계산
    """)
    
    st.markdown("---")
    
    # 목표 추가
    with st.expander("➕ 새 목표 추가", expanded=False):
        with st.form("add_goal_form"):
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                goal_name = st.text_input("목표 이름", placeholder="예: 여행 자금")
                goal_amount = st.number_input("목표 금액 (원)", min_value=0, step=100000, value=3000000)
            
            with col_g2:
                goal_date = st.date_input(
                    "목표 날짜",
                    value=datetime.now() + timedelta(days=365),
                    min_value=datetime.now()
                )
                goal_desc = st.text_area("설명 (선택)", placeholder="목표에 대한 간단한 설명")
            
            submitted = st.form_submit_button("💾 목표 추가", use_container_width=True)
            
            if submitted:
                result = savings_goal_manager.add_goal(
                    name=goal_name,
                    target_amount=goal_amount,
                    target_date=goal_date,
                    description=goal_desc
                )
                
                if result['success']:
                    st.success(result['message'])
                    st.balloons()
                    st.rerun()
                else:
                    st.error(result['message'])
    
    st.markdown("---")
    
    # 활성 목표 목록
    active_goals = savings_goal_manager.get_active_goals()
    
    if not active_goals:
        st.info("📝 아직 설정된 목표가 없습니다. 위에서 새 목표를 추가해보세요!")
    else:
        st.markdown("### 📋 현재 목표")
        
        for goal_data in savings_goal_manager.get_all_progress(df):
            goal = goal_data['goal']
            progress = goal_data['progress']
            
            with st.container():
                st.markdown(f"#### {goal['name']}")
                
                if goal.get('description'):
                    st.caption(goal['description'])
                
                # 진행률 표시
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                
                with col_p1:
                    st.metric(
                        "현재 저축액",
                        f"{progress['current_savings']:,.0f}원",
                        f"{progress['progress_rate']:.1f}%"
                    )
                
                with col_p2:
                    st.metric(
                        "목표 금액",
                        f"{progress['target_amount']:,.0f}원",
                        f"D-{progress['remaining_days']}"
                    )
                
                with col_p3:
                    st.metric(
                        "남은 금액",
                        f"{progress['remaining_amount']:,.0f}원"
                    )
                
                with col_p4:
                    st.metric(
                        "일일 저축 필요액",
                        f"{progress['daily_need']:,.0f}원"
                    )
                
                # 프로그레스 바
                st.progress(min(progress['progress_rate'] / 100, 1.0))
                
                # 달성 가능성 분석
                if progress['estimated_date']:
                    if progress['is_achievable']:
                        st.success(f"✅ 현재 속도로 {progress['estimated_date'].strftime('%Y-%m-%d')}에 달성 가능합니다!")
                    else:
                        st.warning(f"⚠️ 현재 속도로는 {progress['estimated_date'].strftime('%Y-%m-%d')}에 달성됩니다. 더 빠른 저축이 필요합니다.")
                else:
                    st.info("💡 더 많은 데이터가 쌓이면 달성 예측이 표시됩니다")
                
                # 월별 권장 저축액
                monthly_need = savings_goal_manager.suggest_monthly_savings(goal, progress['current_savings'])
                st.info(f"📅 **월별 권장 저축액**: {monthly_need:,.0f}원")
                
                # 목표 관리 버튼
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
                
                with col_btn1:
                    if progress['progress_rate'] >= 100:
                        if st.button("🎉 완료", key=f"complete_{goal['id']}", use_container_width=True):
                            savings_goal_manager.mark_as_completed(goal['id'])
                            st.success("목표를 달성했습니다! 🎉")
                            st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ 삭제", key=f"delete_goal_{goal['id']}", use_container_width=True):
                        savings_goal_manager.delete_goal(goal['id'])
                        st.success("목표가 삭제되었습니다")
                        st.rerun()
                
                st.markdown("---")

# 🆕 탭11: 반복 거래
with tab11:
    st.subheader("🔄 반복 거래 관리")
    
    st.markdown("""
    구독료, 월세, 통신비 등 주기적으로 발생하는 거래를 자동으로 관리하세요.
    - 매일/매주/매월/매년 주기 설정
    - 미래 거래 자동 생성
    - 활성/비활성 전환
    """)
    
    st.markdown("---")
    
    # 반복 거래 추가
    with st.expander("➕ 반복 거래 추가", expanded=False):
        with st.form("add_recurring_form"):
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                rec_name = st.text_input("거래명", placeholder="예: 넷플릭스")
                rec_amount = st.number_input(
                    "금액 (지출은 음수)",
                    value=-14500,
                    step=1000,
                    help="지출: 음수, 수입: 양수"
                )
                rec_category = st.selectbox(
                    "카테고리",
                    options=category_manager.get_all_categories()
                )
            
            with col_r2:
                rec_frequency = st.selectbox(
                    "주기",
                    options=list(recurring_manager.FREQUENCY_TYPES.keys()),
                    format_func=lambda x: recurring_manager.FREQUENCY_TYPES[x]
                )
                
                rec_start = st.date_input(
                    "시작 날짜",
                    value=datetime.now()
                )
                
                if rec_frequency == 'monthly':
                    rec_day = st.number_input("매월 실행일 (1-31)", min_value=1, max_value=31, value=5)
                elif rec_frequency == 'weekly':
                    rec_day = st.selectbox("매주 실행 요일", options=[0,1,2,3,4,5,6], 
                                          format_func=lambda x: ['월','화','수','목','금','토','일'][x])
                else:
                    rec_day = 1
            
            rec_memo = st.text_input("메모 (선택)", placeholder="월 구독료")
            
            submitted_rec = st.form_submit_button("💾 반복 거래 추가", use_container_width=True)
            
            if submitted_rec:
                result = recurring_manager.add_recurring(
                    name=rec_name,
                    amount=rec_amount,
                    category=rec_category,
                    frequency=rec_frequency,
                    start_date=rec_start,
                    day_of_execution=rec_day,
                    memo=rec_memo
                )
                
                if result['success']:
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result['message'])
    
    st.markdown("---")
    
    # 활성 반복 거래 목록
    active_recurring = recurring_manager.get_active_recurring()
    
    if not active_recurring:
        st.info("📝 등록된 반복 거래가 없습니다. 위에서 추가해보세요!")
    else:
        st.markdown("### 📋 등록된 반복 거래")
        
        # 테이블 형식으로 표시
        recurring_data = []
        for rec in active_recurring:
            recurring_data.append({
                'ID': rec['id'],
                '거래명': rec['name'],
                '금액': f"{rec['amount']:,.0f}원",
                '카테고리': rec['category'],
                '주기': recurring_manager.FREQUENCY_TYPES[rec['frequency']],
                '시작일': rec['start_date'],
                '상태': '🟢 활성' if rec.get('active', True) else '⚪ 비활성'
            })
        
        recurring_df = pd.DataFrame(recurring_data)
        st.dataframe(recurring_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 향후 30일 미리보기
        st.markdown("### 📅 향후 30일 예정 거래")
        
        upcoming = recurring_manager.get_upcoming_transactions(days=30)
        
        if upcoming:
            upcoming_df = pd.DataFrame(upcoming)
            upcoming_df['날짜'] = pd.to_datetime(upcoming_df['날짜']).dt.strftime('%Y-%m-%d')
            
            display_cols = ['날짜', '적요', '금액', '분류']
            st.dataframe(
                upcoming_df[display_cols].style.format({'금액': '{:,.0f}원'}),
                use_container_width=True
            )
            
            total_expense = sum(t['금액'] for t in upcoming if t['금액'] < 0)
            total_income = sum(t['금액'] for t in upcoming if t['금액'] > 0)
            
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            with col_sum1:
                st.metric("예정 지출", f"{abs(total_expense):,.0f}원")
            with col_sum2:
                st.metric("예정 수입", f"{total_income:,.0f}원")
            with col_sum3:
                st.metric("순예정액", f"{total_income + total_expense:,.0f}원")
        else:
            st.info("향후 30일 동안 예정된 반복 거래가 없습니다")
        
        st.markdown("---")
        
        # 반복 거래 관리
        st.markdown("### ⚙️ 반복 거래 관리")
        
        col_mgmt1, col_mgmt2 = st.columns(2)
        
        with col_mgmt1:
            st.markdown("**거래 활성/비활성**")
            toggle_id = st.selectbox(
                "거래 선택",
                options=[r['id'] for r in active_recurring],
                format_func=lambda x: next(r['name'] for r in active_recurring if r['id'] == x)
            )
            
            if st.button("🔄 활성/비활성 전환", use_container_width=True):
                result = recurring_manager.toggle_active(toggle_id)
                st.success(result['message'])
                st.rerun()
        
        with col_mgmt2:
            st.markdown("**거래 삭제**")
            delete_id = st.selectbox(
                "삭제할 거래",
                options=[r['id'] for r in active_recurring],
                format_func=lambda x: next(r['name'] for r in active_recurring if r['id'] == x),
                key="delete_recurring_select"
            )
            
            if st.button("🗑️ 삭제", use_container_width=True):
                result = recurring_manager.delete_recurring(delete_id)
                st.success(result['message'])
                st.rerun()
        
        st.markdown("---")
        
        # CSV에 자동 추가
        st.markdown("### 📥 CSV 파일에 반복 거래 자동 추가")
        
        col_auto1, col_auto2 = st.columns(2)
        
        with col_auto1:
            auto_start = st.date_input("추가 시작일", value=datetime.now())
        
        with col_auto2:
            auto_end = st.date_input("추가 종료일", value=datetime.now() + timedelta(days=30))
        
        if st.button("📝 user_expenses.csv에 추가", type="primary", use_container_width=True):
            csv_path = 'data/user_expenses.csv'
            result = recurring_manager.auto_add_to_csv(csv_path, auto_start, auto_end)
            
            if result['success']:
                if result['count'] > 0:
                    st.success(result['message'])
                    st.info("💡 페이지를 새로고침하여 변경사항을 확인하세요")
                else:
                    st.info(result['message'])
            else:
                st.error(result['message'])

# 🆕 탭12: 예측 & 비교 분석
with tab12:
    st.subheader("🔮 지출 예측 & 비교 분석")
    
    st.markdown("""
    과거 데이터를 분석하여 미래를 예측하고, 다양한 관점에서 소비 패턴을 비교하세요.
    """)
    
    # 서브탭
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "🔮 지출 예측",
        "📊 월별 비교",
        "🏷️ 태그 분석",
        "📈 패턴 분석"
    ])
    
    # 서브탭1: 지출 예측
    with subtab1:
        st.markdown("### 🔮 다음 달 지출 예측")
        
        # 전체 예측
        prediction_result = expense_predictor.predict_next_month(df)
        
        if prediction_result['success']:
            col_pred1, col_pred2, col_pred3, col_pred4 = st.columns(4)
            
            with col_pred1:
                st.metric(
                    "다음 달 예상 지출",
                    f"{prediction_result['prediction']:,.0f}원",
                    help="추세 70% + 계절성 30% 반영"
                )
            
            with col_pred2:
                trend_icon = "📈" if prediction_result['trend'] == 'increasing' else "📉" if prediction_result['trend'] == 'decreasing' else "➡️"
                trend_text = "상승" if prediction_result['trend'] == 'increasing' else "하락" if prediction_result['trend'] == 'decreasing' else "안정"
                st.metric(
                    "추세",
                    f"{trend_icon} {trend_text}",
                    help="최근 3개월 추세"
                )
            
            with col_pred3:
                st.metric(
                    "신뢰도",
                    f"{prediction_result['confidence']:.1f}%",
                    help="R² 스코어 기반"
                )
            
            with col_pred4:
                st.metric(
                    "데이터 기간",
                    f"{prediction_result['data_points']}개월",
                    help="예측에 사용된 데이터"
                )
            
            st.markdown("---")
            
            # 카테고리별 예측
            st.markdown("### 📊 카테고리별 예측")
            
            category_predictions = expense_predictor.predict_by_category(df)
            
            if not category_predictions.empty:
                st.dataframe(
                    category_predictions.style.format({
                        '최근 평균': '{:,.0f}원',
                        '예측 금액': '{:,.0f}원',
                        '전월 대비': '{:+.1f}%'
                    }),
                    use_container_width=True
                )
                
                # 예측 차트
                fig_pred = go.Figure()
                
                fig_pred.add_trace(go.Bar(
                    x=category_predictions['카테고리'],
                    y=category_predictions['예측 금액'],
                    name='예측 금액',
                    marker_color='#60a5fa'
                ))
                
                fig_pred.update_layout(
                    title="카테고리별 다음 달 예측",
                    xaxis_title="카테고리",
                    yaxis_title="금액 (원)",
                    template=theme_manager.get_plotly_template(),
                    showlegend=False
                )
                
                st.plotly_chart(fig_pred, use_container_width=True)
            else:
                st.info("카테고리별 예측을 위한 데이터가 부족합니다")
            
            st.markdown("---")
            
            # 예측 정확도
            st.markdown("### 🎯 예측 정확도 평가")
            
            accuracy = expense_predictor.get_prediction_accuracy(df)
            
            if accuracy['success']:
                col_acc1, col_acc2, col_acc3 = st.columns(3)
                
                with col_acc1:
                    st.metric("예측값", f"{accuracy['predicted']:,.0f}원")
                
                with col_acc2:
                    st.metric("실제값", f"{accuracy['actual']:,.0f}원")
                
                with col_acc3:
                    st.metric(
                        "정확도",
                        f"{accuracy['accuracy']:.1f}%",
                        f"{accuracy['error_rate']:+.1f}% 오차"
                    )
                
                if accuracy['accuracy'] >= 80:
                    st.success("✅ 예측 모델의 정확도가 매우 높습니다!")
                elif accuracy['accuracy'] >= 60:
                    st.info("📊 예측 모델의 정확도가 양호합니다")
                else:
                    st.warning("⚠️ 더 많은 데이터가 쌓이면 정확도가 향상됩니다")
            else:
                st.info(accuracy['message'])
            
            st.markdown("---")
            
            # 예산 조정 제안
            if budget_manager.budgets['default']:
                st.markdown("### 💡 예산 조정 제안")
                
                suggestions = expense_predictor.suggest_budget_adjustments(
                    df,
                    budget_manager.budgets['default']
                )
                
                if suggestions:
                    for sugg in suggestions:
                        with st.expander(f"📌 {sugg['카테고리']} - {sugg['사유']}"):
                            col_s1, col_s2, col_s3 = st.columns(3)
                            
                            with col_s1:
                                st.metric("현재 예산", f"{sugg['현재 예산']:,.0f}원")
                            
                            with col_s2:
                                st.metric("예상 지출", f"{sugg['예상 지출']:,.0f}원")
                            
                            with col_s3:
                                st.metric("조정 제안", f"{sugg['조정 제안']:,.0f}원")
                else:
                    st.success("✅ 현재 예산이 적정합니다!")
        
        else:
            st.warning(prediction_result['message'])
    
    # 서브탭2: 월별 비교
    with subtab2:
        st.markdown("### 📊 이번 달 vs 지난 달")
        
        comparison = comparison_analyzer.compare_this_month_vs_last_month(df)
        
        if comparison:
            summary = comparison['summary']
            
            # 요약 지표
            col_comp1, col_comp2 = st.columns(2)
            
            with col_comp1:
                st.markdown(f"#### {summary['month1']}")
                st.metric("지출", f"{summary['expense1']:,.0f}원")
                st.metric("수입", f"{summary['income1']:,.0f}원")
                st.metric("거래 건수", f"{summary['transaction_count1']}건")
            
            with col_comp2:
                st.markdown(f"#### {summary['month2']}")
                st.metric(
                    "지출", 
                    f"{summary['expense2']:,.0f}원",
                    f"{summary['expense_change']:+,.0f}원 ({summary['expense_change_pct']:+.1f}%)"
                )
                st.metric(
                    "수입",
                    f"{summary['income2']:,.0f}원",
                    f"{summary['income_change']:+,.0f}원 ({summary['income_change_pct']:+.1f}%)"
                )
                st.metric(
                    "거래 건수",
                    f"{summary['transaction_count2']}건",
                    f"{summary['transaction_count2'] - summary['transaction_count1']:+}건"
                )
            
            st.markdown("---")
            
            # 카테고리별 비교
            st.markdown("### 📋 카테고리별 변화")
            
            category_comp = comparison['category_comparison']
            
            if not category_comp.empty:
                st.dataframe(
                    category_comp.style.format({
                        summary['month1']: '{:,.0f}원',
                        summary['month2']: '{:,.0f}원',
                        '증감액': '{:+,.0f}원',
                        '증감률(%)': '{:+.1f}%'
                    }),
                    use_container_width=True
                )
                
                # 증감 상위/하위
                col_top1, col_top2 = st.columns(2)
                
                with col_top1:
                    st.markdown("#### 📈 증가 TOP 5")
                    top_increased = category_comp.nlargest(5, '증감액')[['카테고리', '증감액', '증감률(%)']]
                    
                    for _, row in top_increased.iterrows():
                        st.error(f"**{row['카테고리']}**: +{row['증감액']:,.0f}원 ({row['증감률(%)']:+.1f}%)")
                
                with col_top2:
                    st.markdown("#### 📉 감소 TOP 5")
                    top_decreased = category_comp.nsmallest(5, '증감액')[['카테고리', '증감액', '증감률(%)']]
                    
                    for _, row in top_decreased.iterrows():
                        st.success(f"**{row['카테고리']}**: {row['증감액']:,.0f}원 ({row['증감률(%)']:+.1f}%)")
        else:
            st.info("비교할 데이터가 부족합니다")
        
        st.markdown("---")
        
        # 요일별 패턴
        st.markdown("### 📅 요일별 소비 패턴")
        
        weekday_pattern = comparison_analyzer.get_weekday_pattern(df)
        
        if weekday_pattern is not None and not weekday_pattern.empty:
            st.dataframe(
                weekday_pattern.style.format({
                    '총지출': '{:,.0f}원',
                    '평균지출': '{:,.0f}원',
                    '거래건수': '{:.0f}건'
                }),
                use_container_width=True
            )
            
            # 요일별 차트
            fig_weekday = go.Figure()
            
            fig_weekday.add_trace(go.Bar(
                x=weekday_pattern.index,
                y=weekday_pattern['총지출'],
                name='총지출',
                marker_color='#ff5252'
            ))
            
            fig_weekday.update_layout(
                title="요일별 지출",
                xaxis_title="요일",
                yaxis_title="금액 (원)",
                template=theme_manager.get_plotly_template()
            )
            
            st.plotly_chart(fig_weekday, use_container_width=True)
        
        st.markdown("---")
        
        # 소비 속도 (월초/중/말)
        st.markdown("### ⚡ 월내 소비 속도")
        
        velocity = comparison_analyzer.get_spending_velocity(df)
        
        if velocity is not None and not velocity.empty:
            st.dataframe(
                velocity.style.format({
                    '총지출': '{:,.0f}원',
                    '평균지출': '{:,.0f}원',
                    '거래건수': '{:.0f}건'
                }),
                use_container_width=True
            )
            
            total_spending = velocity['총지출'].sum()
            
            for period in velocity.index:
                amount = velocity.loc[period, '총지출']
                percentage = (amount / total_spending * 100) if total_spending > 0 else 0
                
                st.progress(percentage / 100, text=f"{period}: {amount:,.0f}원 ({percentage:.1f}%)")
    
    # 서브탭3: 태그 분석
    with subtab3:
        st.markdown("### 🏷️ 태그 관리")
        
        # 태그 추가
        with st.expander("➕ 거래에 태그 추가", expanded=False):
            st.markdown("**태그를 추가할 거래를 선택하세요**")
            
            # 최근 거래 20건
            recent_df = df.sort_values('날짜', ascending=False).head(20)
            
            for idx, row in recent_df.iterrows():
                transaction_id = f"{row['날짜']}_{row['적요']}_{row['금액']}"
                existing_tags = tag_manager.get_transaction_tags(transaction_id)
                
                col_t1, col_t2, col_t3 = st.columns([2, 2, 1])
                
                with col_t1:
                    st.text(f"{row['날짜'].strftime('%Y-%m-%d')} | {row['적요']}")
                
                with col_t2:
                    st.text(f"{row['금액']:,.0f}원 | {row['분류']}")
                
                with col_t3:
                    if existing_tags:
                        st.caption(f"🏷️ {', '.join(existing_tags)}")
                    else:
                        st.caption("태그 없음")
                
                # 태그 추가 폼
                with st.form(f"tag_form_{idx}"):
                    col_tf1, col_tf2 = st.columns([3, 1])
                    
                    with col_tf1:
                        # 추천 태그
                        suggested = tag_manager.suggest_tags(row['적요'])
                        
                        selected_tags = st.multiselect(
                            "태그 선택",
                            options=tag_manager.get_all_tags(),
                            default=suggested[:2] if suggested else [],
                            key=f"tags_{idx}",
                            label_visibility="collapsed"
                        )
                    
                    with col_tf2:
                        if st.form_submit_button("추가", use_container_width=True):
                            if selected_tags:
                                result = tag_manager.add_tag_to_transaction(transaction_id, selected_tags)
                                if result['success']:
                                    st.success("✅")
                                    st.rerun()
                
                st.markdown("---")
        
        st.markdown("---")
        
        # 태그 통계
        st.markdown("### 📊 태그별 통계")
        
        tag_stats = tag_manager.get_tag_statistics(df)
        
        if not tag_stats.empty:
            st.dataframe(
                tag_stats.style.format({
                    '총 지출': '{:,.0f}원',
                    '평균 지출': '{:,.0f}원'
                }),
                use_container_width=True
            )
            
            # 인기 태그
            st.markdown("### 🌟 인기 태그 TOP 10")
            
            popular = tag_manager.get_popular_tags(10)
            
            if popular:
                for i, (tag, count) in enumerate(popular, 1):
                    st.write(f"{i}. **#{tag}** - {count}건")
        else:
            st.info("아직 태그가 없습니다. 위에서 거래에 태그를 추가해보세요!")
        
        st.markdown("---")
        
        # 태그 필터링
        st.markdown("### 🔍 태그로 필터링")
        
        all_tags = tag_manager.get_all_tags()
        
        if all_tags:
            selected_filter_tags = st.multiselect(
                "필터링할 태그",
                options=all_tags,
                help="선택한 태그가 포함된 거래만 표시"
            )
            
            match_all = st.checkbox("모든 태그 포함 (AND 조건)", value=False)
            
            if selected_filter_tags:
                filtered = tag_manager.filter_by_tags(df, selected_filter_tags, match_all)
                
                st.info(f"📌 {len(filtered)}건의 거래가 필터링되었습니다")
                
                if len(filtered) > 0:
                    display_cols = ['날짜', '적요', '금액', '분류', '태그']
                    st.dataframe(
                        filtered[display_cols].style.format({'금액': '{:,.0f}원'}),
                        use_container_width=True
                    )
                    
                    total_filtered = filtered[filtered['구분'] == '지출']['금액_절대값'].sum()
                    st.metric("필터링된 거래의 총 지출", f"{total_filtered:,.0f}원")
        else:
            st.info("태그를 먼저 추가해주세요")
    
    # 서브탭4: 패턴 분석
    with subtab4:
        st.markdown("### 📈 소비 패턴 분석")
        
        patterns = expense_predictor.detect_spending_patterns(df)
        
        # 패턴 요약
        col_pat1, col_pat2, col_pat3, col_pat4 = st.columns(4)
        
        with col_pat1:
            variance = patterns['monthly_variance']
            var_icon = "📊" if variance['interpretation'] == 'stable' else "📈" if variance['interpretation'] == 'moderate' else "📉"
            var_text = "안정" if variance['interpretation'] == 'stable' else "보통" if variance['interpretation'] == 'moderate' else "불안정"
            
            st.metric(
                "지출 변동성",
                f"{var_icon} {var_text}",
                f"CV: {variance['cv']:.1f}%",
                help="변동계수가 낮을수록 안정적"
            )
        
        with col_pat2:
            peak_day = patterns['peak_spending_day']
            st.metric(
                "최대 지출 요일",
                f"📅 {peak_day if peak_day else '-'}",
                help="가장 지출이 많은 요일"
            )
        
        with col_pat3:
            consistency = patterns['spending_consistency']
            st.metric(
                "소비 일관성",
                f"{consistency:.0f}점",
                help="100점에 가까울수록 규칙적"
            )
        
        with col_pat4:
            concentration = patterns['category_concentration']
            st.metric(
                "지출 집중도",
                f"{concentration:.1f}%",
                help="상위 3개 카테고리 비중"
            )
        
        st.markdown("---")
        
        # 이상 거래 탐지
        st.markdown("### 🚨 이상 거래 탐지")
        
        anomalies = comparison_analyzer.get_anomalies(df, threshold=2.0)
        
        if not anomalies.empty:
            st.warning(f"⚠️ {len(anomalies)}건의 이상 거래가 감지되었습니다")
            
            st.dataframe(
                anomalies.style.format({
                    '금액': '{:,.0f}원',
                    '카테고리평균': '{:,.0f}원',
                    'Z-Score': '{:.2f}'
                }),
                use_container_width=True
            )
            
            st.caption("💡 Z-Score가 2 이상이면 통계적 이상치입니다")
        else:
            st.success("✅ 이상 거래가 감지되지 않았습니다")
        
        st.markdown("---")
        
        # 카테고리 구성 변화
        st.markdown("### 🔄 카테고리 구성 변화 (최근 3개월)")
        
        category_mix = comparison_analyzer.get_category_mix_change(df)
        
        if category_mix is not None and not category_mix.empty:
            st.dataframe(
                category_mix.style.format('{:.1f}%'),
                use_container_width=True
            )
            
            st.caption("각 카테고리가 전체 지출에서 차지하는 비율")
        else:
            st.info("최소 2개월의 데이터가 필요합니다")

st.markdown("---")
st.caption("💡 Expense Analyzer v2.5.0 | 다크모드 + 저축목표 + 반복거래 + 태그 + 비교분석 + AI예측 🚀")
