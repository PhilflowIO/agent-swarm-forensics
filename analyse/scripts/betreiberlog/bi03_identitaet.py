#!/usr/bin/env python3
"""bi03 — Name x IP x Zeit aus den normalisierten Betreiberlogs.

Aufruf:
  analyse/.venv/bin/python analyse/scripts/betreiberlog/bi03_identitaet.py 2604 2605 2606 2607

Liest analyse/data/betreiberlogs/normalisiert/bi_<monat>.tsv.gz (aus bi01)
und schreibt nach analyse/artefakte/betreiberlog_identitaet/:
  bi03_monatsuebersicht.csv     je Monat: Requests, IPs, Namen, Kind-Verteilung
  bi03_name_ip_<monat>.csv      je Name: Requests, IPs, /16, Zeitspanne, Kinds
  bi03_ip_name_<monat>.csv      je IP:   Requests, Namen, Zeitspanne
  bi03_netzbloecke_<monat>.csv  je /16:  Requests, IPs, Namen, Provider (WHOIS-Join)
"""
import csv, collections, gzip, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NORM = os.path.join(BASE, "data", "betreiberlogs", "normalisiert")
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")
os.makedirs(ART, exist_ok=True)

WHOIS = {}
wp = os.path.join(BASE, "artefakte", "paper_netzblock_whois.csv")
if os.path.exists(wp):
    for r in csv.DictReader(open(wp, encoding="utf-8")):
        WHOIS[r["ip16"]] = r["anbieter"]


def monat(m):
    f = gzip.open(os.path.join(NORM, f"bi_{m}.tsv.gz"), "rt", encoding="utf-8")
    rd = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    name_ips   = collections.defaultdict(set)
    name_16    = collections.defaultdict(set)
    name_n     = collections.Counter()
    name_t0    = {}
    name_t1    = {}
    name_kind  = collections.defaultdict(collections.Counter)
    ip_names   = collections.defaultdict(set)
    ip_n       = collections.Counter()
    ip_t0, ip_t1 = {}, {}
    b16_n      = collections.Counter()
    b16_ips    = collections.defaultdict(set)
    b16_names  = collections.defaultdict(set)
    kinds      = collections.Counter()
    rows = 0; benannt = 0; ips = set()
    for r in rd:
        rows += 1
        ts = int(r["ts"]); ip = r["ip"]; nm = r["name"]; k = r["kind"]
        kinds[k] += 1
        ips.add(ip)
        b = ".".join(ip.split(".")[:2])
        b16_n[b] += 1; b16_ips[b].add(ip)
        ip_n[ip] += 1
        if ip not in ip_t0 or ts < ip_t0[ip]: ip_t0[ip] = ts
        if ip not in ip_t1 or ts > ip_t1[ip]: ip_t1[ip] = ts
        if nm:
            benannt += 1
            name_ips[nm].add(ip); name_16[nm].add(b); name_n[nm] += 1
            name_kind[nm][k] += 1
            ip_names[ip].add(nm); b16_names[b].add(nm)
            if nm not in name_t0 or ts < name_t0[nm]: name_t0[nm] = ts
            if nm not in name_t1 or ts > name_t1[nm]: name_t1[nm] = ts
    f.close()

    with open(os.path.join(ART, f"bi03_name_ip_{m}.csv"), "w", newline="", encoding="utf-8") as o:
        w = csv.writer(o); w.writerow(["name", "n_requests", "n_ips", "n_ip16", "t0", "t1",
                                       "spanne_h", "n_save", "n_editform", "n_browse", "n_raw", "n_other"])
        for nm, n in name_n.most_common():
            kk = name_kind[nm]
            w.writerow([nm, n, len(name_ips[nm]), len(name_16[nm]), name_t0[nm], name_t1[nm],
                        round((name_t1[nm] - name_t0[nm]) / 3600, 3),
                        kk["save"], kk["editform"], kk["browse"], kk["raw"],
                        n - kk["save"] - kk["editform"] - kk["browse"] - kk["raw"]])
    with open(os.path.join(ART, f"bi03_ip_name_{m}.csv"), "w", newline="", encoding="utf-8") as o:
        w = csv.writer(o); w.writerow(["ip16", "ip_hash", "n_requests", "n_namen", "t0", "t1", "spanne_h"])
        for ip, n in ip_n.most_common():
            w.writerow([".".join(ip.split(".")[:2]), abs(hash(ip)) % 10**10, n, len(ip_names.get(ip, ())),
                        ip_t0[ip], ip_t1[ip], round((ip_t1[ip] - ip_t0[ip]) / 3600, 3)])
    with open(os.path.join(ART, f"bi03_netzbloecke_{m}.csv"), "w", newline="", encoding="utf-8") as o:
        w = csv.writer(o); w.writerow(["ip16", "anbieter_whois", "n_requests", "n_ips", "n_namen"])
        for b, n in b16_n.most_common():
            w.writerow([b, WHOIS.get(b, ""), n, len(b16_ips[b]), len(b16_names.get(b, ()))])

    mehr = sum(1 for nm in name_ips if len(name_ips[nm]) > 1)
    ipmehr = sum(1 for ip in ip_names if len(ip_names[ip]) > 1)
    return dict(monat=m, requests=rows, mit_name=benannt, namen=len(name_n), ips=len(ips),
                ip16=len(b16_n), namen_mit_mehr_als_1_ip=mehr,
                summe_ips_ueber_namen=sum(len(v) for v in name_ips.values()),
                ips_mit_mehr_als_1_namen=ipmehr,
                requests_je_ip=round(rows / max(len(ips), 1), 3),
                **{f"kind_{k}": v for k, v in kinds.items()})


if __name__ == "__main__":
    res = [monat(m) for m in (sys.argv[1:] or ["2604", "2605", "2606", "2607"])]
    keys = sorted({k for r in res for k in r})
    keys = ["monat"] + [k for k in keys if k != "monat"]
    with open(os.path.join(ART, "bi03_monatsuebersicht.csv"), "w", newline="", encoding="utf-8") as o:
        w = csv.DictWriter(o, fieldnames=keys); w.writeheader()
        for r in res: w.writerow(r)
    for r in res: print(r, flush=True)
