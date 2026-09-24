import json
import os
import pandas as pd

D = "data"


def load_json(name, default):
    p = os.path.join(D, name)
    if os.path.exists(p):
        with open(p) as fh:
            return json.load(fh)
    return default


def save_json(name, obj):
    os.makedirs(D, exist_ok=True)
    with open(os.path.join(D, name), "w") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, default=str)


def load_log():
    p = os.path.join(D, "signals_log.csv")
    return pd.read_csv(p, dtype={"date": str}) if os.path.exists(p) else pd.DataFrame()


def save_log(log):
    os.makedirs(D, exist_ok=True)
    keep = sorted(log["date"].unique())[-400:]
    log[log["date"].isin(keep)].to_csv(os.path.join(D, "signals_log.csv"), index=False)
