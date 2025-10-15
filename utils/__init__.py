"""
utils 패키지
데이터 전처리, AI 분류, 예산 관리, PDF 생성, 카테고리 관리, 검증, 내보내기 모듈
"""

from .preprocess import (
    load_data,
    summarize_by_category,
    summarize_by_month,
    get_summary_metrics,
    filter_by_date_range,
    get_statistics  # (패키지 B에서 이미 있어야 함)
)

from .ai_categorizer import CategoryClassifier
from .budget_manager import BudgetManager
from .pdf_generator import PDFReportGenerator

# 패키지 C: 3개 모듈 추가
from .category_manager import CategoryManager
from .data_validator import DataValidator
from .export_manager import ExportManager

__all__ = [
    # 데이터 전처리
    'load_data',
    'summarize_by_category',
    'summarize_by_month',
    'get_summary_metrics',
    'filter_by_date_range',
    'get_statistics',  
    
    # 핵심 기능
    'CategoryClassifier',
    'BudgetManager',
    'PDFReportGenerator',
    
    # 패키지 C 추가
    'CategoryManager',
    'DataValidator',
    'ExportManager',

    # Phase 1: 편의성 기능
    'ThemeManager',
    'SavingsGoalManager',
    'RecurringTransactionManager',

    # Phase 2: 스마트 기능
    'TagManager',
    'ComparisonAnalyzer',
    'ExpensePredictor',
]

__version__ = '2.5.0'  # 버전 업데이트 (2.1.0 → 2.3.0)