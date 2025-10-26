# ui_main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFileDialog, 
    QTableWidget, QTableWidgetItem, QMessageBox
)
import config
from ui_db_window import DatabaseTablesWindow # Import หน้าต่างที่ 2

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller # รับ "สมอง" (Controller) มา
        self.current_df = None
        
        self.setWindowTitle('Excel Dashboard App')
        self.resize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # --- Layouts & Widgets ---
        self.main_layout = QVBoxLayout(central_widget)
        self.button_layout = QHBoxLayout()
        self.summary_layout = QHBoxLayout()
        
        self.info_label = QLabel('Loading data...')
        self.import_button = QPushButton('Import Excel')
        self.export_button = QPushButton('Export to Excel')
        self.show_tables_button = QPushButton('Show Database Tables')
        self.table = QTableWidget()
        self.total_records_label = QLabel("Total Records: N/A")
        self.column_sum_label = QLabel("Sum: N/A")

        # --- ประกอบร่าง Layout ---
        self.button_layout.addWidget(self.import_button)
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addWidget(self.show_tables_button)
        self.summary_layout.addWidget(self.total_records_label)
        self.summary_layout.addWidget(self.column_sum_label)

        self.main_layout.addWidget(self.info_label)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.summary_layout)
        self.main_layout.addWidget(self.table)
        
        # --- เชื่อม Signals & Slots ---
        self.import_button.clicked.connect(self.handle_import)
        self.export_button.clicked.connect(self.handle_export)
        self.show_tables_button.clicked.connect(self.open_db_tables_window)

        self.load_initial_data()

    def load_initial_data(self):
        """โหลดข้อมูลเริ่มต้น (จากตาราง default) ตอนเปิดแอป"""
        df, error = self.controller.load_dataframe(config.DEFAULT_TABLE)
        
        if error:
            self.info_label.setText(f"No database found or table '{config.DEFAULT_TABLE}' missing. Please import data.")
            return

        if df.empty:
            self.info_label.setText("Database is empty. Please import an Excel file.")
            return
            
        self.current_df = df
        self.info_label.setText("Data loaded from database.")
        self.update_dashboard(df)

    def handle_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return

        action = self.ask_import_action()
        if not action:
            self.info_label.setText("Import cancelled.")
            return

        success, error = self.controller.import_data(
            file_path, config.DEFAULT_TABLE, action
        )

        if success:
            self.info_label.setText(f"Data {action}d successfully.")
            self.load_initial_data() # โหลดข้อมูลใหม่ทั้งหมดมาแสดง
        else:
            self.info_label.setText(f"Import Error: {error}")

    def handle_export(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx)")
        if file_path:
            success, error_msg = self.controller.export_data(self.current_df, file_path)
            if success:
                self.info_label.setText(f"Data successfully exported to {file_path}")
            else:
                self.info_label.setText(f"Export error: {error_msg}")

    def update_dashboard(self, df):
        """อัปเดต UI ทั้งหมด (ตาราง และ ค่าสรุป)"""
        # 1. อัปเดตค่าสรุป
        stats = self.controller.calculate_dashboard_stats(df)
        self.total_records_label.setText(stats['total_records'])
        self.column_sum_label.setText(stats['column_sum_text'])

        # 2. อัปเดตตาราง
        self.table.clear()
        if df.empty:
            return
            
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)
        for row_index, row_data in df.iterrows():
            for col_index, cell_data in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(cell_data)))

    def open_db_tables_window(self):
        # ส่ง "สมอง" (self.controller) ตัวเดียวกันไปให้หน้าต่างที่ 2
        dialog = DatabaseTablesWindow(self.controller, self)
        # เชื่อม "กริ่ง" จากหน้าต่าง 2 ให้มาสั่งโหลดข้อมูลใหม่
        dialog.database_changed.connect(self.load_initial_data)
        dialog.show()

    def ask_import_action(self):
        """ถามผู้ใช้ว่าจะ Replace หรือ Append (สำหรับหน้าหลัก)"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Import")
        msg_box.setText(f"How do you want to import data to '{config.DEFAULT_TABLE}'?")
        replace_button = msg_box.addButton("Replace Old Data", QMessageBox.ButtonRole.DestructiveRole)
        append_button = msg_box.addButton("Append to Old Data", QMessageBox.ButtonRole.AcceptRole)
        msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == replace_button:
            return 'replace'
        elif msg_box.clickedButton() == append_button:
            return 'append'
        else:
            return None