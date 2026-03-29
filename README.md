# PDVM-System (v0.9)

Dieses Projekt ist ein flexibles System zur Datenverwaltung, -Darstellung und kaufmännischen Berechnungen.

---

## Inhaltsverzeichnis

1. [Voraussetzungen installieren](#1-voraussetzungen-installieren)
2. [Repository herunterladen / Branch mergen](#2-repository-herunterladen--branch-mergen)
3. [Abhängigkeiten installieren](#3-abhängigkeiten-installieren)
4. [VS Code öffnen und Workspace neu laden](#4-vs-code-öffnen-und-workspace-neu-laden)
5. [Ersten Benutzer anlegen](#5-ersten-benutzer-anlegen)
6. [Anwendung starten](#6-anwendung-starten)

---

## 1. Voraussetzungen installieren

Stelle sicher, dass folgendes auf deinem Rechner installiert ist:

| Software | Mindestversion | Download |
|---|---|---|
| **Python** | 3.7 | https://www.python.org/downloads/ |
| **Git** | beliebig | https://git-scm.com/downloads |
| **VS Code** | beliebig | https://code.visualstudio.com/ |

> **Hinweis:** Beim Python-Installer unbedingt die Option **„Add Python to PATH"** aktivieren.

---

## 2. Repository herunterladen / Branch mergen

### Erstmalige Installation (Clone)

```bash
git clone https://github.com/norbert-peters/PDVM-System.git
cd PDVM-System
```

### Vorhandenes Repository aktualisieren (Pull & Merge)

Wenn du das Repo bereits lokal hast, führe folgende Schritte aus:

```bash
# Neueste Änderungen vom Server holen
git fetch origin

# In den Hauptbranch wechseln
git checkout main

# Den Fix-Branch einmergen
git merge origin/copilot/fix-github-authentication-error

# Oder: Einfach den aktuellen Branch pullen
git pull
```

> **Was dieser Schritt bewirkt:** Er übernimmt die Einstellung `"github.gitAuthentication": false`
> aus `.vscode/settings.json` in dein lokales Repository. Dadurch wird der
> VS-Code-Fehler *„You have not yet finished authorizing this extension to use GitHub"*
> behoben.

---

## 3. Abhängigkeiten installieren

Öffne ein Terminal (Windows: PowerShell oder CMD) im Projektordner und führe aus:

```bash
pip install PyQt5
```

Alle weiteren Bibliotheken (`sqlite3`, `json`, `hashlib`, …) sind in Python bereits enthalten.

---

## 4. VS Code öffnen und Workspace neu laden

1. VS Code öffnen.
2. **File → Open Folder** → Projektordner `PDVM-System` auswählen.
3. VS Code neu laden: **Strg+Shift+P** → `Developer: Reload Window` → Enter.

Die Einstellung `"github.gitAuthentication": false` wird jetzt automatisch aktiv.
Ab sofort nutzt Git den **Betriebssystem-Schlüsselbund** für GitHub-Zugangsdaten –
kein Browser-Login mehr erforderlich.

---

## 5. Ersten Benutzer anlegen

Vor dem ersten Start muss mindestens ein Benutzer in der Datenbank vorhanden sein.
Führe dazu das mitgelieferte Setup-Skript aus:

```bash
python setup_benutzer.py
```

Das Skript fragt dich interaktiv nach:
- **Benutzername** (z. B. deine E-Mail-Adresse)
- **Passwort**

Der Benutzer wird mit einem SHA-256-Hash (+ Salt) in `PdvmManager.db` gespeichert.

> **Hinweis zur Sicherheit:** SHA-256 ist für die Passwort-Speicherung grundsätzlich
> verwendbar, aber für Produktivsysteme empfiehlt sich ein langsamerer Algorithmus
> wie **bcrypt** oder **Argon2** (geringeres Brute-Force-Risiko). Die aktuelle
> Implementierung entspricht dem bisherigen Stand des Projekts.

---

## 6. Anwendung starten

```bash
python PDVM-Systemstart.py
```

Es öffnet sich das Login-Fenster. Gib den Benutzernamen und das Passwort ein,
die du in Schritt 5 festgelegt hast.

---

## Häufige Fehler

| Fehlermeldung | Ursache | Lösung |
|---|---|---|
| *You have not yet finished authorizing this extension* | VS Code GitHub-Auth-Extension blockiert Git | Schritt 2 und 4 ausführen |
| *ModuleNotFoundError: No module named 'PyQt5'* | PyQt5 nicht installiert | `pip install PyQt5` (Schritt 3) |
| *Benutzer nicht gefunden* | Kein Benutzer in der DB | `python setup_benutzer.py` (Schritt 5) |
| *PdvmManager.db* fehlt | Datenbank noch nicht erzeugt | Schritt 5 ausführen; das Skript legt die DB an |

---

## Features

- Flexibles Datenmodell auf Basis von SQLite + JSON
- PyQt5-GUI mit Login, Menüsystem und Inhaltsbereich
- Benutzerverwaltung mit SHA-256+Salt-Passwort-Hashing
- Erweiterbare Menü- und View-Struktur
