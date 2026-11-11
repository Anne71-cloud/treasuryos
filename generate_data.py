"""
TreasuryOS: synthetic data generator for Groupe Lumen (fictional).

Every figure produced here is invented. Nothing comes from KNR Actions or any real company.
Run:  python scripts/generate_data.py   (writes everything into ./data)
Seeded, so the same data comes out every time.
"""
import csv, json, random, math
from datetime import date, timedelta
from pathlib import Path

random.seed(2026)
OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)

START = date(2026, 8, 10)   # Monday, first day of actuals
END = date(2026, 11, 6)     # Friday, last statement date ("today" in the app)
FIRST_FORECAST_WEEK = date(2026, 11, 9)

# French bank holidays inside the window (TARGET2 / French calendar)
HOLIDAYS = {date(2026, 8, 15), date(2026, 11, 1), date(2026, 11, 11)}

def is_bd(d):
    return d.weekday() < 5 and d not in HOLIDAYS

def bdays(a, b):
    d = a
    while d <= b:
        if is_bd(d):
            yield d
        d += timedelta(days=1)

def roll(d, back=False):
    """Move a date to the next (or previous) business day."""
    step = timedelta(days=-1 if back else 1)
    while not is_bd(d):
        d += step
    return d

# ---------------------------------------------------------------- IBAN helper
def iban(country, bban):
    """Build a valid IBAN (mod-97 check digits) from a country code and BBAN."""
    rearr = bban + country + "00"
    num = "".join(str(int(c, 36)) for c in rearr)
    check = 98 - int(num) % 97
    return f"{country}{check:02d}{bban}"

# ---------------------------------------------------------------- reference data
entities = [
    {"id": "LUM-FR", "name": "Lumen SA", "country": "FR", "city": "Paris", "role": "Holding and French sales",
     "functional_ccy": "EUR", "lei": "969500LUMENFR000SY01"},
    {"id": "LUM-DE", "name": "Lumen Deutschland GmbH", "country": "DE", "city": "Frankfurt am Main", "role": "German sales",
     "functional_ccy": "EUR", "lei": "529900LUMENDE000SY02"},
    {"id": "LUM-UK", "name": "Lumen UK Ltd", "country": "GB", "city": "London", "role": "UK sales",
     "functional_ccy": "GBP", "lei": "213800LUMENUK000SY03"},
    {"id": "LUM-MA", "name": "Lumen Maroc SARL", "country": "MA", "city": "Casablanca", "role": "Assembly plant (buys components in USD)",
     "functional_ccy": "MAD", "lei": "894500LUMENMA000SY04"},
]

banks = [
    {"id": "BNPP", "name": "BNP Paribas", "role": "Lead bank, cash pool header, RCF agent",
     "fees": {"account_maintenance_month": 45, "sepa_ct_out": 0.20, "sepa_ct_in": 0.10, "swift_out": 18.0,
              "ebics_month": 60, "cash_pool_month": 150}},
    {"id": "SOGE", "name": "Société Générale", "role": "Payroll and tax payments in France; Moroccan subsidiary bank",
     "fees": {"account_maintenance_month": 50, "sepa_ct_out": 0.25, "sepa_ct_in": 0.12, "swift_out": 22.0,
              "ebics_month": 55, "cash_pool_month": 0}},
    {"id": "HSBC", "name": "HSBC", "role": "USD collections and UK subsidiary",
     "fees": {"account_maintenance_month": 40, "sepa_ct_out": 0.30, "sepa_ct_in": 0.15, "swift_out": 25.0,
              "ebics_month": 65, "cash_pool_month": 0}},
]
# Market benchmark used later by the bank fee analysis (module 4). Synthetic.
fee_benchmark = {"account_maintenance_month": 40, "sepa_ct_out": 0.18, "sepa_ct_in": 0.08, "swift_out": 15.0,
                 "ebics_month": 50, "cash_pool_month": 120}

