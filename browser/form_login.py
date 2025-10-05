import os, sys, json, base64
from PIL import Image, ImageFilter
from PySide6 import QtCore
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (
    QDialog, QStackedLayout, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QApplication
)
from PySide6.QtGui import QPixmap, QMovie, QFont, QImage

BROWSER_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BACKGROUND_IMAGE = os.path.join(BROWSER_PATH, "ilimg", "back.png")

CONFIG_DIR = os.path.expanduser("~/.pac22_user")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
DEFAULT_FOLDER = os.path.join(CONFIG_DIR, "default")

DEFAULT_CONFIG = {
    "username": "unknown",
    "ram": "2GB",
    "key": base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8"),
    "settings": {
        "JavascriptCanAccessClipboard": True,
        "AutoLoadImages": True,
        "JavascriptEnabled": True,
        "JavascriptCanOpenWindows": True,
        "LinksIncludedInFocusChain": True,
        "LocalStorageEnabled": True,
        "LocalContentCanAccessRemoteUrls": True,
        "XSSAuditingEnabled": True,
        "SpatialNavigationEnabled": True,
        "LocalContentCanAccessFileUrls": True,
        "HyperlinkAuditingEnabled": True,
        "ScrollAnimatorEnabled": False,
        "ErrorPageEnabled": True,
        "PluginsEnabled": True,
        "FullScreenSupportEnabled": True,
        "ScreenCaptureEnabled": True,
        "WebGLEnabled": True,
        "Accelerated2dCanvasEnabled": True,
        "AutoLoadIconsForPage": True,
        "TouchIconsEnabled": True,
        "FocusOnNavigationEnabled": True,
        "PrintElementBackgrounds": True,
        "AllowRunningInsecureContent": True,
        "AllowGeolocationOnInsecureOrigins": True,
        "AllowWindowActivationFromJavaScript": True,
        "ShowScrollBars": True,
        "PlaybackRequiresUserGesture": True,
        "JavascriptCanPaste": True,
        "WebRTCPublicInterfacesOnly": True,
        "DnsPrefetchEnabled": True,
        "PdfViewerEnabled": True,
        "NavigateOnDropEnabled": True,
        "ReadingFromCanvasEnabled": True,
        "ForceDarkMode": True,
        "PrintHeaderAndFooter": True,
        "PreferCSSMarginsForPrinting": True,
        "TouchEventsApiEnabled": True
    }
}

# -------------------- Funções --------------------
def init_user_folder():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(DEFAULT_FOLDER, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f, indent=2)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    changed = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in config:
            config[k] = v
            changed = True
    if "settings" not in config:
        config["settings"] = DEFAULT_CONFIG["settings"]
        changed = True
    else:
        for k, v in DEFAULT_CONFIG["settings"].items():
            if k not in config["settings"]:
                config["settings"][k] = v
                changed = True
    if changed:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    return config

