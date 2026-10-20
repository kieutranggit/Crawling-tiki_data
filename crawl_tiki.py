# Extracting 200000 products
# Stopping by CTRL C

import json, time
from pathlib import Path
import pandas as pd
from curl_cffi import requests

API = "https://api.tiki.vn/product-detail/api/v1/products/{}"
CHUNK = 1000          # 1000ids/file
SLEEP = 1             # rest 1 second between 2 request

OUT = Path("data/products")
ERR = Path("data/errors")
OUT.mkdir(parents=True, exist_ok=True)
ERR.mkdir(parents=True, exist_ok=True)


def extract(p):
    """FROM JSON 59 FIELDS, keepping 6 needed fields"""
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "url_key": p.get("url_key"),
        "price": p.get("price"),
        "description": p.get("description"),  # Keep orginal HTML
        "images_url": [img.get("base_url") for img in (p.get("images") or [])],
    }


def fetch(session, pid, max_tries=5):
    """Return(product, None) if successful, or (None, reason_error)."""
    reason = "unknown"
    for attempt in range(1, max_tries + 1):
        try:
            r = session.get(API.format(pid), timeout=30)
            if r.status_code == 404:
                return None, "404 not found"          # unvalid product
            ctype = r.headers.get("content-type", "")
            if r.status_code == 200 and "json" in ctype:
                return extract(r.json()), None         # Successfull
            reason = f"http {r.status_code}, {ctype[:30]}"   # vd: 200 + text/html = bị chặn
        except Exception as e:
            reason = f"exception: {type(e).__name__}"        
        print(f"  id {pid} lần {attempt}: {reason} -> chờ {30 * attempt}s", flush=True)
        time.sleep(30 * attempt)               # more waitting time 
    return None, reason                         # still error at the end


def main():
    ids = pd.read_excel("products-0-200000.xlsx")["id"].tolist()
    session = requests.Session(impersonate="chrome")   # fingerprinting TLS
    n_chunks = (len(ids) + CHUNK - 1) // CHUNK          # 200 parts

    for i in range(n_chunks):
        out_file = OUT / f"products_{i+1:03d}.json"
        err_file = ERR / f"errors_{i+1:03d}.json"
        if out_file.exists():                  
            continue

        products, errors = [], []
        start = time.time()
        for pid in ids[i * CHUNK:(i + 1) * CHUNK]:
            data, err = fetch(session, pid)
            if data is not None:
                products.append(data)
            else:
                errors.append({"id": pid, "reason": err})
            time.sleep(SLEEP)

        # Extract error list file 1st, products file after:
        err_file.write_text(json.dumps(errors, ensure_ascii=False, indent=1), encoding="utf-8")
        out_file.write_text(json.dumps(products, ensure_ascii=False), encoding="utf-8")
        print(f"Phần {i+1}/{n_chunks}: {len(products)} ok, {len(errors)} lỗi, "
              f"{(time.time() - start) / 60:.1f} phút", flush=True)


if __name__ == "__main__":
    main()