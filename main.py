# main.py
# นำเข้าโมดูลที่จำเป็นสำหรับการทำงานของโปรแกรม
import sys
import os
from urllib.parse import urlparse
from weakref import proxy
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QScrollArea, 
    QFrame, QProgressBar
)
import subprocess
import atexit
import signal
import time
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPalette, QColor, QPainter, QLinearGradient, QBrush, QPixmap, QIcon
from func import check_server
from func.download import Downloader, file_hash
from func.request import get_config, save_image_from_url, download_file
from func.registry import SampRegistry
from func.file import clean_assets, ExtractThread, find_gta_sa, launch_samp

# คลาสสำหรับวาดพื้นหลังแบบ gradient
class GradientWidget(QWidget):
    """Widget สำหรับวาด gradient background"""
    def __init__(self, color1, color2, parent=None):
        super().__init__(parent)
        self.color1 = color1
        self.color2 = color2
        self.setAutoFillBackground(True)
    
    # ฟังก์ชันสำหรับวาด gradient บน widget
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.color1)
        gradient.setColorAt(1, self.color2)
        
        painter.fillRect(self.rect(), gradient)


# คลาสสำหรับแสดงข่าวในรูปแบบการ์ด
class NewsCard(QFrame):
    def __init__(self, title, date, description,
                 gradient_color1=None,
                 gradient_color2=None,
                 parent=None,
                 image_path=None):

        super().__init__(parent)
        self.original_y = None
        self.setFixedHeight(120)

        self.setStyleSheet("""
            NewsCard {
                background: rgba(15, 15, 25, 180);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 16px;
            }
            NewsCard:hover {
                background: rgba(20, 20, 30, 200);
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # =========================
        # Image / Gradient Panel
        # =========================
        # ตรวจสอบว่ามีภาพหรือไม่ ถ้ามีใช้ QLabel แสดงภาพ ถ้าไม่มีใช้ GradientWidget
        if image_path:
            self.image_panel = QLabel(self)
            self.image_panel.setFixedSize(100, 70)
            self.image_panel.setScaledContents(True)
            self.image_panel.setStyleSheet("""
                border-top-left-radius:16px;
                border-bottom-left-radius:16px;
            """)

            pix = QPixmap(image_path)
            self.image_panel.setPixmap(pix)

        else:
            # fallback gradient
            self.image_panel = GradientWidget(
                gradient_color1,
                gradient_color2,
                self
            )
            self.image_panel.setFixedSize(100, 70)

        layout.addWidget(self.image_panel)

        # =========================
        # Content Panel
        # =========================
        content_widget = QWidget(self)
        content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(6)

        title_label = QLabel(title, content_widget)
        title_label.setStyleSheet(
            "color:#ffffff; font-size:17px; font-weight:600;"
        )

        date_label = QLabel(date, content_widget)
        date_label.setStyleSheet(
            "color:#a0a0b0; font-size:12px;"
        )

        desc_label = QLabel(description, content_widget)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            "color:#a0a0b0; font-size:14px;"
        )

        content_layout.addWidget(title_label)
        content_layout.addWidget(date_label)
        content_layout.addWidget(desc_label)
        content_layout.addStretch()

        layout.addWidget(content_widget, 1)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    # ฟังก์ชันเมื่อเมาส์เข้าสู่การ์ด ทำ animation ยกขึ้น
    def enterEvent(self, event):
        if self.original_y is None:
            self.original_y = self.pos().y()

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(180)
        anim.setEndValue(QPoint(self.pos().x(), self.original_y - 4))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

        self.anim = anim
        super().enterEvent(event)

    
    # ฟังก์ชันเมื่อเมาส์ออกจากการ์ด ทำ animation กลับตำแหน่งเดิม
    def leaveEvent(self, event):
        if self.original_y is None:
            return

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(180)
        anim.setEndValue(QPoint(self.pos().x(), self.original_y))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

        self.anim = anim
        super().leaveEvent(event)



# คลาสสำหรับแผงแก้วโปร่งแสง
class GlassPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            GlassPanel {
                background: rgba(15, 15, 25, 180);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 16px;
            }
            GlassPanel QWidget {
                border: none;
            }
            GlassPanel QLabel {
                border: none;
            }
            GlassPanel QLineEdit {
                /* border จะถูกกำหนดใน stylesheet ของ QLineEdit เอง */
            }
        """)


