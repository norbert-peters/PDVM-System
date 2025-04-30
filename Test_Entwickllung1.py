import json
import datenbank as db
import DatenHistAbfragenDic as DHA

row = db.pers_lesen(1)

# JSON-Text in ein Dictionary umwandeln
if row:
    personalstamm_json = row[0]
    personalstamm = json.loads(personalstamm_json)
else:
    personalstamm = {}

print(personalstamm)
print("\n")
print(personalstamm_json)
print("\n")

ausgabe= DHA.konvertiere_ab_zeiten(personalstamm)

print(ausgabe)



db.pers_anlegen(ausgabe)

zeitstempel=2025014.7
steuernummer1 = DHA.name_zu_ab_zeit(ausgabe["Steuer"],"Steuernummer", zeitstempel) 
print("Dieses ist das Ergebnis", steuernummer1)
