import sys
import pandas as pd
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QTableWidget, QTableWidgetItem,
    QDialog, QListWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

DATABASE_FILE = 'my_dashboard_data.db'
TABLE_NAME = 'sales_data'

# --- สร้าง Class สำหรับหน้าต่างที่สอง (เวอร์ชันอัปเกรด) ---
class DatabaseTablesWindow(QDialog):
    database_changed = pyqtSignal() # << สร้าง "กริ่ง" หรือ Signal ของเราเอง

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Manager")
        self.setMinimumSize(400, 300)

        # --- Layouts & Widgets ---
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Tables in database:"))
        self.table_list_widget = QListWidget() # Widget สำหรับแสดงรายชื่อตาราง
        
        # --- สร้างปุ่มและ Layout สำหรับปุ่ม ---
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import to Selected")
        self.export_button = QPushButton("Export Selected")
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)

        self.status_label = QLabel("Please select a table.") # ป้ายแสดงสถานะ

        # --- ประกอบร่าง ---
        layout.addWidget(self.table_list_widget)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)

        # --- เชื่อม Signals & Slots ---
        self.import_button.clicked.connect(self.import_to_selected)
        self.export_button.clicked.connect(self.export_selected)
        # เมื่อมีการเปลี่ยนรายการที่เลือกใน List ให้เคลียร์ข้อความสถานะ
        self.table_list_widget.currentItemChanged.connect(
            lambda: self.status_label.setText("Ready.")
        )
        
        self.load_table_names()

    def load_table_names(self):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            self.table_list_widget.clear()
            for table_name in tables:
                for t in table_name:
                    self.table_list_widget.addItem(t)
            self.status_label.setText("Tables loaded.")
        except Exception as e:
            self.status_label.setText(f"Error loading tables: {e}")

    def get_selected_table(self):
        # ฟังก์ชันช่วยสำหรับดึงชื่อตารางที่กำลังเลือก
        selected_item = self.table_list_widget.currentItem()
        if selected_item:
            return selected_item.text()
        else:
            self.status_label.setText("Error: No table selected!")
            return None

    def import_to_selected(self):
        table_name = self.get_selected_table()
        if not table_name:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File to Import", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                
                # --- ถามผู้ใช้ ---
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Confirm Import")
                msg_box.setText(f"How do you want to import data to '{table_name}'?")
                replace_button = msg_box.addButton("Replace Old Data", QMessageBox.ButtonRole.DestructiveRole)
                append_button = msg_box.addButton("Append to Old Data", QMessageBox.ButtonRole.AcceptRole)
                cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg_box.exec()
                
                if msg_box.clickedButton() == replace_button:
                    action = 'replace'
                elif msg_box.clickedButton() == append_button:
                    action = 'append'
                else:
                    self.status_label.setText("Import cancelled.")
                    return
                # -----------------
                
                conn = sqlite3.connect(DATABASE_FILE)
                df.to_sql(table_name, conn, if_exists=action, index=False)
                conn.close()
                
                self.status_label.setText(f"Data {action}d to '{table_name}' successfully.")
                self.database_changed.emit() # กดกริ่ง (เหมือนเดิม)

            except Exception as e:
                self.status_label.setText(f"Import error: {e}")

    def export_selected(self):
        table_name = self.get_selected_table()
        if not table_name:
            return

        try:
            # ดึงข้อมูลจากตารางที่เลือก
            conn = sqlite3.connect(DATABASE_FILE)
            df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
            conn.close()

            # เปิดหน้าต่าง Save As...
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Table As", f"{table_name}_export.xlsx", "Excel Files (*.xlsx)"
            )
            if file_path:
                df.to_excel(file_path, index=False)
                self.status_label.setText(f"Table '{table_name}' exported successfully.")
        except Exception as e:
            self.status_label.setText(f"Export error: {e}")