# คลาสสำหรับปุ่มที่มีพื้นหลัง gradient
class GradientButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)
        self.original_y = 0
    
    # ฟังก์ชันสำหรับวาดปุ่มด้วย gradient
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#ff0000"))
        gradient.setColorAt(1, QColor("#e33c3c"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        painter.setPen(QColor(Qt.GlobalColor.white))
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
    
    # ฟังก์ชันเมื่อเมาส์เข้าปุ่ม ทำ animation ยกขึ้น
    def enterEvent(self, event):
        if self.original_y == 0:
            self.original_y = self.y()
        
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(200)
        anim.setEndValue(QPoint(self.x(), self.y() - 2))
        anim.start()
        self.anim = anim
        super().enterEvent(event)
    
    # ฟังก์ชันเมื่อเมาส์ออกจากปุ่ม ทำ animation กลับตำแหน่งเดิม
    def leaveEvent(self, event):
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(200)
        anim.setEndValue(QPoint(self.x(), self.original_y))
        anim.start()
        self.anim = anim
        super().leaveEvent(event)


# คลาสสำหรับแสดง notification แบบ popup
class NotificationPopup(QWidget):
    """Custom notification popup แบบ webapp"""
    def __init__(self, message, msg_type, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # กำหนดสีตามประเภทของข้อความ
        colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6'
        }
        self.border_color = colors.get(msg_type, "#d00000")
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container
        container = QFrame(self)
        container.setStyleSheet(f"""
            QFrame {{
                background: rgba(15, 15, 25, 250);
                border: 1px solid {self.border_color};
                border-radius: 12px;
            }}
        """)
        
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(24, 16, 24, 16)
        
        # Message
        msg_label = QLabel(message, container)
        msg_label.setStyleSheet(f"""
            color: white;
            font-size: 14px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        container_layout.addWidget(msg_label)
        
        layout.addWidget(container)
        
        # Adjust size
        self.adjustSize()
        self.setMinimumWidth(300)
        
        # Position at top-right of parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + parent_rect.width() - self.width() - 30 - 100
            y = parent_rect.y() + 30 - 60
            self.move(x, y)
        
        # Slide in animation from right
        self.start_x = x + 400
        self.end_x = x
        self.move(self.start_x, y)
        
        self.slide_in = QPropertyAnimation(self, b"pos")
        self.slide_in.setDuration(250)
        self.slide_in.setStartValue(QPoint(self.start_x, y))
        self.slide_in.setEndValue(QPoint(self.end_x, y))
        self.slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slide_in.start()
        
        # Auto close timer
        self.close_timer = QTimer(self)
        self.close_timer.timeout.connect(self.fade_out)
        self.close_timer.start(3000)
    
    # ฟังก์ชันสำหรับ fade out และปิด popup
    def fade_out(self):
        # Slide out to right
        current_pos = self.pos()
        self.slide_out = QPropertyAnimation(self, b"pos")
        self.slide_out.setDuration(250)
        self.slide_out.setStartValue(current_pos)
        self.slide_out.setEndValue(QPoint(self.start_x, current_pos.y()))
        self.slide_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slide_out.finished.connect(self.close)
        self.slide_out.start()


# คลาสสำหรับ title bar แบบ custom
class TitleBar(QWidget):
    """Custom title bar with close button"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Title
        title = QLabel(f"{resp['hostname']} Launcher", self)
        title.setStyleSheet("color: #ff0000; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        
        layout.addWidget(title)
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(40, 40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                font-size: 18px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 0, 0, 150);
            }
        """)
        close_btn.clicked.connect(self.parent.close)
        
        layout.addWidget(close_btn)
        
        # For dragging window
        self.drag_position = None
    
    # ฟังก์ชันสำหรับกดเมาส์เพื่อลากหน้าต่าง
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()
    
    # ฟังก์ชันสำหรับเคลื่อนเมาส์เพื่อลากหน้าต่าง
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    # ฟังก์ชันสำหรับปล่อยเมาส์หลังลาก
    def mouseReleaseEvent(self, event):
        self.drag_position = None


# คลาสสำหรับพื้นหลัง widget
class BackgroundWidget(QWidget):
    """Widget สำหรับ background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_pixmap = None
        
    # ตั้งค่าพื้นหลังจากภาพ
    def set_background(self, image_path):
        try:
            self.background_pixmap = QPixmap(image_path)
        except:
            self.background_pixmap = None
    
    # ฟังก์ชันสำหรับวาดพื้นหลัง
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0a0a0f"))
        
        if self.background_pixmap and not self.background_pixmap.isNull():
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.setOpacity(0.3)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)


# คลาสหลักสำหรับหน้าต่าง launcher
class MainWindow(QMainWindow):
    def __init__(self, resp, registry, data, is_update=False):
        super().__init__()
        self.resp = resp
        self.registry = registry
        self.data = data
        self.is_updating = False  # แก้ไข: ตั้งค่าเริ่มต้นเป็น False เพื่อหลีกเลี่ยง logic สับสน
        self.has_update = is_update
        self.current_notification = None
        self.setWindowTitle(f"{resp['hostname']} Launcher")
        self.setFixedSize(1280, 720)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.downloader = Downloader(self)
        # Main container
        container = QWidget(self)
        container.setStyleSheet("border: none;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Title bar
        self.title_bar = TitleBar(self)
        container_layout.addWidget(self.title_bar)
        
        # Main widget with background
        self.central_widget = BackgroundWidget(self)
        background = save_image_from_url(data['background_image'])
        self.central_widget.set_background(background)
        
        # Main grid layout
        main_layout = QGridLayout(self.central_widget)
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(20)
        
        # LEFT PANEL - setting
        self.create_left_panel(main_layout)
        
        # CENTER PANEL - News
        self.create_center_panel(main_layout)
        
        # RIGHT PANEL - Actions
        self.create_right_panel(main_layout)
        
        # BOTTOM PANEL - Progress
        self.create_bottom_panel(main_layout)
        
        container_layout.addWidget(self.central_widget)
        self.setCentralWidget(container)
        
        # Start player counter animation
        self.animate_player_count()
        if self.has_update:
            self.on_check_update()  # แก้ไข: ลบ self.is_updating = False เพราะตั้งเป็น False อยู่แล้ว
    
    # สร้างแผงด้านซ้ายสำหรับตั้งค่า
    def create_left_panel(self, main_layout):
        left_panel = GlassPanel(self)
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(20)
        # Header
        header = QLabel("ตั่งค่า", left_panel)
        header.setStyleSheet("""
            color: #ff0000;
            font-size: 24px;
            font-weight: 600;
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 25);
            padding-bottom: 16px;
            background: transparent;
        """)
        
        # Username
        user_label = QLabel("USERNAME", left_panel)
        user_label.setStyleSheet("color: #a0a0b0; font-size: 11px; font-weight: 500; background: transparent; border: none;")
        
        self.username_input = QLineEdit(left_panel)
        self.username_input.setText(self.registry.get_player_name())
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 76);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 10px;
                color: #ffffff;
                font-size: 15px;
                padding: 14px 16px;
            }
            QLineEdit:focus {
                border: 1px solid #ff0000;
                background: rgba(0, 0, 0, 100);
            }
        """)
        
        # setting button
        setting_btn = GradientButton("บันทึกการตั้งค่า", left_panel)
        setting_btn.clicked.connect(self.on_setting)
        
        left_layout.addWidget(header)
        left_layout.addWidget(user_label)
        left_layout.addWidget(self.username_input)
        left_layout.addStretch()
        left_layout.addWidget(setting_btn)
        
        main_layout.addWidget(left_panel, 0, 0, 1, 1)
    
    # สร้างแผงกลางสำหรับแสดงข่าว
    def create_center_panel(self, main_layout):
        center_widget = QWidget(self)
        center_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        center_widget.setStyleSheet("border: none;")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)
        
        # Header
        header = QLabel("ข่าวล่าสุด", center_widget)
        header.setStyleSheet("""
            color: #ff0000;
            font-size: 24px;
            font-weight: 600;
            padding-bottom: 16px;
            background: transparent;
            border: none;
        """)
        
        # Scroll area
        scroll_area = QScrollArea(center_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 50);
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 25);
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 50);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        scroll_content.setStyleSheet("border: none;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        news_list = self.data['news']
        for news in news_list:
            local_path = news['image']
            
            if os.path.exists(local_path):
                image_path = local_path
            else:
                clean_assets()
                image_path = save_image_from_url(news['image'], folder="assets")
            
            scroll_layout.addWidget(
                NewsCard(
                    news["title"],
                    news["date"],
                    news["content"],
                    parent=scroll_content,
                    image_path=image_path
                )
            )


        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        center_layout.addWidget(header)
        center_layout.addWidget(scroll_area)
        
        main_layout.addWidget(center_widget, 0, 1, 1, 1)
    
    # สร้างแผงด้านขวาสำหรับปุ่มและสถานะ
    def create_right_panel(self, main_layout):
        right_widget = QWidget(self)
        right_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        right_widget.setStyleSheet("border: none;")
        right_widget.setFixedWidth(340)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # Connect button
        connect_btn = QPushButton("▶ เข้าเกม", right_widget)
        connect_btn.setMinimumHeight(70)
        connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        connect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #ff0000, stop:1 #7c3aed);
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
            }

            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #e70404, stop:1 #8c4afd);
            }

            QPushButton:disabled {
                background: #1f1f27;
                color: #666;
            }
            """)

        connect_btn.clicked.connect(self.on_connect)
        if not self.resp.get("online", False):  # แก้ไข: ใช้ self.resp แทน resp เพื่อความสอดคล้อง
            connect_btn.setEnabled(False)
        # Secondary buttons
        update_btn = self.create_secondary_button("↻  ตรวจสอบการอัปเดต", right_widget)
        update_btn.clicked.connect(self.on_check_update)
        
        discord_btn = self.create_secondary_button("💬  เข้าร่วม Discord", right_widget)
        discord_btn.clicked.connect(self.on_open_discord)
        
        icon_server = QLabel(right_widget)
        icon_server.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_server.setStyleSheet("background: transparent; border: none;")
        local_path = self.data['ICON_SERVER']
            
        if os.path.exists(local_path):
            image_path = local_path
        else:
            clean_assets()
            image_path = save_image_from_url(self.data['ICON_SERVER'], folder="assets")
        pixmap = QPixmap(image_path)

        # ปรับขนาด (เลือกขนาดได้)
        pixmap = pixmap.scaled(
            150, 150,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        icon_server.setPixmap(pixmap)
        
        # ==============================
        # Server Status Panel
        # ==============================
        status_panel = GlassPanel(right_widget)
        status_layout = QHBoxLayout(status_panel)
        status_layout.setContentsMargins(20, 15, 20, 15)

        status_widget = QWidget(status_panel)
        status_v = QVBoxLayout(status_widget)
        status_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ---- Status Text ----
        online = self.resp.get("online", False)  # แก้ไข: ใช้ self.resp

        status_text = "ออนไลท์" if online else "ออฟไลน์"
        status_color = "#00ff9c" if online else "#ff4b4b"

        self.server_status_label = QLabel(status_text, status_widget)
        self.server_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.server_status_label.setStyleSheet(f"""
            color: {status_color};
            font-size: 20px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)

        status_caption = QLabel("สถานะเซิร์ฟเวอร์", status_widget)
        status_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_caption.setStyleSheet("""
            color: #a0a0b0;
            font-size: 12px;
            background: transparent;
            border: none;
        """)

        status_v.addWidget(self.server_status_label)
        status_v.addWidget(status_caption)

        status_layout.addWidget(status_widget)

        # 👉 add เข้า layout
        right_layout.addWidget(status_panel)


        # Stats panel
        stats_panel = GlassPanel(right_widget)
        stats_layout = QHBoxLayout(stats_panel)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        
        # Players online
        players_widget = QWidget(stats_panel)
        players_widget.setStyleSheet("background: transparent; border: none;")
        players_layout = QVBoxLayout(players_widget)
        players_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        
        self.player_count_label = QLabel("0", players_widget)
        self.player_count_label.setStyleSheet("color: #ff0000; font-size: 28px; font-weight: bold; background: transparent; border: none;")
        self.player_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        players_label = QLabel("ผู้เล่นออนไลน์", players_widget)
        players_label.setStyleSheet("color: #a0a0b0; font-size: 12px; background: transparent; border: none;")
        players_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        players_layout.addWidget(self.player_count_label)
        players_layout.addWidget(players_label)
        
        # Divider
        divider = QFrame(stats_panel)
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("background: rgba(255, 255, 255, 25); border: none;")
        divider.setFixedWidth(1)
        
        # Servers
        servers_widget = QWidget(stats_panel)
        servers_widget.setStyleSheet("background: transparent; border: none;")
        servers_layout = QVBoxLayout(servers_widget)
        servers_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        server_count_label = QLabel(f"{self.resp['max_players']}", servers_widget)  # แก้ไข: ใช้ self.resp
        server_count_label.setStyleSheet(self.player_count_label.styleSheet())
        server_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        servers_label = QLabel("ผู้เล่นสูงสุด", servers_widget)
        servers_label.setStyleSheet(players_label.styleSheet())
        servers_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        servers_layout.addWidget(server_count_label)
        servers_layout.addWidget(servers_label)
        
        stats_layout.addWidget(players_widget, 1)
        stats_layout.addWidget(divider)
        stats_layout.addWidget(servers_widget, 1)
        
        right_layout.addWidget(connect_btn)
        right_layout.addWidget(update_btn)
        right_layout.addWidget(discord_btn)
        right_layout.addWidget(icon_server)
        right_layout.addStretch()
        right_layout.addWidget(stats_panel)
        
        main_layout.addWidget(right_widget, 0, 2, 1, 1)
    
    # สร้างแผงด้านล่างสำหรับ progress bar
    def create_bottom_panel(self, main_layout):
        bottom_panel = GlassPanel(self)
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(20, 16, 20, 16)
        bottom_layout.setSpacing(10)
        
        # Progress info
        info_layout = QHBoxLayout()
        self.progress_text = QLabel("Ready to connect", bottom_panel)
        self.progress_text.setStyleSheet("color: #a0a0b0; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        
        self.progress_percent = QLabel("100%", bottom_panel)
        self.progress_percent.setStyleSheet("color: #ff0000; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        
        info_layout.addWidget(self.progress_text)
        info_layout.addStretch()
        info_layout.addWidget(self.progress_percent)
        
        # Progress bar
        self.progress_bar = QProgressBar(bottom_panel)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(0, 0, 0, 76);
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff0000, stop:1 #7c3aed);
                border-radius: 4px;
            }
        """)
        
        bottom_layout.addLayout(info_layout)
        bottom_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(bottom_panel, 1, 0, 1, 3)
    
    # สร้างปุ่มรอง
    def create_secondary_button(self, text, parent):
        btn = QPushButton(text, parent)
        btn.setMinimumHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(15, 15, 25, 180);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 10px;
                color: #ffffff;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 12);
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)
        return btn
    
    # เริ่ม animation นับจำนวนผู้เล่น
    def animate_player_count(self):
        self.current_count = 0
        self.target_count = self.resp['players']  # แก้ไข: ใช้ self.resp
        
        self.counter_timer = QTimer(self)
        self.counter_timer.timeout.connect(self.update_player_count)
        self.counter_timer.start(25)
    
    # อัพเดทจำนวนผู้เล่นใน animation
    def update_player_count(self):
        self.current_count += 21
        if self.current_count >= self.target_count:
            self.current_count = self.target_count
            self.counter_timer.stop()
        self.player_count_label.setText(str(self.current_count))
    
    # เริ่มดาวน์โหลดไฟล์
    def start_download(self):
        url = self.data['game']['download_url']
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = "download.zip"

        self.save = filename

        self.downloader.start_download(
            url=url,
            save_path=self.save,
            on_progress=self.on_dl_progress,
            on_finished=self.on_dl_done,
            on_error=self.on_dl_error
        )



    # อัพเดท progress การดาวน์โหลด
    def on_dl_progress(self, p):
        self.progress_bar.setValue(p)
        self.progress_percent.setText(f"{p}%")
        self.progress_text.setText("Downloading...")

    # เมื่อดาวน์โหลดเสร็จ
    def on_dl_done(self, path):
        self.show_notification("ดาวน์โหลดเสร็จสมบูรณ์ — กำลังตรวจสอบไฟล์", "info")

        sha256 = file_hash(path)

        if sha256 == self.data['game']['sha256']:

            self.show_notification("ตรวจสอบความถูกต้องของไฟล์สำเร็จ", "success")

            self.has_update = False
            self.is_updating = False

            self.extract_thread = ExtractThread(path)
            self.extract_thread.finished.connect(self.on_extract_done)
            self.extract_thread.start()

        else:
            self.has_update = False
            self.is_updating = False

            self.show_notification("ตรวจสอบความถูกต้องของไฟล์ล้มเหลว", "error")


    # เมื่อ extraction เสร็จ
    def on_extract_done(self, ok, result):
        if ok:
            self.show_notification(f"การแตกไฟล์เสร็จสมบูรณ์เรียบร้อยแล้ว", "success")
            gta_path = find_gta_sa(result)
            hide_ip = "https://raw.githubusercontent.com/Dexedus-Dev/Launcher-SA-MP/main/samp-r1.asi"
            download_file(hide_ip, os.path.join(result, "samp-r1.asi"))
            if gta_path:
                self.registry.save_gta_path(gta_path)  # แก้ไข: ใช้ self.registry
                self.show_notification(f"คุณสามารถเล่นเกมได้แล้ว", "info")
                self.registry.set_version(self.data['version'])
                self.reset_progress()
            else:
                self.show_notification("ไม่พบ GTA San Andreas ในตำแหน่งที่คาดไว้", "warning")
        else:
            self.show_notification(f"การแตกไฟล์ล้มเหลว: {result}", "error")
            print("Error:", result)  

    # เมื่อดาวน์โหลด error
    def on_dl_error(self, err):
        self.show_notification(err, "error")
        print("Download error:", err)

    # เริ่ม animation progress
    def animate_progress(self, duration, callback=None):
        self.progress_elapsed = 0
        self.progress_duration = duration
        self.progress_callback = callback
        
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(50)
    
    # อัพเดท progress ใน animation
    def update_progress(self):
        self.progress_elapsed += 50
        progress = int((self.progress_elapsed * 100) / self.progress_duration)
        
        if progress >= 100:
            progress = 100
            self.progress_timer.stop()
            if self.progress_callback:
                self.progress_callback()
            QTimer.singleShot(2000, self.reset_progress)
        
        self.progress_bar.setValue(progress)
        self.progress_percent.setText(f"{progress}%")
        
        if progress < 33:
            self.progress_text.setText("Initializing...")
        elif progress < 66:
            self.progress_text.setText("Processing...")
        elif progress < 100:
            self.progress_text.setText("Almost done...")
        else:
            self.progress_text.setText("Complete!")
    
    # รีเซ็ต progress bar
    def reset_progress(self):
        self.progress_bar.setValue(100)
        self.progress_text.setText("Ready to connect")
        self.progress_percent.setText("100%")
    
    # แสดง notification
    def show_notification(self, message, msg_type):
        # ปิด notification เก่า (ถ้ามี)
        if self.current_notification:
            try:
                self.current_notification.close()
            except:
                pass
        
        # สร้าง notification ใหม่
        self.current_notification = NotificationPopup(message, msg_type, self)
        self.current_notification.show()
    
    # เมื่อกด connect
    def on_connect(self):
        if self.is_updating:
            self.show_notification("กรุณารอการอัปเดตให้เสร็จสิ้นก่อน", "warning")
            return
        
        username = self.username_input.text()
        if not username:
            self.show_notification("กรุณากรอกชื่อผู้เล่นก่อน", "error")
            self.username_input.setFocus()
            return
        
        self.show_notification(f"กำลังเชื่อมต่อกับเซิร์ฟเวอร์ในฐานะ {username}", "info")
        self.animate_progress(1500, lambda: self.show_notification("เชื่อมต่อสำเร็จ!", "success"))
        get_gta_path = self.registry.get_gta_path()
        launch_samp(
            get_gta_path,
            data['server_game']['ip'],
            data['server_game']['port']
        )
    # เมื่อกด check update (แก้ไข logic เพื่อ re-check version จริงๆ และลบ code ซ้ำ)
    def on_check_update(self):
        if self.is_updating:
            self.show_notification("อยู่ระหว่างดำเนินการอัปเดต", "warning")
            return
        
        self.is_updating = True
        self.show_notification("กำลังตรวจสอบการอัปเดต...", "info")
        
        # Re-check version เพื่อหลีกเลี่ยง bug ที่ไม่ตรวจสอบจริง
        current_version = self.registry.get_version()
        if current_version != self.data['version']:
            self.has_update = True
        else:
            self.has_update = False
        
        def check_complete():
            if self.has_update:
                self.show_notification("พบการอัปเดตใหม่! กำลังดาวน์โหลด...", "info")
                self.start_download()
            else:
                self.is_updating = False
                self.show_notification("คุณใช้เวอร์ชันล่าสุดแล้ว!", "success")
                self.reset_progress()
        
        QTimer.singleShot(1500, check_complete)
    
    # เมื่อกด save setting
    def on_setting(self):
        username = self.username_input.text()
        
        if not username:
            self.show_notification("กรุณากรอกชื่อผู้เล่น", "error")
            return
        
        self.show_notification("กำลังบันทึกการตั้งค่า...", "info")
        def setting_complete():
            self.registry.save_player_name(username)
            self.show_notification(f"ยินดีต้อนรับคุณ {username}!", "success")
        QTimer.singleShot(1000, setting_complete)
    
    # เมื่อกด join discord
    def on_open_discord(self):
        self.show_notification("กำลังเปิด Discord...", "info")

