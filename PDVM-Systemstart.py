# PDVM-Systemstart.py
import sys, io
from pdvm_login import LoginApp
from pdvm_menu_editor import MenuEditor
from pdvm_view_manager import PdvmViewManager
from pdvm_search_list_widget import SearchListWidget
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QApplication
)
from PyQt5.QtCore import Qt

from command_handler import CommandHandler
from menu_handler import MenuHandler

# Umstellung auf UTF-8 für die Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

class MainApp(QMainWindow):
    def __init__(self, user_daten):
        super().__init__()
        self.setWindowTitle("PDVM System - Hauptanwendung")
        self.resize(1000, 600)
        self.user_email = user_daten[0]  # Benutzername
        self.user_guid = user_daten[3]  # Benutzer GUID 
        # user_daten als dict laden
        if isinstance(user_daten[1], str):
            try:
                self.user_daten = json.loads(user_daten[2])
            except json.JSONDecodeError:
                self.user_daten = {}
        else:
            self.user_daten = user_daten[2]

        # Benutzername in der Titelleiste anzeigen
        self.user_name = f"{self.user_daten.get("Benutzer").get("Vorname")} {self.user_daten.get("Benutzer").get("Name")}"
        self.setWindowTitle(f"PDVM System - Hauptanwendung - {self.user_name}")

        self.startmenu_id = self.user_daten.get("Anwendungen", {}).get("MeineApps")
        logging.log(logging.INFO, f"🔹 Starte mit Startmenu-ID: {self.startmenu_id}")


        # Zentrales Widget und Layout
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        central.setLayout(self.main_layout)

        # Linke Sidebar für vertikales Menü
        self.menu_frame = QFrame()
        self.menu_frame.setFrameShape(QFrame.StyledPanel)
        self.menu_frame.setLayout(QVBoxLayout())
        self.main_layout.addWidget(self.menu_frame, 1)

        # Rechter Bereich als Container für Inhalte
        self.content_frame = QWidget()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_frame.setLayout(self.content_layout)
        self.main_layout.addWidget(self.content_frame, 4)

        # Platzhalterbegrüßung
        self._show_label("🔹 Willkommen im PDVM-System!")

        # Handler initialisieren
        self.command_handler = CommandHandler(self)
        self.menu_handler = MenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=self.startmenu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()

    def _show_label(self, text, small=False):
        # Hilfsmethode: löscht Inhalt und zeigt Label an
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        if small:
            lbl.setStyleSheet("font-size: 12px;")
        else:
            lbl.setStyleSheet("font-size: 16px;")
        self.content_layout.addWidget(lbl)

    def show_text(self, text):
        """Normaler Text im Hauptbereich."""
        self._show_label(text)

    def show_text_klein(self, text):
        """Kleine Meldung unten anhängen."""
        # Hänge neuen Text an
        current = []
        for i in range(self.content_layout.count()):
            w = self.content_layout.itemAt(i).widget()
            if isinstance(w, QLabel):
                current.append(w.text())
        combined = "\n".join(current + [text])
        self._show_label(combined, small=True)

    def open_menu_editor(self, menu_type, call_path=None):
        """Zeigt den Menüeditor im Inhaltsbereich an."""
        # Inhalt löschen
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        # Editor instanziieren und anzeigen
        editor = MenuEditor(self.content_frame, self.menu_handler.menu, menu_type, self, call_path)
        self.content_layout.addWidget(editor)

    def open_app_menu(self, user_app):
        """Wechselt in die Menüstruktur einer anderen Anwendung."""
        app_menu_id = self.user_daten.get("Anwendungen", {}).get(user_app, {}).get("Menu")
        self.menu_handler = MenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=app_menu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()
        self.setWindowTitle(f"PDVM {user_app} - {self.user_name}")
        self.show_text(f"🔹 Willkommen in {user_app}!")

    def open_start_menu(self):
        """Lädt erneut das Startmenü."""
        self.menu_handler = MenuHandler(
            root=self,
            menu_widget=self.menu_frame,
            menu_id=self.startmenu_id,
            command_handler=self.command_handler
        )
        self.menu_handler.create_menus()
        self.setWindowTitle("PDVM System - Hauptanwendung - {self.user_name}")
        self.show_text("🔹 Willkommen in der App Auswahl!")

    def pdvm_search(self, view_guid, frame_guid, mode):
        """
        Lädt zunächst die View, dann das Input-Frame im content_area.
        view_guid: GUID aus viewdaten-Tabelle
        frame_guid: GUID aus framedaten-Tabelle
        mode: Modus (aktuell ungenutzt)
        """
        call_daten = {
            "user_guid": self.user_guid,
            "view_guid": view_guid,
            "frame_guid": frame_guid,
            "mode": mode,
        }

        # 1) View laden
        self.view_manager = PdvmViewManager(call_daten=call_daten)
        table_name = self.view_manager.view_table
        # 2) Erzeuge dein SearchListWidget für eine Tabelle, z.B. 'persondaten'
        self.search_widget = SearchListWidget(self.view_manager, table_name=table_name)
        self.content_layout.addWidget(self.search_widget)

    def logout(self):
        """Logout: schließt App und zeigt Login erneut."""
        login = LoginApp(main_app_class=MainApp)
        login.show()
        self.close()


def main():
    app = QApplication(sys.argv)
    # Wir übergeben MainApp als Klassereferenz in den Login:
    login = LoginApp(main_app_class=MainApp)
    login.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()