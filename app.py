"""
Expense Analyzer - 개인 가계부 분석 대시보드
Streamlit 기반 인터랙티브 재무 분석 도구 + AI 자동 분류
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.preprocess import (
    load_data, 
    summarize_by_category, 
    summarize_by_month, 
    get_summary_metrics,
    filter_by_date_range
)
from utils.ai_categorizer import CategoryClassifier
from utils.budget_manager import BudgetManager
from utils.pdf_generator import PDFReportGenerator


# 페이지 설정
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide"
)

# AI 분류기 초기화
@st.cache_resource
def get_classifier():
    """AI 분류기 싱글톤"""
    classifier = CategoryClassifier()
    classifier.load_model()
    return classifier

classifier = get_classifier()

# 예산 관리자 초기화
@st.cache_resource
def get_budget_manager():
    """예산 관리자 싱글톤"""
    return BudgetManager()

budget_manager = get_budget_manager()

# 타이틀
st.title("💰 개인 가계부 분석기")
st.markdown("**CSV 파일을 업로드하여 수입/지출을 분석하세요 + AI 자동 분류 🤖**")

# 사이드바 - 파일 업로드
with st.sidebar:
    st.header("📂 파일 업로드")
    uploaded_file = st.file_uploader(
        "CSV 파일 선택",
        type=['csv'],
        help="날짜, 금액, 분류 컬럼이 포함된 CSV 파일"
    )
    
    st.markdown("---")
    
    # AI 기능 설정
    st.header("🤖 AI 설정")
    use_ai = st.checkbox("AI 자동 분류 사용", value=False, 
                         help="'분류' 컬럼이 없어도 자동으로 카테고리를 예측합니다")
    
    if use_ai:
        st.info("💡 AI가 '적요' 내용을 분석하여 자동으로 카테고리를 분류합니다")
    
    st.markdown("---")
    st.markdown("### 📋 CSV 형식 안내")
    st.code("""
날짜,적요,금액,분류,메모
2025-01-02,스타벅스,-4500,카페,아메리카노
2025-01-03,월급,2500000,급여,1월 급여
    """)

# 메인 영역
if uploaded_file is None:
    st.info("👈 왼쪽 사이드바에서 CSV 파일을 업로드해주세요")
    
    # 샘플 데이터 다운로드 버튼
    st.markdown("---")
    st.subheader("📥 샘플 데이터")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1. 카테고리 포함 버전**")
        sample_data = """날짜,적요,금액,분류,메모
2025-01-02,스타벅스,-4500,카페,아메리카노
2025-01-03,월급,2500000,급여,1월 급여
2025-01-04,이마트,-75000,식비,장보기
2025-01-05,넷플릭스,-14500,구독,월구독료
2025-01-10,CGV,-32000,여가,영화관람
"""
        st.download_button(
            label="샘플 CSV 다운로드",
            data=sample_data,
            file_name="sample_expense.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("**2. AI 자동 분류용 (카테고리 없음)**")
        sample_data_ai = """날짜,적요,금액,메모
