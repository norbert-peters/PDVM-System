import tkinter as tk
from tkinter import ttk

class PdvmDropdownPicker(ttk.Frame):
    def __init__(self, parent, dorp_inst, section_key, current_language="de", stichtag=1001.0, *args, **kwargs):
        """
        Erzeugt einen Dropdown-Picker basierend auf den übergebenen Dropdown-Daten.
        
        :param parent: Übergeordnetes Widget.
        :param config_data: Dictionary mit Dropdown-Daten.
        :param section_key: Der Schlüssel für den spezifischen Dropdown-Bereich (z.B. "anrede" oder "waehrung").
        :param current_language: Sprachcode, z.B. "de" oder "en".
        :param stichtag: Aktueller Stichtag (als float), um bei historischen Dropdowns zu filtern.
        """
        super().__init__(parent, *args, **kwargs)
        self.drop_inst = dorp_inst
        self.config_data = self.drop_inst.get_value(section_key)
        self.section_key = section_key
        self.current_language = current_language
        self.stichtag = float(stichtag)
        self.historical = self.config_data.get("historical", False)
        
        # Lade die Optionsliste anhand des Bereichsschlüssels und des Stichtags
        self.options = self._load_options()
        # Erstelle die Mappings: Anzeige -> key, key -> Anzeige
        self.key_to_display = {}
        self.display_to_key = {}
        self._create_mappings()
        
        # Variable für die Auswahl, und die Combobox
        self.selected_val = tk.StringVar()
        self.combobox = ttk.Combobox(self, textvariable=self.selected_val,
                                     state="readonly", values=self.display_options)
        self.combobox.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        if self.display_options:
            self.selected_val.set(self.display_options[0])
            self.selected_key = self.display_to_key.get(self.display_options[0])
        else:
            self.selected_key = None

    def _load_options(self):
        """Lädt und filtert die Optionen basierend auf den Dropdown-Daten und dem Stichtag."""
        alle_werte = self.config_data.get("werte", [])
        if self.historical:
            valid_options = []
            for option in alle_werte:
                try:
                    abdatum = float(option.get("abdatum", "1001.0"))
                except ValueError:
                    abdatum = 1001.0
                if abdatum <= self.stichtag:
                    valid_options.append(option)
            valid_options.sort(key=lambda opt: float(opt.get("abdatum", "1001.0")))
        else:
            valid_options = alle_werte.copy()
        return valid_options

    def _create_mappings(self):
        """Erzeugt die Mapping-Dictionaries und die Liste display_options anhand der geladenen Optionen."""
        self.display_options = []
        self.key_to_display.clear()
        self.display_to_key.clear()
        for option in self.options:
            # Hole den anzuzeigenden Text in der gewünschten Sprache oder nutze den Schlüssel als Fallback.
            display_val = option.get(self.current_language, option.get("key"))
            self.display_options.append(display_val)
            self.key_to_display[option.get("key")] = display_val
            self.display_to_key[display_val] = option.get("key")

    def refresh_options(self, stichtag):
        """Aktualisiert die Dropdown-Optionen basierend auf dem aktuellen stichtag."""
        self.stichtag = float(stichtag)
        self.options = self._load_options()
        self._create_mappings()
        self.combobox['values'] = self.display_options
        if self.display_options:
            self.selected_val.set(self.display_options[0])
            self.selected_key = self.display_to_key.get(self.display_options[0])
        else:
            self.selected_val.set("")
            self.selected_key = None

    def set_selected_key(self, key):
        """Setzt den aktuell ausgewählten Schlüssel im Dropdown."""
        self.selected_key = key
        display_val = self.key_to_display.get(key)
        if display_val is not None:
            self.selected_val.set(display_val)

    def get_selected_key(self):
        """Gibt den aktuell ausgewählten Schlüssel zurück."""
        sel = self.selected_val.get()
        return self.display_to_key.get(sel, None)

# Beispielhafte Nutzung:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PdvmDropdown Beispiel")

    # Beispiel-Konfiguration für ein Dropdown
    dropdown_config = {
        "gruppe": "anrede",
        "name": "Anrede",
        "historical": False,
        "werte": [
            {"key": "m", "de": "Herr", "en": "Mr", "abdatum": "1001.0"},
            {"key": "w", "de": "Frau", "en": "Ms", "abdatum": "1001.0"},
            {"key": "d", "de": "Herr oder Frau", "en": "Mr or Ms", "abdatum": "1001.0"}
        ]
    }
    
    # Hier wird der Bereich "anrede" als section_key übergeben
    root.columnconfigure(0, weight=1)
    pd_dropdown = PdvmDropdownPicker(root, dropdown_config, "anrede", current_language="de", stichtag=2025059.0)
    pd_dropdown.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    
    def show_sel():
        key = pd_dropdown.get_selected_key()
        print("Ausgewählter Schlüssel:", key)
    
    btn = ttk.Button(root, text="Zeige Auswahl", command=show_sel)
    btn.grid(row=1, column=0, padx=10, pady=10)
    
    root.mainloop()