# --- ปรับปรุง Class หน้าต่างหลัก ---
class MainWindow(QMainWindow): # เปลี่ยนจาก QWidget เป็น QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Excel Dashboard App')
        self.resize(800, 600)
        
        # QMainWindow ต้องมี Central Widget เพื่อวาง Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.current_df = None

        # --- Layouts & Widgets (เหมือนเดิม) ---
        self.main_layout = QVBoxLayout(central_widget) # บอกให้ layout อยู่บน central_widget
        self.button_layout = QHBoxLayout()
        self.summary_layout = QHBoxLayout()
        
        self.info_label = QLabel('Import an Excel file or load data from database.')
        self.import_button = QPushButton('Import Excel')
        self.export_button = QPushButton('Export to Excel')
        self.show_tables_button = QPushButton('Show Database Tables') # << ปุ่มใหม่
        self.table = QTableWidget()
        self.total_records_label = QLabel("Total Records: N/A")
        self.column_sum_label = QLabel("Sum of 'YourColumn': N/A")

        # --- ประกอบร่าง Layout ---
        self.button_layout.addWidget(self.import_button)
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addWidget(self.show_tables_button) # เพิ่มปุ่มใหม่

        # ... (ส่วนที่เหลือของการประกอบร่างเหมือนเดิม) ...
        self.summary_layout.addWidget(self.total_records_label)
        self.summary_layout.addWidget(self.column_sum_label)
        self.main_layout.addWidget(self.info_label)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.summary_layout)
        self.main_layout.addWidget(self.table)
        
        # --- เชื่อม Signals & Slots ---
        self.import_button.clicked.connect(self.import_and_save_data)
        self.export_button.clicked.connect(self.export_data)
        self.show_tables_button.clicked.connect(self.open_db_tables_window) # << เชื่อมปุ่มใหม่

        self.load_data_from_db()

    def open_db_tables_window(self):
        # ฟังก์ชันสำหรับเปิดหน้าต่างที่สอง
        # การสร้าง instance ของหน้าต่างที่สองจะทำให้มันแสดงขึ้นมา
        # self.dialog = DatabaseTablesWindow(self) # สร้าง dialog
        # self.dialog.exec() # .exec() จะแสดงหน้าต่างแบบ Modal (ต้องปิดก่อนถึงจะกลับไปหน้าหลักได้)
        # หรือใช้ show()
        self.dialog = DatabaseTablesWindow(self)
        # << เชื่อมต่อ Signal จากหน้าต่างที่ 2 เข้ากับฟังก์ชันของหน้าต่างนี้
        self.dialog.database_changed.connect(self.load_data_from_db)
        self.dialog.show()

    # ... (ฟังก์ชัน import_and_save_data, load_data_from_db, export_data, display_dataframe เหมือนเดิมทั้งหมด) ...
    def import_and_save_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            try:
                # 1. อ่าน Excel ก่อน
                df = pd.read_excel(file_path)

                # 2. ถามผู้ใช้ว่าจะทำอะไร
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Confirm Import")
                msg_box.setText("How do you want to import this data?")
                replace_button = msg_box.addButton("Replace Old Data", QMessageBox.ButtonRole.DestructiveRole)
                append_button = msg_box.addButton("Append to Old Data", QMessageBox.ButtonRole.AcceptRole)
                cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg_box.exec()
                
                # 3. ตรวจสอบว่าผู้ใช้กดปุ่มไหน
                if msg_box.clickedButton() == replace_button:
                    action = 'replace'
                elif msg_box.clickedButton() == append_button:
                    action = 'append'
                elif msg_box.clickedButton() == cancel_button:
                    self.info_label.setText("Import cancelled.")
                    return # ผู้ใช้กด Cancel ให้ออกจากฟังก์ชัน

                # 4. บันทึกลง DB ตามที่ผู้ใช้เลือก
                conn = sqlite3.connect(DATABASE_FILE)
                df.to_sql(TABLE_NAME, conn, if_exists=action, index=False)
                conn.close()
                
                self.info_label.setText(f"Data {action}d successfully.")
                
                # 5. โหลดข้อมูลทั้งหมดมาแสดง (เพื่อให้เห็นผลลัพธ์ไม่ว่าจะ append หรือ replace)
                self.load_data_from_db()

            except Exception as e:
                self.info_label.setText(f"Error: {e}")

    def load_data_from_db(self):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            df = pd.read_sql(f'SELECT * FROM {TABLE_NAME}', conn)
            conn.close()
            if not df.empty:
                self.info_label.setText("Data loaded from database.")
                self.display_dataframe(df)
            else:
                self.info_label.setText("Database is empty. Please import an Excel file.")
        except Exception as e:
            self.info_label.setText("No database found. Please import an Excel file.")

    def export_data(self):
        if self.current_df is None:
            self.info_label.setText("No data to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx)")
        if file_path:
            try:
                self.current_df.to_excel(file_path, index=False)
                self.info_label.setText(f"Data successfully exported to {file_path}")
            except Exception as e:
                self.info_label.setText(f"Error exporting file: {e}")
    
    def display_dataframe(self, df):
        self.current_df = df
        total_records = len(df)
        self.total_records_label.setText(f"Total Records: {total_records}")
        target_column = 'age' # << อย่าลืมแก้ให้เป็นชื่อคอลัมน์ของคุณ
        if target_column in df.columns:
            if pd.api.types.is_numeric_dtype(df[target_column]):
                column_sum = df[target_column].sum()
                self.column_sum_label.setText(f"Sum of '{target_column}': {column_sum:,.2f}")
            else:
                self.column_sum_label.setText(f"Column '{target_column}' is not numeric.")
        else:
            self.column_sum_label.setText(f"Column '{target_column}' not found.")
        self.table.clear()
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)
        for row_index, row_data in df.iterrows():
            for col_index, cell_data in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(cell_data)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())