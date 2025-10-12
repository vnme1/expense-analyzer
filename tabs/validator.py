"""
데이터 검증 탭
오류, 이상치, 개선 사항 자동 검사
"""
import streamlit as st
import pandas as pd
from utils.data_validator import DataValidator


# 싱글톤
@st.cache_resource
def get_validator():
    return DataValidator()


def render(df):
    """
    데이터 검증 탭 렌더링
    
    Args:
        df: 거래내역 DataFrame
    """
    st.subheader("✅ 데이터 검증 및 품질 체크")
    
    st.markdown("""
    업로드된 데이터의 오류, 이상치, 개선 사항을 자동으로 검사합니다.
    """)
    
    st.markdown("---")
    
    validator = get_validator()
    
    # 검증 실행
    if st.button("🔍 데이터 검증 시작", type="primary", use_container_width=True):
        with st.spinner("검증 중..."):
            validation_results = validator.validate(df)
            summary = validator.get_summary()
            
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
            
            # 오류
            if validation_results['errors']:
                _render_errors(validation_results['errors'])
            
            # 경고
            if validation_results['warnings']:
                _render_warnings(validation_results['warnings'])
            
            # 개선 제안
            if validation_results['suggestions']:
                _render_suggestions(validation_results['suggestions'])
            
            st.markdown("---")
            
            # 통계
            _render_statistics(summary, validation_results)
    
    else:
        st.info("👆 위의 버튼을 클릭하여 데이터 검증을 시작하세요")
        _render_check_list()


def _render_errors(errors):
    """오류 표시"""
    st.markdown("### ❌ 오류 (즉시 수정 필요)")
    
    for error in errors:
        with st.expander(f"🔴 {error['message']}", expanded=True):
            st.error(f"**심각도:** {error['severity']}")
            if 'details' in error:
                st.json(error['details'])


def _render_warnings(warnings):
    """경고 표시"""
    st.markdown("### ⚠️ 경고 (확인 권장)")
    
    for warning in warnings:
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


def _render_suggestions(suggestions):
    """개선 제안 표시"""
    st.markdown("### 💡 개선 제안")
    
    for suggestion in suggestions:
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


def _render_statistics(summary, validation_results):
    """통계 요약"""
    st.markdown("### 📊 검증 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 검사 항목", summary['total_issues'])
    with col2:
        st.metric("오류", len(validation_results['errors']))
    with col3:
        st.metric("경고", len(validation_results['warnings']))
    with col4:
        st.metric("개선 제안", len(validation_results['suggestions']))


def _render_check_list():
    """검증 항목 안내"""
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