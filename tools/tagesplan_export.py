#!/usr/bin/env python3
"""Tagesplan-Backup (JSON) in Tabellen umwandeln.

Erzeugt aus der Backup-Datei der App drei CSV-Dateien:

    tage.csv       eine Zeile pro Tag, Spalten wie die Notion-Datenbank "Tage"
    wochen.csv     eine Zeile pro Woche (Mo bis So), Spalten wie "Wochen"
    aufgaben.csv   Langformat: eine Zeile pro Tag und Aufgabe (fuer Analysen)

Nur Standardbibliothek, keine Installation noetig.

    python3 tools/tagesplan_export.py tagesplan-backup-2026-10-03.json -o daten/

Einlesen mit pandas:

    import pandas as pd
    tage = pd.read_csv("daten/tage.csv", parse_dates=["Datum"])
    tage["Training"] = tage["Training"].eq("Yes")
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import fmean
from typing import Any

DSHORT = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]  # Index = JavaScript getDay()

DAY_HEAD = ["Tag", "Datum", "Wochentag", "Schicht", "Checkliste", "Erledigt", "Aufgaben",
            "Wasser L", "Wasserziel L", "Gemüse", "Obst", "Eiweiß", "Nüsse", "Schlaf h",
            "Energie", "Stimmung", "Gewicht kg", "Training", "Familie", "Offen"]
WEEK_HEAD = ["Woche", "Start", "Tage erfasst", "Checkliste", "Trainings", "Training geplant",
             "Schlaf h", "Energie", "Stimmung", "Wasser L", "Gewicht kg", "Familie",
             "Lief gut", "Nächste Woche"]
TASK_HEAD = ["Datum", "Wochentag", "Uhrzeit", "Aufgabe", "Kategorie", "Erledigt", "ID"]


def js_dow(d: date) -> int:
    """Wochentag wie in JavaScript: 0 = Sonntag."""
    return (d.weekday() + 1) % 7


def mins(t: str) -> int:
    h, m = (int(x) for x in str(t).split(":")[:2])
    return h * 60 + m + (1440 if h < 4 else 0)  # Zeiten vor 4:00 gehoeren zum Vortag


def fmt_t(t: str) -> str:
    h, m = str(t).split(":")[:2]
    return ("00" if int(h) == 0 else str(int(h))) + ":" + m


def num(v: Any, dig: int = 2) -> str:
    if v is None:
        return ""
    return f"{round(float(v), dig):g}"


class Backup:
    def __init__(self, raw: dict[str, Any]):
        if not isinstance(raw.get("days"), dict):
            raise ValueError("Keine Tagesplan-Backup-Datei (Feld 'days' fehlt).")
        self.days: dict[str, dict[str, Any]] = raw["days"]
        self.plan: dict[str, Any] | None = raw.get("plan")
        self.weeks: dict[str, dict[str, Any]] = raw.get("weeks") or {}
        goals = (self.plan or {}).get("goals") or {}
        self.sleep_goal = float(goals.get("sleepH") or 6.5)
        exported = raw.get("exported")
        stamp = datetime.fromisoformat(exported.replace("Z", "+00:00")) if exported else datetime.now()
        self.today = (stamp - timedelta(hours=4)).date().isoformat()  # Tageswechsel der App um 4:00

    # --- Plan und Tag ---
    def plan_day(self, k: str) -> dict[str, Any]:
        if not self.plan:
            return {}
        return self.plan["days"].get(str(js_dow(date.fromisoformat(k))), {})

    def items(self, k: str) -> list[dict[str, Any]]:
        d = self.days.get(k) or {}
        tasks = d.get("tasks") if isinstance(d.get("tasks"), list) else self.plan_day(k).get("tasks", [])
        return sorted(tasks, key=lambda t: mins(t["t"]))

    def shift(self, k: str) -> str:
        d = self.days.get(k) or {}
        return d["shift"] if isinstance(d.get("shift"), str) else self.plan_day(k).get("shift", "")

    def water_goal(self, k: str) -> float:
        d = self.days.get(k) or {}
        return float(d.get("waterGoal") or self.plan_day(k).get("water") or 2.5)

    def done_cats(self, k: str) -> set[str]:
        done = (self.days.get(k) or {}).get("done") or {}
        return {t.get("cat", "other") for t in self.items(k) if done.get(t["id"])}

    def pct(self, k: str) -> float | None:
        its = self.items(k)
        if not its:
            return None
        done = (self.days.get(k) or {}).get("done") or {}
        return sum(1 for t in its if done.get(t["id"])) / len(its)

    @staticmethod
    def has_data(d: dict[str, Any] | None) -> bool:
        if not d:
            return False
        if any((d.get("done") or {}).values()):
            return True
        return bool(d.get("water") or d.get("veg") or d.get("fruit") or d.get("protein")) or any(
            d.get(f) is not None for f in ("sleep", "energy", "mood", "weight"))

    def data_days(self) -> list[str]:
        return sorted(k for k, d in self.days.items() if k <= self.today and self.has_data(d))

    # --- Tabellen ---
    def day_rows(self) -> list[list[Any]]:
        rows = []
        for k in self.data_days():
            d, its = self.days[k], self.items(k)
            done = d.get("done") or {}
            n = sum(1 for t in its if done.get(t["id"]))
            dc = self.done_cats(k)
            dd = date.fromisoformat(k)
            rows.append([
                f"{DSHORT[js_dow(dd)]} {dd:%d.%m.%Y}", k, DSHORT[js_dow(dd)], self.shift(k),
                num(n / len(its)) if its else "", n, len(its),
                num((d.get("water") or 0) * 0.25), num(self.water_goal(k)),
                d.get("veg") or 0, d.get("fruit") or 0, d.get("protein") or 0, d.get("nuts") or 0,
                num(d.get("sleep"), 1), d.get("energy") if d.get("energy") is not None else "",
                d.get("mood") if d.get("mood") is not None else "", num(d.get("weight"), 1),
                "Yes" if "train" in dc else "No", "Yes" if "family" in dc else "No",
                "; ".join(f"{fmt_t(t['t'])} {t['label']}" for t in its if not done.get(t["id"])),
            ])
        return rows

    def task_rows(self) -> list[list[Any]]:
        rows = []
        for k in self.data_days():
            done = self.days[k].get("done") or {}
            for t in self.items(k):
                rows.append([k, DSHORT[js_dow(date.fromisoformat(k))], fmt_t(t["t"]), t["label"],
                             t.get("cat", "other"), 1 if done.get(t["id"]) else 0, t["id"]])
        return rows

    def week_summary(self, mon: str) -> dict[str, Any]:
        r: dict[str, Any] = {"n": 0, "train": 0, "planned": 0, "weight": None, "family": False}
        P, S, E, M, W = [], [], [], [], []
        start = date.fromisoformat(mon)
        for i in range(7):
            k = (start + timedelta(days=i)).isoformat()
            if any(t.get("cat") == "train" for t in self.items(k)):
                r["planned"] += 1
            d = self.days.get(k)
            if not self.has_data(d) or k > self.today:
                continue
            r["n"] += 1
            for lst, f in ((S, "sleep"), (E, "energy"), (M, "mood")):
                if isinstance(d.get(f), (int, float)):
                    lst.append(float(d[f]))
            if isinstance(d.get("weight"), (int, float)):
                r["weight"] = d["weight"]
            dc = self.done_cats(k)
            r["family"] = r["family"] or "family" in dc
            if "train" in dc:
                r["train"] += 1
            if k < self.today:
                p = self.pct(k)
                if p is not None:
                    P.append(p)
                W.append((d.get("water") or 0) * 0.25)
        for key, lst in (("pct", P), ("sleep", S), ("energy", E), ("mood", M), ("water", W)):
            r[key] = fmean(lst) if lst else None
        return r

    def week_rows(self) -> list[list[Any]]:
        mons = {(date.fromisoformat(k) - timedelta(days=date.fromisoformat(k).weekday())).isoformat()
                for k in self.data_days()} | {k for k in self.weeks if len(k) == 10}
        rows = []
        for mon in sorted(mons):
            w, nt = self.week_summary(mon), self.weeks.get(mon) or {}
            m = date.fromisoformat(mon)
            end = m + timedelta(days=6)
            rows.append([
                f"KW {m.isocalendar()[1]} · {m:%d.%m.} bis {end:%d.%m.%Y}", mon, w["n"],
                num(w["pct"]), w["train"], w["planned"], num(w["sleep"], 1), num(w["energy"], 1),
                num(w["mood"], 1), num(w["water"]), num(w["weight"], 1),
                "Yes" if w["family"] else "No", nt.get("good", ""), nt.get("next", ""),
            ])
        return rows


def write_csv(path: Path, head: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("backup", type=Path, help="Backup-Datei aus der App (tagesplan-backup-JJJJ-MM-TT.json)")
    ap.add_argument("-o", "--out", type=Path, default=Path("daten"), help="Zielordner (Standard: daten/)")
    a = ap.parse_args(argv)

    bk = Backup(json.loads(a.backup.read_text(encoding="utf-8")))
    a.out.mkdir(parents=True, exist_ok=True)
    tage, wochen, aufgaben = bk.day_rows(), bk.week_rows(), bk.task_rows()
    write_csv(a.out / "tage.csv", DAY_HEAD, tage)
    write_csv(a.out / "wochen.csv", WEEK_HEAD, wochen)
    write_csv(a.out / "aufgaben.csv", TASK_HEAD, aufgaben)
    print(f"{len(tage)} Tage, {len(wochen)} Wochen, {len(aufgaben)} Aufgaben-Zeilen nach {a.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
