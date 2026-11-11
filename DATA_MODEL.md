# TreasuryOS: data model (modèle de données)

Groupe Lumen is a **fictional** smart-lighting group. Every name, IBAN, amount and rate in this project is synthetic. Nothing comes from a real company.

Actuals run for 13 weeks, from Monday 10 August 2026 to Friday 6 November 2026. The forecast starts on Monday 9 November 2026.

## 1. The group (le groupe)

| Entity | Company | Country | Functional currency | Role |
|---|---|---|---|---|
| LUM-FR | Lumen SA | France (Paris HQ) | EUR | Holding and French sales, borrower under the RCF |
| LUM-DE | Lumen Deutschland GmbH | Germany | EUR | German sales |
| LUM-UK | Lumen UK Ltd | United Kingdom | GBP | UK sales |
| LUM-MA | Lumen Maroc SARL | Morocco | MAD | Assembly plant, buys components in USD |

USD enters the group from a US customer (into Lumen SA) and leaves it through Lumen Maroc's component purchases. That gives the FX module (couverture) something real to work on.

## 2. Banks and accounts (banques et comptes)

| Account | Bank | Currency | IBAN | Use | Cash pool |
|---|---|---|---|---|---|
| FR-BNPP-EUR | BNP Paribas | EUR | FR9330004008200001025874192 | Main operating account | Header (compte centralisateur) |
| FR-SOGE-EUR | Société Générale | EUR | FR1630003036200002014785236 | Payroll, social charges, tax | Participant |
| FR-HSBC-USD | HSBC | USD | FR9830056001480148003652147 | USD collections | Outside the pool |
| DE-BNPP-EUR | BNP Paribas | EUR | DE24512108000012345678 | German operations | Participant |
| UK-HSBC-GBP | HSBC UK | GBP | GB03HBUK40127631485972 | UK operations | Outside the pool |
| MA-SOGE-MAD | Société Générale Maroc | MAD | MA89022780000123456789012345 | Moroccan operations | Outside the pool (exchange controls) |

The IBANs have valid check digits but belong to no real account. Every account has signatories, a two-signature rule above EUR 50,000 and a bank channel (EBICS T or SWIFTNet FileAct).

**Revolving credit facility (crédit renouvelable, RCF):** EUR 25m, syndicated between BNP Paribas (40%, agent), Société Générale (35%) and HSBC (25%). EURIBOR 3M + 1.40%, commitment fee 35% of the margin on the undrawn part. Drawn EUR 8m at the start, EUR 2m repaid on 30 September 2026. Three covenants: leverage at or below 3.0x, interest cover at or above 4.0x, and minimum liquidity of EUR 15m.

## 3. Files (fichiers)

| File | What it holds |
|---|---|
| entities.json | The four companies |
| banks.json | Banks, their fee schedules and a market fee benchmark |
| accounts.json | The six accounts: IBAN, BIC, currency, signatories, channel, pool role, opening balance |
| facility.json | The RCF, its lenders, drawings, covenants and quarterly EBITDA, net debt and interest |
| categories.json | The cash flow categories, in English and French |
| rules.json | Categorisation rules, in priority order |
| counterparties.json | Fictional customers and suppliers |
| fx_rates.csv | Daily EUR/USD, EUR/GBP, EUR/MAD (synthetic) |
| transactions.csv | 665 bank lines across the six accounts |
| daily_balances.csv | Closing balance of each account each business day, in currency and in EUR |
| open_receivables.csv | Customer invoices due in the next 13 weeks (feeds the forecast) |
| open_payables.csv | Supplier invoices due in the next 8 weeks (feeds the forecast) |

One transaction line holds: account, entity, bank, currency, booking date, value date, signed amount, counterparty, remittance text, ISO 20022 bank transaction code, end-to-end ID, and the true category (used only to test the rules).

## 4. Categories (rubriques du plan de trésorerie)

| Code | English | Français |
|---|---|---|
| CUST | Customer receipts | Encaissements clients |
| SUPP | Supplier payments | Décaissements fournisseurs |
| PAYR | Payroll | Salaires |
| SOCL | Social charges | Charges sociales |
| TAXV | VAT | TVA |
| TAXC | Corporate and payroll taxes | Impôts et taxes |
| RENT | Rent | Loyers |
| FEES | Bank fees | Frais bancaires |
| INTR | Interest | Intérêts |
| ICO | Intercompany | Flux intragroupe |
| POOL | Cash pool sweep | Équilibrage (centralisation de trésorerie) |
| FIN | Financing (RCF) | Financement (RCF) |
| CAPX | Capital expenditure | Investissements |
| FX | FX conversion | Opérations de change |
| UNC | Uncategorised, to review | Non catégorisé, à revoir |

The 16 rules categorise 663 of the 665 lines correctly (99.7%). The two lines left over, an insurance payout and an HMRC refund, are planted on purpose so the app can show a review queue, as Kyriba and Agicap do.

## 5. Glossary (lexique), for interviews

| English | Français | In one sentence |
|---|---|---|
| Cash position | Position de trésorerie | How much cash the group holds today, account by account and in total, in one currency. |
| Booking date / value date | Date d'opération / date de valeur | The day the bank records a line, versus the day the money actually counts for balance and interest. |
| Bank statement (end of day) | Relevé de compte (fin de journée) | camt.053 in ISO 20022, MT940 in the older SWIFT format. |
| Bank transaction code | Code opération (BTC) | ISO 20022 code such as PMNT-RCDT-ESCT (a received SEPA transfer), which lets rules categorise lines automatically. |
| Cash flow plan | Plan de trésorerie | The categories that every receipt and payment is sorted into, used for both actuals and forecast. |
| Header account | Compte centralisateur (compte pivot) | The pool account that receives every surplus and funds every shortfall. |
| Zero balancing (ZBA) | Équilibrage à zéro | Each evening the bank brings every participant account back to zero against the header account. |
| Intercompany loan | Prêt / emprunt intragroupe | What a subsidiary is owed by, or owes to, the group because of the sweeps. Interest is charged on it. |
| Revolving credit facility | Crédit renouvelable (RCF) | A credit line the group can draw, repay and redraw up to EUR 25m. |
| Commitment fee | Commission de non-utilisation | What the banks charge on the undrawn part of the facility. |
| Covenant | Covenant (ratio financier) | A ratio the group promises the banks to respect, tested every quarter. |
| Liquidity headroom | Marge de liquidité | Cash plus undrawn facility, minus the minimum buffer. |
| Exchange controls | Réglementation des changes | Morocco restricts dirham transfers abroad, so the MAD account stays out of the cash pool. |

## 6. Regenerate

```
python scripts/generate_data.py
```

The generator is seeded, so it rebuilds the same data every time. It also prints the closing balance of each account and the group total (EUR 12.1m on 6 November 2026).
