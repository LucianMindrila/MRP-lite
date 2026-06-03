# Syncing MRP-lite between machines

How to move your work between the **work PC**, **home PC**, and the office server
without losing data or getting the two copies out of step.

## The one concept that makes this make sense

- Your **code** travels through **git** (GitHub).
- Your **data does NOT travel as the `mrp.db` file.** The database is deliberately
  kept out of git. Instead, your data travels as **`scripts/db_export.json`** (which
  *is* committed to git) and gets **rebuilt** on the other machine.

So the rule is:

> **"Latest data" on any machine = pull the latest `db_export.json`, then rebuild the
> database from it with `setup_real_data.py`.**

## Before you STOP working on a machine

If you changed any data (added BOMs, edited materials, etc.), push it so the next
machine can pick it up:

```cmd
python scripts/import_boms.py     REM only if you filled in the BOM template
python scripts/export_db.py       REM refresh db_export.json with the latest data
git add -A
git commit -m "Describe what you changed"
git push
```

After this, GitHub has your latest data.

## When you START on another machine

If the repo already exists on that machine:

```cmd
cd <your MRP-lite folder>
git pull
venv\Scripts\activate
pip install -r requirements.txt          REM installs any new dependencies (e.g. openpyxl)
python scripts/setup_real_data.py --force REM rebuild the catalog from the latest snapshot
```

If the repo is NOT on that machine yet (first time):

```cmd
git clone https://github.com/LucianMindrila/MRP-lite.git
cd MRP-lite
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
REM create a .env file in the project root (it is gitignored — copy values from README.md)
python scripts/setup_real_data.py
```

Notes:
- **`pip install -r requirements.txt` is not optional** — if a new library was added
  (like `openpyxl` for the BOM template), the scripts will error without it.
- **`--force`** wipes that machine's old catalog and reloads the current one. It is safe:
  it **refuses** if the machine has live orders/stock, so it can't destroy real work.
  If it ever refuses and you want a guaranteed clean slate, delete `instance\mrp.db`
  on that machine and run `setup_real_data.py` without `--force`.

## The rule that catches people out

**`bom_template.xlsx` does NOT sync through git** — it's a scratch working file, and
it's gitignored. Your filled-in BOMs only become real and portable once you
**import them** (`import_boms.py`) and then **export + commit + push**.

> Simplest habit: do all your template work on **one** machine, import it, push —
> *then* switch machines. If you fill in the template but don't import and push, that
> work stays trapped on that one PC.

To recreate the template on any machine: `python scripts/make_bom_template.py`.

## A note about OneDrive

The working folder currently lives inside OneDrive. If another PC logs into the same
OneDrive account, this folder (including the database and template) *may* appear there
automatically. **Don't rely on it** — OneDrive syncing a live database and a `.git`
folder can cause conflicts or "file in use" errors. Treat **git as the source of
truth** and follow the steps above; let OneDrive be a convenience, not the mechanism.

## TL;DR

**Stopping (if you changed data):** `import_boms.py` (if used) → `export_db.py` →
`git add -A` → `git commit` → `git push`

**Starting elsewhere:** `git pull` → `pip install -r requirements.txt` →
`python scripts/setup_real_data.py --force`
