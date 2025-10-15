"""
SQLite 데이터베이스 관리 모듈
CSV 데이터를 SQLite로 마이그레이션하고 관리
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json


class ExpenseDatabase:
    """가계부 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path='data/expense.db'):
        """초기화"""
        self.project_root = Path(__file__).parent.parent
        self.db_path = self.project_root / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """데이터베이스 연결"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 반환
        return conn
    
    def init_database(self):
        """데이터베이스 초기화 (테이블 생성)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 거래 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                memo TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 예산 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, month)
            )
        """)
        
        # 저축 목표 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                target_date TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 반복 거래 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                frequency TEXT NOT NULL,
                start_date TEXT NOT NULL,
                day_of_execution INTEGER,
                memo TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 태그 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE CASCADE
            )
        """)
        
        # 인덱스 생성 (검색 속도 향상)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON transactions(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_amount ON transactions(amount)")
        
        conn.commit()
        conn.close()
    
    # === 거래 관련 메서드 ===
    
    def add_transaction(self, date, description, amount, category='기타', memo=''):
        """거래 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transactions (date, description, amount, category, memo)
            VALUES (?, ?, ?, ?, ?)
        """, (date, description, float(amount), category, memo))
        
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'id': transaction_id, 'message': '거래가 추가되었습니다'}
    
    def get_all_transactions(self):
        """모든 거래 조회"""
        conn = self.get_connection()
        query = "SELECT * FROM transactions ORDER BY date DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['날짜'] = pd.to_datetime(df['date'])
            df['적요'] = df['description']
            df['금액'] = df['amount']
            df['분류'] = df['category']
            df['메모'] = df['memo']
        
        return df
    
    def update_transaction(self, transaction_id, **kwargs):
        """거래 수정"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['date', 'description', 'amount', 'category', 'memo']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return {'success': False, 'message': '수정할 항목이 없습니다'}
        
        values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        values.append(transaction_id)
        
        query = f"UPDATE transactions SET {', '.join(updates)}, updated_at = ? WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': '거래가 수정되었습니다'}
    
    def delete_transaction(self, transaction_id):
        """거래 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': '거래가 삭제되었습니다'}
    
    def search_transactions(self, query='', date_from=None, date_to=None, 
                          categories=None, amount_min=None, amount_max=None):
        """고급 검색"""
        conn = self.get_connection()
        
        sql = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        # 텍스트 검색
        if query:
            sql += " AND (description LIKE ? OR memo LIKE ?)"
            params.extend([f'%{query}%', f'%{query}%'])
        
        # 날짜 범위
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        
        # 카테고리
        if categories:
            placeholders = ','.join('?' * len(categories))
            sql += f" AND category IN ({placeholders})"
            params.extend(categories)
        
        # 금액 범위
        if amount_min is not None:
            sql += " AND ABS(amount) >= ?"
            params.append(amount_min)
        
        if amount_max is not None:
            sql += " AND ABS(amount) <= ?"
            params.append(amount_max)
        
        sql += " ORDER BY date DESC"
        
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        
        return df
    
    # === 예산 관련 메서드 ===
    
    def set_budget(self, category, amount, month=None):
        """예산 설정"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO budgets (category, amount, month)
            VALUES (?, ?, ?)
        """, (category, float(amount), month))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': '예산이 설정되었습니다'}
    
    def get_budgets(self, month=None):
        """예산 조회"""
        conn = self.get_connection()
        
        if month:
            query = "SELECT * FROM budgets WHERE month = ? OR month IS NULL"
            df = pd.read_sql_query(query, conn, params=(month,))
        else:
            query = "SELECT * FROM budgets WHERE month IS NULL"
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    # === CSV 마이그레이션 ===
    
    def import_from_csv(self, csv_path):
        """CSV 파일을 데이터베이스로 가져오기"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # 컬럼 매핑
            df.columns = df.columns.str.strip()
            
            required_cols = {'날짜': 'date', '적요': 'description', '금액': 'amount'}
            optional_cols = {'분류': 'category', '메모': 'memo'}
            
            # 필수 컬럼 확인
            for kr, en in required_cols.items():
                if kr not in df.columns:
                    return {'success': False, 'message': f'필수 컬럼 누락: {kr}'}
            
            # 데이터 정제
            df['date'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
            df['description'] = df['적요'].fillna('거래')
            df['amount'] = pd.to_numeric(df['금액'], errors='coerce')
            df['category'] = df.get('분류', '기타').fillna('기타')
            df['memo'] = df.get('메모', '').fillna('')
            
            # NaN 제거
            df = df.dropna(subset=['amount'])
            
            # 데이터베이스에 삽입
            conn = self.get_connection()
            
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT INTO transactions (date, description, amount, category, memo)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['date'], row['description'], row['amount'], row['category'], row['memo']))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'count': len(df), 'message': f'{len(df)}건의 거래가 가져와졌습니다'}
        
        except Exception as e:
            return {'success': False, 'message': f'가져오기 실패: {str(e)}'}
    
    def export_to_csv(self, output_path):
        """데이터베이스를 CSV로 내보내기"""
        try:
            df = self.get_all_transactions()
            
            # 컬럼 매핑
            export_df = df[['날짜', '적요', '금액', '분류', '메모']].copy()
            
            export_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            return {'success': True, 'message': 'CSV로 내보내기 완료'}
        
        except Exception as e:
            return {'success': False, 'message': f'내보내기 실패: {str(e)}'}
    
    # === 통계 메서드 ===
    
    def get_summary_by_category(self):
        """카테고리별 지출 요약"""
        conn = self.get_connection()
        
        query = """
            SELECT category, SUM(ABS(amount)) as total
            FROM transactions
            WHERE amount < 0
            GROUP BY category
            ORDER BY total DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_summary_by_month(self):
        """월별 수입/지출 요약"""
        conn = self.get_connection()
        
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expense
            FROM transactions
            GROUP BY month
            ORDER BY month
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    # === 백업 & 복원 ===
    
    def create_backup(self, backup_path=None):
        """데이터베이스 백업"""
        import shutil
        
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.db_path.parent / f'backup_expense_{timestamp}.db'
        
        try:
            shutil.copy2(self.db_path, backup_path)
            return {'success': True, 'path': str(backup_path), 'message': '백업 완료'}
        except Exception as e:
            return {'success': False, 'message': f'백업 실패: {str(e)}'}
    
    def restore_from_backup(self, backup_path):
        """백업에서 복원"""
        import shutil
        
        try:
            # 현재 DB 백업
            emergency_backup = self.db_path.parent / f'emergency_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(self.db_path, emergency_backup)
            
            # 복원
            shutil.copy2(backup_path, self.db_path)
            
            return {'success': True, 'message': '복원 완료'}
        except Exception as e:
            return {'success': False, 'message': f'복원 실패: {str(e)}'}