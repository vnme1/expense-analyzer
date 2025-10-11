"""
데이터 전처리 모듈
CSV 파일 로드, 데이터 정제, 집계 함수 제공
"""
import pandas as pd
from datetime import datetime


def load_data(file):
    """
    CSV 파일을 읽어 DataFrame으로 변환
    
    Args:
        file: Streamlit file_uploader 객체
        
    Returns:
        pd.DataFrame: 정제된 거래내역 데이터
    """
    df = pd.read_csv(file, encoding='utf-8-sig')
    
    # 필수 컬럼 확인
    required_cols = ['날짜', '금액']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"필수 컬럼이 누락되었습니다: {required_cols}")
    
    # 날짜 형식 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['년월'] = df['날짜'].dt.to_period('M').astype(str)
    
    # 금액을 숫자로 변환
    df['금액'] = pd.to_numeric(df['금액'], errors='coerce')
    
    # 수입/지출 구분
    df['구분'] = df['금액'].apply(lambda x: '수입' if x > 0 else '지출')
    df['금액_절대값'] = df['금액'].abs()
    
    # 결측치 제거
    df = df.dropna(subset=['금액'])
    
    # 분류 컬럼이 없으면 기본값 설정
    if '분류' not in df.columns:
        df['분류'] = '기타'
    
    return df.sort_values('날짜')


def summarize_by_category(df):
    """
    카테고리별 지출 합계 계산
    
    Args:
        df: 전처리된 DataFrame
        
    Returns:
        pd.Series: 카테고리별 지출 합계 (내림차순)
    """
    expense_df = df[df['구분'] == '지출']
    summary = expense_df.groupby('분류')['금액_절대값'].sum()
    return summary.sort_values(ascending=False)


def summarize_by_month(df):
    """
    월별 수입/지출 집계
    
    Args:
        df: 전처리된 DataFrame
        
    Returns:
        pd.DataFrame: 월별 수입/지출 pivot 테이블
    """
    monthly = df.groupby(['년월', '구분'])['금액_절대값'].sum().unstack(fill_value=0)
    
    # 컬럼이 없는 경우 0으로 채움
    if '수입' not in monthly.columns:
        monthly['수입'] = 0
    if '지출' not in monthly.columns:
        monthly['지출'] = 0
    
    monthly['잔액'] = monthly['수입'] - monthly['지출']
    return monthly


def get_summary_metrics(df):
    """
    전체 요약 지표 계산
    
    Args:
        df: 전처리된 DataFrame
        
    Returns:
        dict: 총 수입, 총 지출, 잔액
    """
    total_income = df[df['구분'] == '수입']['금액_절대값'].sum()
    total_expense = df[df['구분'] == '지출']['금액_절대값'].sum()
    balance = total_income - total_expense
    
    return {
        '총_수입': total_income,
        '총_지출': total_expense,
        '잔액': balance
    }


def filter_by_date_range(df, start_date, end_date):
    """
    날짜 범위로 데이터 필터링
    
    Args:
        df: 전처리된 DataFrame
        start_date: 시작 날짜
        end_date: 종료 날짜
        
    Returns:
        pd.DataFrame: 필터링된 데이터
    """
    mask = (df['날짜'] >= pd.to_datetime(start_date)) & (df['날짜'] <= pd.to_datetime(end_date))
    return df[mask]