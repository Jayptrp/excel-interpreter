# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui_main_window import MainWindow
from data_controller import DataController

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 1. สร้าง "สมอง" (Controller)
    controller = DataController()
    
    # 2. สร้าง "หน้าบ้าน" (View) และส่งสมองเข้าไป
    window = MainWindow(controller)
    window.show()
    
    sys.exit(app.exec())