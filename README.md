# 🎓 Student Management System

A simple, beginner-friendly web application for managing college student records.
Built with **Python**, **Streamlit**, **SQLite** and **Pandas**.

## Features

| Page | What it does |
|------|--------------|
| 🏠 Dashboard | Welcome banner, total students, students per department (cards + bar chart) |
| ➕ Add Student | Form with validation; duplicate roll numbers are rejected |
| 📋 View Students | Table with filter box, sorting and **Export as CSV** |
| 🔍 Search Student | Search by name or roll number; friendly message if nothing is found |
| ✏️ Update Student | Pick a student, edit the details, save |
| 🗑️ Delete Student | Pick a student, tick a confirmation box, delete |

Also included: automatic database creation, parameterized SQL queries (no SQL injection),
a sidebar button to download a database backup, and 22 automated tests.

## Project files

```
student-management-system/
├── app.py              # The whole application
├── requirements.txt    # Python packages
├── test_students.py    # Automated tests
├── README.md           # This file
├── PROJECT_DOCUMENTATION.md   # Abstract, viva questions, etc.
└── .gitignore          # Files Git should ignore (e.g. *.db)
```

## Run locally

You need **Python 3.9 or newer** ([python.org](https://www.python.org/downloads/)).

```bash
# 1. Go into the project folder
cd student-management-system

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows

# 3. Install packages
pip install -r requirements.txt

# 4. Start the app
streamlit run app.py
```

The app opens at <http://localhost:8501>. A file called `students.db` is created automatically
the first time you run it.

### Run the tests

```bash
python -m unittest test_students -v
```

## Validation rules

- **Name**: required; letters, spaces, `.` `-` `'` only
- **Roll number**: required; letters, digits, `-`, `/`, `_`; stored in UPPER CASE; must be unique (case-insensitive)
- **Email**: required; must look like `name@domain.com`
- **Phone**: required; exactly 10 digits (spaces and dashes are ignored)

---

## Deployment guide (GitHub + Streamlit Community Cloud)

> ⚠️ This project has **not** been deployed by the author of this guide. Follow the steps below
> with your own GitHub and Streamlit accounts.

### Step 1: Create a GitHub repository

1. Sign in (or sign up) at <https://github.com>.
2. Click **+ → New repository**.
3. Name it, for example, `student-management-system`.
4. Choose **Public** (the free Streamlit Community Cloud tier deploys from public repos; private repos also work after you grant access).
5. Leave "Add a README" **unchecked** (you already have one), then click **Create repository**.

### Step 2: Upload the project files

**Option A: Browser upload (easiest)**
1. On the new repository page click **uploading an existing file**.
2. Drag in `app.py`, `requirements.txt`, `README.md`, `PROJECT_DOCUMENTATION.md`, `test_students.py` and `.gitignore`.
3. Click **Commit changes**.

**Option B: Git command line**

```bash
cd student-management-system
git init
git add .
git commit -m "Initial commit: Student Management System"
git branch -M main
git remote add origin https://github.com/<your-username>/student-management-system.git
git push -u origin main
```

Never commit `students.db`: the `.gitignore` already excludes it.

### Step 3: Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io> and sign in with GitHub (authorize access when asked).
2. Click **Create app** (or **New app**) → **Deploy a public app from GitHub**.
3. Fill in the settings listed below, then click **Deploy**.
4. Wait a few minutes while packages install. You'll get a URL like `https://<your-app-name>.streamlit.app`.

### Required configuration settings

| Setting | Value |
|---------|-------|
| Repository | `<your-username>/student-management-system` |
| Branch | `main` |
| Main file path | `app.py` |
| App URL | any available name you like |
| Python version | Advanced settings → pick 3.11 or 3.12 |
| Secrets | **None required** for the default SQLite setup |
| Optional env variable | `STUDENT_DB_PATH`: custom location of the SQLite file (default `students.db`) |

`requirements.txt` is detected automatically from the repository root.

---

## Persistent database storage (important!)

Streamlit Community Cloud runs your app in a container whose **disk is not permanent**.
A SQLite file (`students.db`) works, but **its data can be lost** when the app restarts, is
redeployed, or goes to sleep after inactivity and is rebuilt. This is fine for a demo,
but not for real data. Choose one of these approaches:

### Option 1: Demo only (what this project does by default)
Use SQLite as is. Before a presentation, add a few sample students. Use the sidebar button
**💾 Download database backup** to save a copy of `students.db`.

### Option 2: Hosted database (recommended for lasting data)
Move the storage to a free hosted database and keep the credentials in **Streamlit Secrets**
(app menu → **Settings → Secrets**), never in GitHub:

- **Supabase** or **Neon**: free hosted PostgreSQL. Use `psycopg2-binary` or `SQLAlchemy`.
- **Turso**: hosted SQLite-compatible (libSQL). Keeps SQL almost identical to this project.

Because all database code lives in the functions at the top of `app.py`
(`init_db`, `add_student`, `get_all_students`, `search_students`, `get_student_by_id`,
`update_student`, `delete_student`, `count_by_department`), switching databases means
rewriting only those functions; the pages stay the same. Note that PostgreSQL uses `%s`
placeholders instead of `?`, and `SERIAL` instead of `AUTOINCREMENT`.

Example secrets file (`Settings → Secrets` on Streamlit Cloud, or `.streamlit/secrets.toml` locally; it is git-ignored):

```toml
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
```

### Option 3: Other hosts with a persistent disk
Render, Railway, Fly.io or a college server can run `streamlit run app.py` with a mounted
volume. Point `STUDENT_DB_PATH` at a file on that volume.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `streamlit: command not found` | Activate your virtual environment, or run `python -m streamlit run app.py` |
| Deployed app shows no students after a while | Expected with SQLite on Streamlit Cloud; see *Persistent database storage* |
| `ModuleNotFoundError` on deploy | Make sure `requirements.txt` is in the repository root |
| Port already in use | `streamlit run app.py --server.port 8502` |

## License

Free to use for educational purposes.