accounts = [
    {"id": "FR-BNPP-EUR", "entity": "LUM-FR", "bank": "BNPP", "bic": "BNPAFRPPXXX", "ccy": "EUR",
     "iban": iban("FR", "30004" + "00820" + "00010258741" + "92"), "purpose": "Main operating account, cash pool header (compte centralisateur)",
     "pool": "EUR-ZBA", "pool_role": "header", "opening": 7_650_000.00},
    {"id": "FR-SOGE-EUR", "entity": "LUM-FR", "bank": "SOGE", "bic": "SOGEFRPPXXX", "ccy": "EUR",
     "iban": iban("FR", "30003" + "03620" + "00020147852" + "36"), "purpose": "Payroll, social charges and tax",
     "pool": "EUR-ZBA", "pool_role": "participant", "opening": 0.00},
    {"id": "FR-HSBC-USD", "entity": "LUM-FR", "bank": "HSBC", "bic": "CCFRFRPPXXX", "ccy": "USD",
     "iban": iban("FR", "30056" + "00148" + "01480036521" + "47"), "purpose": "USD collections from US customers",
     "pool": None, "pool_role": None, "opening": 920_000.00},
    {"id": "DE-BNPP-EUR", "entity": "LUM-DE", "bank": "BNPP", "bic": "BNPADEFFXXX", "ccy": "EUR",
     "iban": iban("DE", "51210800" + "0012345678"), "purpose": "German operating account",
     "pool": "EUR-ZBA", "pool_role": "participant", "opening": 0.00},
    {"id": "UK-HSBC-GBP", "entity": "LUM-UK", "bank": "HSBC", "bic": "HBUKGB4BXXX", "ccy": "GBP",
     "iban": iban("GB", "HBUK" + "401276" + "31485972"), "purpose": "UK operating account",
     "pool": None, "pool_role": None, "opening": 780_000.00},
    {"id": "MA-SOGE-MAD", "entity": "LUM-MA", "bank": "SOGE", "bic": "SGMBMAMCXXX", "ccy": "MAD",
     "iban": iban("MA", "022" + "780" + "0001234567890123" + "45"), "purpose": "Moroccan operating account (dirham, exchange controls apply)",
     "pool": None, "pool_role": None, "opening": 6_500_000.00},
]
for a in accounts:
    a["signatories"] = {
        "LUM-FR": ["Claire Moreau (CFO)", "Julien Petit (Group Treasurer)"],
        "LUM-DE": ["Claire Moreau (CFO)", "Anna Weber (Geschäftsführerin)"],
        "LUM-UK": ["Claire Moreau (CFO)", "James Carter (Managing Director)"],
        "LUM-MA": ["Claire Moreau (CFO)", "Youssef Benali (Directeur général)"],
    }[a["entity"]]
    a["signing_rule"] = "Two signatures above EUR 50,000 equivalent"
    a["status"] = "Active"
    a["channel"] = "EBICS T" if a["bank"] != "HSBC" or a["ccy"] == "USD" else "SWIFTNet FileAct"

facility = {
    "id": "RCF-2025",
    "type": "Revolving credit facility (crédit renouvelable), syndicated",
    "borrower": "LUM-FR",
    "commitment_eur": 25_000_000,
    "lenders": [{"bank": "BNPP", "share_pct": 40, "role": "Agent"},
                {"bank": "SOGE", "share_pct": 35, "role": "Lender"},
                {"bank": "HSBC", "share_pct": 25, "role": "Lender"}],
    "signed": "2025-06-30", "maturity": "2030-06-30",
    "margin_pct": 1.40, "reference_rate": "EURIBOR 3M (synthetic 2.05%)", "reference_rate_pct": 2.05,
    "commitment_fee_pct_of_margin": 35,
    "drawn_history": [{"date": "2026-08-07", "drawn_eur": 8_000_000},
                      {"date": "2026-09-30", "drawn_eur": 6_000_000, "note": "EUR 2m repaid"}],
    "covenants": [
        {"name": "Leverage (net debt / EBITDA)", "fr": "Levier (dette nette / EBITDA)", "test": "max", "limit": 3.0},
        {"name": "Interest cover (EBITDA / net interest)", "fr": "Couverture des intérêts (EBITDA / frais financiers nets)", "test": "min", "limit": 4.0},
        {"name": "Minimum liquidity (cash + undrawn RCF), EUR m", "fr": "Liquidité minimale (trésorerie + RCF non tiré), M EUR", "test": "min", "limit": 15.0},
    ],
    # LTM figures by quarter end, EUR m (synthetic)
    "financials_ltm": [
        {"period": "2025-12-31", "ebitda": 18.6, "net_debt": 21.4, "net_interest": 2.9},
        {"period": "2026-03-31", "ebitda": 19.2, "net_debt": 20.1, "net_interest": 2.8},
        {"period": "2026-06-30", "ebitda": 19.9, "net_debt": 17.8, "net_interest": 2.7},
        {"period": "2026-09-30", "ebitda": 20.4, "net_debt": 15.9, "net_interest": 2.6},
    ],
}

