import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from pd_datetime import Pdvm_DateTime
import pdvm_gui_utils as gui  # Unser neues Hilfsmodul

class PdvmDateTimePicker(ttk.Frame):
    def __init__(self, parent, pdvm_datetime, display="all", display_time_short=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pdvm_datetime = pdvm_datetime
        self.display = display
        self.display_time_short = display_time_short

        if self.display in ("all", "only_date"):
            self.date_entry = gui.create_date_entry(self, date=self.pdvm_datetime.Date)
            self.date_entry.pack(side=tk.LEFT, anchor="w", padx=2, pady=2)
            self.date_entry.bind("<<DateEntrySelected>>", lambda e: self.update_pdvm_datetime())

        if self.display in ("all", "only_time"):
            self.time_frame = ttk.Frame(self)
            self.time_frame.pack(side=tk.LEFT, anchor="w", padx=2, pady=2)

            self.hour_var = tk.StringVar(value=self.pdvm_datetime.Hour)
            self.minute_var = tk.StringVar(value=self.pdvm_datetime.Minute)
            if not self.display_time_short:
                self.second_var = tk.StringVar(value=self.pdvm_datetime.Second)

            self.hour_spin = gui.create_spinbox(self.time_frame, from_=0, to=23, textvariable=self.hour_var)
            self.hour_spin.pack(side=tk.LEFT, padx=(5, 2))
            self.minute_spin = gui.create_spinbox(self.time_frame, from_=0, to=59, textvariable=self.minute_var)
            self.minute_spin.pack(side=tk.LEFT, padx=2)

            if not self.display_time_short:
                self.second_spin = gui.create_spinbox(self.time_frame, from_=0, to=59, textvariable=self.second_var)
                self.second_spin.pack(side=tk.LEFT, padx=2)

            self.hour_var.trace_add("write", lambda *args: self.update_pdvm_datetime())
            self.minute_var.trace_add("write", lambda *args: self.update_pdvm_datetime())
            if not self.display_time_short:
                self.second_var.trace_add("write", lambda *args: self.update_pdvm_datetime())

    def update_pdvm_datetime(self):
        if self.display in ("all", "only_date"):
            try:
                day, month, year = map(int, self.date_entry.get().split("."))
            except Exception:
                from datetime import datetime
                now = datetime.today()
                year, month, day = now.year, now.month, now.day
            self.pdvm_datetime.setPdvmNewDate((year, month, day))
            if self.display == "only_date":
                self.pdvm_datetime.setPdvmNewTime((0, 0, 0, 0))

        if self.display in ("all", "only_time"):
            try:
                hour = int(self.hour_var.get() or 0)
                minute = int(self.minute_var.get() or 0)
                second = 0 if self.display_time_short else int(self.second_var.get() or 0)
            except ValueError:
                hour, minute, second = 0, 0, 0
            self.pdvm_datetime.setPdvmNewTime((hour, minute, second, 0))

    def get_pdvm_datetime(self):
        self.update_pdvm_datetime()
        return self.pdvm_datetime
