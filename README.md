# Tagesplan

Persönliche iPhone-App (Progressive Web App) für den Alltag mit Früh- und Spätschicht: Tages-Checkliste mit eigenem Wochenplan (Aufgaben, Uhrzeiten, Schicht, Wasserziel pro Wochentag, in der App bearbeitbar), Wasser- und Essenszähler, Schlaf, Energie, Stimmung, Gewicht und Gewichtsverlauf für Oktober und November 2026.

## Installieren

1. `https://sadiq422.github.io/tagesplan/` in **Safari** auf dem iPhone öffnen.
2. Unten auf **Teilen** tippen, dann **Zum Home-Bildschirm**.
3. Die App über das neue Symbol öffnen.

## Daten

- Alle Einträge werden nur auf dem Gerät gespeichert (`localStorage`), nichts geht an einen Server.
- Die App funktioniert offline (Service Worker in `sw.js`).
- Über **Backup speichern** entsteht eine JSON-Datei mit Einträgen, Plan, Zielen und Listen, die sich in Dateien sichern und mit **Backup laden** wiederherstellen lässt.
- Jeder Tag speichert den Plan, der an dem Tag galt. Planänderungen wirken ab heute, vergangene Tage bleiben unverändert.

## Aufbau

| Datei | Zweck |
| --- | --- |
| `index.html` | Die komplette App (HTML, CSS, JavaScript) |
| `manifest.webmanifest` | Name, Symbol und Vollbildmodus für den Home-Bildschirm |
| `sw.js` | Offline-Cache; bei Änderungen die Versionsnummer `CACHE` erhöhen |
| `icons/` | App-Symbole |
| `fonts/` | Schriften Figtree, Bricolage Grotesque, IBM Plex Mono (SIL Open Font License) |