categories = [
    # id, English, French, direction, section of the cash flow plan
    ("CUST", "Customer receipts", "Encaissements clients", "in", "Operating"),
    ("SUPP", "Supplier payments", "Décaissements fournisseurs", "out", "Operating"),
    ("PAYR", "Payroll", "Salaires", "out", "Operating"),
    ("SOCL", "Social charges", "Charges sociales", "out", "Operating"),
    ("TAXV", "VAT", "TVA", "both", "Operating"),
    ("TAXC", "Corporate and payroll taxes", "Impôts et taxes", "out", "Operating"),
    ("RENT", "Rent", "Loyers", "out", "Operating"),
    ("FEES", "Bank fees", "Frais bancaires", "out", "Financial"),
    ("INTR", "Interest", "Intérêts", "both", "Financial"),
    ("ICO", "Intercompany", "Flux intragroupe", "both", "Intercompany"),
    ("POOL", "Cash pool sweep", "Équilibrage (centralisation de trésorerie)", "both", "Intercompany"),
    ("FIN", "Financing (debt and equity)", "Financement (dette et capitaux propres)", "both", "Financing"),
    ("CAPX", "Capital expenditure", "Investissements", "out", "Investing"),
    ("FX", "FX conversion", "Opérations de change", "both", "Financial"),
    ("UNC", "Uncategorised", "Non catégorisé", "both", "To review"),
]
categories = [{"id": c[0], "en": c[1], "fr": c[2], "direction": c[3], "section": c[4]} for c in categories]

# ISO 20022 bank transaction codes (Domain-Family-SubFamily)
BTC = {
    "sct_in": "PMNT-RCDT-ESCT", "sct_out": "PMNT-ICDT-ESCT", "xct_in": "PMNT-RCDT-XBCT", "xct_out": "PMNT-ICDT-XBCT",
    "dd_out": "PMNT-IDDT-ESDD", "sal": "PMNT-ICDT-SALA", "fee": "ACMT-MDOP-CHRG", "int": "ACMT-MDOP-INTR",
    "fx": "FORX-SPOT-SPOT", "zba": "CAMT-ACCB-ZABA", "loan": "LDAS-CSLN-PPAY", "tax": "PMNT-ICDT-TAXS",
}

rules = [
    # Evaluated in priority order; first match wins. Fields are matched case-insensitively.
    {"priority": 5, "if_btc": "CAMT-ACCB-ZABA", "category": "POOL", "why": "Zero-balancing sweep code"},
    {"priority": 10, "if_btc": "ACMT-MDOP-CHRG", "category": "FEES", "why": "Bank charge code"},
    {"priority": 11, "if_btc": "ACMT-MDOP-INTR", "category": "INTR", "why": "Interest code"},
    {"priority": 12, "if_btc": "FORX-SPOT-SPOT", "category": "FX", "why": "Spot FX code"},
    {"priority": 13, "if_btc": "LDAS-CSLN-PPAY", "category": "FIN", "why": "Loan principal code"},
    {"priority": 20, "if_text": "RCF", "category": "FIN", "why": "Mentions the revolving facility"},
    {"priority": 21, "if_text": "INTERCO", "category": "ICO", "why": "Group company as counterparty"},
    {"priority": 30, "if_text": "URSSAF|SOZIALVERS|CNSS|AGIRC|RETRAITE|PREVOYANCE", "category": "SOCL", "why": "Social charge collector"},
    {"priority": 31, "if_text": "SALAIRE|GEHALT|SALARY|PAYROLL|\\bPAIE\\b", "category": "PAYR", "why": "Payroll wording"},
    {"priority": 32, "if_btc": "PMNT-ICDT-SALA", "category": "PAYR", "why": "Salary payment code"},
    {"priority": 33, "if_text": "TVA|UMSATZSTEUER|VAT RETURN|HMRC VAT", "category": "TAXV", "why": "VAT authority"},
    {"priority": 34, "if_text": "DGFIP|IMPOT|FINANZAMT|HMRC PAYE|DGI ", "category": "TAXC", "why": "Tax authority"},
    {"priority": 35, "if_text": "LOYER|MIETE|RENT ", "category": "RENT", "why": "Rent wording"},
    {"priority": 36, "if_text": "CAPEX|MACHINE|EQUIPEMENT|INVESTISSEMENT", "category": "CAPX", "why": "Capex wording"},
    {"priority": 50, "if_sign": "+", "if_text": "FACT|INV|RECHNUNG|FACTURE", "category": "CUST", "why": "Incoming payment quoting an invoice"},
    {"priority": 51, "if_sign": "-", "if_btc_family": "ICDT", "category": "SUPP", "why": "Outgoing transfer, default supplier"},
    {"priority": 52, "if_sign": "-", "if_btc_family": "IDDT", "category": "SUPP", "why": "Direct debit, default supplier"},
]

