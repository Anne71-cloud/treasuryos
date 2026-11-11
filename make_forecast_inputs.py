"""
TreasuryOS: inputs for module 2 (prévisionnel / cash forecast). All synthetic.

Writes:
  data/forecast_calendar.json   recurring and one-off flows the treasurer already knows about (payroll, taxes, rent...)
  data/forecast_settings.json   forecast start, weekly seasonality, 12-month drivers, liquidity policy
  data/forecast_snapshot.csv    the 13-week forecast the team made on 7 Aug 2026, to compare with what really happened
Run after generate_data.py:  python scripts/make_forecast_inputs.py
"""
import csv, json, random
from datetime import date, timedelta
from pathlib import Path

random.seed(46)
DATA = Path(__file__).resolve().parent

# ------------------------------------------------------------------ known flows (calendar-driven)
# day: day of month the flow happens (rolled to the next business day), or "last" for the last business day.
# months_factor: seasonality on a given month (13th month salary in France in December, for example).
calendar = [
    # Lumen SA (France)
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "PAYR", "en": "Salaries", "fr": "Salaires", "day": 27, "roll": "prev", "amount": -1_900_000, "months_factor": {"12": 1.5}},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "SOCL", "en": "URSSAF social charges", "fr": "Cotisations URSSAF", "day": 15, "amount": -1_200_000, "months_factor": {"1": 1.5}},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "SOCL", "en": "Pension contributions (AGIRC-ARRCO)", "fr": "Retraite complémentaire (AGIRC-ARRCO)", "day": 15, "amount": -220_000},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "TAXV", "en": "VAT return (CA3)", "fr": "TVA (déclaration CA3)", "day": 24, "amount": -900_000},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "RENT", "en": "Paris office rent", "fr": "Loyer bureaux Paris", "day": 1, "amount": -86_500},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "SUPP", "en": "Energy and telecom direct debits", "fr": "Prélèvements énergie et télécoms", "day": 8, "amount": -50_500},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "ICO", "en": "Payment to Lumen Maroc for products", "fr": "Règlement Lumen Maroc (produits)", "day": 12, "amount": -1_150_000},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "ICO", "en": "Management fee from Lumen Deutschland", "fr": "Management fees Lumen Deutschland", "day": 5, "amount": 120_000},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "ICO", "en": "Brand royalty from Lumen UK", "fr": "Redevance de marque Lumen UK", "day": 20, "amount": 65_000},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "FEES", "en": "Bank fees", "fr": "Frais bancaires", "day": 1, "amount": -1_400},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "TAXC", "en": "Corporate tax instalment", "fr": "Acompte d'impôt sur les sociétés", "dates": ["2026-12-15", "2027-03-16", "2027-06-15", "2027-09-15"], "amount": -1_180_000},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "INTR", "en": "RCF interest (EURIBOR 3M + 1.40% on EUR 6m)", "fr": "Intérêts RCF (Euribor 3M + 1,40 % sur 6 M EUR)", "dates": ["2026-12-31", "2027-03-31", "2027-06-30", "2027-09-30"], "amount": -52_900},
    {"entity": "LUM-FR", "ccy": "EUR", "cat": "FEES", "en": "RCF commitment fee", "fr": "Commission de non-utilisation RCF", "dates": ["2026-12-31", "2027-03-31", "2027-06-30", "2027-09-30"], "amount": -23_800},
    # Lumen Deutschland
    {"entity": "LUM-DE", "ccy": "EUR", "cat": "PAYR", "en": "Salaries (Gehalt)", "fr": "Salaires", "day": 28, "roll": "prev", "amount": -750_000, "months_factor": {"11": 1.6}},
    {"entity": "LUM-DE", "ccy": "EUR", "cat": "SOCL", "en": "Social security (Sozialversicherung)", "fr": "Charges sociales", "day": 26, "roll": "prev", "amount": -345_000},
    {"entity": "LUM-DE", "ccy": "EUR", "cat": "TAXV", "en": "VAT (Umsatzsteuer)", "fr": "TVA", "day": 10, "amount": -290_000},
    {"entity": "LUM-DE", "ccy": "EUR", "cat": "RENT", "en": "Office rent", "fr": "Loyer", "day": 1, "amount": -41_200},
    {"entity": "LUM-DE", "ccy": "EUR", "cat": "ICO", "en": "Management fee to Lumen SA", "fr": "Management fees à Lumen SA", "day": 5, "amount": -120_000},
    {"entity": "LUM-DE", "ccy": "EUR", "cat": "FEES", "en": "Bank fees", "fr": "Frais bancaires", "day": 1, "amount": -130},
    # Lumen UK
    {"entity": "LUM-UK", "ccy": "GBP", "cat": "PAYR", "en": "Salaries", "fr": "Salaires", "day": 25, "roll": "prev", "amount": -420_000},
    {"entity": "LUM-UK", "ccy": "GBP", "cat": "TAXC", "en": "HMRC PAYE", "fr": "HMRC PAYE (prélèvement à la source)", "day": 22, "amount": -182_000},
    {"entity": "LUM-UK", "ccy": "GBP", "cat": "TAXV", "en": "Quarterly VAT return", "fr": "TVA trimestrielle", "dates": ["2027-01-07", "2027-04-07", "2027-07-07", "2027-10-07"], "amount": -250_000},
    {"entity": "LUM-UK", "ccy": "GBP", "cat": "RENT", "en": "Office rent", "fr": "Loyer", "day": 1, "amount": -23_750},
    {"entity": "LUM-UK", "ccy": "GBP", "cat": "ICO", "en": "Brand royalty to Lumen SA (EUR 65,000)", "fr": "Redevance de marque à Lumen SA (65 000 EUR)", "day": 20, "amount": "SPOT:-65000:GBP"},
    {"entity": "LUM-UK", "ccy": "GBP", "cat": "FEES", "en": "Bank fees", "fr": "Frais bancaires", "day": 1, "amount": -120},
    # Lumen Maroc
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "PAYR", "en": "Salaries (paie)", "fr": "Paie", "day": "last", "amount": -3_220_000},
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "SOCL", "en": "CNSS contributions", "fr": "Cotisations CNSS", "day": 10, "amount": -900_000},
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "TAXV", "en": "VAT (DGI)", "fr": "TVA (DGI)", "day": 24, "amount": -1_200_000},
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "RENT", "en": "Plant rent", "fr": "Loyer usine", "day": 1, "amount": -310_000},
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "ICO", "en": "Receipt from Lumen SA for products", "fr": "Encaissement Lumen SA (produits)", "day": 13, "amount": "SPOT:1150000:MAD"},
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "CAPX", "en": "Assembly line 3, final instalment", "fr": "Ligne d'assemblage 3, solde", "dates": ["2027-01-20"], "amount": -1_200_000},
    {"entity": "LUM-MA", "ccy": "MAD", "cat": "FEES", "en": "Bank fees", "fr": "Frais bancaires", "day": 1, "amount": -700},
]