# -------------------- Form Login --------------------
class FormLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 450)
        self.setWindowTitle("Pac22 Login")
        self.username = None
        self.diretorio = CONFIG_DIR
        self.start_clicked = False  # só abre browser se clicar Start

        # Background borrado
        self.background_label = QLabel(self)
        self.set_background()

        # Stack layout
        self.stack = QStackedLayout()
        self.setLayout(self.stack)

        # Páginas
        self.page_create = self.build_create_page()
        self.page_loading = self.build_loading_page()
        self.page_start = self.build_start_page()

        self.stack.addWidget(self.page_create)
        self.stack.addWidget(self.page_loading)
        self.stack.addWidget(self.page_start)

        # Inicializa pastas/config
        init_user_folder()
        data = load_config()
        if data.get("username") and data["username"] != "unknown":
            self.username = data["username"]
            self.update_start_page()
            self.stack.setCurrentWidget(self.page_start)
        else:
            self.stack.setCurrentWidget(self.page_create)

        # CSS moderno
        self.setStyleSheet("""
            QWidget { font-family: 'JetBrains Mono'; }
            QLabel { color: #fff; font-size: 18px; }
            QLineEdit { border: none; border-bottom: 2px solid #555; background: transparent; color: #fff; padding: 5px; text-align: center; }
        """)

    def set_background(self):
        img = Image.open(BACKGROUND_IMAGE).convert("RGBA")
        img = img.resize((self.width(), self.height()), Image.Resampling.LANCZOS)
        blurred = img.filter(ImageFilter.GaussianBlur(7))

        data = blurred.tobytes("raw", "RGBA")
        qimg = QImage(data, blurred.width, blurred.height, QImage.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)

        self.background_label.setPixmap(pix)
        self.background_label.setGeometry(self.rect())
        self.background_label.setScaledContents(True)
        self.background_label.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_background()

    # -------------------- Estilo de botão com vidro fake --------------------
    def style_button(self, button: QPushButton):
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 40);  /* vidro fake */
                color: #fff;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                border: 1px solid rgba(255, 255, 255, 80);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 80);
            }
        """)
        button.setFixedSize(240, 50)

    # -------------------- Páginas --------------------
    def build_create_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("Registro de User")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("JetBrains Mono", 20, QFont.Bold))

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Digite seu nome...")
        self.input_username.setAlignment(Qt.AlignCenter)

        self.btn_create = QPushButton("CRIAR USER")
        self.btn_create.clicked.connect(self.handle_create_user)
        self.style_button(self.btn_create)

        layout.addWidget(title)
        layout.addWidget(self.input_username)
        layout.addWidget(self.btn_create, alignment=Qt.AlignCenter)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addStretch()
        wrapper_layout.addLayout(layout)
        wrapper_layout.addStretch()
        return wrapper

    def build_loading_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.loading_gif = QLabel()
        self.loading_gif.setAlignment(Qt.AlignCenter)
        gif_path = os.path.join(BROWSER_PATH, "ilimg", "loading.gif")
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            movie.setScaledSize(QSize(80,80))
            self.loading_gif.setMovie(movie)
            movie.start()

        layout.addWidget(self.loading_gif)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addStretch()
        wrapper_layout.addLayout(layout)
        wrapper_layout.addStretch()
        return wrapper

    def build_start_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        self.label_user = QLabel("USER: ???")
        self.label_user.setAlignment(Qt.AlignCenter)
        self.label_user.setFont(QFont("JetBrains Mono", 18, QFont.Bold))

        self.btn_start = QPushButton("START BROWSER")
        self.btn_start.clicked.connect(self.start_browser)
        self.style_button(self.btn_start)

        layout.addWidget(self.label_user)
        layout.addWidget(self.btn_start, alignment=Qt.AlignCenter)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.addStretch()
        wrapper_layout.addLayout(layout)
        wrapper_layout.addStretch()
        return wrapper

    # -------------------- Funções --------------------
    def handle_create_user(self):
        username = self.input_username.text().strip()
        if not username:
            return
        self.username = username
        self.stack.setCurrentWidget(self.page_loading)
        QTimer.singleShot(1200, self.create_user_config)

    def create_user_config(self):
        config = load_config()
        config["username"] = self.username
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        self.update_start_page()
        self.stack.setCurrentWidget(self.page_start)

    def update_start_page(self):
        self.label_user.setText(f"USER: {self.username}")

    def start_browser(self):
        self.start_clicked = True
        print("Abrindo browser agora!")
        self.close()

    def closeEvent(self, event):
        if not self.start_clicked:
            event.accept()
            QApplication.quit()
            sys.exit(0)
        else:
            event.accept()

# -------------------- Main --------------------
def main():
    app = QApplication(sys.argv)
    f = FormLogin()
    f.show()
    app.exec()

    if f.start_clicked:
        print("Aqui você chama o Browser real")
        # import browser
        # browser.main()

if __name__ == "__main__":
    main()