# ฟังก์ชันหลักสำหรับรันโปรแกรม
def main(ctx):
    resp = ctx["resp"]
    registry = ctx["registry"]
    data = ctx["data"]
    is_update = ctx["is_update"]

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon("icon.ico"))
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 15))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(15, 15, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 20, 30))
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(15, 15, 25))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    app.setPalette(dark_palette)
    
    window = MainWindow(resp, registry, data, is_update)
    window.show()
    
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    atexit.register(stop_proxy)

    exit_code = app.exec()
    sys.exit(exit_code)

proxy_process = None


def resource_path(path):
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, path)


# ==============================
# 🔥 Kill process ที่ใช้ PORT
# ==============================
def kill_port(port):
    try:
        cmd = f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /PID %a /F'
        subprocess.call(cmd, shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except:
        pass


# ==============================
# 🚀 START PROXY
# ==============================
def start_proxy(data):
    global proxy_process

    print("Cleaning port 7777...")
    kill_port(7777)

    proxy_path = resource_path("func/fake_server.exe")

    proxy_process = subprocess.Popen(
        [
            proxy_path,
            "--local-ip", "127.0.0.1",
            "--local-port", "7777",
            "--server-ip", data['server_game']['ip'],
            "--server-port", str(data['server_game']['port'])
        ],
        creationflags=(
            subprocess.CREATE_NO_WINDOW #DEBUG: หาก server ไม่ทำงาน ให้ลอง comment บรรทัดนี้ออกเพื่อดู error
            | subprocess.CREATE_NEW_PROCESS_GROUP 
        )  # แก้ไข: เพิ่ม CREATE_NEW_PROCESS_GROUP เพื่อให้สามารถ kill tree ได้ง่ายขึ้น
    )

    print("Proxy PID:", proxy_process.pid)

    time.sleep(1.5)


# ==============================
# 🛑 STOP PROXY (KILL TREE)
# ==============================
def stop_proxy():
    global proxy_process

    if not proxy_process:
        return

    try:
        if proxy_process.poll() is None:
            print("Stopping proxy...")

            # 🔥 kill ทั้ง process tree
            subprocess.call(
                f"taskkill /PID {proxy_process.pid} /T /F",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    except Exception as e:
        print("Force kill:", e)

    proxy_process = None


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    launcher_setting = "$SETTINGS_LINK"
    data = get_config(launcher_setting)

    start_proxy(data)

    resp = check_server.query_server(
        '127.0.0.1',
        7777
    )

    registry = SampRegistry(resp['hostname'])

    is_update = False

    if not registry.get_version():
        print("SAMP not found!")
        is_update = True

    if registry.get_version() != data['version']:
        print("New version available!")
        is_update = True

    context = {
        "data": data,
        "resp": resp,
        "registry": registry,
        "is_update": is_update
    }

    try:
        main(context)
    finally:
        stop_proxy()
