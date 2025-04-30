import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
from pdvm_datenbank import PdvmDatenbank
from pd_datetime import Pdvm_DateTime
from pdvm_date_time_picker import PdvmDateTimePicker
from pdvm_dropdown_picker import PdvmDropdownPicker    # Für den Bearbeitungsdialog
import json
import importlib
from pdvm_gui_utils import create_standard_label, create_standard_entry, apply_standard_padding

def get_pdvm_instance(class_name, guid):
    module_name = class_name.lower()
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return cls(guid)
    except (ImportError, AttributeError) as e:
        print(f"Fehler beim dynamischen Import von {class_name}: {e}")
        return None

class PdvmInputFrame(ttk.Frame):
    def __init__(self, parent, config, **kwargs):
        """
        Erzeugt ein dynamisches Input-Frame mit integriertem Info-Bereich für den Stichtag.
        Zusätzlich wird eine globale Dropdown-Instanz erstellt, falls in den call-daten
        ein Dropdown-Schlüssel vorhanden ist.
        Für Felder vom Typ "dropdown" wird im normalen Modus ausschließlich der
        übersetzte Text (read‑only) angezeigt.
        """
        super().__init__(parent, **kwargs)
        self.config_dict = config
        self.stichtag = self.config_dict.get("stichtag", {})
        self.language = self.config_dict.get("language", "de")  

        self.display_stichtag = self.config_dict.get("display_stichtag", True)
        self.display_st_typ = self.config_dict.get("display_st_typ", "all")
        self.display_st_time_short = self.config_dict.get("display_st_time_short", False)

        # Erstelle die globale Dropdown-Instanz, sofern in den call-daten vorhanden.
        self.dropdown_inst = None
        if "dropdown" in self.config_dict:
            dd_cfg = self.config_dict["dropdown"]
            dd_guid = dd_cfg.get("GUID")
            if dd_guid:
                from pdvmdropdown import PdvmDropdown   # Deine globale Dropdown-Klasse
                self.dropdown_inst = PdvmDropdown(dd_guid)

        self.instances = {}
        for key, cfg in self.config_dict.items():
            if key.startswith("pdvm") and key not in ["framedaten", "protokolldaten", "anwendungsdaten", "checksdaten"]:
                class_name = "Pdvm" + key[4:].capitalize()
                guid = cfg.get("GUID")
                if guid is None:
                    print(f"Keine GUID für {class_name} angegeben.")
                    continue
                instance = get_pdvm_instance(class_name, guid)
                if instance is not None:
                    self.instances[key] = instance

        self.framedaten = PdvmDatenbank("PdvmManager.db", "framedaten", False).lesen(self.config_dict["framedaten"]["GUID"])

        self.input_controls = {}

        header_text = self.config_dict.get("header_text", "PDVM - Eingabemaske")
        header = ttk.Label(self, text=header_text, font=("Helvetica", 16, "bold"), justify="left",
                           padding=(10, 1, 10, 1))
        header.pack(pady=10, anchor="w")

        # Info-Bereich für den Stichtag
        self.info_frame = tk.Frame(self, borderwidth=3, relief="groove", padx=5, pady=5)
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
              
        dt_inst = Pdvm_DateTime('DEU')
        try:
            st_date = float(self.stichtag)
        except (ValueError, TypeError):
            st_date = 0.0
        if not self.display_stichtag or st_date < 1001.0:
            dt_inst.PdvmDateTime = dt_inst.PdvmDateTimeNow()
        else:
            dt_inst.PdvmDateTime = st_date
        self.stichtag_dt = dt_inst

        if self.display_stichtag:
            st_label = ttk.Label(self.info_frame, text="Stichtag:", font=("Helvetica", 12))
            st_label.pack(side=tk.LEFT, padx=(0,5))
            self.stichtag_picker = PdvmDateTimePicker(self.info_frame, dt_inst,
                                                       display=self.display_st_typ,
                                                       display_time_short=self.display_st_time_short)
            self.stichtag_picker.pack(side=tk.LEFT, padx=5)
        else:
            self.stichtag_dt.PdvmDateTime = self.stichtag_dt.PdvmDateTimeNow()

        self.stichtag_display_var = tk.StringVar(value=str(self.stichtag_dt.FormTimeStamp))
        st_display_entry = create_standard_entry(self.info_frame, textvariable=self.stichtag_display_var, width=20)
        st_display_entry.config(state="readonly", font=("Helvetica", 12))
        st_display_entry.pack(side=tk.LEFT, padx=5)

        refresh_btn = ttk.Button(self.info_frame, text="Refresh", command=self.refresh_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_input_controls()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        self.btn_speichern = ttk.Button(btn_frame, text="Speichern", command=self.speichern)
        self.btn_speichern.pack(side=tk.LEFT, padx=10)
        self.btn_abbrechen = ttk.Button(btn_frame, text="Abbrechen", command=self.abbrechen)
        self.btn_abbrechen.pack(side=tk.LEFT, padx=10)

    def refresh_data(self):
        new_dt = self.stichtag_picker.get_pdvm_datetime()
        self.stichtag_dt = new_dt
        self.stichtag_display_var.set(str(self.stichtag_dt.FormTimeStamp))
        self.stichtag = self.stichtag_dt.PdvmDateTime
        for key, conf in self.framedaten.items():
            if key in self.input_controls and "row" in self.input_controls[key]:
                self.display_input_control(conf, self.input_controls[key]["row"], key)

    def create_input_controls(self):
        for key, conf in self.framedaten.items():
            row = ttk.Frame(self.controls_frame)
            row.pack(fill=tk.X, pady=5, padx=5)
            self.input_controls[key] = {"row": row}

            label_text = conf.get("label", key)
            lbl = create_standard_label(row, label_text)
            lbl.grid(row=0, column=0, sticky="w", **apply_standard_padding(lbl))

            curr_val, curr_abdatum = self.get_field_value_with_abdatum(key)
            field_type = conf.get("type", "text")
            match field_type:
                case "text":    
                    self.input_controls[key]["type"] = "text"   
                case "datetime":
                    pd_dt = Pdvm_DateTime('DEU')
                    try:
                        pd_dt.PdvmDateTime = float(curr_val)
                    except:
                        pd_dt.PdvmDateTime = 1001.0
                    self.input_controls[key]["datetime_inst"] = pd_dt
                    self.input_controls[key]["type"] = "datetime"   
                case "dropdown":
                    section_key = conf.get("dropdown")
                    if not section_key:
                        section_key = key
                    self.input_controls[key]["section_key"] = section_key
                    self.input_controls[key]["type"] = "dropdown"   
                case _:
                    self.input_controls[key]["type"] = "text"
            
            if conf.get("historical", False):
                pd_ab_inst = Pdvm_DateTime('DEU')
                self.input_controls[key]["abdatum_inst"] = pd_ab_inst

            self.display_input_control(conf, row, key)

            btn = ttk.Button(row, text="Bearbeiten", command=lambda k=key: self.edit_fields(k))
            btn.grid(row=0, column=4, padx=5)
            if conf.get("historical", False) and conf.get("abdatum", False):
                del_btn = ttk.Button(row, text="Löschen", command=lambda k=key: self.delete_field(k))
                del_btn.grid(row=1, column=4, padx=5, sticky="w")

    def display_input_control(self, conf, row, key):
        curr_val, curr_abdatum = self.get_field_value_with_abdatum(key)

        field_type = self.input_controls[key]["type"]
        if field_type == "text":
            self.display_text(curr_val, row, key)

        elif field_type == "datetime":
            pd_dt = self.input_controls[key]["datetime_inst"]
            self.display_text(pd_dt.Date, row, key)
        elif field_type == "dropdown":
            section_key = self.input_controls[key]["section_key"]
            self.display_text(self.dropdown_inst.get_translation(section_key, curr_val, self.language), 
                              row, key)
        else:
            self.display_text(curr_val, row, key)

        if conf.get("historical", False):
            pd_ab_inst = self.input_controls[key].get("abdatum_inst")
            pd_ab_inst.PdvmDateTime = float(curr_abdatum)

            if conf.get("abdatum", False):
                print(f"-- Abdatum: {curr_abdatum} --")
                if curr_abdatum == "1001.00000":
                    abdatum_disp = ""
                else:
                    abdatum_disp = pd_ab_inst.FormTimeStamp
                abdatum_var = tk.StringVar(value=str(abdatum_disp))
                abdatum_entry = create_standard_entry(row, textvariable=abdatum_var)
                abdatum_entry.config(state="readonly", font=("Helvetica", 10))
                abdatum_entry.grid(row=1, column=2, sticky="e", padx=5)
                self.input_controls[key]["abdatum_var"] = abdatum_var

    def display_text(self, curr_val, row, key):
        var = tk.StringVar(value=str(curr_val))
        spacer = ttk.Frame(row, width=20)
        spacer.grid(row=0, column=1)
        entry = create_standard_entry(row, textvariable=var, width=40)
        entry.config(state="readonly", font=("Helvetica", 12))
        entry.grid(row=0, column=2, sticky="e", padx=5)
        row.columnconfigure(2, weight=2)
        self.input_controls[key]["var"] = var

    def split_key(self, key):
        parts = key.split("_", 2)
        if len(parts) != 3:
            return None, None, None
        class_key, group, field = parts
        return class_key.lower(), group.upper(), field.upper()

    def get_field_value_with_abdatum(self, key):
        class_key, group, field = self.split_key(key)
        instance = self.instances.get(class_key.lower())
        if instance is None:
            return "", "1001.0"
        result = instance.get_value(group, field, self.stichtag)
        if result is None:
            return "", "1001.0"
        return result.get("wert", ""), result.get("ab_zeit", "1001.0")

    def speichern(self):
        # Hier muss das Speichern der Instanzen in die Datenbank erfolgen.
        for key, instance in self.instances.items():
            instance.save_values()  # Hier wird die Methode zum Speichern aufgerufen
            print(f"Instanz {key} gespeichert.\n{json.dumps(instance.data, indent=4)}")
        

        messagebox.showinfo("Erfolg", "Daten erfolgreich gespeichert.")

    def save_value(self, key, value):
        class_key, group, field = self.split_key(key)
        instance = self.instances.get(class_key.lower())
        if instance is None:
            return
        
        pd_ab_inst = self.input_controls[key].get("abdatum_inst")
        if pd_ab_inst is not None:
            ab_value = pd_ab_inst.PdvmDateTime
            if ab_value < 1001.0:
                ab_date = self.stichtag
            else:
                ab_date = ab_value
        else:
            ab_date = self.stichtag
        
        instance.set_value(group, field, value, ab_date)

    def delete_field(self, key):
        class_key, group, field = self.split_key(key)
        instance = self.instances.get(class_key.lower())
        if instance is None:
            messagebox.showwarning("Fehler", "Instanz nicht gefunden!")
            return

        pd_ab_inst = self.input_controls[key].get("abdatum_inst")
        if pd_ab_inst is not None:
            ab_date = pd_ab_inst.PdvmDateTime
            if ab_date < 1001.0:
                ab_date = self.stichtag
        else:
            ab_date = self.stichtag

        result = instance.delete_value(group, field, ab_zeit=ab_date)
        if result:
            messagebox.showinfo("Erfolg", "Wert konnte gelöscht werden.")
        else:
            messagebox.showinfo("Hinweis", "Wert wurde nicht gefunden oder darf nicht gelöscht werden.")
        conf = self.framedaten[key]
        self.display_input_control(conf, self.input_controls[key]["row"], key)

    def abbrechen(self):
        self.destroy()

    def edit_fields(self, key):
        class_key, group, field = self.split_key(key)
        conf = self.framedaten[key]
        value, abdatum = self.get_field_value_with_abdatum(key)
        label_text = conf.get("label", f"{group} - {field}")

        dialog = tk.Toplevel(self.master)
        dialog.title(f"Bearbeite {label_text}")
        dialog.resizable(False, False)
        dialog.geometry("450x180")

        dialog.grid_rowconfigure(2, weight=1)
        dialog.grid_columnconfigure(0, weight=1)

        lbl = create_standard_label(dialog, label_text)
        lbl.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        new_val_var = tk.StringVar(value=value)

        field_type = self.input_controls[key]["type"]
        if field_type == "text":
            entry = create_standard_entry(dialog, textvariable=new_val_var)
            entry.grid(row=0, column=1, padx=5, pady=10, sticky="nw")
            self.input_controls[key]["value_picker"] = entry
        elif field_type == "datetime":
            pd_val_dt = self.input_controls[key].get("datetime_inst")
            if pd_val_dt is None:
                pd_val_dt = Pdvm_DateTime('DEU')
                self.input_controls[key]["datetime_inst"] = pd_val_dt
                pd_val_dt.PdvmDateTime = 1001.0
            display = conf.get("display_val", "all")
            display_time_short = conf.get("display_ti_val_short", False)
            val_picker = PdvmDateTimePicker(dialog, pd_val_dt,
                                            display=display,
                                            display_time_short=display_time_short)
            val_picker.grid(row=0, column=1, padx=5, pady=10, sticky="nw")
            self.input_controls[key]["value_picker"] = val_picker
        elif field_type == "dropdown":
            section_key = self.input_controls[key]["section_key"]
            if self.dropdown_inst is None:
                messagebox.showerror("Fehler", "Globale Dropdown-Instanz nicht konfiguriert!")
                return
            picker = PdvmDropdownPicker(dialog, self.dropdown_inst, section_key,
                                        self.language, stichtag=self.stichtag)
            picker.set_selected_key(value)
            picker.grid(row=0, column=1, padx=5, pady=10, sticky="nw")
            self.input_controls[key]["value_picker"] = picker
        else:
            entry = create_standard_entry(dialog, textvariable=new_val_var)
            entry.grid(row=0, column=1, padx=5, pady=10, sticky="nw")
            self.input_controls[key]["value_picker"] = entry

        has_abdatum = conf.get("historical", False) and conf.get("abdatum", False)
        if has_abdatum:
            lbl_ab = create_standard_label(dialog, "Ab-Datum/Zeit:")
            lbl_ab.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
            pd_ab_dt = self.input_controls[key].get("abdatum_inst")
            if pd_ab_dt is None:
                pd_ab_dt = Pdvm_DateTime('DEU')
                self.input_controls[key]["abdatum_inst"] = pd_ab_dt
            try:
                pd_ab_dt.PdvmDateTime = float(abdatum)
            except:
                pd_ab_dt.PdvmDateTime = 1001.0
            display_ab = conf.get("display_ab", "all")
            display_ab_short = conf.get("display_ti_ab_short", False)
            abdatum_picker = PdvmDateTimePicker(dialog, pd_ab_dt,
                                                display=display_ab,
                                                display_time_short=display_ab_short)
            abdatum_picker.grid(row=1, column=1, padx=5, pady=10, sticky="nw")
            print(f"-- abdatum ende -- {abdatum_picker.get_pdvm_datetime} --")
            print(f"-- abdatum picker ende -- {pd_ab_dt.PdvmDateTime} --")
            self.input_controls[key]["abdatum_picker"] = abdatum_picker

        spacer = ttk.Frame(dialog)
        spacer.grid(row=2, column=0, columnspan=2, sticky="nsew")

        def save_changes():
            if conf.get("type", "").lower() == "dropdown":
                new_value = self.input_controls[key]["value_picker"].get_selected_key()
            elif conf.get("type") == "datetime":
                pdvm_val = self.input_controls[key].get("value_picker")
                if pdvm_val is not None:
                    pd_ab_instance = pdvm_val.get_pdvm_datetime()
                    new_value = pd_ab_instance.PdvmDateTime
                else:
                    new_value = 1001.0
            else:
                new_value = new_val_var.get().strip()

            if new_value == "":
                messagebox.showwarning("Warnung", f"{label_text} darf nicht leer sein!")
                return

            # Für historische Felder (mit abdatum) den aktuellen Wert aus dem DateTimePicker abfragen:
            if conf.get("historical", False) and conf.get("abdatum", False):
                pd_ab_picker = self.input_controls[key].get("abdatum_picker")
                if pd_ab_picker is not None:
                    pd_ab_instance = pd_ab_picker.get_pdvm_datetime()
                    abdatum = pd_ab_instance.PdvmDateTime
                else:
                    abdatum = 1001.0
            else:
                abdatum = self.stichtag

            print(f"Abdatum: {abdatum}")
            self.save_value(key, new_value)
            self.display_input_control(conf, self.input_controls[key]["row"], key)
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="sew")

        save_btn = ttk.Button(btn_frame, text="Speichern", command=save_changes)
        save_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(btn_frame, text="Abbrechen", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("PdvmDataFrame Beispiel testen")
    call_daten = {
        "stichtag": "2025106.0",
        "display_stichtag": True,
        "display_st_typ": "all",
        "display_st_time_short": False,
        "language": "de",
        "header_text": "PDVM - Eingabemaske Test",
        "anwendungsdaten": {"GUID": None, "HIST": False},
        "checksdaten": {"GUID": None, "HIST": False},
        "dropdown": {"GUID": "ddaa6590-6d08-461b-a061-75faec26f4ba", "HIST": False},
        "pdvmfinanzen": {"GUID": "74352176-bd00-4254-8ff7-6dab9a466e84", "HIST": False},
        "framedaten": {"GUID": "4078079f-4028-45ed-879c-3c779ecf3d0d", "HIST": False},
#        "pdvmperson": {"GUID": "58c0acaa-fd40-4444-b516-c162f17a39b8", "HIST": True},   # Testdaten 1
        "pdvmperson": {"GUID": "6dbbdd2a-5a15-4c51-b138-750493b74127", "HIST": True},   # Testdaten weitere
        "protokolldaten": {"GUID": None, "HIST": True}
    }
    input_frame = PdvmInputFrame(root, call_daten)
    input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    root.mainloop()
