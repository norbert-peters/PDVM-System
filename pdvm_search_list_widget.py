from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit,
    QLabel, QPushButton, QSpinBox, QHeaderView, QGroupBox,
    QToolBar, QAction, QStyle, QComboBox, QApplication, QSizePolicy,
    QScrollArea
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QSize
from datetime import datetime
from functools import partial
from PyQt5.QtCore import QTimer


# Logging-Setup
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pdvm_app.log"),
        logging.StreamHandler()
    ]
)

class PdvmTableModel(QAbstractTableModel):
    """
    TableModel, das dynamisch Zeilen vom ViewManager übernimmt und darstellt.
    """
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.rows = []

    def update_data(self, rows: list, columns: list):
        """Zeilen und Spalten gleichzeitig updaten."""
        self.beginResetModel()
        self.rows = rows
        self.columns = columns
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        col = self.columns[index.column()]
        val = row.get(col)
        if isinstance(val, datetime):
            return val.strftime('%d.%m.%Y')
        return val

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return super().headerData(section, orientation, role)

    def guid_for_row(self, row_idx):
        return self.rows[row_idx]['GUID']

class SearchListWidget(QWidget):
    """
    Such- und Auswahlliste mit Filter, Sortierung, Paging
    und Datumsteilen als leere Textfelder in Mode 0.
    """
    selectionChanged = pyqtSignal(list)

    def _create_text_filter(self, col: str, placeholder: str, slot_fn):
        """
        Erzeugt ein QLineEdit mit Clear-Button, Platzhalter und Signal-Binding.
        :param col: Spaltenname
        :param placeholder: Text für setPlaceholderText()
        :param slot_fn: Methode, die beim textChanged gerufen wird (z. B. self._set_contains)
        """
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setClearButtonEnabled(True)
        le.textChanged.connect(partial(slot_fn, col))
        return le

    def __init__(self, view_manager, table_name, parent=None):
        super().__init__(parent)
        self.vm = view_manager
        self.table = table_name
        self.filters = {}
        self.sort = []
        self.page = 0
        self.page_size = 25
        self.total = 0
        self.column_widths_applied = False

        self.setStyleSheet("""
            QGroupBox { font-weight: bold; margin-top: 10px; }
            QToolBar { background: #f0f0f0; border: none; }
            QTableView { gridline-color: #ddd; }
            QPushButton { border-radius: 5px; padding: 4px 8px; }
        """
        )
        layout = QVBoxLayout(self)

        # Filter-Section
        fb = QGroupBox("Filter")
        fl = QHBoxLayout(fb)
        definition = self.vm.get_view_definition(self.table)
        self.columns = [c['name'] for c in definition['columns']]
        self.meta = {c['name']: c for c in definition['columns']}
        self.filter_widgets = {}


        for col in self.columns:
            meta = self.meta[col]
            if not meta.get('searchable'):
                continue
            fl.addWidget(QLabel(col + ':'))
            ft = meta.get('filterType')
            if ft == 'dateRange' and self.vm.mode == 0:
                ft = 'dateParts'

            # 1) Contains
            if ft == 'contains':
                le = self._create_text_filter(col, 'enthält …', self._set_contains)
                fl.addWidget(le)
                self.filter_widgets[col] = le

            # 2) Dropdown (unverändert)
            elif ft == 'dropdown':
                cb = QComboBox()
                cb.addItem('-- alle --', None)
                for opt in self.vm.get_lookup_options(meta.get('lookup', {})):
                    cb.addItem(str(opt), opt)
                cb.currentIndexChanged.connect(partial(self._set_dropdown, col, cb))
                fl.addWidget(cb)
                self.filter_widgets[col] = cb

            # 3) DateParts (Textfelder statt Spinner)
            elif ft == 'dateParts':
                for suffix, ph, w in [
                    ('_tag',   'TT',   45),
                    ('_monat', 'MM',   45),
                    ('_jahr',  'JJJJ', 60),
                ]:
                    le = QLineEdit()
                    le.setPlaceholderText(ph)
                    le.setClearButtonEnabled(True)
                    le.setFixedWidth(w)
                    # Bind col und suffix, das txt kommt automatisch vom Signal
                    le.textChanged.connect(partial(self._set_datepart, col, suffix))
                    fl.addWidget(le)
                    self.filter_widgets[col + suffix] = le

            # 4) Fallback wie contains, aber ohne Platzhalter-Text
            else:
                le = self._create_text_filter(col, '', self._set_contains)
                fl.addWidget(le)
                self.filter_widgets[col] = le

        layout.addWidget(fb)

        # Toolbar
        tb = QToolBar()
        size = self.style().pixelMetric(QStyle.PM_SmallIconSize)
        tb.setIconSize(QSize(size,size))
        p = QAction(self.style().standardIcon(QStyle.SP_ArrowLeft), 'Prev', self)
        n = QAction(self.style().standardIcon(QStyle.SP_ArrowRight), 'Next', self)
        p.triggered.connect(self._prev_page); n.triggered.connect(self._next_page)
        tb.addAction(p); tb.addWidget(QLabel('Seite:')); self.lbl_page=QLabel(); tb.addWidget(self.lbl_page)
        tb.addAction(n); tb.addSeparator(); tb.addWidget(QLabel('Zeilen/Seite:'))
        sp = QSpinBox(value=self.page_size, minimum=1, maximum=500)
        sp.valueChanged.connect(self._set_page_size); tb.addWidget(sp)
        layout.addWidget(tb)

        # Table
        self.model = PdvmTableModel(self.columns)
        tv = QTableView()
        tv.setModel(self.model)
        tv.setAlternatingRowColors(True)
        tv.setSortingEnabled(True)

        hdr = tv.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.sectionClicked.connect(self._on_header)

        # Scroll-Container erzeugen
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container-Widget für die Tabelle erstellen
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(tv)

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        # Referenz behalten
        self.table_view = tv  # bleibt gleich


        # Selection
        btn = QPushButton('Ausgewählte GUIDs übernehmen')
        btn.clicked.connect(self._emit_selection); layout.addWidget(btn)

        # initial load
        self._reload()

        # verzögertes erstes Anwenden
        QTimer.singleShot(0, self._apply_column_widths)

        #QTimer.singleShot(0, lambda: (self._apply_display_width(), self._apply_column_widths()))

    def _set_contains(self, col, txt):
        self.filters[col] = {'type':'contains','value': txt}
        self.page=0; self._reload()

    def _set_dropdown(self, col, combo, idx):
        val = combo.currentData()
        self.filters[col] = {'type':'dropdown','value': val}
        self.page=0; self._reload()

    def _set_datepart(self, col, suffix, txt):
        key = col + suffix
        txt = txt.strip()
        if txt == '':
            self.filters.pop(key, None)
        else:
            self.filters[key] = {'type':'contains','value': txt}
        self.page=0; self._reload()

    def _set_page_size(self, v):
        self.page_size=v; self.page=0; self._reload()

    def _prev_page(self):
        if self.page>0: self.page-=1; self._reload()

    def _next_page(self):
        if (self.page+1)*self.page_size<self.total: self.page+=1; self._reload()

    def _on_header(self, idx):
        col=self.columns[idx]
        cur = next((s for s in self.sort if s[0]==col), None)
        direction = 'asc' if not cur or cur[1]=='desc' else 'desc'
        self.sort = [(col,direction)]; self._reload()

    def _reload(self):
        rows, self.total = self.vm.query_view(
            table=self.table,
            filters=self.filters,
            sort=self.sort,
            page=self.page,
            page_size=self.page_size
        )

        # Datum/Lookup konvertieren wie gehabt
        for r in rows:
            for c, m in self.meta.items():
                if m['type']=='date' and r.get(c):
                    r[c] = self.vm.pdvm_to_date(float(r[c]))
                if m['type']=='lookup' and r.get(c) is not None:
                    r[c] = self.vm.get_lookup_display_value(m['lookup'], r[c])

        # Daten ins Model
        self.model.update_data(rows, self.columns)

        # Paging-Label
        pages = (self.total + self.page_size - 1) // self.page_size
        self.lbl_page.setText(f"{self.page+1}/{pages}")

        # **Neu**: Spaltenbreiten anwenden
        self._apply_column_widths()

    def _emit_selection(self):
        sel=self.table_view.selectionModel().selectedRows()
        guids=[self.model.guid_for_row(idx.row()) for idx in sel]
        self.selectionChanged.emit(guids)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _apply_column_widths(self):
        logging.debug(f"Spaltenbreiten anwenden: {self.column_widths_applied}")
        if self.column_widths_applied:
            return  # Nur 1× ausführen
        self.column_widths_applied = True

        raw_fields = self.vm.metadata[self.table]['felder']
        pct_list = []
        for name in self.columns:
            fld = next((f for f in raw_fields if f.get("name", f.get("feld")) == name), None)
            raw = fld.get("ui", {}).get("width", "0%") if fld else "0%"
            try:
                pct = int(str(raw).rstrip("%"))
            except ValueError:
                pct = 0

            logging.debug(f"Spalte {name}: {pct}%") 

            pct_list.append(pct)
            logging.debug(f"Pct_list {pct_list}")

        total_pct = sum(pct_list) or 1
        logging.debug(f"Total Pct: {total_pct}")
        if total_pct == 0:
            logging.debug("Keine Spaltenbreiten definiert, keine Anpassung.")
            return
        # Feste Basis-Breite über display_width
        logging.debug(f"Display Width: {self.vm.display_width}")
        dw = str(getattr(self.vm, "display_width", "100")).rstrip("%")
        logging.debug(f"Display Width: {dw}")
        if dw == "0":
            logging.debug("Display Width ist 0%, keine Anpassung.")
            return
        try:
            dw_val = int(dw)
        except ValueError:
            dw_val = 100
        logging.debug(f"Display Width Value: {dw_val}")
        parent_w = self.parent().width() if self.parent() else self.width()
        full_width = round(parent_w * (dw_val / 100.0))
        logging.debug(f"Full Width: {full_width}")
        self.table_view.setFixedWidth(full_width+20)  # +20 für Scrollbar
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Spaltenbreiten setzen (fix)
        for idx, pct in enumerate(pct_list):
            w = round(full_width * (pct / total_pct))
            self.table_view.setColumnWidth(idx, w)
