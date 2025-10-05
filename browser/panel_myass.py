import tldextract, sys, uuid, json, os, importlib, requests

BROWSER_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append( BROWSER_PATH );

from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QTextEdit, QHBoxLayout, QWidget, QTabWidget, QListWidget, QPushButton, QButtonGroup, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize

from browser.ui.table import *

class PanelMyass(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent);
        self.parent_ = parent;
        self.path_config = os.path.join(os.path.expanduser("~/pac22/"), "myass.json");
        if os.path.exists(self.path_config):
            self.config = json.loads( open(self.path_config, "r").read() );
        else:
            return;
        self.tab_myass = QTabWidget();
        self.tab_myass.setTabsClosable(False);
        self.tab_myass.setDocumentMode(True);
        self.tab_myass_works = QWidget()
        self.tab_myass.addTab(self.tab_myass_works,    "Tasks")
        self.tab_myass_settings = QWidget()
        self.tab_myass.addTab(self.tab_myass_settings, "Settings");
        layout = QVBoxLayout();
        layout.addWidget(self.tab_myass);
        self.setLayout(layout);
        #--------------------------- works --------------
        self.table = Table.widget_tabela(self.parent_, ["result", "workflow"], double_click=self.table_double_click); #, 
        layout = QVBoxLayout();
        layout.addWidget(self.table);
        btn_atualizar = QPushButton("Atualizar");
        layout.addWidget(btn_atualizar);
        btn_atualizar.clicked.connect(self.btn_atualizar_click);
        self.tab_myass_works.setLayout(layout);
    def table_double_click(self, item):
        f = FormWork(self.table.lista[self.table.currentRow()]);
        f.exec_();
        pass;
    def send_server(self, envelope):
        try:
            self.config = json.loads( open(self.path_config, "r").read() );
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'}
            page = requests.post(self.config["url"] + "service/works_list.php", timeout=30, headers=headers, json={ "device": "browser", "publick_key_name" : self.config["token"]});
            texto = ""
            if page.status_code == 200:
                texto = page.text;
                self.close();
            else:
                print(page.text);
                print("Satus request:", page.status_code);
            texto = texto.replace(self.config["token"],"");
            return texto;
        except:
            traceback.print_exc();
    def btn_atualizar_click(self):
        self.table.cleanList();
        trabalhos = self.works();
        #trabalhos = [{"campo1" : "a", "campo2" : "b"}, {"campo1" : "a", "campo2" : "b"}]
        #self.table.populate(trabalhos, ["campo1", "campo2"])
        for item in trabalhos:
            self.table.add([item["result"], item["workflow"]], item);
    
    def works(self):
        page = self.send_server({});
        trabalhos = json.loads(page);
        retorno = [];
        for trabalho in trabalhos:
            workflow = trabalho["workflow"];
            if workflow == None:
                workflow = "";
            step = trabalho.get("step");
            if step == None:
                step = "";
            result = trabalho["result"];
            if result == None:
                result = "";
            work = trabalho["data"];
            if work == None:
                work = "";
            retorno.append({"workflow" : workflow, "step" : step, "result" : result, "work" : work});
        return retorno;

class FormWork(QDialog):
    def __init__(self, work):
        super().__init__();
        self.resize(600, 320);
        layout = QGridLayout();
        layout.setContentsMargins(20, 20, 20, 20);
        layout.setSpacing(10);
        self.textEdit = QTextEdit();
        text = work["workflow"] + "\n----------\n" + work["work"] + "\n----------\n" + work["result"];
        self.textEdit.setPlainText( text );
        layout.addWidget(self.textEdit, 3, 0, 1, 3)
        #btn_myass = QPushButton("Delete to MyAss")
        #btn_myass.clicked.connect(self.start_myass_click)
        #layout.addWidget(btn_myass, 4, 1)
        self.setLayout(layout)