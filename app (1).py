"""
Student Management System
=========================
A beginner-friendly web app built with Python, Streamlit, SQLite and Pandas.

Features: Dashboard, Add, View (sort/search/export CSV), Search, Update, Delete.

Run locally:   streamlit run app.py
"""

import html
import os
import re
import sqlite3
from contextlib import closing

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------------------

APP_NAME = "Student Management System"

# Where the SQLite file lives. You can override it with an environment
# variable (useful for testing or for pointing to a different disk).
DB_FILE = os.environ.get("STUDENT_DB_PATH", "students.db")

DEPARTMENTS = ["CSE", "ECE", "EEE", "Mechanical", "Civil", "IT", "AI & DS", "Other"]
YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

# Friendly column names shown to the user (database name -> display name)
COLUMN_LABELS = {
    "id": "ID",
    "name": "Student Name",
    "roll_number": "Roll Number",
    "department": "Department",
    "academic_year": "Academic Year",
    "email": "Email",
    "phone": "Phone",
    "created_at": "Added On",
}


# ---------------------------------------------------------------------------
# 2. DATABASE FUNCTIONS (every query uses ? placeholders -> no SQL injection)
# ---------------------------------------------------------------------------

def get_connection():
    """Open a connection to the SQLite database file."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def init_db():
    """Create the students table if it does not exist yet."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                roll_number   TEXT NOT NULL UNIQUE COLLATE NOCASE,
                department    TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                email         TEXT NOT NULL,
                phone         TEXT NOT NULL,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def add_student(name, roll_number, department, academic_year, email, phone):
    """Insert a new student. Returns (success: bool, message: str)."""
    try:
        with closing(get_connection()) as conn, conn:
            conn.execute(
                "INSERT INTO students (name, roll_number, department, "
                "academic_year, email, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (name, roll_number, department, academic_year, email, phone),
            )
        return True, f"Student '{name}' was added successfully."
    except sqlite3.IntegrityError:
        # Raised by the UNIQUE constraint on roll_number
        return False, f"Roll number '{roll_number}' already exists. Please use a different one."
    except sqlite3.Error as err:
        return False, f"Database error: {err}"


def get_all_students():
    """Return every student as a Pandas DataFrame."""
    with closing(get_connection()) as conn:
        return pd.read_sql_query("SELECT * FROM students ORDER BY name", conn)


def search_students(term):
    """Find students whose name or roll number contains the search text."""
    pattern = f"%{term}%"
    with closing(get_connection()) as conn:
        return pd.read_sql_query(
            "SELECT * FROM students WHERE name LIKE ? OR roll_number LIKE ? ORDER BY name",
            conn,
            params=(pattern, pattern),
        )


def get_student_by_id(student_id):
    """Return one student as a dict, or None if not found."""
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def update_student(student_id, name, roll_number, department, academic_year, email, phone):
    """Update an existing student. Returns (success, message)."""
    try:
        with closing(get_connection()) as conn, conn:
            cursor = conn.execute(
                "UPDATE students SET name = ?, roll_number = ?, department = ?, "
                "academic_year = ?, email = ?, phone = ? WHERE id = ?",
                (name, roll_number, department, academic_year, email, phone, student_id),
            )
        if cursor.rowcount == 0:
            return False, "That student no longer exists."
        return True, f"Student '{name}' was updated successfully."
    except sqlite3.IntegrityError:
        return False, f"Roll number '{roll_number}' already belongs to another student."
    except sqlite3.Error as err:
        return False, f"Database error: {err}"


def delete_student(student_id):
    """Delete a student by id. Returns (success, message)."""
    try:
        with closing(get_connection()) as conn, conn:
            cursor = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        if cursor.rowcount == 0:
            return False, "That student no longer exists."
        return True, "Student record deleted successfully."
    except sqlite3.Error as err:
        return False, f"Database error: {err}"


