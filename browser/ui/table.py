import tldextract, sys, uuid, json, os, importlib

BROWSER_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append( BROWSER_PATH );

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSize,  Signal;

class Table(QTableWidget):
    doubleSelect = Signal( object );
    def __init__(self, parent=None, double_select=None):
        super().__init__(parent);
        self.lista = [];
        self.total_linhas = 0;
        self.doubleClicked.connect( self.__doubleSelect__ );
        self.double_select = double_select;
        self.selected = None;
    
    def cleanList(self):
        self.lista = [];
        self.total_linhas = 0;
        self.setRowCount( 0 );

    def add(self, array_colunas, objeto):
        self.setRowCount( self.total_linhas + 1 );
        for i in range(len(array_colunas)):
            self.setItem( self.total_linhas , i, QTableWidgetItem( array_colunas[i] ) );
        self.lista.append( objeto );
        self.total_linhas += 1;

    def populate(self, lista, fields):
        self.lista = lista;
        self.total_linhas = len( self.lista );
        self.setRowCount( len(self.lista) );
        for i in range(len(self.lista)):
            for j in range(len(fields)):
                self.setItem( i , j, QTableWidgetItem( self.lista[i][fields[j]])  );
    
    def __doubleSelect__(self):
        if self.double_select != None:
            self.selected = self.lista[self.currentRow().row()];
            self.doubleSelect.emit( self.get() );

    def get(self):

        return self.lista[self.currentRow()];

    def index(self):
        return self.currentRow();

    @staticmethod
    def widget_tabela(parent, colunas, tamanhos=None, double_click=None):
        if tamanhos == None:
            tamanhos = [];
            for i in range(len(colunas)):
                if i == 0:
                    tamanhos.append(QHeaderView.Stretch);
                else:
                    tamanhos.append(QHeaderView.ResizeToContents);
        table = Table(parent=parent);
        if double_click != None:
            table.doubleClicked.connect( double_click );
        js = {};
        for coluna in colunas:
            js[coluna] = "";
        table.setSelectionBehavior(QAbstractItemView.SelectRows); 
        table.setColumnCount(len(colunas));
        table.setEditTriggers(QAbstractItemView.NoEditTriggers);
        table.setHorizontalHeaderLabels(js.keys());
        header = table.horizontalHeader() 
        for i in range(len(tamanhos)):
            header.setSectionResizeMode(i, tamanhos[i]);
        table.setRowCount(0)
        return table;