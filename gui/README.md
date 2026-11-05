# Settler GUI

A client-side Python (Pyodide) front end for [`settle_expenses.py`](../settle_expenses.py).
The settlement engine is loaded unchanged from the repository root at runtime.

## Files

- `index.html` — page and Pyodide loader
- `style.css` — responsive UI
- `app.js` — UI, CSV import/export, and Python bridge

## Run locally

Opening `index.html` directly as a `file://` URL will usually fail because the browser
blocks `fetch()` of the Python source. Serve the repository over HTTP instead.

From the repository root:

```bash
python -m http.server 8000
```

Then open:

<http://localhost:8000/gui/>

No Python packages need to be installed. The browser downloads Pyodide from its CDN
on first load, then fetches `../settle_expenses.py` from this repository.

## GitHub Pages

If Pages publishes the repository root, the GUI is available at:

`https://<username>.github.io/<repository>/gui/`

The relative `../settle_expenses.py` URL works for project Pages as well as local
HTTP serving. Ensure the root Python file is included in the published branch.

## Behaviour / assumptions

- Amounts are entered in GBP, converted to integer pence, and passed to Python.
- Each expense has one payer and a semicolon/comma-separated participant list.
- Payer need not be a participant, consistent with `spec.md`.
- Settlement method selector supports `auto`, `exact`, and `heuristic`.
- `auto` uses the same `_EXACT_THRESHOLD = 18` behaviour as the core.
- CSV import/export uses `case_id,payer,amount,participants`; amount is integer pence.
- Description is UI-only because it is not part of the existing core CSV schema.
- Expense data is held in JavaScript memory only; refreshing the tab clears it.
- No backend, analytics, account, or persistent storage is used.

## Browser requirements

Modern browser with WebAssembly support and access to the Pyodide CDN and repository
file. Internet access is needed for initial Pyodide loading.