def count_by_department():
    """Return a list of (department, count) pairs, biggest first."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT department, COUNT(*) AS total FROM students "
            "GROUP BY department ORDER BY total DESC, department"
        ).fetchall()
    return [(row["department"], row["total"]) for row in rows]


# ---------------------------------------------------------------------------
# 3. VALIDATION HELPERS
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'\-]+$")
ROLL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-/_]*$")


def clean_inputs(name, roll_number, email, phone):
    """Tidy up text typed by the user (trim spaces, normalise case, etc.)."""
    name = " ".join(str(name).split())                 # collapse extra spaces
    roll_number = str(roll_number).strip().upper()
    email = str(email).strip().lower()
    phone = re.sub(r"[\s\-]", "", str(phone))          # remove spaces and dashes
    return name, roll_number, email, phone


def validate_student(name, roll_number, email, phone):
    """Check the cleaned inputs. Returns a list of error messages (empty = valid)."""
    errors = []
    if not name:
        errors.append("Student name is required.")
    elif not NAME_PATTERN.match(name):
        errors.append("Student name may only contain letters, spaces, dots, hyphens and apostrophes.")

    if not roll_number:
        errors.append("Roll number is required.")
    elif not ROLL_PATTERN.match(roll_number):
        errors.append("Roll number may only contain letters, digits, '-', '/' and '_'.")

    if not email:
        errors.append("Email address is required.")
    elif not EMAIL_PATTERN.match(email):
        errors.append("Please enter a valid email address (e.g. name@college.edu).")

    if not phone:
        errors.append("Phone number is required.")
    elif not (phone.isdigit() and len(phone) == 10):
        errors.append("Phone number must be exactly 10 digits.")
    return errors


# ---------------------------------------------------------------------------
# 4. UI HELPERS
# ---------------------------------------------------------------------------

def apply_custom_css():
    """Inject a little CSS for the summary cards and a consistent colour scheme."""
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem;}
        .hero {background: linear-gradient(135deg,#4338ca,#6366f1 60%,#38bdf8);
               color:#fff; padding:1.6rem 2rem; border-radius:16px; margin-bottom:1.2rem;}
        .hero h1 {color:#fff; margin:0 0 .3rem 0; font-size:2rem;}
        .hero p {margin:0; opacity:.92; font-size:1.05rem;}
        .card {color:#fff; padding:1.1rem 1rem; border-radius:14px; text-align:center;
               box-shadow:0 4px 12px rgba(67,56,202,.18); margin-bottom:.8rem;}
        .card .value {font-size:2.3rem; font-weight:700; line-height:1.1;}
        .card .label {font-size:.95rem; opacity:.92;}
        .card-total {background: linear-gradient(135deg,#4f46e5,#7c3aed);}
        .card-dept  {background: linear-gradient(135deg,#2563eb,#0ea5e9);}
        .student-card {border:1px solid #e0e7ff; border-left:5px solid #6366f1;
                       border-radius:10px; padding:.8rem 1rem; margin-bottom:.6rem;
                       background: rgba(99,102,241,.06);}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title, subtitle):
    """Show a consistent page heading."""
    st.title(title)
    st.caption(subtitle)


def summary_card(label, value, css_class):
    """Draw one coloured summary card."""
    st.markdown(
        f'<div class="card {css_class}"><div class="value">{html.escape(str(value))}</div>'
        f'<div class="label">{html.escape(str(label))}</div></div>',
        unsafe_allow_html=True,
    )


def set_flash(kind, message):
    """Remember a message to show after the page reloads ('success', 'error', 'warning')."""
    st.session_state["flash"] = (kind, message)


def show_flash():
    """Display (and clear) a message saved by set_flash()."""
    flash = st.session_state.pop("flash", None)
    if flash:
        kind, message = flash
        icons = {"success": "✅", "error": "🚫", "warning": "⚠️"}
        getattr(st, kind)(message, icon=icons.get(kind))


def to_display_table(df):
    """Rename database columns to friendly names for showing in tables."""
    return df.rename(columns=COLUMN_LABELS)


def student_label(student_row):
    """Text shown in the dropdown, e.g. 'CS101 - Asha Rao (CSE)'."""
    return f"{student_row['roll_number']} - {student_row['name']} ({student_row['department']})"


def choose_student(key):
    """Show a dropdown of students. Returns the selected student dict, or None if empty."""
    df = get_all_students()
    if df.empty:
        st.info("No students registered yet. Add one from the 'Add Student' page.", icon="ℹ️")
        return None
    labels = {int(row["id"]): student_label(row) for _, row in df.iterrows()}
    student_id = st.selectbox(
        "Select a student", options=list(labels.keys()),
        format_func=lambda sid: labels[sid], key=key,
    )
    return get_student_by_id(student_id)


def options_with_current(options, current):
    """Make sure the student's current value is in a dropdown list."""
    return options if current in options else options + [current]


# ---------------------------------------------------------------------------
# 5. PAGES
# ---------------------------------------------------------------------------

