# Student Management System: Project Documentation

## 1. Abstract

The Student Management System is a web application that helps a college store and manage
student information in one place. It is written in Python using the Streamlit framework for the
user interface, SQLite for data storage and Pandas for handling tabular data. Staff can add new
students, view and search records, update details, delete records after confirmation and export
data to CSV. A dashboard summarises the total number of students and the count in each
department. The application validates all inputs, rejects duplicate roll numbers and uses
parameterized SQL queries for security. It is simple enough for beginners to understand and can
be deployed free on Streamlit Community Cloud.

## 2. Problem Statement

Many small departments still keep student details in paper registers or scattered spreadsheets.
This makes it slow to find a student, easy to create duplicate or inconsistent entries and hard
to produce summaries such as "how many students are in each department". A simple, reliable and
easy-to-use system is needed to keep student records organised and accurate.

## 3. Objectives

1. Provide a single place to store student details (name, roll number, department, year, email, phone).
2. Allow records to be added, viewed, searched, updated and deleted (CRUD).
3. Prevent invalid data and duplicate roll numbers.
4. Show quick statistics on a dashboard.
5. Allow data export to CSV for reports.
6. Build the application with beginner-friendly, well-commented code.
7. Make the application deployable online at no cost.

## 4. Software and Hardware Requirements

**Software**

| Item | Requirement |
|------|-------------|
| Operating system | Windows 10/11, macOS or Linux |
| Language | Python 3.9 or newer |
| Libraries | streamlit, pandas (sqlite3 is built into Python) |
| Database | SQLite 3 |
| Browser | Chrome, Edge, Firefox or Safari (latest) |
| Tools | VS Code (or any editor), Git, GitHub account |

**Hardware** (minimum)

| Item | Requirement |
|------|-------------|
| Processor | Dual-core, 1.5 GHz or better |
| RAM | 4 GB |
| Storage | 500 MB free |
| Network | Internet needed only for installation and deployment |

## 5. System Architecture

```
┌──────────────────────┐
│   User (Browser)     │
└──────────┬───────────┘
           │ HTTP
┌──────────▼───────────┐
│ Presentation layer   │  Streamlit pages: Dashboard, Add, View,
│ (app.py page_*)      │  Search, Update, Delete + sidebar menu
└──────────┬───────────┘
           │ function calls
┌──────────▼───────────┐
│ Logic layer          │  clean_inputs(), validate_student()
│ (validation)         │
└──────────┬───────────┘
           │ function calls
┌──────────▼───────────┐
│ Data access layer    │  add_student(), search_students(), ...
│ (sqlite3 + pandas)   │  parameterized SQL
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│ SQLite file          │  students.db  →  table: students
└──────────────────────┘
```

Streamlit re-runs `app.py` from top to bottom whenever the user interacts with a widget. The
sidebar radio button decides which `page_*` function is drawn. `st.session_state` keeps small
pieces of information (like success messages) between re-runs.

## 6. Database Table Structure

**Table: `students`**

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal unique id |
| `name` | TEXT | NOT NULL | Student's full name |
| `roll_number` | TEXT | NOT NULL, UNIQUE, COLLATE NOCASE | College roll number (no duplicates, case-insensitive) |
| `department` | TEXT | NOT NULL | e.g. CSE, ECE, Mechanical |
| `academic_year` | TEXT | NOT NULL | 1st Year to 4th Year |
| `email` | TEXT | NOT NULL | Email address |
| `phone` | TEXT | NOT NULL | 10-digit phone number |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | When the record was added |

## 7. Main Python Functions

**Database functions**

| Function | Purpose |
|----------|---------|
| `get_connection()` | Opens the SQLite file and returns a connection |
| `init_db()` | Creates the `students` table automatically if missing |
| `add_student(...)` | Inserts a record; returns `(False, message)` if the roll number already exists |
| `get_all_students()` | Returns all records as a Pandas DataFrame |
| `search_students(term)` | Finds records where name or roll number contains the text |
| `get_student_by_id(id)` | Returns one record as a dictionary |
| `update_student(...)` | Updates a record; blocks changing to someone else's roll number |
| `delete_student(id)` | Deletes a record by id |
| `count_by_department()` | Returns department-wise counts for the dashboard |

**Validation and helper functions**

