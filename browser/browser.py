#!/usr/bin/env python3
import tldextract, sys, json, os, pathlib, requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QTabWidget, QListWidget, QPushButton, QTabBar, QStyle, QProxyStyle,
    QLabel, QGroupBox, QRadioButton, QButtonGroup, QScrollArea
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QEvent, QUrl, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from browser.panel_myass import PanelMyass
from browser.ui.custom_web_engine_page import CustomWebEnginePage
from browser.ui.private_profile import PrivateProfile

#Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0.6 Safari/605.1.15

HISTORY_FILE = "history.json"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 (KHTML, like Gecko) Firefox/131.0 Windows 10"

BROWSER_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if BROWSER_PATH is None:
    BROWSER_PATH = str(pathlib.Path(__file__).parent.parent.resolve())
sys.path.append(BROWSER_PATH)


class NoFocusProxyStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return
        super().drawPrimitive(element, option, painter, widget)


# ---------------- BrowserTab ----------------
class BrowserTab(QWidget):
    def __init__(self, browser, url=None):
        super().__init__()
        self.browser = browser
        self.user_agent = browser.user_agent
        self.profile = browser.profile
        self.user_typing = False

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- Navegação ---
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.reload_button = QPushButton("⟳")

        for btn in [self.back_button, self.forward_button, self.reload_button]:
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                color: #fff; 
                margin-top: -3px;
                outline: none;
            """)
            btn.setCursor(Qt.PointingHandCursor)

        # Barra de URL
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(24)
        self.url_bar.setPlaceholderText("Enter URL...")
        self.url_bar.textChanged.connect(self.on_text_changed)
        self.url_bar.returnPressed.connect(self.handle_enter_press)
        self.url_bar.keyPressEvent = self.handle_keypress
        self.url_bar.focusInEvent = self.on_url_focus_in
        self.url_bar.focusOutEvent = self.on_url_focus_out
        self.url_bar.setStyleSheet("""
            background-color: #2e2e2e; 
            color: #fff; 
            border: 1px solid #555; 
            border-radius: 3px; 
            outline: none;
        """)

        # --- NOVO LAYOUT: botões à direita ---
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        top_layout.addWidget(self.url_bar)  # URL bar cresce à esquerda

        # Layout horizontal só pros botões, à direita
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        for btn in [self.back_button, self.forward_button, self.reload_button]:
            btn_layout.addWidget(btn)

        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        top_layout.addWidget(btn_widget)

        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        top_widget.setFixedHeight(28)
        top_widget.setStyleSheet("background-color: #1e1e1e; border: none;")
        self.layout.addWidget(top_widget)

        # Lista de histórico
        self.history_list = QListWidget(self)
        self.history_list.setWindowFlags(Qt.Widget)
        self.history_list.setFocusPolicy(Qt.NoFocus)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setStyleSheet("""
            background-color: #2e2e2e; 
            color: #fff; 
            border: 1px solid #555; 
            outline: none;
        """)
        self.history_list.hide()
        self.history_list.itemClicked.connect(self.select_history_item)
        self.history_list.itemActivated.connect(self.select_history_item)

        # WebView
        self.web_view = QWebEngineView()
        self.web_view.setPage(CustomWebEnginePage(self.profile, self))
        self.web_view.page().profile().setHttpUserAgent(self.user_agent)

        # Scrollbar dark
        self.web_view.loadFinished.connect(self.apply_custom_scrollbar)
        self.web_view.page().urlChanged.connect(self.update_url_bar)
        self.web_view.titleChanged.connect(self.update_tab_title)
        self.web_view.urlChanged.connect(self.update_tab_title)

        self.layout.addWidget(self.web_view, 1)
        self.setLayout(self.layout)

        # --- Conectar botões ---
        self.back_button.clicked.connect(self.web_view.back)
        self.forward_button.clicked.connect(self.web_view.forward)
        self.reload_button.clicked.connect(self.web_view.reload)

        # Eventos globais
        self.url_bar.installEventFilter(self)
        self.web_view.installEventFilter(self)
        self.installEventFilter(self)

        if url:
            self.url_bar.setText(url)
            self.load_url()

    # --- Funções auxiliares ---
    def apply_custom_scrollbar(self, ok):
        if not ok: return
        js = """
        (function(){
            if (document.getElementById('qt-custom-scrollbar')) return;
            var style = document.createElement('style');
            style.id = 'qt-custom-scrollbar';
            style.innerHTML = `
                body { background-color: #1e1e1e !important; color: #e0e0e0 !important; }
                *::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
                *::-webkit-scrollbar-track { background: #2e2e2e !important; border-radius: 3px !important; }
                *::-webkit-scrollbar-thumb { background: #555 !important; border-radius: 3px !important; }
                *::-webkit-scrollbar-thumb:hover { background: #888 !important; }
            `;
            (document.head || document.documentElement).appendChild(style);
        })();
        """
        self.web_view.page().runJavaScript(js)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.history_list.isVisible() and obj not in [self.url_bar, self.history_list]:
                self.history_list.hide()
        return super().eventFilter(obj, event)

    def on_text_changed(self, text):
        if self.user_typing:
            self.show_suggestions()
        else:
            self.history_list.hide()

    def handle_keypress(self, event):
        self.user_typing = True
        if event.key() == Qt.Key_Down and self.history_list.isVisible():
            self.history_list.setFocus()
            self.history_list.setCurrentRow(0)
        else:
            QLineEdit.keyPressEvent(self.url_bar, event)

    def on_url_focus_in(self, event):
        QLineEdit.focusInEvent(self.url_bar, event)

    def on_url_focus_out(self, event):
        self.user_typing = False
        self.history_list.hide()
        QLineEdit.focusOutEvent(self.url_bar, event)

    def load_url(self):
        url = self.url_bar.text().strip()
        if not url: return
        if not url.startswith("http"): url = "https://" + url
        self.web_view.setUrl(QUrl(url))
        self.web_view.setFocus()
        self.history_list.hide()
        if url not in self.browser.history:
            self.browser.history.append(url)
            self.browser.save()

    def handle_enter_press(self):
        self.load_url()
        self.history_list.hide()

    def update_url_bar(self, url):
        if not isinstance(url, str): url = url.toString()
        self.url_bar.setText(url)
        self.url_bar.setCursorPosition(0)

    def reposition_history_list(self):
        if self.history_list.isVisible():
            pos = self.url_bar.mapToParent(self.url_bar.rect().bottomLeft())
            self.history_list.move(pos)
            self.history_list.setFixedWidth(self.url_bar.width())
            self.history_list.raise_()

    def show_suggestions(self):
        text = self.url_bar.text().strip().lower()
        if text:
            suggestions = [url for url in self.browser.history if text in url.lower()]
            if suggestions:
                self.history_list.clear()
                self.history_list.addItems(suggestions)
                self.history_list.setFixedHeight(min(len(suggestions) * 20, 200))
                self.reposition_history_list()
                self.history_list.show()
                return
        self.history_list.hide()

    def select_history_item(self, item):
        self.url_bar.setText(item.text())
        self.load_url()

    def update_tab_title(self, *args):
        url = self.web_view.url().toString()
        if url:
            ext = tldextract.extract(url)
            domain = ext.domain + "." + ext.suffix if ext.domain else url
            index = self.browser.tabs.indexOf(self)
            if index != -1 and index < self.browser.tabs.count() - 1:
                self.browser.tabs.setTabText(index, domain)

    # --- Funções ---
    def apply_custom_scrollbar(self, ok):
        if not ok: return
        js = """
        (function(){
            if (document.getElementById('qt-custom-scrollbar')) return;
            var style = document.createElement('style');
            style.id = 'qt-custom-scrollbar';
            style.innerHTML = `
                body { background-color: #1e1e1e !important; color: #e0e0e0 !important; }
                *::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
                *::-webkit-scrollbar-track { background: #2e2e2e !important; border-radius: 3px !important; }
                *::-webkit-scrollbar-thumb { background: #555 !important; border-radius: 3px !important; }
                *::-webkit-scrollbar-thumb:hover { background: #888 !important; }
            `;
            (document.head || document.documentElement).appendChild(style);
        })();
        """
        self.web_view.page().runJavaScript(js)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.history_list.isVisible() and obj not in [self.url_bar, self.history_list]:
                self.history_list.hide()
        return super().eventFilter(obj, event)

    def on_text_changed(self, text):
        if self.user_typing:
            self.show_suggestions()
        else:
            self.history_list.hide()

    def handle_keypress(self, event):
        self.user_typing = True
        if event.key() == Qt.Key_Down and self.history_list.isVisible():
            self.history_list.setFocus()
            self.history_list.setCurrentRow(0)
        else:
            QLineEdit.keyPressEvent(self.url_bar, event)

    def on_url_focus_in(self, event):
        QLineEdit.focusInEvent(self.url_bar, event)

    def on_url_focus_out(self, event):
        self.user_typing = False
        self.history_list.hide()
        QLineEdit.focusOutEvent(self.url_bar, event)

    def load_url(self):
        url = self.url_bar.text().strip()
        if not url: return
        if not url.startswith("http"): url = "https://" + url
        self.web_view.setUrl(QUrl(url))
        self.web_view.setFocus()
        self.history_list.hide()
        if url not in self.browser.history:
            self.browser.history.append(url)
            self.browser.save()

    def handle_enter_press(self):
        self.load_url()
        self.history_list.hide()

    def update_url_bar(self, url):
        if not isinstance(url, str): url = url.toString()
        self.url_bar.setText(url)
        self.url_bar.setCursorPosition(0)

    def reposition_history_list(self):
        if self.history_list.isVisible():
            pos = self.url_bar.mapToParent(self.url_bar.rect().bottomLeft())
            self.history_list.move(pos)
            self.history_list.setFixedWidth(self.url_bar.width())
            self.history_list.raise_()

    def show_suggestions(self):
        text = self.url_bar.text().strip().lower()
        if text:
            suggestions = [url for url in self.browser.history if text in url.lower()]
            if suggestions:
                self.history_list.clear()
                self.history_list.addItems(suggestions)
                self.history_list.setFixedHeight(min(len(suggestions) * 20, 200))
                self.reposition_history_list()
                self.history_list.show()
                return
        self.history_list.hide()

    def select_history_item(self, item):
        self.url_bar.setText(item.text())
        self.load_url()

    def update_tab_title(self, *args):
        url = self.web_view.url().toString()
        if url:
            ext = tldextract.extract(url)
            domain = ext.domain + "." + ext.suffix if ext.domain else url
            index = self.browser.tabs.indexOf(self)
            if index != -1 and index < self.browser.tabs.count() - 1:
                self.browser.tabs.setTabText(index, domain)

# ---------------- SettingsTab ----------------
class SettingsTab(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #1e1e1e; border: none;")
        main_widget = QWidget()
        scroll.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.user_agent_info = {
            "pc": ["Windows 11", "Windows 10", "Windows 7", "Windows XP", "Mac 64x", "MacOS Ventura", "MacOS Sonoma", "Linux Mint", "Arch Linux", "Debian Linux", "Ubuntu 22.04", "Linux x86_64"],
            "browser": ["Chrome", "Firefox", "Safari", "Edge", "Opera", "Vivaldi", "LibreWolf"]
        }

        group_pc = QGroupBox()
        pc_layout = QVBoxLayout()
        group_pc.setLayout(pc_layout)
        label_pc = QLabel("<b>Computer:</b>")
        pc_layout.addWidget(label_pc)
        self.pc_buttons = QButtonGroup()
        for pc in self.user_agent_info["pc"]:
            btn = QRadioButton(pc)
            pc_layout.addWidget(btn)
            self.pc_buttons.addButton(btn)
        self.pc_buttons.buttons()[0].setChecked(True)
        layout.addWidget(group_pc)

        group_browser = QGroupBox()
        browser_layout = QVBoxLayout()
        group_browser.setLayout(browser_layout)
        label_browser = QLabel("<b>Browser:</b>")
        browser_layout.addWidget(label_browser)
        self.browser_buttons = QButtonGroup()
        for b in self.user_agent_info["browser"]:
            btn = QRadioButton(b)
            browser_layout.addWidget(btn)
            self.browser_buttons.addButton(btn)
        self.browser_buttons.buttons()[0].setChecked(True)
        layout.addWidget(group_browser)

        layout.addStretch()
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        for btn_group in [self.pc_buttons, self.browser_buttons]:
            for btn in btn_group.buttons():
                btn.toggled.connect(self.update_user_agent)

    def update_user_agent(self):
        pc = next((b.text() for b in self.pc_buttons.buttons() if b.isChecked()), "")
        browser = next((b.text() for b in self.browser_buttons.buttons() if b.isChecked()), "")
        ua = f"Mozilla/5.0 ({pc}) AppleWebKit/605.1.15 (KHTML, like Gecko) {browser} Version/17.0.6 {pc}"
        self.browser.user_agent = ua
        for i in range(self.browser.tabs.count() - 1):
            tab = self.browser.tabs.widget(i)
            if hasattr(tab, "web_view"):
                tab.web_view.page().profile().setHttpUserAgent(ua)

# ---------------- Browser ----------------
class Browser(QMainWindow):
    def __init__(self, path, user_agent=None):
        super().__init__()
        self.path = path
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.config = {}
        self.history = []

        config_path = os.path.join(self.path, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {"default": {"url": "https://www.google.com"}}

        self.profile = PrivateProfile(self.path, self.config)

        history_path = os.path.join(self.profile.path, HISTORY_FILE)
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                self.history = json.load(f)

        self.setWindowTitle("Pac22 Browser")
        self.setStyle(NoFocusProxyStyle())
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e1e; color: #ffffff; outline: none; border: none; }
            QLineEdit { background-color: #2e2e2e; color: #fff; border: 1px solid #555; border-radius: 3px; outline: none; }
            QListWidget { background-color: #2e2e2e; color: #fff; border: 1px solid #555; outline: none; }
            QPushButton { background-color: #3a3a3a; color: #fff; border: 1px solid #555; border-radius: 3px; outline: none; }
            QPushButton:hover { background-color: #505050; }
            QTabWidget::pane { border: none; background-color: #2e2e2e; }
            QTabBar::tab { background: #2e2e2e; color: #fff; border: none; padding: 4px; margin: 1px; outline: none; }
            QTabBar::tab:selected { background: #555555; }
            QTabBar::tab:hover { background: #444444; }
        """)

        # Browser com abas
        self.tab_principal = QTabWidget()
        self.tab_principal.setTabsClosable(False)
        self.tab_principal.setDocumentMode(True)
        self.tab_principal.setTabPosition(QTabWidget.TabPosition.West)
        self.setCentralWidget(self.tab_principal)

        # Outras abas
        self.tab_page_browser = QWidget()
        self.tab_page_download = QWidget()
        self.invidious_view = QWebEngineView()
        self.invidious_loaded = False

        # Botões flutuantes Invidious
        self.btn_invidious_back = QPushButton("←", self.tab_page_download)
        self.btn_invidious_reload = QPushButton("⟳", self.tab_page_download)
        for btn in [self.btn_invidious_back, self.btn_invidious_reload]:
            btn.setFixedSize(39, 39)
            btn.setStyleSheet("""
                background-color: #3a3a3a; 
                color: #fff; 
                border: 1px solid #555; 
                border-radius: 5px;
            """)
        self.btn_invidious_back.clicked.connect(lambda: self.invidious_view.back())
        self.btn_invidious_reload.clicked.connect(lambda: self.invidious_view.reload())

        invidious_layout = QVBoxLayout()
        invidious_layout.setContentsMargins(0, 0, 0, 0)
        invidious_layout.setSpacing(0)
        invidious_layout.addWidget(self.invidious_view)
        self.tab_page_download.setLayout(invidious_layout)

        self.tab_page_download.resizeEvent = self.update_invidious_buttons_position

        self.tab_page_navigate = QWidget()
        self.navigation_list = QListWidget()
        nav_layout = QVBoxLayout()
        nav_layout.addWidget(self.navigation_list)
        self.tab_page_navigate.setLayout(nav_layout)
        self.update_navigation_list()

        self.tab_page_myass = PanelMyass(parent=self)
        self.tab_page_settings = SettingsTab(self)

        self.tab_principal.addTab(self.tab_page_browser, "Browser")
        self.tab_principal.addTab(self.tab_page_download, "Invidious")
        self.tab_principal.addTab(self.tab_page_navigate, "Navigation")
        self.tab_principal.addTab(self.tab_page_settings, "Settings")

        # Abas do navegador interno
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.South)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.check_plus_tab)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)
        self.tab_page_browser.setLayout(layout)

        self.add_plus_tab()
        self.tab_principal.currentChanged.connect(self.lazy_load_tabs)
        self.init_shortcuts()

    # ---------------- Funções do Browser ----------------
    def update_navigation_list(self):
        self.navigation_list.clear()
        for url in self.history:
            self.navigation_list.addItem(url)

    def lazy_load_tabs(self, index):
        widget = self.tab_principal.widget(index)
        if widget == self.tab_page_download and not self.invidious_loaded:
            self.invidious_loaded = True
            self.invidious_view.page().profile().setHttpUserAgent(self.user_agent)
            self.invidious_view.setUrl(QUrl("https://inv.nadeko.net/feed/popular"))
            self.invidious_view.loadFinished.connect(self.apply_custom_scrollbar_invidious)

    def apply_custom_scrollbar_invidious(self, ok):
        if ok:
            js = """
            (function(){
                if (document.getElementById('qt-custom-scrollbar')) return;
                var style = document.createElement('style');
                style.id = 'qt-custom-scrollbar';
                style.innerHTML = `
                    body { background-color: #1e1e1e !important; color: #e0e0e0 !important; }
                    *::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
                    *::-webkit-scrollbar-track { background: #2e2e2e !important; border-radius: 3px !important; }
                    *::-webkit-scrollbar-thumb { background: #555 !important; border-radius: 3px !important; }
                    *::-webkit-scrollbar-thumb:hover { background: #888 !important; }
                `;
                (document.head || document.documentElement).appendChild(style);
            })();
            """
            self.invidious_view.page().runJavaScript(js)

    def update_invidious_buttons_position(self, event):
        margin = 10
        w = self.tab_page_download.width()
        h = self.tab_page_download.height()
        self.btn_invidious_back.move(w - 2 * (39 + margin), h - 39 - margin)
        self.btn_invidious_reload.move(w - (39 + margin), h - 39 - margin)
        self.btn_invidious_back.raise_()
        self.btn_invidious_reload.raise_()
        event.accept()

    def new_tab(self, url=None):
        tab = BrowserTab(self, url or "https://www.google.com")
        index = max(0, self.tabs.count() - 1)
        self.tabs.insertTab(index, tab, "New Tab")
        self.tabs.setCurrentIndex(index)
        tab.url_bar.setFocus()

    def add_plus_tab(self):
        self.plus_tab = QWidget()
        index = self.tabs.addTab(self.plus_tab, "+")
        self.tabs.tabBar().setTabButton(index, QTabBar.LeftSide, None)
        self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, None)
        self.tabs.setTabEnabled(index, True)

        self.update_plus_tab_style()

        self.tabs.tabBar().installEventFilter(self)
        self.tabs.tabBar().tabMoved.connect(self.on_tab_moved)
        self.tabs.currentChanged.connect(self.check_plus_tab)

    def eventFilter(self, obj, event):
        if obj == self.tabs.tabBar():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.tabs.tabBar().tabAt(event.position().toPoint())
                if index == self.tabs.indexOf(self.plus_tab):
                    self.new_tab()
                    return True
            if event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonDblClick]:
                index = self.tabs.tabBar().tabAt(event.position().toPoint())
                if index == self.tabs.indexOf(self.plus_tab):
                    return True
        return super().eventFilter(obj, event)

    def update_plus_tab_style(self):
        plus_index = self.tabs.indexOf(self.plus_tab)
        style = f"""
            QTabBar::tab {{ 
                background: transparent; 
                color: #fff; 
                border: none; 
                padding: 4px; 
                margin: 1px; 
                min-width: 24px; 
                text-align: center;
            }}
            QTabBar::tab:hover {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
            QTabBar::tab:selected {{ background: #555555; }}
            QTabBar::tab:nth-child({plus_index + 1}) {{
                font-weight: bold; 
                color: white; 
                background: transparent;
            }}
        """
        self.tabs.tabBar().setStyleSheet(style)

    def on_tab_moved(self, from_index, to_index):
        plus_index = self.tabs.indexOf(self.plus_tab)
        if from_index == plus_index or to_index == plus_index:
            QTimer.singleShot(0, lambda: self.tabs.tabBar().moveTab(self.tabs.indexOf(self.plus_tab), self.tabs.count() - 1))
        QTimer.singleShot(0, self.update_plus_tab_style)

    def check_plus_tab(self, index):
        if self.tabs.widget(index) == self.plus_tab:
            self.new_tab()

    def save(self):
        history_path = os.path.join(self.profile.path, HISTORY_FILE)
        with open(history_path, "w") as f:
            json.dump(self.history, f)

    def close_application(self):
        QApplication.quit()
        sys.exit(0)

    def close_tab(self, index):
        if index == self.tabs.count() - 1:
            return
        if index == self.tabs.currentIndex():
            self.tabs.setCurrentIndex(index - 1 if index > 0 else 0)
        self.tabs.removeTab(index)

    def init_shortcuts(self):
        shortcuts = [
            ("Ctrl+Q", self.close_application),
            ("Ctrl+T", lambda: self.new_tab()),
            ("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex())),
            ("Ctrl+N", self.showMinimized),
        ]
        for key, func in shortcuts:
            a = QAction(self)
            a.setShortcut(key)
            a.triggered.connect(func)
            self.addAction(a)

        # F12 DevTools
        QShortcut(QKeySequence("F12"), self, activated=lambda: self.tabs.currentWidget().web_view.page().setDevToolsPage(QWebEngineView().page()))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = Browser(os.getcwd())
    browser.show()
    sys.exit(app.exec())