# Counterparties (all fictional)
customers = {
    "LUM-FR": ["Batimax Distribution", "Electra Ouest SAS", "Domotik France", "Habitat Plus Groupe", "Lumi Pro Négoce",
               "Rexa Bâtiment", "Cité Éclairage", "Atelier Nordlys", "Somelec Grand Est", "Vallée Distribution"],
    "LUM-DE": ["Lichtwerk Handel GmbH", "Bauhaus Partner Süd", "Elektro Krämer KG", "Nordlicht Vertrieb GmbH", "Hellmann Projekte AG"],
    "LUM-UK": ["Brightway Wholesale Ltd", "Kingsley Electrical Ltd", "Northern Light Supplies", "Fenwick Build Ltd"],
    "LUM-MA": ["Atlas Électricité SARL", "Maghreb Éclairage", "Sofadis Maroc"],
}
suppliers = {
    "LUM-FR": ["Transports Moreau", "Optiverre Composants", "Cartonnages du Rhône", "Agence Lumen Digital", "Delta Logistique"],
    "LUM-DE": ["Spedition Hartmann", "Kunststoff Becker GmbH", "IT Service Rhein GmbH"],
    "LUM-UK": ["Dawson Freight Ltd", "Pemberton Packaging", "Ashford IT Services"],
    "LUM-MA": ["Casa Logistique", "Plastimaroc", "Shenzhen Brightchip Co"],
}

# ---------------------------------------------------------------- FX rates (synthetic random walk)
fx_mid = {"USD": 1.105, "GBP": 0.862, "MAD": 10.82}   # units of currency per 1 EUR
vol = {"USD": 0.0045, "GBP": 0.0030, "MAD": 0.0020}
fx_rows, fx = [], {}
d = START - timedelta(days=3)
lvl = dict(fx_mid)
while d <= END:
    if is_bd(d) or d < START:
        for c in lvl:
            lvl[c] *= math.exp(random.gauss(0, vol[c]))
        fx[d] = {c: round(v, 4) for c, v in lvl.items()}
        fx_rows.append({"date": d.isoformat(), "EURUSD": fx[d]["USD"], "EURGBP": fx[d]["GBP"], "EURMAD": fx[d]["MAD"]})
    d += timedelta(days=1)

def rate(day, ccy):
    if ccy == "EUR":
        return 1.0
    while day not in fx:
        day -= timedelta(days=1)
    return fx[day][ccy]

# ---------------------------------------------------------------- transactions
txns = []
seq = {"n": 0}
acct = {a["id"]: a for a in accounts}

def add(account_id, booking, amount, cpty, info, btc, cat, value_lag=0, cpty_iban=""):
    seq["n"] += 1
    a = acct[account_id]
    val = booking
    for _ in range(value_lag):
        val = roll(val + timedelta(days=1))
    txns.append({
        "txn_id": f"TX{seq['n']:05d}",
        "account_id": account_id, "entity": a["entity"], "bank": a["bank"], "currency": a["ccy"],
        "booking_date": booking.isoformat(), "value_date": val.isoformat(),
        "amount": round(amount, 2),
        "counterparty": cpty, "counterparty_iban": cpty_iban,
        "remittance_info": info, "bank_txn_code": btc,
        "end_to_end_id": f"E2E-{a['entity'][-2:]}-{seq['n']:06d}",
        "category_true": cat,
    })

def amt(base, spread=0.35):
    return round(base * random.uniform(1 - spread, 1 + spread), -1)

inv_no = {"n": 1040}
def invoice(prefix="FA-2026-"):
    inv_no["n"] += random.randint(1, 4)
    return f"{prefix}{inv_no['n']}"

days = list(bdays(START, END))
month_days = {}
for d in days:
    month_days.setdefault((d.year, d.month), []).append(d)

def nth_bd(y, m, day):
    return roll(date(y, m, day))

def last_bd(y, m):
    return month_days[(y, m)][-1] if (y, m) in month_days else None

