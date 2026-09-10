"""30: revisions.jsonl -> parquet (schlanke Spalten) fuer alle 3x_-Skripte."""
import json, pandas as pd, pathlib
B = pathlib.Path(__file__).resolve().parent.parent
rows = []
for l in open(B/"data/revisions.jsonl"):
    d = json.loads(l)
    rows.append({k: d.get(k) for k in
        ("rev_id","page_key","wiki","name","seq","body","body_len","label","ip16","time","change_summary")})
df = pd.DataFrame(rows)
df["time"] = pd.to_datetime(df["time"], utc=True)
df = df.sort_values("time").reset_index(drop=True)
df["body"] = df["body"].fillna("")
df.to_parquet(B/"artefakte/schwarm_revisions.parquet", index=False)
with open(B/"artefakte/_audit.log","a") as f:
    f.write(f"30_load: raw={len(rows)} parquet={len(df)} span={df.time.min()}..{df.time.max()}\n")
print(len(df), df.time.min(), df.time.max())