| Function | Purpose |
|----------|---------|
| `clean_inputs(...)` | Trims spaces, upper-cases roll numbers, lower-cases email, strips phone separators |
| `validate_student(...)` | Returns a list of error messages (empty list = valid) |
| `apply_custom_css()` | Adds the card and banner styling |
| `summary_card(...)` | Draws one coloured dashboard card |
| `set_flash()` / `show_flash()` | Keep a success/error message across a page reload |
| `choose_student(key)` | Dropdown used by the Update and Delete pages |
| `to_display_table(df)` | Renames columns to readable names |

**Page functions:** `page_dashboard`, `page_add_student`, `page_view_students`,
`page_search_student`, `page_update_student`, `page_delete_student`. `main()` sets up the
page, creates the database and shows the selected page.

## 8. Expected Output

- **Dashboard:** a purple banner "Student Management System", a card with the total number of students, one blue card per department and a bar chart.
- **Add Student:** after a valid submission, a green message "Student 'Asha Rao' was added successfully." and an empty form. A repeated roll number shows a red message: "Roll number 'CS101' already exists."
- **View Students:** a table with columns *Student Name, Roll Number, Department, Academic Year, Email, Phone, Added On*, plus an **Export as CSV** button that downloads `students.csv`.
- **Search:** matching students appear as cards and a table; otherwise "No student found matching '...'".
- **Update:** current values are pre-filled; "Student ... was updated successfully."
- **Delete:** details are shown with a warning; deletion works only after the confirmation box is ticked; then "Student record deleted successfully."

## 9. Testing Summary

`test_students.py` contains 22 automated tests covering: automatic table creation, adding,
duplicate rejection (including different letter case), search, SQL-injection attempt, update,
duplicate-on-update, delete, department counts, CSV content, empty/invalid inputs and
the real pages of the app (add, search, update, view, delete-with-confirmation).
Run them with `python -m unittest test_students -v`.

## 10. Future Enhancements

1. Login system with admin and staff roles.
2. Extra fields: photo, date of birth, address, guardian details, marks and attendance.
3. Import students from a CSV or Excel file.
4. Charts for year-wise and gender-wise statistics.
5. Persistent cloud database (PostgreSQL / Supabase) for lasting storage.
6. Email notifications and PDF report or ID-card generation.
7. Pagination for very large tables and audit logs of who changed what.
8. Dark mode toggle and multi-language support.

## 11. Viva Questions and Answers

**1. What is Streamlit and why did you use it?**
Streamlit is an open-source Python library for building web apps using only Python. I used it
because it needs no HTML/CSS/JavaScript knowledge and gives ready-made widgets, tables and charts.

**2. Why did you choose SQLite as the database?**
SQLite is a lightweight, file-based database built into Python. It needs no server or
installation, which makes it ideal for small projects and demonstrations.

**3. How do you prevent duplicate roll numbers?**
The `roll_number` column has a `UNIQUE` constraint (case-insensitive). If a duplicate is inserted,
SQLite raises `sqlite3.IntegrityError`, which I catch and show as a friendly error message.

**4. What is SQL injection and how does your project prevent it?**
SQL injection is an attack where malicious text typed by a user changes the meaning of an SQL
query. I prevent it with parameterized queries: the SQL uses `?` placeholders and values are
passed separately, so they are always treated as data, never as SQL code.

**5. What is CRUD? Show where it appears in your project.**
CRUD means Create, Read, Update, Delete. Create → `add_student()`, Read → `get_all_students()` /
`search_students()`, Update → `update_student()`, Delete → `delete_student()`.

**6. What is Pandas used for here?**
Pandas reads query results into a DataFrame, which Streamlit displays as a table. It also sorts,
filters and converts the data to CSV for export.

**7. How does Streamlit handle user interaction?**
Every time a widget changes or a button is clicked, Streamlit re-runs the script from top to
bottom. `st.session_state` stores values that must survive between re-runs.

**8. How does the delete confirmation work?**
The Delete page shows the student's details and a checkbox. If the button is pressed without
ticking the checkbox, an error is displayed and nothing is deleted. Only a ticked checkbox allows `delete_student()` to run.

**9. What input validation have you implemented?**
Required-field checks, name and roll-number character rules, an email pattern (regular
expression), and a 10-digit phone check. Input is also cleaned (trimmed, normalised) before saving.

**10. What is the limitation of SQLite on Streamlit Community Cloud and how can it be solved?**
The cloud container's disk is temporary, so `students.db` can be reset when the app restarts.
The solution is a hosted database such as Supabase/Neon (PostgreSQL) or Turso, with credentials
stored in Streamlit Secrets. Because the database code is in separate functions, only those functions need to change.
