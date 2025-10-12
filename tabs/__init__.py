"""
탭 모듈 패키지
각 탭을 독립적인 모듈로 분리
"""

from . import dashboard
from . import analysis
from . import monthly_trend
from . import budget
from . import statistics
from . import data_explorer
from . import category_tab  # ✅ 파일명 변경됨
from . import validator
from . import ai_learning
from . import savings_goal
from . import recurring
from . import prediction

__all__ = [
    'dashboard',
    'analysis',
    'monthly_trend',
    'budget',
    'statistics',
    'data_explorer',
    'category_tab',
    'validator',
    'ai_learning',
    'savings_goal',
    'recurring',
    'prediction'
]