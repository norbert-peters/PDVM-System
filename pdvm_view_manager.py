import logging
import json
import importlib
from typing import Optional, Dict, List, Tuple
from datetime import date

from pdvm_datenbank import PdvmDatenbank as PdvmDB
import pd_datetime as dt  # Enthält PdvmDateTimeNow()

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def has_content(eintrag: dict, suchfelder: List[str], debug: bool = False) -> bool:
    """
    Prüft, ob ein Eintrag in mindestens einem der Suchfelder nicht leer ist.
    """
    for feld in suchfelder:
        wert = eintrag.get(feld)
        if debug:
            logger.debug(f"Prüfe Feld '{feld}': Wert = {wert!r}")
        if wert is None:
            continue
        if isinstance(wert, str) and wert.strip() == "":
            continue
        if isinstance(wert, (list, dict)) and not wert:
            continue
        return True
    return False


def get_pdvm_instance(class_name: str, guid: str):
    module_name = class_name.lower()
    try:
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        return cls(guid)
    except (ImportError, AttributeError) as e:
        logger.error(f"Fehler beim dynamischen Import von {class_name}: {e}")
        return None


class PdvmViewManager:
    def __init__(self, call_daten: dict):
        logger.info("PdvmViewManager initialisiert.")
        self.call_daten = call_daten
        self.user_guid = call_daten.get("user_guid")
        self.view_guid = call_daten.get("view_guid")
        self.mode = call_daten.get("mode", None)

        # View-Metadaten
        self.view_db = PdvmDB("PdvmManager.db", "viewdaten", hist=False)
        self.view_data = self.view_db.lesen(self.view_guid) or {}

        # Root-Tabelle bestimmen
        vt = self.view_data.get("view_table")
        if not vt:
            tables = self.view_data.get("view_tables", [])
            vt = tables[0] if tables else None
        self.view_table = vt

        # Historie & Metadata
        self.historisch = self.view_data.get("historisch", False)
        self.display_width = self.view_data.get("display_width", "100%" )
        self.metadata = self.view_data.get("metadata", {})

        # Zeitverwaltung
        self.dt_instance = dt.Pdvm_DateTime("DEU")
        self.current_time = self.dt_instance.PdvmDateTimeNow()
        self.stichtag = call_daten.get("stichtag", float(f"{int(self.current_time)}.0"))

        # Steuerungsdaten
        self.steuerung_db = PdvmDB("PdvmManager.db", "systemsteuerung", hist=False)
        self.steuerung_data_user = self.steuerung_db.lesen(self.user_guid) or {}
        self.steuerung_data_sys = self.steuerung_db.lesen(
            "00000000-0000-0000-0000-000000000000"
        ) or {}

        # Temp-View Cache
        self.user_view_db = PdvmDB("PdvmManager.db", "benutzerviews", hist=False)
        self.user_view_data: Dict[str, List[dict]] = {}

        # Lookup-Daten (z.B. Dropdownwerte)
        self.lookup_data: Dict[str, List[dict]] = self.view_data.get("lookups", {})

    def get_view_definition(self, table: str) -> dict:
        """Liefert die Spalten-Definitionen für das Widget."""
        fields = self.metadata.get(table, {}).get("felder", [])
        return {
            "columns": [
                {
                    "name":        f.get("name", f.get("feld")),
                    "type":        f.get("type", "string"),
                    "searchable":  f.get("ui", {}).get("searchable", False),
                    "sortable":    f.get("ui", {}).get("sortable", False),
                    "filterType":  f.get("ui", {}).get("filterType", "contains"),
                    "selectable":  f.get("ui", {}).get("selectable", True),
                    "lookup":      f.get("lookup"),
                }
                for f in fields
            ]
        }

    def get_temp_view(self, table: str) -> List[dict]:
        """Stellt sicher, dass die TempView aktuell ist und gibt die List[dict] zurück."""
        self._aktualisiere_temp_view()
        return self.user_view_data.get(table, [])

    def get_lookup_options(self, lookup_def: dict) -> List:
        """Dropdown-Werte aus der Lookup-Definition."""
        if not lookup_def:
            return []
        tbl = lookup_def.get("table")
        val_field = lookup_def.get("value")
        return [row.get(val_field) for row in self.lookup_data.get(tbl, [])]

    def get_lookup_display_value(self, lookup_def: dict, key) -> str:
        """
        Holt das Anzeige-Label für ein Lookup-Feld:
        - lookup_def["table"] = Name der Lookup-Tabelle
        - lookup_def["key"]   = GUID des Lookup-Datensatzes
        - lookup_def["value"] = Name des Feldes in der JSON-Struktur
        - key                  = der tatsächliche Lookup-Key (z.B. 'w')
        """
        logger.debug(f"get_lookup_display_value: {lookup_def}, key={key}")

        if not lookup_def or key is None:
            return ""

        tbl       = lookup_def.get("table")
        tbl_id    = lookup_def.get("key")
        value_key = lookup_def.get("value")
        if not tbl or not tbl_id or not value_key:
            return str(key)

        # Lade den Lookup-Datensatz
        db  = PdvmDB("PdvmManager.db", tbl, hist=False)
        rec = db.lesen(tbl_id)
        if not rec:
            logger.debug(f"Lookup-Datensatz {tbl_id} nicht gefunden in Tabelle {tbl}")
            return str(key)

        # 1) Falls es im rec ein Feld "daten" gibt, darin JSON, sonst rec selbst nutzen
        raw_outer = rec.get("daten", rec)
        try:
            outer = json.loads(raw_outer) if isinstance(raw_outer, str) else (raw_outer or {})
        except json.JSONDecodeError:
            logger.debug("JSON-Fehler beim Parsen von rec['daten']")
            outer = {}

        # 2) Suche das Teil-Objekt (z.B. outer['anrede'])
        inner_raw = outer.get(value_key)
        if inner_raw is None:
            logger.debug(f"Kein inneres Feld '{value_key}' in Lookup-Daten")
            return str(key)

        # 3) Falls inner_raw wieder JSON-String ist, decodiere ihn
        try:
            inner = json.loads(inner_raw) if isinstance(inner_raw, str) else (inner_raw or {})
        except json.JSONDecodeError:
            logger.debug(f"JSON-Fehler beim Parsen von inner_raw für '{value_key}'")
            return str(key)

        # 4) Liste der Werte
        werte = inner.get("werte", [])
        if not isinstance(werte, list):
            logger.debug(f"Lookup-Feld 'werte' ist kein Array, sondern {type(werte)}")
            return str(key)

        # 5) Finde alle Einträge mit passendem key
        candidates = [w for w in werte if w.get("key") == key]
        if not candidates:
            logger.debug(f"Kein Lookup-Wert matching key={key}")
            return str(key)

        # 6) Historische Logik
        if self.historisch:
            valid = []
            for w in candidates:
                try:
                    if float(w.get("abdatum", 0)) <= float(self.stichtag):
                        valid.append(w)
                except (TypeError, ValueError):
                    continue
            if not valid:
                logger.debug(f"Keine historischen Werte <= Stichtag gefunden für key={key}")
                return str(key)
            best = max(valid, key=lambda w: float(w.get("abdatum", 0)))
        else:
            best = candidates[0]

        logger.debug(f"Lookup-Wert ausgewählt: {best}")
        # 7) Gib das deutsche Label zurück
        return best.get("de", str(key))

    def pdvm_to_date(self, pdvm_value: float) -> date:
        """Konvertiert Pdvm-Format YYYYDDD.x zu einem datetime.date."""
        self.dt_instance.PdvmDateTime = pdvm_value
        return self.dt_instance.Date

    def _aktualisiere_temp_view(self):
        table = self.view_table
        ts_ctrl = self.steuerung_data_sys.get(table, {}).get("last_change")
        ts_user = self.steuerung_data_user.get(self.view_guid, {}).get("last_created_at")

        if ts_user is None or ts_ctrl is None or ts_ctrl > ts_user or self._stichtag_geaendert():
            # neu bauen
            data = self._erzeuge_view_daten(table, debug_skip=False)
            self.user_view_data[table] = data
            # persistieren
            self.user_view_db.speichern(self.user_guid, {table: data})
            self.steuerung_data_user.setdefault(self.view_guid, {})["last_created_at"] = self.current_time
            self.steuerung_data_user[self.view_guid]["stichtag"] = self.stichtag
            self.steuerung_db.speichern(self.user_guid, self.steuerung_data_user)
        else:
            # aus Cache laden
            cached = self.user_view_db.lesen(self.user_guid) or {}
            self.user_view_data[table] = cached.get(table, [])

    def _stichtag_geaendert(self) -> bool:
        ts = self.steuerung_data_user.get(self.view_guid, {}).get("stichtag")
        return ts is None or ts != self.stichtag

    def _erzeuge_view_daten(self, table: str, debug_skip: bool = False) -> List[dict]:
        """
        Baut die View-Daten auf, filtert leere Suchfelder raus
        und zerlegt Datum intern in *_tag, *_monat, *_jahr.
        """
        fields = self.metadata.get(table, {}).get("felder", [])
        all_ds = PdvmDB("PdvmManager.db", table, hist=self.historisch).lesen_alle() or []
        view_data = []
        skipped = 0

        # Suchspaltennamen ermitteln
        searchable = [
            f.get("name", f.get("feld"))
            for f in fields
            if f.get("ui", {}).get("searchable", False)
        ]

        for ds in all_ds:
            uid = ds.get("uid")
            if uid == "00000000-0000-0000-0000-000000000000":
                continue

            raw = ds.get("daten", {})
            data = json.loads(raw) if isinstance(raw, str) else raw or {}
            entry = {"GUID": uid}

            for f in fields:
                grp = f.get("gruppe", "").upper()
                fld = f.get("feld",    "").upper()
                name = f.get("name", fld)

                # Wert aus historisch oder aktuell
                if self.historisch:
                    val = self._get_value(grp, fld, data, self.stichtag)
                else:
                    val = self._get_value_only(grp, fld, data)

                entry[name] = val

                # Datum intern splitten, falls vorhanden
                if f.get("type") == "date" and val is not None:
                    self.dt_instance.PdvmDateTime = float(val)
                    d = self.dt_instance.Day
                    m = self.dt_instance.Month
                    y = self.dt_instance.Year
                    entry[f"{name}_tag"]   = f"{d:02d}"
                    entry[f"{name}_monat"] = f"{m:02d}"
                    entry[f"{name}_jahr"]  = str(y)

            # Filter: nur Einträge mit Inhalt in suchbaren Feldern
            if searchable and not has_content(entry, searchable, debug=debug_skip):
                skipped += 1
                if debug_skip:
                    logger.debug(f"Überspringe leeren Eintrag: {entry!r}")
                continue

            view_data.append(entry)

        logger.info(f"Erzeugt {len(view_data)} Einträge für '{table}'.")
        if skipped:
            logger.info(f"{skipped} Einträge übersprungen (leere Suchfelder).")

        return view_data

    def _get_value(self, gruppe, feld, daten, ab_zeit):
        import json
        grp = daten.get(gruppe)
        grp = json.loads(grp) if isinstance(grp, str) else grp or {}
        valr = grp.get(feld)
        vald = json.loads(valr) if isinstance(valr, str) else valr or {}
        times = [float(t) for t in vald.keys() if float(t) <= float(ab_zeit)]
        if not times:
            return None
        best = format(max(times), ".5f")
        return vald.get(best)

    def _get_value_only(self, gruppe, feld, daten):
        import json
        grp = daten.get(gruppe)
        grp = json.loads(grp) if isinstance(grp, str) else grp or {}
        val = grp.get(feld)
        if isinstance(val, dict):
            times = sorted(float(t) for t in val.keys())
            key = format(times[-1], ".5f")
            return val.get(key)
        return val

    def query_view(
        self,
        table: str,
        filters: Optional[Dict[str, dict]] = None,
        sort: Optional[List[Tuple[str, str]]] = None,
        page: int = 0,
        page_size: int = 50
    ) -> Tuple[List[dict], int]:
        # Daten holen
        data = self.get_temp_view(table)

        # Filter anwenden
        if filters:
            data = self._apply_filters(data, filters)

        # Sortierung
        if sort:
            for col, d in reversed(sort):
                non_null = [r for r in data if r.get(col) is not None]
                nulls     = [r for r in data if r.get(col) is None]
                non_null.sort(key=lambda r: r.get(col), reverse=(d == "desc"))
                data = non_null + nulls

        # Paging
        total = len(data)
        start = page * page_size
        end   = start + page_size
        return data[start:end], total

    def _apply_filters(self, data: List[dict], filters: Dict[str, dict]) -> List[dict]:
        """
        Wendet alle Filter an: 'contains', 'dropdown', 'dateRange' und auch
        Tag/Monat/Jahr-Filter als separate 'contains' auf *_tag, *_monat, *_jahr.
        """
        out = []
        for row in data:
            ok = True
            for col, f in filters.items():
                v = row.get(col)
                t = f.get("type")

                if t == "contains":
                    if f.get("value", "").lower() not in str(v or "").lower():
                        ok = False

                elif t == "dropdown":
                    if v != f.get("value"):
                        ok = False

                elif t == "dateRange":
                    # Bereichsfilter: erwartet 'from'/'to' als datetime.date
                    row_date = self.pdvm_to_date(float(v)) if v is not None else None
                    fr = f.get("from")
                    to = f.get("to")
                    if row_date is None or (fr and row_date < fr) or (to and row_date > to):
                        ok = False

                # Andere Filtertypen (z.B. Tag/Monat/Jahr) sind mit 'contains' über *_tag/_monat/_jahr abgedeckt

                if not ok:
                    break

            if ok:
                out.append(row)

        return out
