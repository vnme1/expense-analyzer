"""
대시보드 탭 모듈
요약 지표, 카테고리별 차트, 월별 추이, PDF 리포트
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
from utils.preprocess import (
    get_summary_metrics,
    summarize_by_category,
    summarize_by_month,
    filter_by_date_range
)


def render(df, budget_manager):
    """
    대시보드 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        budget_manager: BudgetManager 인스턴스
    """
    # 이번 달 요약 카드
    _render_monthly_summary(df, budget_manager)
    st.markdown("---")
    
    # 전체 요약 지표
    _render_metrics(df)
    st.markdown("---")
    
    # 차트
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_category_chart(df)
    
    with col_right:
        _render_monthly_chart(df)
    
    # PDF 리포트 생성
    st.markdown("---")
    _render_pdf_report(df, budget_manager)


def _render_monthly_summary(df, budget_manager):
    """이번 달 요약 카드"""
    st.markdown("### 📊 이번 달 요약")
    
    current_month = pd.Timestamp.now().strftime('%Y-%m')
    this_month_df = df[df['년월'] == current_month]
    
    last_month = (pd.Timestamp.now() - pd.DateOffset(months=1)).strftime('%Y-%m')
    last_month_df = df[df['년월'] == last_month]
    
    # 계산
    this_expense = this_month_df[this_month_df['구분'] == '지출']['금액_절대값'].sum()
    last_expense = last_month_df[last_month_df['구분'] == '지출']['금액_절대값'].sum()
    expense_change = this_expense - last_expense
    
    this_income = this_month_df[this_month_df['구분'] == '수입']['금액_절대값'].sum()
    
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
            f"{this_expense:,.0f}원",
            delta=f"{expense_change:,.0f}원" if last_expense > 0 else None,
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "💵 이번 달 수입",
            f"{this_income:,.0f}원"
        )
    
    with col3:
        st.metric(
            "🏆 최다 지출",
            top_category,
            f"{top_category_amount:,.0f}원"
        )
    
    with col4:
        savings_rate = ((this_income - this_expense) / this_income * 100) if this_income > 0 else 0
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


def _render_metrics(df):
    """총 수입/지출/잔액"""
    metrics = get_summary_metrics(df)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💵 총 수입", f"{metrics['총_수입']:,.0f}원")
    with col2:
        st.metric("💸 총 지출", f"{metrics['총_지출']:,.0f}원")
    with col3:
        st.metric("💰 잔액", f"{metrics['잔액']:,.0f}원")


def _render_category_chart(df):
    """카테고리별 파이차트"""
    st.subheader("📊 카테고리별 지출 비율")
    
    category_summary = summarize_by_category(df)
    
    if not category_summary.empty:
        fig = px.pie(
            values=category_summary.values,
            names=category_summary.index,
            title="지출 카테고리 분포",
            hole=0.4
        )
        fig.update_traces(
            textposition='inside',
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>금액: %{value:,.0f}원<br>비율: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("지출 데이터가 없습니다")


def _render_monthly_chart(df):
    """월별 수입/지출 막대그래프"""
    st.subheader("📈 월별 수입/지출")
    
    monthly_summary = summarize_by_month(df)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=monthly_summary.index,
        y=monthly_summary['수입'],
        name='수입',
        marker_color='#4CAF50'
    ))
    
    fig.add_trace(go.Bar(
        x=monthly_summary.index,
        y=monthly_summary['지출'],
        name='지출',
        marker_color='#FF5252'
    ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title="월",
        yaxis_title="금액 (원)",
        legend=dict(orientation="h", y=1.1),
        xaxis=dict(type='category')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_pdf_report(df, budget_manager):
    """PDF 리포트 생성"""
    from utils.pdf_generator import PDFReportGenerator
    
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
                    pdf_generator = PDFReportGenerator()
                    pdf_buffer = pdf_generator.generate_report(filtered_df, budget_manager)
                    
                    st.success("✅ 리포트 생성 완료!")
                    
                    # PDF 미리보기
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
                    
                    # 다운로드 버튼
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