settings = {
    "forecast_start": "2026-11-09",
    "as_of": "2026-11-06",
    "weeks": 13,
    "holidays": ["2026-11-11", "2026-12-25", "2026-12-26", "2027-01-01", "2027-04-05", "2027-05-01", "2027-05-08", "2027-05-13", "2027-05-24", "2027-07-14", "2027-08-15", "2027-11-01", "2027-11-11"],
    # Weekly seasonality on receipts and supplier payments (Christmas slowdown)
    "week_season": {"2026-12-21": 0.85, "2026-12-28": 0.45, "2027-01-04": 0.9},
    # Open supplier invoices are only known 8 weeks ahead; customer invoices up to 13.
    "ap_horizon_weeks": 8,
    "liquidity_policy": {"min_group_cash_eur": 6_000_000, "rcf_commitment_eur": 25_000_000, "rcf_drawn_eur": 6_000_000},
    # 12-month forecast drivers
    "m12": {
        "months": ["2026-11", "2026-12", "2027-01", "2027-02", "2027-03", "2027-04", "2027-05", "2027-06", "2027-07", "2027-08", "2027-09", "2027-10"],
        "activity_growth_pct": 4.0,
        "seasonality": {"11": 1.05, "12": 0.95, "01": 0.85, "02": 0.95, "03": 1.05, "04": 1.0, "05": 1.0, "06": 1.05, "07": 0.95, "08": 0.8, "09": 1.1, "10": 1.1},
        "one_offs": [
            {"month": "2027-05", "cat": "TAXC", "en": "Corporate tax balance (solde d'IS)", "fr": "Solde d'impôt sur les sociétés", "amount_eur": -650_000},
            {"month": "2027-06", "cat": "FIN", "en": "Dividend to shareholders", "fr": "Dividende aux actionnaires", "amount_eur": -3_000_000},
            {"month": "2027-03", "cat": "CAPX", "en": "Warehouse automation, Lyon", "fr": "Automatisation de l'entrepôt de Lyon", "amount_eur": -1_800_000},
        ],
    },
}

