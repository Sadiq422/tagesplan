# Tagesplan

Persönliche iPhone-App (Progressive Web App) für den Alltag mit Früh- und Spätschicht: Tages-Checkliste mit eigenem Wochenplan (Aufgaben, Uhrzeiten, Schicht, Wasserziel pro Wochentag, in der App bearbeitbar), Wasser- und Essenszähler, Schlaf, Energie, Stimmung, Gewicht und Gewichtsverlauf, dazu eine Auswertung mit Durchschnitten, Verlauf, Zusammenhängen (Pearson r, zum Beispiel Schlaf und Energie) und Wochentag-Mustern.

## Installieren

1. `https://sadiq422.github.io/tagesplan/` in **Safari** auf dem iPhone öffnen.
2. Unten auf **Teilen** tippen, dann **Zum Home-Bildschirm**.
3. Die App über das neue Symbol öffnen.

## Daten

- Alle Einträge werden nur auf dem Gerät gespeichert (`localStorage`), nichts geht an einen Server.
- Die App funktioniert offline (Service Worker in `sw.js`).
- Über **Backup speichern** entsteht eine JSON-Datei mit Einträgen, Plan, Zielen und Listen, die sich in Dateien sichern und mit **Backup laden** wiederherstellen lässt.
- Jeder Tag speichert den Plan, der an dem Tag galt. Planänderungen wirken ab heute, vergangene Tage bleiben unverändert.

## Datenfluss

```
iPhone (App, localStorage)
  ├─ Backup speichern  → JSON mit Tagen, Plan, Zielen, Listen, Wochennotizen
  ├─ Tage als CSV      → Spalten wie Notion-Datenbank "Tage"
  └─ Wochen als CSV    → Spalten wie Notion-Datenbank "Wochen"
        │
        ├─ Notion: Datei an Claude schicken (Upsert per Datum) oder "Merge with CSV"
        └─ Computer: tools/tagesplan_export.py → daten/tage.csv, wochen.csv, aufgaben.csv
```

Die App hat keinen Server und keinen Notion-Schlüssel im Code. Das Repo ist öffentlich, `.gitignore` hält Backups und CSV-Dateien heraus.

### Auf dem Computer

```bash
python3 tools/tagesplan_export.py ~/Downloads/tagesplan-backup-2026-10-03.json -o daten/
```

```python
import pandas as pd
tage = pd.read_csv("daten/tage.csv", parse_dates=["Datum"])
tage["Training"] = tage["Training"].eq("Yes")
tage[["Schlaf h", "Energie", "Stimmung"]].corr()
```

CSV-Format: Komma als Trenner, Punkt als Dezimalzeichen, UTF-8 (RFC 4180). Excel: Daten > Aus Text/CSV, Dateiursprung UTF-8.

## Aufbau

| Datei | Zweck |
| --- | --- |
| `index.html` | Die komplette App (HTML, CSS, JavaScript) |
| `manifest.webmanifest` | Name, Symbol und Vollbildmodus für den Home-Bildschirm |
| `sw.js` | Offline-Cache; bei Änderungen die Versionsnummer `CACHE` erhöhen |
| `icons/` | App-Symbole |
| `tools/tagesplan_export.py` | Backup-JSON in CSV-Tabellen umwandeln (nur Standardbibliothek) |
| `fonts/` | Schriften Figtree, Bricolage Grotesque, IBM Plex Mono (SIL Open Font License) |
