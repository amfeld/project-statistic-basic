# Project Financial Analytics for Odoo v18

Ein umfassendes Finanzanalyse-Modul für Odoo v18-Projekte mit vollständiger NET/GROSS-Trennung, deutscher Buchhaltung (SKR03/SKR04) und Skonto-Tracking.

---

## 📋 Inhaltsverzeichnis

1. [Was macht dieses Modul?](#was-macht-dieses-modul)
2. [Schnellstart](#schnellstart)
3. [Berechnete Kennzahlen](#berechnete-kennzahlen)
4. [Praktische Beispiele](#praktische-beispiele)
5. [Limitationen & Hinweise](#limitationen--hinweise)
6. [Technische Details](#technische-details)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)
9. [Installation & Konfiguration](#installation--konfiguration)
10. [Module Deinstallation](#module-deinstallation)

---

## Was macht dieses Modul?

Dieses Modul bietet **Echtzeit-Finanzanalyse** für Odoo-Projekte durch automatisches Tracking von:

- 💶 **Kundenrechnungen** (NETTO & BRUTTO) - mit Zahlungsstatus
- 📝 **Lieferantenrechnungen** (NETTO & BRUTTO) - externe Kosten
- ⏱️ **Arbeitskosten** (Timesheets) - interne Kosten
- 💰 **Skonto-Tracking** (Gewährte & Erhaltene Skonti)
- 📊 **Gewinn/Verlust** (NETTO-basiert) - echte Projektkalkulation

### 🎯 Hauptvorteil: NET/GROSS-Trennung

**Warum ist das wichtig?**

```
BEISPIEL:
Kunde bezahlt: €10.000 (BRUTTO mit 19% MwSt)
Echte Einnahme: €8.403,36 (NETTO ohne MwSt)

Lieferant kostet: €3.000 (BRUTTO mit 19% MwSt)
Echte Kosten: €2.521,01 (NETTO ohne MwSt)

❌ FALSCH (BRUTTO-Vergleich): €10.000 - €3.000 = €7.000 Gewinn
✅ RICHTIG (NETTO-Vergleich): €8.403,36 - €2.521,01 = €5.882,35 Gewinn

Die MwSt ist ein Durchlaufposten - sie gehört nicht zum echten Gewinn!
```

**Dieses Modul zeigt BEIDE Werte:**
- NETTO für echte Gewinnberechnung
- BRUTTO für Liquiditätsplanung

---

## 🚀 Schnellstart

### Voraussetzungen

1. **Odoo v18** (Enterprise oder Community mit Accounting)
2. **Analytische Buchführung aktiviert**
3. **Projekte mit analytischen Konten verknüpft**

### Erster Blick

1. **Accounting → Project Analytics → Dashboard**
2. Wähle ein Projekt aus
3. Klicke auf **"Financial Analysis"** Button
4. Siehst du Werte? ✅ Alles OK!
5. Siehst du nur Nullen? ⚠️ Siehe [Troubleshooting](#troubleshooting)

### Wichtigster Button: "Refresh Financial Data"

Klicke diesen Button, wenn:
- Neue Rechnungen gebucht wurden
- Zahlungen eingegangen sind
- Timesheets erfasst wurden
- Daten nicht aktuell erscheinen

**Der Button berechnet ALLE Finanzdaten neu und lädt die Ansicht automatisch neu.**

---

## 📊 Berechnete Kennzahlen

### 1. Kundenrechnungen (Revenue)

| Feld | NETTO | BRUTTO | Beschreibung |
|------|-------|--------|--------------|
| **Invoiced Amount** | ✅ | ✅ | Gesamtsumme aller gebuchten Rechnungen |
| **Paid Amount** | ✅ | ✅ | Bereits erhaltene Zahlungen |
| **Outstanding Amount** | ✅ | ✅ | Noch ausstehende Forderungen |

**Berechnung:**
```python
# NETTO (ohne MwSt)
invoiced_net = sum(line.price_subtotal * analytic_percentage)
paid_net = invoiced_net * (invoice.paid_ratio)
outstanding_net = invoiced_net - paid_net

# BRUTTO (mit MwSt)
invoiced_gross = sum(line.price_total * analytic_percentage)
paid_gross = invoiced_gross * (invoice.paid_ratio)
outstanding_gross = invoiced_gross - paid_gross
```

### 2. Lieferantenrechnungen (Vendor Bills)

| Feld | NETTO | BRUTTO | Beschreibung |
|------|-------|--------|--------------|
| **Vendor Bills Total** | ✅ | ✅ | Gesamtkosten aller Lieferantenrechnungen |

**Berechnung:**
```python
# NETTO (ohne MwSt)
vendor_bills_net = sum(line.price_subtotal * analytic_percentage)

# BRUTTO (mit MwSt)
vendor_bills_gross = sum(line.price_total * analytic_percentage)
```

### 3. Interne Kosten

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| **Total Hours Booked** | Stunden | Alle gebuchten Zeiteinträge |
| **Labor Costs** | NETTO | Kosten der Arbeitsstunden (NETTO, keine MwSt) |
| **Other Costs** | NETTO | Sonstige Kosten (NETTO) |
| **Total Costs** | NETTO | Labor + Other Costs |

### 4. Skonto (Cash Discounts)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| **Customer Cash Discounts** | NETTO | Gewährte Skonti (reduziert Einnahmen) |
| **Vendor Cash Discounts Received** | NETTO | Erhaltene Skonti (reduziert Kosten) |

**Skonto-Erkennung:**
- Kunde: Konten 7300-7303, 2130 (Gewährte Skonti)
- Lieferant: Konten 4730-4733, 2670 (Erhaltene Skonti)

### 5. Gewinn/Verlust (NETTO-basiert)

| Feld | Formel | Beschreibung |
|------|--------|--------------|
| **Profit/Loss (Net)** | Revenue - Costs | Echter Projektgewinn (NETTO) |
| **Losses (Net)** | abs(min(0, Profit)) | Verluste als positive Zahl |

**Formel:**
```python
# Bereinigte Einnahmen (NETTO)
adjusted_revenue_net = invoiced_net - customer_skonto_taken

# Bereinigte Kosten (NETTO)
adjusted_vendor_costs_net = vendor_bills_net - vendor_skonto_received

# Gewinn/Verlust (NETTO-Vergleich)
profit_loss_net = adjusted_revenue_net - adjusted_vendor_costs_net - total_costs_net
```

---

## 💡 Praktische Beispiele

### Beispiel 1: Einfaches Projekt

**Projekt: "Website-Entwicklung für Kunde A"**

```
EINNAHMEN:
✅ Rechnung INV/2024/001: €10.000 BRUTTO (€8.403,36 NETTO) - 100% bezahlt
✅ Rechnung INV/2024/002: €5.000 BRUTTO (€4.201,68 NETTO) - 0% bezahlt

Ergebnis:
- Invoiced (Net): €12.605,04
- Invoiced (Gross): €15.000,00
- Paid (Net): €8.403,36
- Paid (Gross): €10.000,00
- Outstanding (Net): €4.201,68
- Outstanding (Gross): €5.000,00

KOSTEN:
✅ Lieferantenrechnung BILL/2024/001: €3.000 BRUTTO (€2.521,01 NETTO)
✅ Arbeitszeit: 80 Stunden à €50/h = €4.000 NETTO

Ergebnis:
- Vendor Bills (Net): €2.521,01
- Labor Costs: €4.000,00
- Total Costs (Net): €6.521,01

GEWINN/VERLUST:
- Profit/Loss (Net): €12.605,04 - €2.521,01 - €4.000,00 = €6.084,03 ✅
```

**Interpretation:**
- ✅ Projekt ist profitabel (€6.084,03 Gewinn)
- ⚠️ Noch €4.201,68 (NETTO) ausstehend
- 💰 Liquidität: €10.000 (BRUTTO) erhalten, €3.000 (BRUTTO) ausgegeben

---

### Beispiel 2: Projekt mit Skonto

**Projekt: "Software-Implementation für Kunde B"**

```
EINNAHMEN:
✅ Rechnung INV/2024/010: €50.000 BRUTTO (€42.016,81 NETTO)
   - Zahlungsbedingung: 2% Skonto bei Zahlung innerhalb 10 Tagen
   - Kunde zahlt: €49.000 BRUTTO (€41.176,47 NETTO)
   - Skonto: €1.000 BRUTTO (€840,34 NETTO)

KOSTEN:
✅ Lieferantenrechnung BILL/2024/020: €20.000 BRUTTO (€16.806,72 NETTO)
   - Zahlungsbedingung: 2% Skonto bei Zahlung innerhalb 10 Tagen
   - Wir zahlen: €19.600 BRUTTO (€16.470,59 NETTO)
   - Skonto erhalten: €400 BRUTTO (€336,13 NETTO)
✅ Arbeitszeit: 200 Stunden à €60/h = €12.000 NETTO

BERECHNUNG:
1. Bereinigte Einnahmen (NETTO):
   €42.016,81 (invoiced_net) - €840,34 (customer_skonto) = €41.176,47

2. Bereinigte Kosten (NETTO):
   €16.806,72 (vendor_bills_net) - €336,13 (vendor_skonto) = €16.470,59
   + €12.000 (labor_costs) = €28.470,59

3. Gewinn/Verlust (NETTO):
   €41.176,47 - €28.470,59 = €12.705,88 ✅

ANZEIGE IM MODUL:
- Invoiced (Net): €42.016,81
- Customer Cash Discounts: €840,34 (verringert Einnahmen)
- Vendor Bills (Net): €16.806,72
- Vendor Cash Discounts Received: €336,13 (verringert Kosten)
- Labor Costs: €12.000,00
- Profit/Loss (Net): €12.705,88
```

**Interpretation:**
- ✅ Skonto wird automatisch erkannt und verarbeitet
- ✅ Echter Gewinn: €12.705,88 (nach Berücksichtigung aller Skonti)
- 💰 Beide Seiten haben Skonto genutzt (win-win)

---

### Beispiel 3: Multi-Projekt Rechnung

**Rechnung mit Aufteilung auf 2 Projekte**

```
RECHNUNG INV/2024/100: €12.000 BRUTTO (€10.084,03 NETTO)

Positionen:
1. Zeile 1: Projekt A - €6.000 BRUTTO (€5.042,02 NETTO) - 50% Anteil
2. Zeile 2: Projekt B - €6.000 BRUTTO (€5.042,02 NETTO) - 50% Anteil

Rechnung ist zu 50% bezahlt (€6.000 BRUTTO)

PROJEKT A - Anzeige:
- Invoiced (Net): €5.042,02 (100% der zugewiesenen Zeile)
- Paid (Net): €2.521,01 (50% von €5.042,02) ⚠️
- Outstanding (Net): €2.521,01

PROJEKT B - Anzeige:
- Invoiced (Net): €5.042,02 (100% der zugewiesenen Zeile)
- Paid (Net): €2.521,01 (50% von €5.042,02) ⚠️
- Outstanding (Net): €2.521,01
```

**⚠️ WICHTIG - Limitation:**

Das Modul kann **NICHT** wissen, ob der Kunde speziell für Projekt A oder B gezahlt hat. Es verteilt die Zahlung **proportional** auf beide Projekte.

**Echtheit könnte sein:**
- Kunde hat €6.000 nur für Projekt A gezahlt
- Aber Odoo trackt Zahlungen auf Rechnungsebene, nicht Zeilenebene

**Workaround:**
- Verwende **separate Rechnungen pro Projekt** für präzises Payment-Tracking
- Oder akzeptiere proportionale Verteilung als Schätzung

---

### Beispiel 4: Teilweise bezahlte Rechnung

**Projekt: "Beratungsprojekt"**

```
RECHNUNG INV/2024/050: €20.000 BRUTTO (€16.806,72 NETTO)
- Position 1: Beratung Phase 1 - €10.000 BRUTTO
- Position 2: Beratung Phase 2 - €10.000 BRUTTO

Zahlung: €5.000 BRUTTO (25% der Rechnung)

ANZEIGE IM MODUL:
- Invoiced (Net): €16.806,72
- Paid (Net): €4.201,68 (25% von €16.806,72)
- Outstanding (Net): €12.605,04
```

**Was in der Realität sein könnte:**
- Kunde hat €5.000 speziell für Phase 1 bezahlt
- Oder: Anzahlung ohne Zuordnung zu einer Phase

**Was das Modul zeigt:**
- 25% von ALLEN Positionen als bezahlt
- Proportionale Verteilung

**Limitation:** Odoo unterstützt keine Zahlungszuordnung auf Zeilenebene.

---

## ⚠️ Limitationen & Hinweise

### 1. 🔴 KRITISCH: Analytische Buchführung erforderlich

**Das Modul funktioniert NUR mit aktivierter analytischer Buchführung!**

```
✅ ERFORDERLICH:
- Einstellungen → Buchhaltung → Analytische Buchführung aktiviert
- Jedes Projekt hat ein analytisches Konto (Plan: Projects)
- Rechnungszeilen haben analytic_distribution gesetzt
- Lieferantenrechnungszeilen haben analytic_distribution gesetzt

❌ OHNE analytische Buchführung:
- Alle Werte = 0.00
- Modul kann nicht funktionieren
- Keine Fehlermeldung, aber keine Daten
```

**Prüfen:**
```
1. Accounting → Configuration → Settings
2. Suche: "Analytic Accounting"
3. Muss aktiviert sein ✓
4. Projekt öffnen → Tab "Settings" → "Analytic Account" muss ausgefüllt sein
```

---

### 2. 🟡 MEDIUM: Zahlungszuordnung nur proportional

**Problem:** Odoo trackt Zahlungen auf **Rechnungsebene**, nicht auf **Zeilenebene**.

**Beispiel:**
```
Rechnung: €100 (Zeile A: €50 + Zeile B: €50)
Zahlung: €50 (50% der Rechnung)

Modul zeigt:
- Zeile A: €25 bezahlt (50% von €50)
- Zeile B: €25 bezahlt (50% von €50)

Realität könnte sein:
- Zeile A: €50 bezahlt (100%)
- Zeile B: €0 bezahlt (0%)
```

**Lösung:**
- ✅ Eine Rechnung pro Projekt (beste Genauigkeit)
- ⚠️ Oder: Proportionale Verteilung als Schätzung akzeptieren

---

### 3. 🟡 MEDIUM: Skonto-Erkennung limitiert

**Das Modul erkennt Skonto über Kontonummern:**

```
Kundenrabatte (Gewährte Skonti):
- 7300, 7301, 7302, 7303 (SKR03/SKR04)
- 2130 (Bilanz-Konto)

Lieferantenrabatte (Erhaltene Skonti):
- 4730, 4731, 4732, 4733 (SKR03/SKR04)
- 2670 (Bilanz-Konto)
```

**Nicht erkannt:**
- Skonto ohne analytic_distribution
- Skonto auf anderen Konten (custom Chart of Accounts)
- Skonto in manuellen Buchungen ohne Analytik

**Lösung:**
- Immer analytic_distribution bei Skonto-Buchungen setzen
- Standard SKR03/SKR04 Konten verwenden
- Oder Code anpassen in `_get_skonto_from_analytic()` Methode

---

### 4. 🔴 KRITISCH: Keine Multi-Währung Unterstützung

**Das Modul summiert ALLE Beträge ohne Währungsumrechnung!**

```
❌ FALSCH (Multi-Währung):
Rechnung 1: €10.000
Rechnung 2: $10.000
Summe: €20.000 (FALSCH!)

✅ RICHTIG (Einzel-Währung):
Rechnung 1: €10.000
Rechnung 2: €5.000
Summe: €15.000 (KORREKT!)
```

**Lösung:**
- ✅ Projekte nur in EINER Währung
- ❌ Keine Multi-Währungs-Projekte

---

### 5. 🟢 NIEDRIG: Performance bei großen Projekten

**Symptom:** Langsame Ladezeiten bei Projekten mit 1000+ Rechnungszeilen

**Ursache:**
- Echtzeit-Berechnung bei jedem Seitenaufruf
- Viele Datenbankabfragen

**Lösung:**
- Filter verwenden (Status, Datum, etc.)
- Paginierung nutzen (50-100 Projekte pro Seite)
- "Refresh Financial Data" nur bei Bedarf klicken

---

### 6. 🟢 NIEDRIG: Timesheet-Kosten abhängig von HR-Konfiguration

**Das Modul LIEST nur Timesheet-Kosten - es berechnet sie nicht!**

```
✅ Korrekt konfiguriert:
- Mitarbeiter haben Stundensätze in HR
- Timesheets zeigen Kosten in account.analytic.line
- Modul summiert diese Kosten

❌ Nicht konfiguriert:
- Stundensätze = 0
- Timesheet-Kosten = 0
- Modul zeigt 0.00 Labor Costs
```

**Lösung:**
- HR → Mitarbeiter → Kosten pro Stunde konfigurieren
- Odoo Enterprise: Automatische Berechnung
- Odoo Community: Manuell setzen oder Modul installieren

---

### 7. 🟡 MEDIUM: Gutschriften & Stornos

**Das Modul überspringt Storno-Buchungen automatisch:**

```
✅ Automatisch behandelt:
- Rechnungs-Gutschriften (out_refund) → reduzieren Umsatz
- Lieferanten-Gutschriften (in_refund) → reduzieren Kosten
- Storno-Buchungen (reversed_entry_id) → werden übersprungen

⚠️ Edge Case:
- Manuell erstellte Stornos ohne Odoo-Kennzeichen
- Könnten doppelt gezählt werden
```

**Lösung:**
- Immer Odoo's "Reverse Entry" Button verwenden
- Keine manuellen Storno-Buchungen

---

### 8. 🟡 MEDIUM: Analytische Verteilung

**Das Modul unterstützt prozentuale Aufteilung:**

```json
{
  "123": 50.0,   // Projekt A: 50%
  "456": 30.0,   // Projekt B: 30%
  "789": 20.0    // Projekt C: 20%
}
```

**Edge Cases:**
- Prozente addieren sich nicht zu 100% → Keine Validierung
- Sehr kleine Prozente (<0.01%) → Rundungsfehler möglich
- Fehlerhaftes JSON → Zeile wird übersprungen

**Best Practice:**
- Prozente sollten = 100% sein
- Ganze Zahlen bevorzugen (25%, 50%, 75%)
- Unter 1% vermeiden

---

## 🔧 Technische Details

### Odoo v18 Kompatibilität

**Neu in v18:**
- `analytic_distribution` JSON-Feld (ersetzt alte analytic_account_id)
- `aggregator` statt `group_operator`
- `parent_state` statt `state` für move_lines

**Das Modul nutzt:**
- ✅ Moderne v18 API
- ✅ JSON-basierte Analytik
- ✅ Stored computed fields für Performance
- ✅ Automatische Trigger bei Änderungen

### Datenfluss

```
1. INVOICE/BILL ERSTELLEN
   └─> account.move.line mit analytic_distribution

2. INVOICE/BILL BUCHEN
   └─> parent_state = 'posted'
   └─> Trigger in account_move_line.py
   └─> Markiert betroffene Projekte

3. PROJECT ÖFFNEN / REFRESH KLICKEN
   └─> _compute_financial_data() wird aufgerufen
   └─> Sucht alle relevanten account.move.line
   └─> Berechnet NET/GROSS Werte
   └─> Speichert in project_project Tabelle

4. ANZEIGE
   └─> Views zeigen gespeicherte Werte
   └─> Pivot/Graph nutzen aggregator='sum'
```

### Berechnungsmethoden

**Hauptmethode:** `_compute_financial_data()`
- Wird getriggert von `@api.depends('partner_id', 'user_id')`
- Speichert mit `store=True`
- Läuft in Batches (50 Projekte auf einmal)

**Hilfsmethoden:**
- `_get_customer_invoices_from_analytic()` - Kundenrechnungen
- `_get_vendor_bills_from_analytic()` - Lieferantenrechnungen
- `_get_skonto_from_analytic()` - Skonto-Tracking
- `_get_timesheet_costs()` - Arbeitskosten
- `_get_other_costs_from_analytic()` - Sonstige Kosten

### Automatische Neuberechnung

**Trigger:** `account_move_line.py`

```python
@api.model_create_multi
def create(self, vals_list):
    # ... Zeilen erstellen
    # Markiere betroffene Projekte für Neuberechnung
    self._trigger_project_analytics_recompute()

def write(self, vals):
    # ... Änderungen speichern
    # Markiere betroffene Projekte für Neuberechnung
    self._trigger_project_analytics_recompute()

def unlink(self):
    # Markiere betroffene Projekte BEVOR gelöscht wird
    self._trigger_project_analytics_recompute()
    # ... Zeilen löschen
```

**Batch Processing:**
- 50 Projekte auf einmal
- Verhindert Performance-Probleme
- Automatisch im Hintergrund

---

## 🐛 Troubleshooting

### Problem: Alle Werte zeigen 0.00

**Mögliche Ursachen:**

1. **Keine analytische Buchführung aktiviert** 🔴
   ```
   ✅ Lösung:
   - Einstellungen → Buchhaltung → Analytische Buchführung aktivieren
   - Odoo neu starten
   - Modul upgraden
   ```

2. **Projekt hat kein analytisches Konto** 🔴
   ```
   ✅ Lösung:
   - Projekt öffnen → Tab "Settings"
   - "Analytic Account" Feld prüfen
   - Falls leer: Neues analytisches Konto erstellen
   ```

3. **Rechnungen haben keine analytic_distribution** 🔴
   ```
   ✅ Lösung:
   - Rechnung öffnen → Tab "Other Info"
   - Rechnungszeilen prüfen
   - "Analytic Distribution" muss ausgefüllt sein
   ```

4. **Rechnungen sind nicht gebucht** 🟡
   ```
   ✅ Lösung:
   - Nur gebuchte Rechnungen (state='posted') werden gezählt
   - Entwürfe werden ignoriert
   ```

5. **Diagnostic Logs prüfen** 🟢
   ```
   ✅ Lösung:
   - "Refresh Financial Data" klicken
   - Logs in odoo.sh ansehen
   - Oder: Einstellungen → Technical → Logging

   DIAGNOSTIC Logs zeigen:
   - Total move lines in database: XXXX
   - Customer invoice lines (any state): XXXX
   - Posted customer invoice lines: XXXX
   - Posted customer lines WITH analytic_distribution: XXXX

   Wenn eine Zahl 0 ist → Das ist das Problem!
   ```

---

### Problem: Zahlungen werden nicht angezeigt

**Mögliche Ursachen:**

1. **Rechnung nicht als bezahlt markiert**
   ```
   ✅ Lösung:
   - Rechnung öffnen
   - "Amount Due" prüfen
   - Muss < "Amount Total" sein für Teilzahlung
   - Muss = 0.00 sein für volle Zahlung
   ```

2. **Zahlung nicht reconciled**
   ```
   ✅ Lösung:
   - Rechnung → "Payments" Tab
   - Zahlungen müssen reconciled sein
   - Status: "Paid" oder "Partial"
   ```

3. **Neuberechnung notwendig**
   ```
   ✅ Lösung:
   - "Refresh Financial Data" Button klicken
   - Wartet auf Seitenreload (erfolgt automatisch)
   ```

---

### Problem: Skonto wird nicht erkannt

**Mögliche Ursachen:**

1. **Falsche Kontonummer**
   ```
   ✅ Lösung:
   - Prüfe: Konten 7300-7303 (Kunde) oder 4730-4733 (Lieferant)
   - Oder: 2130 (Kunde Bilanz), 2670 (Lieferant Bilanz)
   - Code anpassen für custom Chart of Accounts
   ```

2. **Keine analytic_distribution gesetzt**
   ```
   ✅ Lösung:
   - Skonto-Buchung öffnen
   - Zeile mit Skonto-Konto
   - "Analytic Distribution" muss gesetzt sein!
   ```

3. **Manuell gebuchtes Skonto**
   ```
   ✅ Lösung:
   - Skonto via Journal Entry
   - Analytic Distribution manuell setzen
   - Oder: Odoo's automatisches Skonto verwenden
   ```

---

### Problem: Performance ist langsam

**Lösungen:**

1. **Filter verwenden**
   ```
   ✅ Lösung:
   - Filter nach Status, Datum, Kunde
   - Reduziert Anzahl angezeigter Projekte
   - Schnellere Berechnung
   ```

2. **Paginierung aktivieren**
   ```
   ✅ Lösung:
   - Standard: 500 Projekte pro Seite
   - Reduzieren auf 50-100 bei Bedarf
   - In views/project_analytics_views.xml: limit="50"
   ```

3. **Nur bei Bedarf neu berechnen**
   ```
   ✅ Lösung:
   - "Refresh Financial Data" nur klicken wenn nötig
   - Nicht bei jedem Seitenaufruf
   - Trigger läuft automatisch bei Invoice-Änderungen
   ```

---

### Problem: Werte stimmen nicht

**Debugging-Schritte:**

1. **Logs aktivieren**
   ```
   ✅ Lösung:
   - odoo.sh: Web-Interface → Logs
   - Lokal: tail -f /var/log/odoo/odoo.log
   - Nach "Searching for invoice lines" suchen
   ```

2. **DIAGNOSTIC Logs prüfen**
   ```
   Die neuen DIAGNOSTIC Logs zeigen:

   DIAGNOSTIC: Total move lines in database: 12547
   DIAGNOSTIC: Customer invoice lines (any state): 842
   DIAGNOSTIC: Posted customer invoice lines: 756
   DIAGNOSTIC: Posted customer lines WITH analytic_distribution: 124
   Found 124 potential invoice lines (before analytic filter)
   Matched 12 invoice lines for analytic account 35

   → Jeder Schritt reduziert die Anzahl
   → Findet den Filter, der das Problem verursacht
   ```

3. **Manuell prüfen**
   ```sql
   -- Kundenrechnungen mit Analytik für Projekt
   SELECT aml.id, aml.name, aml.price_subtotal, aml.price_total,
          aml.analytic_distribution, am.name as invoice_name
   FROM account_move_line aml
   JOIN account_move am ON aml.move_id = am.id
   WHERE aml.analytic_distribution IS NOT NULL
     AND am.state = 'posted'
     AND am.move_type = 'out_invoice'
     AND aml.analytic_distribution::text LIKE '%"35"%'  -- Analytic Account ID
   ```

4. **Testrechnung erstellen**
   ```
   ✅ Lösung:
   - Neue Rechnung mit nur 1 Zeile
   - Analytic Distribution setzen
   - Buchen
   - "Refresh Financial Data" klicken
   - Erscheint der Betrag? → Basis funktioniert
   ```

---

## ❓ FAQ

### Q1: Kann ich das Modul in Odoo Community verwenden?

**A:** Ja, aber mit Einschränkungen:
- ✅ Grundfunktionen laufen
- ⚠️ Timesheet-Kosten erfordern zusätzliche Konfiguration
- ⚠️ Einige Enterprise-Features fehlen
- ✅ NET/GROSS-Trennung funktioniert vollständig

---

### Q2: Unterstützt das Modul mehrere Unternehmen (Multi-Company)?

**A:** Ja, das Modul respektiert Odoo's Multi-Company Regeln:
- Jedes Unternehmen hat eigene analytische Konten
- Projekte werden pro Unternehmen gefiltert
- Keine Cross-Company Berechnungen

---

### Q3: Kann ich eigene Felder hinzufügen?

**A:** Ja, Erweiterung ist möglich:

```python
# custom_module/models/project_analytics.py
from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    custom_margin = fields.Float(
        string='Custom Margin %',
        compute='_compute_custom_margin',
        store=True
    )

    @api.depends('profit_loss_net', 'customer_invoiced_amount_net')
    def _compute_custom_margin(self):
        for project in self:
            if project.customer_invoiced_amount_net > 0:
                project.custom_margin = (
                    project.profit_loss_net /
                    project.customer_invoiced_amount_net * 100
                )
            else:
                project.custom_margin = 0.0
```

---

### Q4: Werden Anzahlungen (Down Payments) unterstützt?

**A:** Ja, Anzahlungen werden automatisch behandelt:
- Anzahlungsrechnungen mit analytic_distribution werden gezählt
- Endrechnung mit Anzahlungsabzug wird korrekt berechnet
- Keine Doppelzählung durch Odoo's Standard-Mechanismus

---

### Q5: Was passiert bei Gutschriften?

**A:** Gutschriften reduzieren automatisch die Beträge:

```
Beispiel:
1. Rechnung: +€10.000 → Invoiced = €10.000
2. Gutschrift: -€2.000 → Invoiced = €8.000
3. Final: €8.000 NETTO Umsatz
```

- out_refund: Reduziert Kundenrechnungen
- in_refund: Reduziert Lieferantenkosten

---

### Q6: Kann ich historische Projekte analysieren?

**A:** Ja, das Modul analysiert ALLE Projekte:
- Aktive Projekte
- Abgeschlossene Projekte
- Archivierte Projekte

**Tipp:** Verwende Filter für bessere Performance:
- Filter nach "Create Date"
- Filter nach "Stage"
- Filter nach "Customer"

---

### Q7: Wie genau ist die Zahlungszuordnung?

**A:** Genauigkeit hängt von der Rechnungsstruktur ab:

| Szenario | Genauigkeit | Empfehlung |
|----------|-------------|------------|
| 1 Rechnung = 1 Projekt | 100% genau ✅ | Beste Praxis |
| 1 Rechnung = Mehrere Projekte | Proportional geschätzt ⚠️ | OK für Übersicht |
| Teilzahlungen | Proportional verteilt ⚠️ | Vollzahlung bevorzugen |

---

### Q8: Unterstützt das Modul Fremdwährungen?

**A:** Nein, keine Währungsumrechnung:
- ❌ Multi-Währungs-Projekte: Falsche Summen
- ✅ Einzel-Währung pro Projekt: Korrekt

**Alternative:** Odoo's Standard Multi-Currency Accounting verwenden.

---

### Q9: Kann ich die Berechnung anpassen?

**A:** Ja, alle Methoden sind überschreibbar:

```python
# Beispiel: Eigene Profit-Formel
class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.depends('partner_id', 'user_id')
    def _compute_financial_data(self):
        # Standard-Berechnung ausführen
        super()._compute_financial_data()

        # Eigene Anpassungen
        for project in self:
            # Z.B. 10% Overhead hinzufügen
            project.profit_loss_net -= project.labor_costs * 0.1
```

---

### Q10: Gibt es Automated Tests?

**A:** Ja, 6 Test Cases:
1. Projekt ohne analytisches Konto
2. Kundenrechnung Basic
3. Lieferantenrechnung Basic
4. Skonto Kunde
5. Skonto Lieferant
6. Gewinn/Verlust Berechnung

**Ausführen:**
```bash
odoo-bin -c odoo.conf -d test_db -i project_statistic --test-enable --stop-after-init
```

---

## 📦 Installation & Konfiguration

### Schritt 1: Modul installieren

```bash
# odoo.sh:
# 1. Git Push zum Branch
# 2. odoo.sh deployed automatisch
# 3. Apps → "Project Statistic" → Install

# Lokal:
# 1. Kopiere Modul nach addons/
# 2. odoo-bin -c odoo.conf -d your_db -i project_statistic
# 3. Oder: Apps → Update Apps List → Install
```

### Schritt 2: Analytische Buchführung aktivieren

```
1. Einstellungen → Buchhaltung → Settings
2. Suche: "Analytic Accounting"
3. Aktiviere Feature ✓
4. Speichern
```

### Schritt 3: Projekte verknüpfen

```
FÜR NEUE PROJEKTE:
1. Project → Create
2. Tab "Settings"
3. "Analytic Account" → Auto-erstellt ✓

FÜR BESTEHENDE PROJEKTE:
1. Project → Open
2. Tab "Settings"
3. "Analytic Account" → Create & Link
4. Speichern
```

### Schritt 4: Rechnungen mit Analytik verknüpfen

```
AB JETZT bei jeder Rechnung:
1. Accounting → Customers → Invoices → Create
2. Invoice Lines Tab
3. Jede Zeile: "Analytic Distribution" ausfüllen
   - Projekt auswählen
   - Prozent eingeben (z.B. 100%)
4. Rechnung buchen

⚠️ WICHTIG: Ohne Analytic Distribution → Keine Daten im Modul!
```

### Schritt 5: Erste Analyse

```
1. Accounting → Project Analytics → Dashboard
2. Wähle Projekt
3. Klicke "Financial Analysis"
4. Siehe Daten? ✅
5. Nur Nullen? → Siehe Troubleshooting
```

---

## 🗑️ Module Deinstallation

### Was passiert beim Deinstallieren?

Das Modul entfernt **automatisch alle Datenbank-Spalten**:

```python
# Automatischer uninstall_hook entfernt:
- Alle NET/GROSS Felder
- Alle Skonto Felder
- Alle Kosten-Felder
- Alle Gewinn/Verlust Felder
- client_name, head_of_project, sequence

Ergebnis: Saubere Datenbank, keine verwaisten Spalten
```

### Sicher deinstallieren

```
1. Apps → Project Statistic
2. Uninstall Button
3. Bestätigen
4. ✅ Alle Spalten werden automatisch entfernt
5. ✅ Keine manuellen SQL-Befehle nötig
```

---

## 📊 Zusammenfassung der Limitationen

| Limitation | Auswirkung | Schwere | Lösung |
|------------|------------|---------|--------|
| Analytische Buchführung erforderlich | Keine Daten ohne Analytik | 🔴 Kritisch | Analytik aktivieren |
| Zahlungszuordnung nur proportional | Schätzung bei Multi-Projekt-Rechnungen | 🟡 Mittel | 1 Rechnung = 1 Projekt |
| Skonto-Konten hardcoded | Nur SKR03/SKR04 | 🟡 Mittel | Code anpassen |
| Keine Multi-Währung | Falsche Summen | 🔴 Kritisch | Nur 1 Währung |
| Performance bei 1000+ Zeilen | Langsam | 🟡 Mittel | Filter verwenden |
| Timesheet-Kosten von HR abhängig | 0.00 wenn nicht konfiguriert | 🟡 Mittel | HR konfigurieren |
| Storno-Erkennung limitiert | Manuelle Stornos ggf. doppelt | 🟢 Niedrig | Odoo's "Reverse Entry" nutzen |
| Prozentuale Verteilung ohne Validierung | Rundungsfehler möglich | 🟢 Niedrig | 100% sicherstellen |

**Legende:**
- 🔴 Kritisch: Muss behoben werden
- 🟡 Mittel: Sollte beachtet werden
- 🟢 Niedrig: Geringe Auswirkung

---

## 🎯 Best Practices

### ✅ DO's

1. **Immer Analytic Distribution setzen** bei Rechnungen
2. **Eine Rechnung pro Projekt** für genaue Zahlungszuordnung
3. **Odoo's Standard-Features nutzen** (Reverse Entry, Skonto)
4. **Filter verwenden** für Performance
5. **"Refresh Financial Data"** nach größeren Änderungen
6. **HR-Kosten konfigurieren** für Timesheet-Tracking
7. **Nur eine Währung** pro Projekt
8. **Tests durchführen** vor Produktiveinsatz

### ❌ DON'Ts

1. **Nicht ohne Analytik** buchen
2. **Keine Multi-Währungs-Projekte**
3. **Keine manuellen Stornos** (ohne Odoo-Kennzeichen)
4. **Nicht alle Projekte auf einmal laden** (Performance)
5. **Keine Teilzahlungen** auf Multi-Projekt-Rechnungen
6. **Nicht ohne Test** in Produktion nehmen
7. **Keine custom Skonto-Konten** ohne Code-Anpassung

---

## 🚀 Production Readiness

### Status: ✅ PRODUKTIONSREIF

- ✅ Vollständige NET/GROSS-Trennung
- ✅ Deutscher Kontenrahmen (SKR03/SKR04)
- ✅ Skonto-Tracking automatisch
- ✅ Automated Tests (6 Test Cases)
- ✅ Clean Uninstall (uninstall_hook)
- ✅ Odoo v18 kompatibel
- ✅ Performance-optimiert (Batch Processing)
- ✅ Umfassende Dokumentation
- ✅ Troubleshooting & FAQ
- ✅ Diagnostic Logs für Debugging

---

## 📞 Support & Lizenz

**Modul:** project_statistic
**Version:** 18.0.1.0.5
**Lizenz:** LGPL-3
**Autor:** Alex Feld

**Support:**
1. README durchlesen (diese Datei)
2. Troubleshooting Sektion prüfen
3. FAQ durchsehen
4. Diagnostic Logs aktivieren

**Customization:**
- Alle Methoden überschreibbar
- Gut dokumentierter Code
- Modulare Struktur
- Einfach erweiterbar

---

## 🏁 Schnellreferenz

### Wichtigste Felder

| Feld | Typ | Verwendung |
|------|-----|------------|
| `customer_invoiced_amount_net` | NETTO | Gewinn-Berechnung |
| `customer_invoiced_amount_gross` | BRUTTO | Liquiditäts-Planung |
| `vendor_bills_total_net` | NETTO | Kosten-Tracking |
| `labor_costs` | NETTO | Interne Kosten |
| `profit_loss_net` | NETTO | Projekt-Erfolg |

### Wichtigste Buttons

| Button | Funktion | Wann nutzen? |
|--------|----------|--------------|
| **Financial Analysis** | Öffnet Detail-Ansicht | Projekt-Details sehen |
| **Refresh Financial Data** | Neuberechnung + Reload | Nach Buchungen/Zahlungen |
| **Analytic Entries** | Zeigt alle Buchungen | Debugging |

### Wichtigste Formeln

```python
# Gewinn/Verlust (NETTO)
profit_net = (invoiced_net - customer_skonto) - (vendor_bills_net - vendor_skonto + total_costs_net)

# Ausstehend (NETTO)
outstanding_net = invoiced_net - paid_net

# Zahlungsquote
payment_ratio = (amount_total - amount_residual) / amount_total
```

---

**🎉 Viel Erfolg mit der Projekt-Finanzanalyse!**
