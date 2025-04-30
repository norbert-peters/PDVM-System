import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from pdvm_view_manager import PdvmViewManager  # dein bereits existierendes Modul
from pdvm_search_list_widget import SearchListWidget  # das neue Widget aus dem PyQt‑Gerüst
import logging


class MainWindow(QMainWindow):
    def __init__(self, call_daten, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Meine Pdvm‑App (PyQt5)")
        # 1) Instanziere hier deinen Business‑Manager
        self.vm = PdvmViewManager(call_daten)
        # 2) Erzeuge dein SearchListWidget für eine Tabelle, z.B. 'persondaten'
        self.search_widget = SearchListWidget(self.vm, table_name="persondaten")
        self.setCentralWidget(self.search_widget)

if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s")
    app = QApplication(sys.argv)

    call_daten = {
        "user_guid": "4886ad26-061b-4662-a762-c8c83f36692d",
        "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
        "frame_guid": None,
        "mode": 0,
    }

    window = MainWindow(call_daten)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