2025-01-02,스타벅스,-4500,아메리카노
2025-01-03,월급,2500000,1월 급여
2025-01-04,이마트,-75000,장보기
2025-01-05,넷플릭스,-14500,월구독료
2025-01-10,CGV,-32000,영화관람
"""
        st.download_button(
            label="AI용 샘플 다운로드",
            data=sample_data_ai,
            file_name="sample_expense_ai.csv",
            mime="text/csv"
        )
    
    st.stop()

# 데이터 로드
try:
    df = load_data(uploaded_file)
    
    # AI 자동 분류 적용
    if use_ai:
        if '분류' not in df.columns or df['분류'].isna().any() or (df['분류'] == '기타').any():
            with st.spinner('🤖 AI가 카테고리를 분석 중입니다...'):
                df = classifier.auto_categorize_dataframe(df)
                
                # 분류 컬럼이 없거나 '기타'인 경우 AI 결과를 사용
                if '분류' not in df.columns:
                    df['분류'] = df['분류_AI']
                else:
                    # 비어있거나 '기타'인 분류만 AI로 채움
                    mask = df['분류'].isna() | (df['분류'] == '기타')
                    df.loc[mask, '분류'] = df.loc[mask, '분류_AI']
                
            st.success(f"✅ {len(df)}건의 거래 내역을 불러왔습니다 (AI 자동 분류 적용)")
            
            # AI 분류 통계 표시
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 대시보드", 
    "📈 상세 분석", 
    "📅 월별 추이", 
    "💰 예산 관리",
    "🔍 데이터 탐색",
    "🤖 AI 학습"
])

# ========== 탭1: 대시보드 ==========
with tab1:
    # 요약 지표
    metrics = get_summary_metrics(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💵 총 수입", f"{metrics['총_수입']:,.0f}원")
    with col2:
        st.metric("💸 총 지출", f"{metrics['총_지출']:,.0f}원")
    with col3:
        st.metric("💰 잔액", f"{metrics['잔액']:,.0f}원")
    
    st.markdown("---")
    
    # 차트 영역
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
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
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
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ========== 탭2: 상세 분석 ==========
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

# ========== 탭3: 월별 추이 ==========
with tab3:
    st.subheader("📅 월별 수입/지출 추이")
    
    monthly_summary = summarize_by_month(df)
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['수입'],
        mode='lines+markers',
        name='수입',
        line=dict(color='#4CAF50', width=3)
    ))
    fig_line.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['지출'],
        mode='lines+markers',
        name='지출',
        line=dict(color='#FF5252', width=3)
    ))
    fig_line.add_trace(go.Scatter(
        x=monthly_summary.index,
        y=monthly_summary['잔액'],
        mode='lines+markers',
        name='잔액',
        line=dict(color='#2196F3', width=3, dash='dot')
    ))
    fig_line.update_layout(
        xaxis_title="월",
        yaxis_title="금액 (원)",
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("### 📊 월별 상세 내역")
    monthly_display = monthly_summary.copy()
    monthly_display.columns = ['수입', '지출', '잔액']
    st.dataframe(
        monthly_display.style.format('{:,.0f}원'),
        use_container_width=True
    )

# ========== 탭4: 예산 관리 ==========
with tab4:
    st.subheader("💰 예산 관리")
    
    # 예산 알림
    alerts = budget_manager.get_alerts(df)
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
    
    # 전체 요약
    summary = budget_manager.get_monthly_summary(df)
    
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
    
    # 예산 설정 섹션
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("### ⚙️ 예산 설정")
        
        # 카테고리 선택
        categories = df['분류'].unique().tolist()
        selected_category = st.selectbox("카테고리 선택", categories)
        
        # 현재 예산 표시
        current_budget = budget_manager.get_budget(selected_category)
        st.info(f"현재 예산: {current_budget:,.0f}원")
        
        # 예산 입력
        new_budget = st.number_input(
            "새 예산 설정 (원)",
            min_value=0,
            value=int(current_budget) if current_budget > 0 else 100000,
            step=10000
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 예산 저장", type="primary"):
                budget_manager.set_budget(selected_category, new_budget)
                st.success(f"✅ {selected_category} 예산이 {new_budget:,.0f}원으로 설정되었습니다!")
                st.rerun()
        
        with col_btn2:
            if st.button("🗑️ 예산 삭제"):
                budget_manager.delete_budget(selected_category)
                st.success(f"✅ {selected_category} 예산이 삭제되었습니다!")
                st.rerun()
        
        # 예산 추천
        st.markdown("---")
        st.markdown("### 💡 AI 예산 추천")
        st.caption("과거 지출 평균 + 20% 여유분")
        
        if st.button("🔮 예산 추천 받기"):
            suggested = budget_manager.suggest_budget(df)
            
            st.markdown("**추천 예산:**")
            for cat, amount in suggested.items():
                st.write(f"- **{cat}**: {amount:,.0f}원")
            
            if st.button("📥 추천 예산 일괄 적용"):
                for cat, amount in suggested.items():
                    budget_manager.set_budget(cat, amount)
                st.success("✅ 추천 예산이 일괄 적용되었습니다!")
                st.rerun()
    
    with col_right:
        st.markdown("### 📊 예산 현황")
        
        analysis = budget_manager.analyze_spending(df)
        
        if not analysis.empty:
            # 데이터프레임 표시
            st.dataframe(
                analysis.style.format({
                    '예산': '{:,.0f}원',
                    '지출': '{:,.0f}원',
                    '잔여': '{:,.0f}원',
                    '사용률(%)': '{:.1f}%'
                }),
                use_container_width=True
            )
            
            # 진행률 바 차트
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

# ========== 탭5: 데이터 탐색 ==========
with tab5:
    st.subheader("🔍 원본 데이터 탐색")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        filter_category = st.multiselect(
            "카테고리 필터",
            options=df['분류'].unique(),
            default=df['분류'].unique()
        )
    
    with col_f2:
        filter_type = st.multiselect(
            "구분 필터",
            options=['수입', '지출'],
            default=['수입', '지출']
        )
    
    filtered_df = df[
        (df['분류'].isin(filter_category)) & 
        (df['구분'].isin(filter_type))
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
    
    # AI 분류 결과가 있으면 표시
    display_cols = ['날짜', '적요', '금액', '분류', '구분']
    if '분류_AI' in display_df.columns:
        display_cols.append('분류_AI')
    if '메모' in display_df.columns:
        display_cols.append('메모')
    
    st.dataframe(
        display_df[display_cols].style.format({
            '금액': '{:,.0f}원'
        }),
        use_container_width=True
    )
    
    csv = display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 필터링된 데이터 다운로드 (CSV)",
        data=csv,
        file_name="filtered_expense.csv",
        mime="text/csv"
    )

# ========== 탭6: AI 학습 ==========
with tab6:
    st.subheader("🤖 AI 모델 학습 및 평가")
    
    st.markdown("""
    ### AI 자동 분류란?
    - '적요' (거래 내역 설명)를 분석하여 자동으로 카테고리를 예측합니다
    - 예: "스타벅스" → 카페, "이마트" → 식비, "CGV" → 여가
    
    ### 학습 방법
    1. 카테고리가 포함된 CSV 파일 업로드
    2. 아래 '모델 학습' 버튼 클릭
    3. 이후 카테고리 없는 데이터도 자동 분류 가능!
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 현재 모델 상태")
        if classifier.pipeline is None:
            st.warning("⚠️ 학습된 모델이 없습니다")
        else:
            st.success("✅ 모델 로드 완료")
            
            # 평가하기
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
    
    # 테스트 예측
    st.markdown("### 🧪 실시간 예측 테스트")
    test_text = st.text_input(
        "적요 입력",
        placeholder="예: 스타벅스, 이마트, CGV 등",
        help="거래 내역 설명을 입력하면 AI가 카테고리를 예측합니다"
    )
    
    if test_text:
        predicted_category = classifier.predict(test_text)
        st.success(f"🎯 예측 카테고리: **{predicted_category}**")

# 푸터
st.markdown("---")
st.caption("💡 Expense Analyzer v2.0 | Powered by Streamlit, Plotly & AI 🤖")