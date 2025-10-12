"""
예측 & 비교 분석 탭
지출 예측, 월별 비교, 태그 분석, 패턴 탐지
"""
import streamlit as st
import plotly.graph_objects as go
from utils.expense_predictor import ExpensePredictor
from utils.comparison_analyzer import ComparisonAnalyzer
from utils.tag_manager import TagManager
from utils.theme_manager import ThemeManager


# 싱글톤
@st.cache_resource
def get_managers():
    return {
        'predictor': ExpensePredictor(),
        'analyzer': ComparisonAnalyzer(),
        'tag_manager': TagManager(),
        'theme_manager': ThemeManager()
    }


def render(df, budget_manager):
    """
    예측 & 비교 분석 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
        budget_manager: BudgetManager 인스턴스
    """
    st.subheader("🔮 지출 예측 & 비교 분석")
    
    managers = get_managers()
    
    # 서브탭
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "🔮 지출 예측",
        "📊 월별 비교",
        "🏷️ 태그 분석",
        "📈 패턴 분석"
    ])
    
    with subtab1:
        _render_prediction(df, managers['predictor'], budget_manager)
    
    with subtab2:
        _render_comparison(df, managers['analyzer'])
    
    with subtab3:
        _render_tags(df, managers['tag_manager'])
    
    with subtab4:
        _render_patterns(df, managers['predictor'], managers['analyzer'])


def _render_prediction(df, predictor, budget_manager):
    """지출 예측"""
    st.markdown("### 🔮 다음 달 지출 예측")
    
    prediction_result = predictor.predict_next_month(df)
    
    if prediction_result['success']:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("다음 달 예상 지출", f"{prediction_result['prediction']:,.0f}원")
        
        with col2:
            trend_icon = "📈" if prediction_result['trend'] == 'increasing' else "📉" if prediction_result['trend'] == 'decreasing' else "➡️"
            trend_text = "상승" if prediction_result['trend'] == 'increasing' else "하락" if prediction_result['trend'] == 'decreasing' else "안정"
            st.metric("추세", f"{trend_icon} {trend_text}")
        
        with col3:
            st.metric("신뢰도", f"{prediction_result['confidence']:.1f}%")
        
        with col4:
            st.metric("데이터 기간", f"{prediction_result['data_points']}개월")
        
        st.markdown("---")
        
        # 카테고리별 예측
        st.markdown("### 📊 카테고리별 예측")
        
        category_predictions = predictor.predict_by_category(df)
        
        if not category_predictions.empty:
            st.dataframe(
                category_predictions.style.format({
                    '최근 평균': '{:,.0f}원',
                    '예측 금액': '{:,.0f}원',
                    '전월 대비': '{:+.1f}%'
                }),
                use_container_width=True
            )
        
        # 예산 조정 제안
        if budget_manager.budgets['default']:
            st.markdown("---")
            st.markdown("### 💡 예산 조정 제안")
            
            suggestions = predictor.suggest_budget_adjustments(df, budget_manager.budgets['default'])
            
            if suggestions:
                for sugg in suggestions:
                    with st.expander(f"📌 {sugg['카테고리']} - {sugg['사유']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("현재 예산", f"{sugg['현재 예산']:,.0f}원")
                        with col2:
                            st.metric("예상 지출", f"{sugg['예상 지출']:,.0f}원")
                        with col3:
                            st.metric("조정 제안", f"{sugg['조정 제안']:,.0f}원")
            else:
                st.success("✅ 현재 예산이 적정합니다!")
    else:
        st.warning(prediction_result['message'])


def _render_comparison(df, analyzer):
    """월별 비교"""
    st.markdown("### 📊 이번 달 vs 지난 달")
    
    comparison = analyzer.compare_this_month_vs_last_month(df)
    
    if comparison and comparison.get('summary'):
        summary = comparison['summary']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {summary['month1']}")
            st.metric("지출", f"{summary['expense1']:,.0f}원")
            st.metric("수입", f"{summary['income1']:,.0f}원")
        
        with col2:
            st.markdown(f"#### {summary['month2']}")
            st.metric(
                "지출",
                f"{summary['expense2']:,.0f}원",
                f"{summary['expense_change']:+,.0f}원 ({summary['expense_change_pct']:+.1f}%)"
            )
            st.metric(
                "수입",
                f"{summary['income2']:,.0f}원",
                f"{summary['income_change']:+,.0f}원"
            )
        
        st.markdown("---")
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
    else:
        st.info("비교할 데이터가 부족합니다")
    
    st.markdown("---")
    st.markdown("### 📅 요일별 소비 패턴")
    
    weekday_pattern = analyzer.get_weekday_pattern(df)
    
    if weekday_pattern is not None and not weekday_pattern.empty:
        st.dataframe(
            weekday_pattern.style.format({
                '총지출': '{:,.0f}원',
                '평균지출': '{:,.0f}원',
                '거래건수': '{:.0f}건'
            }),
            use_container_width=True
        )


def _render_tags(df, tag_manager):
    """태그 분석"""
    st.markdown("### 🏷️ 태그 관리")
    
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
    else:
        st.info("아직 태그가 없습니다")


def _render_patterns(df, predictor, analyzer):
    """패턴 분석"""
    st.markdown("### 📈 소비 패턴 분석")
    
    patterns = predictor.detect_spending_patterns(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        variance = patterns['monthly_variance']
        var_icon = "📊" if variance['interpretation'] == 'stable' else "📈"
        var_text = "안정" if variance['interpretation'] == 'stable' else "불안정"
        st.metric("지출 변동성", f"{var_icon} {var_text}", f"CV: {variance['cv']:.1f}%")
    
    with col2:
        peak_day = patterns['peak_spending_day']
        st.metric("최대 지출 요일", f"📅 {peak_day if peak_day else '-'}")
    
    with col3:
        consistency = patterns['spending_consistency']
        st.metric("소비 일관성", f"{consistency:.0f}점")
    
    with col4:
        concentration = patterns['category_concentration']
        st.metric("지출 집중도", f"{concentration:.1f}%")
    
    st.markdown("---")
    st.markdown("### 🚨 이상 거래 탐지")
    
    anomalies = analyzer.get_anomalies(df, threshold=2.0)
    
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
    else:
        st.success("✅ 이상 거래가 감지되지 않았습니다")