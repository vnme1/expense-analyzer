"""
데이터 전처리 모듈
CSV/Excel 파일 로드, 데이터 정제, 집계 함수 제공
"""
import pandas as pd
from datetime import datetime


def load_data(file):
    """
    CSV 또는 Excel 파일을 읽어 DataFrame으로 변환
    
    Args:
        file: Streamlit file_uploader 객체 또는 파일 경로
        
    Returns:
        pd.DataFrame: 정제된 거래내역 데이터
    """
    # 파일 타입 확인
    file_name = getattr(file, 'name', str(file))
    
    if file_name.endswith(('.xlsx', '.xls')):
        # Excel 파일 읽기
        df = pd.read_excel(file, engine='openpyxl')
    else:
        # ✅ CSV 파일 읽기 (다중 인코딩 시도)
        encodings = ['utf-8-sig', 'cp949', 'euc-kr', 'utf-8', 'latin1']
        df = None
        last_error = None
        
        for encoding in encodings:
            try:
                # 파일 포인터 리셋 (재시도 시 필요)
                if hasattr(file, 'seek'):
                    file.seek(0)
                
                df = pd.read_csv(file, encoding=encoding)
                break  # 성공하면 루프 종료
                
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                continue
        
        if df is None:
            raise ValueError(f"지원하지 않는 파일 인코딩입니다. 시도한 인코딩: {encodings}\n마지막 오류: {last_error}")
    
    # 필수 컬럼 확인
    required_cols = ['날짜', '금액']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_cols}")
    
    # 날짜 형식 변환
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    
    # 날짜 변환 실패 체크
    if df['날짜'].isna().any():
        invalid_count = df['날짜'].isna().sum()
        raise ValueError(f"날짜 형식이 잘못된 행이 {invalid_count}건 있습니다")
    
    df['년월'] = df['날짜'].dt.to_period('M').astype(str)
    
    # 금액을 숫자로 변환
    df['금액'] = pd.to_numeric(df['금액'], errors='coerce')
    
    # 금액 변환 실패 체크
    if df['금액'].isna().any():
        invalid_count = df['금액'].isna().sum()
        print(f"⚠️ 금액이 잘못된 행 {invalid_count}건 제거")
    
    # 결측치 제거
    df = df.dropna(subset=['금액', '날짜'])
    
    # 수입/지출 구분
    df['구분'] = df['금액'].apply(lambda x: '수입' if x > 0 else '지출')
    df['금액_절대값'] = df['금액'].abs()
    
    # 분류 컬럼이 없으면 기본값 설정
    if '분류' not in df.columns:
        df['분류'] = '기타'
    
    # 적요 컬럼이 없으면 생성
    if '적요' not in df.columns:
        df['적요'] = '거래'
    
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
    
    if len(expense_df) == 0:
        return pd.Series(dtype=float)
    
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


def get_statistics(df):
    """
    통계 지표 계산
    
    Args:
        df: 전처리된 DataFrame
        
    Returns:
        dict: 다양한 통계 지표
    """
    expense_df = df[df['구분'] == '지출']
    income_df = df[df['구분'] == '수입']
    
    # 월별 데이터
    monthly = summarize_by_month(df)
    
    stats = {
        # 기본 지표
        '총_수입': income_df['금액_절대값'].sum(),
        '총_지출': expense_df['금액_절대값'].sum(),
        '순수익': income_df['금액_절대값'].sum() - expense_df['금액_절대값'].sum(),
        
        # 평균 지표
        '평균_지출': expense_df['금액_절대값'].mean() if len(expense_df) > 0 else 0,
        '월평균_지출': monthly['지출'].mean() if len(monthly) > 0 else 0,
        '월평균_수입': monthly['수입'].mean() if len(monthly) > 0 else 0,
        
        # 최대/최소
        '최대_지출': expense_df['금액_절대값'].max() if len(expense_df) > 0 else 0,
        '최소_지출': expense_df['금액_절대값'].min() if len(expense_df) > 0 else 0,
        '최대_지출_항목': expense_df.loc[expense_df['금액_절대값'].idxmax(), '적요'] if len(expense_df) > 0 else '-',
        
        # 거래 건수
        '총_거래건수': len(df),
        '지출_건수': len(expense_df),
        '수입_건수': len(income_df),
        
        # 카테고리
        '카테고리_수': df['분류'].nunique(),
        '최다_지출_카테고리': expense_df.groupby('분류')['금액_절대값'].sum().idxmax() if len(expense_df) > 0 else '-',
        
        # 저축률
        '저축률': ((income_df['금액_절대값'].sum() - expense_df['금액_절대값'].sum()) / 
                   income_df['금액_절대값'].sum() * 100) if income_df['금액_절대값'].sum() > 0 else 0
    }
    
    return stats