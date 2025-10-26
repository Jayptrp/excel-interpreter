# ui_db_window.py
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QListWidget, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

class DatabaseTablesWindow(QDialog):
    database_changed = pyqtSignal() # "กริ่ง" (Signal) ที่บอกหน้าหลักว่า DB เปลี่ยน

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller # รับ "สมอง" (Controller) มาจากหน้าหลัก
        
        self.setWindowTitle("Database Manager")
        self.setMinimumSize(400, 300)

        # --- Layouts & Widgets ---
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Tables in database:"))
        self.table_list_widget = QListWidget()
        
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import to Selected")
        self.export_button = QPushButton("Export Selected")
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)

        self.status_label = QLabel("Please select a table.")
        
        layout.addWidget(self.table_list_widget)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)

        # --- เชื่อม Signals & Slots ---
        self.import_button.clicked.connect(self.handle_import)
        self.export_button.clicked.connect(self.handle_export)
        self.table_list_widget.currentItemChanged.connect(
            lambda: self.status_label.setText("Ready.")
        )
        
        self.load_table_names()

    def load_table_names(self):
        tables, error = self.controller.get_table_names()
        if error:
            self.status_label.setText(f"Error loading tables: {error}")
            return
            
        self.table_list_widget.clear()
        self.table_list_widget.addItems(tables)
        self.status_label.setText("Tables loaded.")

    def get_selected_table(self):
        selected_item = self.table_list_widget.currentItem()
        if selected_item:
            return selected_item.text()
        else:
            self.status_label.setText("Error: No table selected!")
            return None

    def handle_import(self):
        table_name = self.get_selected_table()
        if not table_name:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File to Import", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            action = self.ask_import_action(table_name)
            if not action:
                self.status_label.setText("Import cancelled.")
                return

            success, error = self.controller.import_data(file_path, table_name, action)
            
            if success:
                self.status_label.setText(f"Data {action}d to '{table_name}' successfully.")
                self.database_changed.emit() # กดกริ่ง!
            else:
                self.status_label.setText(f"Import error: {error}")

    def handle_export(self):
        table_name = self.get_selected_table()
        if not table_name:
            return

        df, error = self.controller.load_dataframe(table_name)
        if error:
            self.status_label.setText(f"Export error: {error}")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Table As", f"{table_name}_export.xlsx", "Excel Files (*.xlsx)"
        )
        if file_path:
            success, error_msg = self.controller.export_data(df, file_path)
            if success:
                self.status_label.setText(f"Table '{table_name}' exported successfully.")
            else:
                self.status_label.setText(f"Export error: {error_msg}")

    def ask_import_action(self, table_name):
        """ถามผู้ใช้ว่าจะ Replace หรือ Append"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Import")
        msg_box.setText(f"How do you want to import data to '{table_name}'?")
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