"""
TreasuryOS: turn the synthetic transactions into real bank statement files.

- camt.053.001.08 (ISO 20022 XML, end-of-day statement) for the BNP Paribas and Société Générale accounts
- MT940 (SWIFT, older text format) for the two HSBC accounts

One file per account, one statement per business day. Everything is synthetic (Groupe Lumen is fictional).
Run after generate_data.py:  python scripts/make_statements.py
"""
import csv, json
from datetime import date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
DATA = OUT = ROOT
OUT.mkdir(exist_ok=True)

accounts = json.loads((DATA / "accounts.json").read_text(encoding="utf-8"))
txns = list(csv.DictReader(open(DATA / "transactions.csv", encoding="utf-8")))
days = sorted({r["date"] for r in csv.DictReader(open(DATA / "daily_balances.csv", encoding="utf-8"))})

MT940_ACCOUNTS = {"FR-HSBC-USD", "UK-HSBC-GBP"}
SWIFT_TYPE = {"ACMT-MDOP-CHRG": "NCHG", "ACMT-MDOP-INTR": "NINT", "FORX-SPOT-SPOT": "NFEX",
              "LDAS-CSLN-PPAY": "NLDP", "CAMT-ACCB-ZABA": "NSWP"}

def fmt_xml_amt(x):
    return f"{abs(x):.2f}"

def fmt_mt_amt(x):
    return f"{abs(x):.2f}".replace(".", ",")

def by_account_day(acc_id):
    out = {}
    for t in txns:
        if t["account_id"] == acc_id:
            out.setdefault(t["booking_date"], []).append(t)
    return out

# ------------------------------------------------------------------ camt.053
def camt053(acc):
    lines = by_account_day(acc["id"])
    bal = acc["opening"]
    stmts = []
    for n, d in enumerate(days, start=1):
        rows = lines.get(d, [])
        opening = bal
        cr = [float(t["amount"]) for t in rows if float(t["amount"]) > 0]
        db = [float(t["amount"]) for t in rows if float(t["amount"]) < 0]
        bal = round(opening + sum(cr) + sum(db), 2)
        entries = []
        for i, t in enumerate(rows, start=1):
            a = float(t["amount"])
            dom, fam, sub = t["bank_txn_code"].split("-")
            party = "Dbtr" if a > 0 else "Cdtr"
            entries.append(f"""      <Ntry>
        <NtryRef>{i}</NtryRef>
        <Amt Ccy="{acc['ccy']}">{fmt_xml_amt(a)}</Amt>
        <CdtDbtInd>{'CRDT' if a > 0 else 'DBIT'}</CdtDbtInd>
        <Sts><Cd>BOOK</Cd></Sts>
        <BookgDt><Dt>{t['booking_date']}</Dt></BookgDt>
        <ValDt><Dt>{t['value_date']}</Dt></ValDt>
        <AcctSvcrRef>{acc['bank']}{t['txn_id'][2:]}{d.replace('-', '')}</AcctSvcrRef>
        <BkTxCd><Domn><Cd>{dom}</Cd><Fmly><Cd>{fam}</Cd><SubFmlyCd>{sub}</SubFmlyCd></Fmly></Domn></BkTxCd>
        <NtryDtls><TxDtls>
          <Refs><EndToEndId>{t['end_to_end_id']}</EndToEndId></Refs>
          <RltdPties><{party}><Pty><Nm>{escape(t['counterparty'])}</Nm></Pty></{party}></RltdPties>
          <RmtInf><Ustrd>{escape(t['remittance_info'])}</Ustrd></RmtInf>
        </TxDtls></NtryDtls>
      </Ntry>""")
        created = f"{d}T20:15:00+01:00"
        stmts.append(f"""    <Stmt>
      <Id>{acc['id']}-{d.replace('-', '')}</Id>
      <ElctrncSeqNb>{n}</ElctrncSeqNb>
      <CreDtTm>{created}</CreDtTm>
      <Acct>
        <Id><IBAN>{acc['iban']}</IBAN></Id>
        <Ccy>{acc['ccy']}</Ccy>
        <Ownr><Nm>{escape(acc['owner_name'])}</Nm></Ownr>
        <Svcr><FinInstnId><BICFI>{acc['bic']}</BICFI></FinInstnId></Svcr>
      </Acct>
      <Bal>
        <Tp><CdOrPrtry><Cd>OPBD</Cd></CdOrPrtry></Tp>
        <Amt Ccy="{acc['ccy']}">{fmt_xml_amt(opening)}</Amt>
        <CdtDbtInd>{'CRDT' if opening >= 0 else 'DBIT'}</CdtDbtInd>
        <Dt><Dt>{d}</Dt></Dt>
      </Bal>
      <Bal>
        <Tp><CdOrPrtry><Cd>CLBD</Cd></CdOrPrtry></Tp>
        <Amt Ccy="{acc['ccy']}">{fmt_xml_amt(bal)}</Amt>
        <CdtDbtInd>{'CRDT' if bal >= 0 else 'DBIT'}</CdtDbtInd>
        <Dt><Dt>{d}</Dt></Dt>
      </Bal>
      <TxsSummry>
        <TtlNtries><NbOfNtries>{len(rows)}</NbOfNtries></TtlNtries>
        <TtlCdtNtries><NbOfNtries>{len(cr)}</NbOfNtries><Sum>{sum(cr):.2f}</Sum></TtlCdtNtries>
        <TtlDbtNtries><NbOfNtries>{len(db)}</NbOfNtries><Sum>{-sum(db):.2f}</Sum></TtlDbtNtries>
      </TxsSummry>
{chr(10).join(entries)}
    </Stmt>""")
    msg_id = f"CAMT053-{acc['id']}-{days[-1].replace('-', '')}"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Synthetic statement for the fictional Groupe Lumen. Built by TreasuryOS. -->
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
  <BkToCstmrStmt>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{days[-1]}T20:30:00+01:00</CreDtTm>
    </GrpHdr>
{chr(10).join(stmts)}
  </BkToCstmrStmt>
