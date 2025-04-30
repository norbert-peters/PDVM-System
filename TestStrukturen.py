def pdvm_struktur():
    return {
       "PD_commands": {
            "Basis_Hilfe": "self.show_text('Mein Hilfetext')",
            "Basis_Abmelden": "self.logout()",
            "Basis": "show_basis",
            "Horizontal": "show_horizontal",
            "Vertikal": "show_vertical",
            "Option 1": "show_option_1",
            "Option 2": "show_option_2",
            "Option 3": "show_option_3",
            "Option 1.1": "show_option_1_1",
            "Option 1.2": "show_option_1_2",
            "Option 1.3": "show_option_1_3",
            "Option 2.1": "show_option_2_1",
            "Option 2.3": "show_option_2_3",
            "SV Option 1": "show_sv_option_1",
            "SV Option 2": "show_sv_option_2",
            "SV Option 3": "show_sv_option_3",
            "ST Option 1": "show_st_option_1",
            "ST Option 3": "show_st_option_3"
        },
        "PD_grund" : {
            "Basis": ["Hilfe", "separator", "Abmelden"],
            "Einstellungen": {
                "Schrift": ["Schriftart", "Schriftgröße", "Standardfarbe"],
                "Layout": ["Standardgröße", "Hintergrund"],
            },
        },
        "PD_zusatz" : {
            "PD_z_Grund" : {
                "Einstellungen.Layout" : ["hinzufügen", "speichern"],
            },
            "PD_z_Menu" : {
                "Personaldaten.Person.Steuer": {
                    "Lohnsteuer": {
                        "Anmeldung": ["Formular", "Versand"],
                        "Daten": ["Steuernummer", "Steuerklasse", "Finanzamt"],
                    },
                    "Zusatzangaben": {
                        "Meine Bemerkung": ["Bemerkung_1", "Bemerkung_2", "Bemerkung_3", "Bemerkung_4", "Bemerkung_5"],
                        "Hinweise": ["Hinweis_1", "Hinweis_2", "Hinweis_3", "Hinweis_4", "Hinweis_5", "Hinweis_6", "Hinweis_7"],
                    }
                }
            }
        },
        "PD_menu" : {
            "Einstellungen": {
                "Menüs": ["Basis", "Horizontal", "Vertikal"],
                "Menü_1": ["Option_1", "Option_2", "Option_3"],
                "Menü_2": ["Option_1", "Option_2", "Option_3"],
            },
            "Personaldaten": {
                "Person": {
                    "Basis": ["Option_1", "Option_2", "Option_3"],
                    "Horizontal": ["Option_1.1", "Option_1.2", "Option_1.3"],
                    "Vertikal": ["Option_2.1", "Option_2.3"],
                    "Anschrift": ["Option_1", "Option_2", "Option_3"],
                    "Sozialversicherung": ["Option1", "Option_2", "Option_3"],
                    "Steuer": ["Lohnsteuer", "Umsatzsteuer", "Formulare"],
                },
            },
            "Personalberechnung": {
                "Lohnrechnung": ["Option_1", "Option_2", "Option_3"],
                "Reisekosten": ["Option_1", "Option_2", "Option_3"],
            }
        }
    }

def pdvm_commands():
    return {"PD_commands": {
        "Basis_Hilfe": "self.show_text('Mein Hilfetext')",
        "Basis_Abmelden": "self.logout()",
        "Basis": "show_basis",
        "Horizontal": "show_horizontal",
        "Vertikal": "show_vertical",
        "Option 1": "show_option_1",
        "Option 2": "show_option_2",
        "Option 2.3": "show_option_2_3",
        "SV Option 1": "show_sv_option_1",
        "SV Option 2": "show_sv_option_2",
        "SV Option 3": "show_sv_option_3",
        "ST Option 1": "show_st_option_1",
        "ST Option 3": "show_st_option_3"
    }}

def pdvm_grund():
    return {
        "PD_grund" : {
            "Basis": ["Hilfe", "separator", "Abmelden"],
            "Einstellungen": {
                "Schrift": ["Schriftart", "Schriftgröße", "Standardfarbe"],
            },
        }
    }

def pdvm_menu():
    return {
        "PD_menu" : {
            "Einstellungen": {
                "Menüs": ["Basis", "Horizontal", "Vertikal"],
                "Menü_1": ["Option_1", "Option_2", "Option_3"],
                "Menü_2": ["Option_1", "Option_2", "Option_3"],
            },
            "Personaldaten": {
                "Person": {
                    "Basis": ["Option_1", "Option_2", "Option_3"],
                    "Horizontal": ["Option_1.1", "Option_1.2", "Option_1.3"],
                    "Vertikal": ["Option_2.1", "Option_2.3"],
                    "Anschrift": ["Option_1", "Option_2", "Option_3"],
                    "Sozialversicherung": ["Option1", "Option_2", "Option_3"],
                    "Steuer": ["Lohnsteuer", "Umsatzsteuer", "Formulare"],
                },
            },
            "Personalberechnung": {
                "Lohnrechnung": ["Option_1", "Option_2", "Option_3"],
                "Reisekosten": ["Option_1", "Option_2", "Option_3"],
            }
        }
    }

def pdvm_zusatz():
    return {
        # Zusatzmenüs: anhand des Pfads wird hier eingefügt:
        "Einstellungen_Layout": ["hinzufügen", "speichern"],
        "Personaldaten_Person_Steuer": {
            "Lohnsteuer": {
                "Anmeldung": ["Formular", "Versand"],
                "Daten": ["Steuernummer", "Steuerklasse", "Finanzamt"],
            },
            "Zusatzangaben": {
                "Meine Bemerkung": ["Bemerkung_1", "Bemerkung_2", "Bemerkung_3", "Bemerkung_4", "Bemerkung_5"],
                "Hinweise": ["Hinweis_1", "Hinweis_2", "Hinweis_3", "Hinweis_4", "Hinweis_5", "Hinweis_6", "Hinweis_7"],
            }
        }
    }

"""
"PD_commands": {},
"PD_grund" : {},
"PD_zusatz" : {
    "PD_z_Grund" : {},
    "PD_z_Menu" : {}
},
"PD_menu" : {}
"""