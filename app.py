#!/usr/bin/env python3
import os
import sys
from PySide6.QtWidgets import QApplication
from browser.browser import Browser
from browser.form_login import FormLogin

# Força Qt usar o rendering | Arch + Wayland
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_WEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"

# Base path do browser
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
os.environ["BROWSER_PATH"] = BASE_PATH
os.environ["BROWSER_SECURE"] = "0"

#Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 (KHTML, like Gecko) Firefox/131.0 Windows 10 || Google Normal
#Mozilla/5.0 Windows 10 AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox Version/17.0.6 Windows 10 || Google 1990

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 (KHTML, like Gecko) Firefox/131.0 Windows 10"


def main():
    app = QApplication(sys.argv)

    f = FormLogin()
    f.exec()

    # Se usuário não passou nada, cai fora
    if not f.diretorio:
        print("Nenhum diretório definido pelo login, saindo...")
        sys.exit(0)

    # Inicializa browser já com diretório vindo do FormLogin
    browser = Browser(f.diretorio, user_agent=USER_AGENT)
    browser.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

#if __name__ == "__main__":
#    if os.name != "nt":
#        main()
#    else:
#        print("Windows causa dor de cabeça!") <- inativo pro win pegar. infelizmente!
