"""
통계 대시보드 탭
고급 통계 분석 및 패턴 탐지
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.preprocess import get_statistics


def render(df):
    """
    통계 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
    """
    st.subheader("📉 고급 통계 분석")
    
    stats = get_statistics(df)
    
    # 핵심 지표
    st.markdown("### 💡 핵심 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("월평균 지출", f"{stats['월평균_지출']:,.0f}원")
    with col2:
        st.metric("평균 거래 금액", f"{stats['평균_지출']:,.0f}원")
    with col3:
        st.metric("저축률", f"{stats['저축률']:.1f}%")
    with col4:
        st.metric("카테고리 수", f"{stats['카테고리_수']}개")
    
    st.markdown("---")
    
    # 지출/수입 통계
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_expense_stats(stats)
    
    with col_right:
        _render_income_stats(stats)
    
    st.markdown("---")
    
    # 지출 금액 분포
    _render_amount_distribution(df)
    
    st.markdown("---")
    
    # 요일별 패턴
    _render_weekday_pattern(df)


def _render_expense_stats(stats):
    """지출 통계"""
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
    
    st.dataframe(expense_stats, use_container_width=True, hide_index=True)
    st.info(f"💡 **최대 지출 항목**: {stats['최대_지출_항목']}")


def _render_income_stats(stats):
    """수입 통계"""
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
    
    st.dataframe(income_stats, use_container_width=True, hide_index=True)


def _render_amount_distribution(df):
    """지출 금액 분포"""
    st.markdown("### 📊 지출 금액 분포")
    
    expense_df = df[df['구분'] == '지출']
    
    if len(expense_df) > 0:
        fig = px.histogram(
            expense_df,
            x='금액_절대값',
            nbins=20,
            labels={'금액_절대값': '지출 금액 (원)', 'count': '거래 건수'},
            title='지출 금액 분포 히스토그램',
            color_discrete_sequence=['#FF5252']
        )
        
        fig.update_layout(
            xaxis_title="지출 금액 (원)",
            yaxis_title="거래 건수",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("지출 데이터가 없습니다")


def _render_weekday_pattern(df):
    """요일별 지출 패턴"""
    st.markdown("### 📅 요일별 지출 패턴")
    
    expense_df = df[df['구분'] == '지출'].copy()
    expense_df['요일'] = expense_df['날짜'].dt.day_name()
    
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_map = {
        'Monday': '월', 'Tuesday': '화', 'Wednesday': '수',
        'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'
    }
    
    weekday_spending = expense_df.groupby('요일')['금액_절대값'].sum().reindex(weekday_order, fill_value=0)
    weekday_spending.index = [weekday_map[day] for day in weekday_spending.index]
    
    fig = px.bar(
        x=weekday_spending.index,
        y=weekday_spending.values,
        labels={'x': '요일', 'y': '총 지출 (원)'},
        title='요일별 지출 금액',
        color=weekday_spending.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # 요일별 평균
    weekday_avg = expense_df.groupby('요일')['금액_절대값'].mean().reindex(weekday_order, fill_value=0)
    weekday_avg.index = [weekday_map[day] for day in weekday_avg.index]
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        max_day = weekday_avg.idxmax()
        st.info(f"📈 **가장 많이 쓰는 요일**: {max_day} ({weekday_avg.max():,.0f}원/건)")
    
    with col_w2:
        min_day = weekday_avg.idxmin()
        st.success(f"📉 **가장 적게 쓰는 요일**: {min_day} ({weekday_avg.min():,.0f}원/건)")