def page_dashboard():
    """Welcome banner, total students and per-department summary cards."""
    st.markdown(
        f'<div class="hero"><h1>🎓 {APP_NAME}</h1>'
        "<p>Welcome! Manage student records quickly: add, view, search, update and delete.</p></div>",
        unsafe_allow_html=True,
    )
    show_flash()

    df = get_all_students()
    dept_counts = count_by_department()

    summary_card("Total Registered Students", len(df), "card-total")

    st.subheader("📊 Students by Department")
    if not dept_counts:
        st.info("No students yet. Use 'Add Student' in the sidebar to get started.", icon="ℹ️")
        return

    # Show up to 4 department cards per row
    for start in range(0, len(dept_counts), 4):
        chunk = dept_counts[start:start + 4]
        cols = st.columns(4)
        for col, (dept, total) in zip(cols, chunk):
            with col:
                summary_card(dept, total, "card-dept")

    chart_df = pd.DataFrame(dept_counts, columns=["Department", "Students"]).set_index("Department")
    st.bar_chart(chart_df, color="#6366f1")


def page_add_student():
    """Form for registering a new student."""
    page_header("➕ Add Student", "Fill in all fields marked with * and click Add Student.")
    show_flash()

    # Changing this number gives the form fresh (empty) widgets after a successful add
    version = st.session_state.get("add_form_version", 0)

    with st.form(f"add_form_{version}"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Student Name *", key=f"add_name_{version}")
        roll = col2.text_input("Roll Number *", key=f"add_roll_{version}")
        dept = col1.selectbox("Department *", DEPARTMENTS, key=f"add_dept_{version}")
        year = col2.selectbox("Academic Year *", YEARS, key=f"add_year_{version}")
        email = col1.text_input("Email Address *", key=f"add_email_{version}")
        phone = col2.text_input("Phone Number * (10 digits)", key=f"add_phone_{version}")
        submitted = st.form_submit_button("Add Student", type="primary")

    if submitted:
        name, roll, email, phone = clean_inputs(name, roll, email, phone)
        errors = validate_student(name, roll, email, phone)
        if errors:
            for error in errors:
                st.error(error, icon="🚫")
            return
        success, message = add_student(name, roll, dept, year, email, phone)
        if success:
            set_flash("success", message)
            st.session_state["add_form_version"] = version + 1
            st.rerun()
        else:
            st.error(message, icon="🚫")


def page_view_students():
    """Table of all students with filter, sorting and CSV export."""
    page_header("📋 View Students", "Browse all records. Click a column header to sort.")
    show_flash()

    df = get_all_students()
    if df.empty:
        st.info("No students registered yet.", icon="ℹ️")
        return

    # Quick filter across every text column
    query = st.text_input("🔎 Filter table", placeholder="Type a name, roll number, department...")
    if query.strip():
        mask = df.astype(str).apply(
            lambda col: col.str.contains(query.strip(), case=False, regex=False)
        ).any(axis=1)
        df = df[mask]

    # Sorting controls
    sort_col1, sort_col2 = st.columns(2)
    sort_by = sort_col1.selectbox(
        "Sort by", [c for c in COLUMN_LABELS if c != "id"],
        format_func=lambda c: COLUMN_LABELS[c],
    )
    ascending = sort_col2.radio("Order", ["Ascending", "Descending"], horizontal=True) == "Ascending"
    df = df.sort_values(by=sort_by, ascending=ascending, key=lambda s: s.astype(str).str.lower())

    st.write(f"Showing **{len(df)}** record(s).")
    if df.empty:
        st.warning("No records match your filter.", icon="⚠️")
        return

    display_df = to_display_table(df)
    st.dataframe(display_df, width="stretch", hide_index=True)

    st.download_button(
        "⬇️ Export as CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="students.csv",
        mime="text/csv",
    )


def page_search_student():
    """Search by name or roll number."""
    page_header("🔍 Search Student", "Search by student name or roll number.")
    term = st.text_input("Enter name or roll number", placeholder="e.g. Asha or CS101").strip()

    if not term:
        st.info("Type something above to start searching.", icon="ℹ️")
        return

    results = search_students(term)
    if results.empty:
        st.warning(f"No student found matching '{term}'. Check the spelling and try again.", icon="⚠️")
        return

    st.success(f"Found {len(results)} matching student(s).", icon="✅")
    for _, row in results.iterrows():
        st.markdown(
            f'<div class="student-card"><b>{html.escape(row["name"])}</b> '
            f'&nbsp;|&nbsp; Roll No: <b>{html.escape(row["roll_number"])}</b><br>'
            f'🏫 {html.escape(row["department"])} &nbsp;•&nbsp; 📅 {html.escape(row["academic_year"])}'
            f' &nbsp;•&nbsp; ✉️ {html.escape(row["email"])} &nbsp;•&nbsp; 📞 {html.escape(row["phone"])}</div>',
            unsafe_allow_html=True,
        )
    st.dataframe(to_display_table(results), width="stretch", hide_index=True)


def page_update_student():
    """Pick a student, edit the details and save."""
    page_header("✏️ Update Student", "Select a student, change the details and save.")
    show_flash()

    student = choose_student("update_select")
    if student is None:
        return
    sid = student["id"]

    with st.form(f"update_form_{sid}"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Student Name *", value=student["name"], key=f"upd_name_{sid}")
        roll = col2.text_input("Roll Number *", value=student["roll_number"], key=f"upd_roll_{sid}")
        dept_options = options_with_current(DEPARTMENTS, student["department"])
        year_options = options_with_current(YEARS, student["academic_year"])
        dept = col1.selectbox("Department *", dept_options,
                              index=dept_options.index(student["department"]), key=f"upd_dept_{sid}")
        year = col2.selectbox("Academic Year *", year_options,
                              index=year_options.index(student["academic_year"]), key=f"upd_year_{sid}")
        email = col1.text_input("Email Address *", value=student["email"], key=f"upd_email_{sid}")
        phone = col2.text_input("Phone Number * (10 digits)", value=student["phone"], key=f"upd_phone_{sid}")
        submitted = st.form_submit_button("Save Changes", type="primary")

    if submitted:
        name, roll, email, phone = clean_inputs(name, roll, email, phone)
        errors = validate_student(name, roll, email, phone)
        if errors:
            for error in errors:
                st.error(error, icon="🚫")
            return
        success, message = update_student(sid, name, roll, dept, year, email, phone)
        if success:
            set_flash("success", message)
            st.rerun()
        else:
            st.error(message, icon="🚫")


def page_delete_student():
    """Pick a student and delete after an explicit confirmation."""
    page_header("🗑️ Delete Student", "This action cannot be undone.")
    show_flash()

    student = choose_student("delete_select")
    if student is None:
        return
    sid = student["id"]

    st.markdown(
        f'<div class="student-card"><b>{html.escape(student["name"])}</b> '
        f'&nbsp;|&nbsp; Roll No: <b>{html.escape(student["roll_number"])}</b><br>'
        f'🏫 {html.escape(student["department"])} &nbsp;•&nbsp; 📅 {html.escape(student["academic_year"])}'
        f' &nbsp;•&nbsp; ✉️ {html.escape(student["email"])} &nbsp;•&nbsp; 📞 {html.escape(student["phone"])}</div>',
        unsafe_allow_html=True,
    )
    st.warning("You are about to permanently delete this student record.", icon="⚠️")
    confirmed = st.checkbox("Yes, I want to delete this student.", key=f"confirm_delete_{sid}")

    if st.button("Delete Student", type="primary", key=f"delete_btn_{sid}"):
        if not confirmed:
            st.error("Please tick the confirmation box before deleting.", icon="🚫")
        else:
            success, message = delete_student(sid)
            if success:
                set_flash("success", message)
                st.rerun()
            else:
                st.error(message, icon="🚫")


# ---------------------------------------------------------------------------
# 6. MAIN APP
# ---------------------------------------------------------------------------

PAGES = {
    "🏠 Dashboard": page_dashboard,
    "➕ Add Student": page_add_student,
    "📋 View Students": page_view_students,
    "🔍 Search Student": page_search_student,
    "✏️ Update Student": page_update_student,
    "🗑️ Delete Student": page_delete_student,
}


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="wide")
    apply_custom_css()

    # Create the database/table automatically on first run
    try:
        init_db()
    except sqlite3.Error as err:
        st.error(f"Could not set up the database: {err}")
        st.stop()

    st.sidebar.title("🎓 Student Management")
    choice = st.sidebar.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

    # Backup download (helpful on Streamlit Cloud where disk storage is temporary)
    st.sidebar.divider()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as db_file:
            st.sidebar.download_button(
                "💾 Download database backup", data=db_file.read(),
                file_name="students_backup.db", mime="application/octet-stream",
            )

    try:
        PAGES[choice]()
    except sqlite3.Error as err:
        st.error(f"Database error: {err}")


if __name__ == "__main__":
    main()
