# Tiki Product Crawler

Download 200,000 products from the Tiki API, keep 6 fields, normalize the product description,
and record every product that could not be downloaded together with the reason.

## Result

| | Count |
|---|---|
| Product ids in the input list | 200,000 |
| Products downloaded | 124,299 |
| Errors (all `404 not found`: the product no longer exists) | 75,701 |
| Check: products + errors | **200,000** (0 duplicates, 0 missing) |

Each product keeps 6 fields: `id`, `name`, `url_key`, `price`, `description`, `images_url`.

## Project structure

```
crawl_tiki.py              download script (run in the terminal)
id_info.ipynb              checks the id list, tests the API, verifies the download
description_clean.ipynb    normalizes the description field
products-0-200000.xlsx     input: list of 200,000 product ids
data/
  products/   products_001.json ... products_200.json   raw download (1,000 ids per file)
  errors/     errors_001.json   ... errors_200.json     failed ids + reason
  clean/      products_001.json ... products_200.json   same products, description normalized
```

### Data download

The data folders are too big for GitHub (about 680 MB), so only one sample file of each folder
is included (`products_001.json`, `errors_001.json`). The full data is on Google Drive:

| File | Content | Size |
|---|---|---|
| [tiki_products_raw.zip](<https://drive.google.com/file/d/13dodYNIV-6C-5cercohJcriPA0DuqWN4/view?usp=drive_link>) | `data/products/`, 200 files, description as raw HTML | 99 MB |
| [tiki_products_clean.zip](<https://drive.google.com/file/d/12GjZI05yLXcFPNsDQLcODiqBlatQ92K1/view?usp=drive_link>) | `data/clean/`, 200 files, description normalized | 75 MB |
| [tiki_errors.zip](<https://drive.google.com/file/d/1qkSejIVINj_R3DpVPeW1t5Ot2y7W_bPq/view?usp=drive_link>) | `data/errors/`, 200 files (failed ids + reason) | 460 KB |

Unzip them inside the project folder: `unzip tiki_products_clean.zip` creates `data/clean/`.

## How it works

### 1. Check the input (`id_info.ipynb`, Part 1)
200,000 ids, 0 empty, 0 duplicates.

### 2. Test the API (`id_info.ipynb`, Part 2)
- The normal `requests` library gets **403**: Tiki recognises Python by its secure (TLS) connection.
  `curl_cffi` with `impersonate="chrome"` (acting like the Chrome browser) solves it.
- Calling with no pause: Tiki blocks us after about 10 requests. When blocked it still answers
  status **200**, but with an HTML page instead of JSON data.
- With a 1 second pause between requests: not blocked.

### 3. Download everything (`crawl_tiki.py`)
- 1 second pause after every request.
- A product is ok only if status is 200 **and** Content-Type is JSON.
- `404` is saved as an error and not retried. Other failures are retried up to 5 times,
  waiting longer each time (30, 60, 90 ... seconds).
- One file per 1,000 ids. If a file already exists, it is skipped, so the script can be
  stopped and started again (resume). The full run took about 3 days.
- Each file is written to a `.tmp` file first and then renamed, so a file is never half written.

### 4. Normalize the description (`description_clean.ipynb`)
The description from the API is HTML. Normalizing means:
- keep only the text a buyer reads, one idea per line (remove HTML tags, CSS, videos);
- decode HTML entities (`&amp;` becomes `&`);
- remove invisible characters (non-breaking space, zero-width space, BOM);
- use one Unicode form for Vietnamese text (NFC);
- remove the sentence "Giá sản phẩm trên Tiki đã bao gồm thuế..." that Tiki adds to every product.

Result: 0 tax sentences left; 1,744 descriptions are empty (the original had only the tax
sentence or only images); 30 products (0.02%) still contain tag-like text written by the shop
or broken HTML from the source. These were accepted and left as they are.

### 5. Verify (`id_info.ipynb`, Part 3)
Products + errors = 200,000, and the ids match the input list exactly.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python crawl_tiki.py            # download (stop with Ctrl+C, run again to continue)
```
Then open `description_clean.ipynb` and run all cells to create `data/clean/`.

## Possible improvements
- Find the shortest safe pause between requests to make the download faster.
- Handle the few descriptions with broken HTML.
