# data_controller.py
import pandas as pd
import sqlite3
import config
from PyQt6.QtCore import QObject

class DataController(QObject):
    def __init__(self):
        super().__init__()
        self.db_path = config.DATABASE_FILE

    def _get_connection(self):
        """สร้างและคืนค่า connection"""
        return sqlite3.connect(self.db_path)

    def get_table_names(self):
        """ดึงชื่อตารางทั้งหมดจาก DB"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            conn.close()
            return tables, None
        except Exception as e:
            return [], str(e)

    def load_dataframe(self, table_name):
        """โหลดข้อมูลจากตารางที่ระบุมาเป็น DataFrame"""
        try:
            conn = self._get_connection()
            df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
            conn.close()
            return df, None
        except Exception as e:
            # เกิดข้อผิดพลาด (เช่น ไม่มีตาราง)
            return pd.DataFrame(), str(e)

    def import_data(self, file_path, table_name, action):
        """นำเข้าข้อมูลจาก Excel ไปยัง DB"""
        try:
            df = pd.read_excel(file_path)
            conn = self._get_connection()
            df.to_sql(table_name, conn, if_exists=action, index=False)
            conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    def export_data(self, df, file_path):
        """ส่งออก DataFrame เป็นไฟล์ Excel"""
        if df is None or df.empty:
            return False, "No data to export."
        try:
            df.to_excel(file_path, index=False)
            return True, None
        except Exception as e:
            return False, str(e)

    def calculate_dashboard_stats(self, df):
        """คำนวณค่าสรุปสำหรับ Dashboard"""
        stats = {
            'total_records': "N/A",
            'column_sum_text': "N/A"
        }
        
        if df is None or df.empty:
            return stats

        # 1. Total Records
        stats['total_records'] = f"Total Records: {len(df)}"

        # 2. Column Sum
        target_col = config.TARGET_COLUMN_FOR_SUM
        if target_col in df.columns:
            if pd.api.types.is_numeric_dtype(df[target_col]):
                col_sum = df[target_col].sum()
                stats['column_sum_text'] = f"Sum of '{target_col}': {col_sum:,.2f}"
            else:
                stats['column_sum_text'] = f"Column '{target_col}' is not numeric."
        else:
            stats['column_sum_text'] = f"Column '{target_col}' not found."
            
        return stats