</Document>
"""

# ------------------------------------------------------------------ MT940
def wrap86(text):
    """Field 86 is at most 6 lines of 65 characters."""
    text = text[:390]
    return [text[i:i + 65] for i in range(0, len(text), 65)]

def mt940(acc):
    lines = by_account_day(acc["id"])
    bal = acc["opening"]
    out = []
    for n, d in enumerate(days, start=1):
        rows = lines.get(d, [])
        dd = date.fromisoformat(d)
        yymmdd = dd.strftime("%y%m%d")
        opening = bal
        out += [f":20:STMT{d.replace('-', '')}",
                f":25:{acc['bic'][:8]}/{acc['iban']}",
                f":28C:{n:05d}/1",
                f":60F:{'C' if opening >= 0 else 'D'}{yymmdd}{acc['ccy']}{fmt_mt_amt(opening)}"]
        for t in rows:
            a = float(t["amount"])
            vd = date.fromisoformat(t["value_date"])
            ttype = SWIFT_TYPE.get(t["bank_txn_code"], "NTRF")
            custref = t["end_to_end_id"][-16:]
            bankref = f"HSBC{t['txn_id'][2:]}"
            # :61: value date (YYMMDD) + entry date (MMDD) + C/D + amount + type + references
            out.append(f":61:{vd.strftime('%y%m%d')}{dd.strftime('%m%d')}{'C' if a > 0 else 'D'}{fmt_mt_amt(a)}{ttype}{custref}//{bankref}")
            info = f"/NAME/{t['counterparty']}/REMI/{t['remittance_info']}/BTC/{t['bank_txn_code']}/EREF/{t['end_to_end_id']}"
            l86 = wrap86(info)
            out.append(":86:" + l86[0])
            out += l86[1:]
        bal = round(opening + sum(float(t["amount"]) for t in rows), 2)
        out += [f":62F:{'C' if bal >= 0 else 'D'}{yymmdd}{acc['ccy']}{fmt_mt_amt(bal)}",
                f":64:{'C' if bal >= 0 else 'D'}{yymmdd}{acc['ccy']}{fmt_mt_amt(bal)}",
                "-"]
    return "\r\n".join(out) + "\r\n"

entity_names = {e["id"]: e["name"] for e in json.loads((DATA / "entities.json").read_text(encoding="utf-8"))}
files = []
for acc in accounts:
    acc["owner_name"] = entity_names[acc["entity"]]
    if acc["id"] in MT940_ACCOUNTS:
        name = f"mt940_{acc['id']}.sta"
        (OUT / name).write_text(mt940(acc), encoding="utf-8", newline="")
        fmt = "MT940"
    else:
        name = f"camt053_{acc['id']}.xml"
        (OUT / name).write_text(camt053(acc), encoding="utf-8")
        fmt = "camt.053.001.08"
    files.append({"file": name, "format": fmt, "account_id": acc["id"], "bank": acc["bank"]})
(OUT / "manifest.json").write_text(json.dumps(files, indent=2), encoding="utf-8")
for f in files:
    print(f"{f['file']:32s} {f['format']:16s} {(OUT / f['file']).stat().st_size/1024:7.1f} KB")