for d in days:
    wd = d.weekday()
    # ---- Customer receipts (daily, lumpy)
    for _ in range(random.choice([1, 2, 2, 3])):
        add("FR-BNPP-EUR", d, amt(200_000), random.choice(customers["LUM-FR"]), f"VIR SEPA FACT {invoice()}", BTC["sct_in"], "CUST")
    if random.random() < 0.8:
        add("DE-BNPP-EUR", d, amt(165_000), random.choice(customers["LUM-DE"]), f"RECHNUNG {invoice('RE-26-')}", BTC["sct_in"], "CUST")
    if random.random() < 0.8:
        add("UK-HSBC-GBP", d, amt(95_000), random.choice(customers["LUM-UK"]), f"INV {invoice('UK-INV-')}", BTC["sct_in"], "CUST")
    if random.random() < 0.55:
        add("MA-SOGE-MAD", d, amt(420_000), random.choice(customers["LUM-MA"]), f"REGLEMENT FACTURE {invoice('MA-F-')}", BTC["sct_in"], "CUST")
    # ---- Supplier payments: weekly payment runs (Tuesday FR/DE, Wednesday UK, Thursday MA)
    if wd == 1:
        for s in random.sample(suppliers["LUM-FR"], 4):
            add("FR-BNPP-EUR", d, -amt(170_000), s, f"PAIEMENT FOURNISSEUR {invoice('F-')}", BTC["sct_out"], "SUPP")
        for s in random.sample(suppliers["LUM-DE"], 2):
            add("DE-BNPP-EUR", d, -amt(110_000), s, f"ZAHLUNG LIEFERANT {invoice('L-')}", BTC["sct_out"], "SUPP")
    if wd == 2:
        for s in random.sample(suppliers["LUM-UK"], 2):
            add("UK-HSBC-GBP", d, -amt(70_000), s, f"SUPPLIER PAYMENT {invoice('PO-')}", BTC["sct_out"], "SUPP")
    if wd == 3:
        for s in ["Casa Logistique", "Plastimaroc"]:
            add("MA-SOGE-MAD", d, -amt(380_000), s, f"VIREMENT FOURNISSEUR {invoice('MAF-')}", BTC["sct_out"], "SUPP")
        # USD component purchase paid from the MAD account (bank converts MAD to USD)
        usd = amt(165_000, 0.2)
        add("MA-SOGE-MAD", d, -round(usd * rate(d, "MAD") / rate(d, "USD"), 2), "Shenzhen Brightchip Co",
            f"SWIFT USD {usd:,.0f} COMPONENTS PO {invoice('CN-')}", BTC["xct_out"], "SUPP", value_lag=1)
    # ---- USD collections every other Friday
    if wd == 4 and ((d - START).days // 7) % 2 == 0:
        add("FR-HSBC-USD", d, amt(260_000, 0.2), "Brightline Lighting Inc", f"WIRE INV US-{invoice('')}", BTC["xct_in"], "CUST", value_lag=1)
    # ---- Direct debits (energy, telecom, leasing) in France on the 8th
    if d == nth_bd(d.year, d.month, 8):
        add("FR-BNPP-EUR", d, -amt(38_000, 0.1), "EDF Entreprises", "PRLV SEPA ENERGIE", BTC["dd_out"], "SUPP")
        add("FR-BNPP-EUR", d, -amt(12_500, 0.1), "Orange Business", "PRLV SEPA TELECOM", BTC["dd_out"], "SUPP")

for (y, m), mds in month_days.items():
    first, last = mds[0], mds[-1]
    def on(day):
        dd = nth_bd(y, m, day)
        return dd if START <= dd <= END else None
    # Rent on the 1st business day
    if first.day <= 3:
        add("FR-BNPP-EUR", first, -86_500.00, "SCI Haussmann Bureaux", f"LOYER {m:02d}/{y} BUREAUX PARIS 9", BTC["sct_out"], "RENT")
        add("DE-BNPP-EUR", first, -41_200.00, "Mainzer Immobilien GmbH", f"MIETE {m:02d}/{y} BUERO", BTC["sct_out"], "RENT")
        add("UK-HSBC-GBP", first, -23_750.00, "Holborn Estates Ltd", f"RENT {m:02d}/{y} OFFICE", BTC["sct_out"], "RENT")
        add("MA-SOGE-MAD", first, -310_000.00, "Zone Industrielle Ain Sebaa", f"LOYER USINE {m:02d}/{y}", BTC["sct_out"], "RENT")
    # Bank fees on the 1st business day (previous month)
    for a in accounts:
        if first.day <= 3:
            b = next(x for x in banks if x["id"] == a["bank"])["fees"]
            base_eur = b["account_maintenance_month"] + b["ebics_month"] + b["cash_pool_month"] * (a["pool_role"] == "header")
            vol_eur = {"FR-BNPP-EUR": 60 * b["sepa_ct_in"] + 18 * b["sepa_ct_out"] + 4 * b["swift_out"],
                       "FR-SOGE-EUR": 120 * b["sepa_ct_out"] + 2 * b["swift_out"],
                       "FR-HSBC-USD": 6 * b["swift_out"] + 35,
                       "DE-BNPP-EUR": 25 * b["sepa_ct_in"] + 10 * b["sepa_ct_out"],
                       "UK-HSBC-GBP": 28 * b["sepa_ct_in"] + 10 * b["sepa_ct_out"] + 2 * b["swift_out"],
                       "MA-SOGE-MAD": 15 * b["swift_out"] + 40}[a["id"]]
            fee = -(base_eur + vol_eur) * rate(first, a["ccy"]) * random.uniform(0.95, 1.08)
            add(a["id"], first, round(fee, 2), next(x for x in banks if x["id"] == a["bank"])["name"],
                f"FRAIS BANCAIRES / COMMISSIONS {m-1 if m > 1 else 12:02d}/{y}", BTC["fee"], "FEES")
    # Management fee DE -> FR on the 5th
    d5 = on(5)
    if d5:
        add("DE-BNPP-EUR", d5, -120_000.00, "Lumen SA", f"INTERCO MANAGEMENT FEE {m:02d}/{y}", BTC["sct_out"], "ICO")
        add("FR-BNPP-EUR", d5, 120_000.00, "Lumen Deutschland GmbH", f"INTERCO MANAGEMENT FEE {m:02d}/{y}", BTC["sct_in"], "ICO")
    # FR pays Lumen Maroc for assembled products on the 12th (EUR leaves FR, MAD arrives in MA)
    d12 = on(12)
    if d12:
        eur = round(random.uniform(1_050_000, 1_250_000), -3)
        add("FR-BNPP-EUR", d12, -eur, "Lumen Maroc SARL", f"INTERCO FACTURE PRODUITS {m:02d}/{y}", BTC["xct_out"], "ICO")
        add("MA-SOGE-MAD", roll(d12 + timedelta(days=1)), round(eur * rate(d12, "MAD") * 0.997, 2), "Lumen SA",
            f"INTERCO REGLEMENT PRODUITS EUR {eur:,.0f}", BTC["xct_in"], "ICO")
    # UK pays brand royalty to FR on the 20th, in EUR bought from GBP
    d20 = on(20)
    if d20:
        eur = 65_000.00
        add("UK-HSBC-GBP", d20, -round(eur * rate(d20, "GBP"), 2), "Lumen SA", f"INTERCO ROYALTY {m:02d}/{y} EUR 65,000", BTC["xct_out"], "ICO")
        add("FR-BNPP-EUR", d20, eur, "Lumen UK Ltd", f"INTERCO ROYALTY {m:02d}/{y}", BTC["xct_in"], "ICO")
    # Payroll
    d27 = on(27) if on(27) else None
    if d27:
        add("FR-SOGE-EUR", d27, -round(random.uniform(1.86e6, 1.94e6), 2), "Salariés Lumen SA", f"SALAIRES {m:02d}/{y} VIREMENTS GROUPES", BTC["sal"], "PAYR")
    d28 = on(28)
    if d28:
        add("DE-BNPP-EUR", d28, -round(random.uniform(7.3e5, 7.7e5), 2), "Mitarbeiter Lumen DE", f"GEHALT {m:02d}/{y}", BTC["sal"], "PAYR")
        add("DE-BNPP-EUR", roll(d28 - timedelta(days=2), back=True), -round(random.uniform(3.3e5, 3.6e5), 2),
            "Techniker Krankenkasse", f"SOZIALVERSICHERUNG BEITRAEGE {m:02d}/{y}", BTC["dd_out"], "SOCL")
    d25 = on(25)
    if d25:
        add("UK-HSBC-GBP", d25, -round(random.uniform(4.1e5, 4.3e5), 2), "Lumen UK staff", f"SALARY {m:02d}/{y} BACS", BTC["sal"], "PAYR")
    if last >= date(y, m, 26):
        add("MA-SOGE-MAD", last, -round(random.uniform(3.15e6, 3.3e6), 2), "Personnel Lumen Maroc", f"PAIE {m:02d}/{y}", BTC["sal"], "PAYR")
    # Social charges and taxes
    d15 = on(15)
    if d15:
        add("FR-SOGE-EUR", d15, -round(random.uniform(1.15e6, 1.25e6), 2), "URSSAF Ile-de-France", f"URSSAF DSN {m-1 if m > 1 else 12:02d}/{y}", BTC["dd_out"], "SOCL")
        add("FR-SOGE-EUR", d15, -round(random.uniform(2.1e5, 2.3e5), 2), "AGIRC-ARRCO Retraite", "RETRAITE COMPLEMENTAIRE", BTC["dd_out"], "SOCL")
    d10 = on(10)
    if d10:
        add("DE-BNPP-EUR", d10, -round(random.uniform(2.6e5, 3.2e5), 2), "Finanzamt Frankfurt", f"UMSATZSTEUER VORANMELDUNG {m-1:02d}/{y}", BTC["tax"], "TAXV")
        add("MA-SOGE-MAD", d10, -round(random.uniform(8.5e5, 9.5e5), 2), "CNSS Casablanca", f"CNSS COTISATIONS {m-1:02d}/{y}", BTC["dd_out"], "SOCL")
    d24 = on(24)
    if d24:
        add("FR-SOGE-EUR", d24, -round(random.uniform(8.4e5, 9.6e5), 2), "DGFIP SIE Paris 9", f"TVA CA3 {m-1:02d}/{y}", BTC["tax"], "TAXV")
        add("MA-SOGE-MAD", d24, -round(random.uniform(1.1e6, 1.3e6), 2), "DGI Casablanca", f"DGI TVA {m-1:02d}/{y}", BTC["tax"], "TAXV")
    d22 = on(22)
    if d22:
        add("UK-HSBC-GBP", d22, -round(random.uniform(1.75e5, 1.9e5), 2), "HMRC", f"HMRC PAYE {m-1:02d}/{y}", BTC["tax"], "TAXC")

# One-offs
add("FR-SOGE-EUR", date(2026, 9, 15), -1_180_000.00, "DGFIP SIE Paris 9", "IMPOT SOCIETES ACOMPTE 3", BTC["tax"], "TAXC")
add("UK-HSBC-GBP", date(2026, 10, 7), -248_600.00, "HMRC", "HMRC VAT RETURN Q3", BTC["tax"], "TAXV")
add("FR-BNPP-EUR", date(2026, 9, 30), -2_000_000.00, "BNP Paribas (Agent)", "RCF-2025 REMBOURSEMENT PARTIEL", BTC["loan"], "FIN")
add("FR-BNPP-EUR", date(2026, 9, 30), -round(8e6 * (2.05 + 1.40) / 100 * 91 / 360, 2), "BNP Paribas (Agent)", "RCF-2025 INTERETS T3", BTC["int"], "INTR")
add("FR-BNPP-EUR", date(2026, 9, 30), -round(17e6 * 1.40 * 0.35 / 100 * 91 / 360, 2), "BNP Paribas (Agent)", "RCF-2025 COMMISSION DE NON-UTILISATION T3", BTC["fee"], "FEES")
add("MA-SOGE-MAD", date(2026, 10, 14), -2_450_000.00, "Atlas Machines Industrielles", "CAPEX MACHINE ASSEMBLAGE LIGNE 3", BTC["sct_out"], "CAPX")
add("FR-HSBC-USD", date(2026, 10, 16), -600_000.00, "HSBC Continental Europe", "SPOT USD/EUR VENTE USD 600,000", BTC["fx"], "FX")
add("FR-BNPP-EUR", date(2026, 10, 16), round(600_000 / rate(date(2026, 10, 16), "USD"), 2), "HSBC Continental Europe", "SPOT USD/EUR ACHAT EUR", BTC["fx"], "FX")
# A few "difficult" lines that the rules will not catch (to show the review queue)
add("FR-BNPP-EUR", date(2026, 10, 21), -4_380.00, "M. Dupont Remi", "REMBT NOTE DE FRAIS SEPT", BTC["sct_out"], "SUPP")
add("FR-BNPP-EUR", date(2026, 9, 3), 18_250.00, "Assurances Mutuelles Pro", "INDEMNITE SINISTRE 2026-0412", BTC["sct_in"], "CUST")
add("UK-HSBC-GBP", date(2026, 10, 29), 3_120.00, "HMRC", "HMRC REPAYMENT", BTC["sct_in"], "TAXC")

txns.sort(key=lambda t: (t["booking_date"], t["account_id"], t["txn_id"]))

# ---------------------------------------------------------------- balances + end-of-day zero balancing
# Each evening the bank sweeps every participant account of the EUR pool back to zero:
# a surplus goes up to the header account, a shortfall is funded from it.
bal = {a["id"]: a["opening"] for a in accounts}
min_bal = dict(bal)
daily = []
by_day = {}
for t in txns:
    by_day.setdefault(t["booking_date"], []).append(t)
header = next(a["id"] for a in accounts if a["pool_role"] == "header")
participants = [a["id"] for a in accounts if a["pool_role"] == "participant"]
for d in days:
    for t in by_day.get(d.isoformat(), []):
        bal[t["account_id"]] += t["amount"]
    for p in participants:
        sweep = round(-bal[p], 2)
        if abs(sweep) < 0.01:
            continue
        pe = acct[p]["entity"]
        add(p, d, sweep, "ZBA sweep to header" if sweep < 0 else "ZBA funding from header",
            f"EQUILIBRAGE ZBA EUR-ZBA {'REMONTEE' if sweep < 0 else 'DESCENTE'} {pe}", BTC["zba"], "POOL")
        add(header, d, -sweep, f"ZBA {p}", f"EQUILIBRAGE ZBA EUR-ZBA {'REMONTEE' if sweep < 0 else 'DESCENTE'} {p}", BTC["zba"], "POOL")
        bal[p] += sweep
        bal[header] -= sweep
    for a in accounts:
        min_bal[a["id"]] = min(min_bal[a["id"]], bal[a["id"]])
        daily.append({"date": d.isoformat(), "account_id": a["id"], "currency": a["ccy"],
                      "closing_balance": round(bal[a["id"]], 2),
                      "closing_balance_eur": round(bal[a["id"]] / rate(d, a["ccy"]), 2)})
txns.sort(key=lambda t: (t["booking_date"], t["account_id"], t["txn_id"]))

# ---------------------------------------------------------------- open items for the forecast (module 2)
ar, ap = [], []
for e, names in customers.items():
    ccy = {"LUM-FR": "EUR", "LUM-DE": "EUR", "LUM-UK": "GBP", "LUM-MA": "MAD"}[e]
    weekly = {"LUM-FR": 1_650_000, "LUM-DE": 330_000, "LUM-UK": 205_000, "LUM-MA": 1_200_000}[e]
    for w in range(13):
        wk = FIRST_FORECAST_WEEK + timedelta(weeks=w)
        remaining = weekly * random.uniform(0.85, 1.15) * (1 - 0.06 * w if w < 8 else 0.5)  # less is invoiced far out
        while remaining > 0:
            inv = min(remaining, random.uniform(40_000, 220_000) * (10 if ccy == "MAD" else 1))
            due = wk + timedelta(days=random.randint(0, 4))
            ar.append({"entity": e, "customer": random.choice(names), "invoice": invoice("AR-"),
                       "currency": ccy, "amount": round(inv, 2), "due_date": due.isoformat(),
                       "probability_pct": random.choice([100, 100, 95, 90, 80])})
            remaining -= inv
    if e == "LUM-FR":
        for w in range(0, 13, 2):
            ar.append({"entity": e, "customer": "Brightline Lighting Inc", "invoice": invoice("US-"), "currency": "USD",
                       "amount": round(random.uniform(230_000, 290_000), 2),
                       "due_date": (FIRST_FORECAST_WEEK + timedelta(weeks=w, days=4)).isoformat(), "probability_pct": 95})
for e, names in suppliers.items():
    ccy = {"LUM-FR": "EUR", "LUM-DE": "EUR", "LUM-UK": "GBP", "LUM-MA": "MAD"}[e]
    weekly = {"LUM-FR": 700_000, "LUM-DE": 300_000, "LUM-UK": 190_000, "LUM-MA": 760_000}[e]
    for w in range(8):
        wk = FIRST_FORECAST_WEEK + timedelta(weeks=w)
        for n in names:
            if n == "Shenzhen Brightchip Co":
                ap.append({"entity": e, "supplier": n, "invoice": invoice("CN-"), "currency": "USD",
                           "amount": round(random.uniform(140_000, 190_000), 2), "due_date": (wk + timedelta(days=3)).isoformat()})
                continue
            ap.append({"entity": e, "supplier": n, "invoice": invoice("AP-"), "currency": ccy,
                       "amount": round(weekly / len(names) * random.uniform(0.7, 1.3), 2),
                       "due_date": (wk + timedelta(days=1)).isoformat()})

# ---------------------------------------------------------------- write files
def jdump(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def cdump(name, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

jdump("entities.json", entities)
jdump("banks.json", {"banks": banks, "fee_benchmark": fee_benchmark})
jdump("accounts.json", accounts)
jdump("facility.json", facility)
jdump("categories.json", categories)
jdump("rules.json", rules)
jdump("counterparties.json", {"customers": customers, "suppliers": suppliers})
cdump("fx_rates.csv", fx_rows)
cdump("transactions.csv", txns)
cdump("daily_balances.csv", daily)
cdump("open_receivables.csv", ar)
cdump("open_payables.csv", ap)

print(f"{len(txns)} transactions, {len(ar)} receivables, {len(ap)} payables")
for a in accounts:
    print(f"{a['id']:13s} {a['ccy']}  open {a['opening']:>14,.0f}  close {bal[a['id']]:>14,.0f}  min {min_bal[a['id']]:>14,.0f}")
tot = sum(bal[a['id']] / rate(END, a['ccy']) for a in accounts)
print(f"Group cash at {END}: EUR {tot:,.0f}")
