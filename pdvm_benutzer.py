import hashlib
import os
import json

class PdvmBenutzer:
    def __init__(self, benutzer, password_hash, settings_json):
        print(f"in Benutzer angekommen - benutzer: {benutzer} - passwort hash: {password_hash} - settings_json: {settings_json}")
        """
        :param benutzer: Der Benutzername, in der Regel die Email-Adresse.
        :param password_hash: Der gespeicherte Passwort-Hash (z.B. "hash:salt").
        :param settings_json: JSON-Daten als String oder Dict mit zusätzlichen Einstellungen (z.B. GUIDs).
        """
        self.benutzer = benutzer
        self.password_hash = password_hash
        # Falls settings_json ein String ist, wird er in ein Dict umgewandelt.
        if isinstance(settings_json, str):
            self.settings = json.loads(settings_json)
        else:
            self.settings = settings_json
        print(f"am Ende von init - benutzer: {self.benutzer} - passwort hash: {self.password_hash} - settings_json: {self.settings}")

    @staticmethod
    def hash_password(password, salt=None):
        """
        Erzeugt einen sicheren Hash für das gegebene Passwort.
        Wird kein Salt angegeben, wird ein zufälliges generiert.
        Rückgabeformat: "hash:salt"
        """
        if salt is None:
            # Erzeugen eines zufälligen 16-Byte-Salts (hexadezimal)
            salt = os.urandom(16).hex()
        # Hashing mit SHA-256 (alternativ: PBKDF2, bcrypt o.ä. für mehr Sicherheit)
        hash_obj = hashlib.sha256()
        hash_obj.update((salt + password).encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        return f"{password_hash}:{salt}"

    @staticmethod
    def verify_password(stored_password_hash, provided_password):
        """
        Vergleicht das gegebene Passwort mit dem in der Datenbank gespeicherten Hash.
        Erwartetes Format: "hash:salt"
        """
        try:
            stored_hash, salt = stored_password_hash.split(":")
        except ValueError:
            # Falsches Format
            return False

        hash_obj = hashlib.sha256()
        hash_obj.update((salt + provided_password).encode('utf-8'))
        provided_hash = hash_obj.hexdigest()
        return stored_hash == provided_hash

    def to_json(self):
        """
        Gibt die Benutzerdaten (ohne Passwort) als JSON-String zurück.
        Hier könntest Du auch settings und andere relevante Informationen speichern.
        """
        data = {
            "benutzer": self.benutzer,
            "settings": self.settings
        }
        return json.dumps(data)

