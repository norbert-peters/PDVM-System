# setup_benutzer.py
# Legt den ersten Benutzer in PdvmManager.db an.
# Aufruf: python setup_benutzer.py

import getpass
import json

try:
    from pdvm_user_db import PdvmUserDatenbank
    from pdvm_benutzer import PdvmBenutzer
except ImportError as e:
    print(f"Fehler beim Laden der Module: {e}")
    print("Bitte stelle sicher, dass:")
    print("  1. Du dich im Projektordner 'PDVM-System' befindest.")
    print("  2. PyQt5 installiert ist: pip install PyQt5")
    raise SystemExit(1)

def main():
    print("=" * 50)
    print("  PDVM-System – Ersten Benutzer anlegen")
    print("=" * 50)

    benutzername = input("Benutzername (z. B. E-Mail-Adresse): ").strip()
    if not benutzername:
        print("Fehler: Benutzername darf nicht leer sein.")
        return

    passwort = getpass.getpass("Passwort: ")
    if not passwort:
        print("Fehler: Passwort darf nicht leer sein.")
        return

    passwort_wdh = getpass.getpass("Passwort wiederholen: ")
    if passwort != passwort_wdh:
        print("Fehler: Passwörter stimmen nicht überein.")
        return

    vorname = input("Vorname: ").strip()
    nachname = input("Nachname: ").strip()

    passwort_hash = PdvmBenutzer.hash_password(passwort)

    benutzer_daten = {
        "Benutzer": {
            "Vorname": vorname,
            "Name": nachname
        },
        "Anwendungen": {
            "MeineApps": None
        }
    }

    db = PdvmUserDatenbank()

    # Prüfen ob Benutzer bereits existiert
    if db.lesen(benutzername):
        print(f"\nHinweis: Benutzer '{benutzername}' existiert bereits in der Datenbank.")
        return

    erfolg = db.anlegen(
        benutzer=benutzername,
        passwort=passwort_hash,
        daten=benutzer_daten
    )

    if erfolg:
        print(f"\nBenutzer '{benutzername}' wurde erfolgreich angelegt.")
        print("Du kannst die Anwendung jetzt starten:")
        print("  python PDVM-Systemstart.py")
    else:
        print("\nFehler: Benutzer konnte nicht angelegt werden.")

if __name__ == "__main__":
    main()
