"""32: Delta-Extraktion. UseMod-Bodies sind kumulativ; Marker duerfen nur auf NEUEM Text gezaehlt werden."""
import pandas as pd, pathlib
B = pathlib.Path(__file__).resolve().parent.parent; A = B/"artefakte"
df = pd.read_parquet(A/"schwarm_revisions.parquet").sort_values(["page_key","time","seq"])
out = []
for pk, g in df.groupby("page_key", sort=False):
    prev = set()
    for r in g.itertuples(index=False):
        lines = [l.strip() for l in r.body.split("\n")]
        new = [l for l in lines if l and l not in prev]
        prev.update(l for l in lines if l)
        out.append((r.rev_id, "\n".join(new), len("\n".join(new))))
dl = pd.DataFrame(out, columns=["rev_id","delta","delta_len"])
m = df.merge(dl, on="rev_id", validate="1:1")
m.to_parquet(A/"schwarm_deltas.parquet", index=False)
tot_body = int(m.body_len.sum()); tot_delta = int(m.delta_len.sum())
with open(A/"_audit.log","a") as f:
    f.write(f"32_delta: revs={len(m)} body_bytes={tot_body} delta_bytes={tot_delta} ratio={tot_delta/tot_body:.3f} "
            f"leere_deltas={int((m.delta_len==0).sum())}\n")
print(len(m), tot_body, tot_delta, round(tot_delta/tot_body,3), int((m.delta_len==0).sum()))