# ------------------------------------------------------------------ the forecast made on 7 Aug 2026 (for prévu / réalisé)
fx = {r["date"]: r for r in csv.DictReader(open(DATA / "fx_rates.csv"))}
def eur(amount, ccy, d):
    if ccy == "EUR":
        return amount
    while d not in fx:
        d = (date.fromisoformat(d) - timedelta(days=1)).isoformat()
    return amount / float(fx[d]["EUR" + ccy])

actual = {}
for t in csv.DictReader(open(DATA / "transactions.csv", encoding="utf-8")):
    if t["category_true"] == "POOL":
        continue
    d = date.fromisoformat(t["booking_date"])
    wk = (d - timedelta(days=d.weekday())).isoformat()
    k = (wk, t["entity"], t["category_true"])
    actual[k] = actual.get(k, 0) + eur(float(t["amount"]), t["currency"], t["booking_date"])

# How the August forecast differed from reality, by category:
# receipts were forecast a little too optimistically, supplier payments well, calendar items almost exactly,
# and some one-offs were simply not in the forecast.
noise = {"CUST": (1.05, 0.14), "SUPP": (1.0, 0.08), "PAYR": (1.0, 0.01), "SOCL": (1.0, 0.02), "TAXV": (1.0, 0.06),
         "TAXC": (1.0, 0.0), "RENT": (1.0, 0.0), "FEES": (1.0, 0.15), "ICO": (1.0, 0.04), "INTR": (1.0, 0.0), "FIN": (1.0, 0.0)}
missed = {"CAPX", "FX", "UNC"}   # not forecast at all in August
snap = []
for (wk, ent, cat), a in sorted(actual.items()):
    if cat in missed:
        continue
    if cat == "FIN":
        f = a  # the EUR 2m RCF repayment was planned
    else:
        bias, sd = noise.get(cat, (1.0, 0.1))
        f = a * random.gauss(bias, sd)
    snap.append({"week_start": wk, "entity": ent, "category": cat, "forecast_eur": round(f, 2)})
# timing error: one large customer collection forecast a week early in France
for r in snap:
    if r["week_start"] == "2026-09-14" and r["entity"] == "LUM-FR" and r["category"] == "CUST":
        r["forecast_eur"] = round(r["forecast_eur"] + 650_000, 2)
    if r["week_start"] == "2026-09-21" and r["entity"] == "LUM-FR" and r["category"] == "CUST":
        r["forecast_eur"] = round(r["forecast_eur"] - 650_000, 2)

# intercompany legs in local currency at the 6 Nov spot rate, so they net to zero at group level
spot = fx[settings["as_of"]]
for c in calendar:
    if isinstance(c["amount"], str):
        _, eur_amt, ccy = c["amount"].split(":")
        c["amount"] = round(float(eur_amt) * float(spot["EUR" + ccy]), 2)
(DATA / "forecast_calendar.json").write_text(json.dumps(calendar, indent=1, ensure_ascii=False), encoding="utf-8")
(DATA / "forecast_settings.json").write_text(json.dumps(settings, indent=1, ensure_ascii=False), encoding="utf-8")
with open(DATA / "forecast_snapshot.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["week_start", "entity", "category", "forecast_eur"])
    w.writeheader(); w.writerows(snap)
print(len(calendar), "calendar items,", len(snap), "snapshot rows")
