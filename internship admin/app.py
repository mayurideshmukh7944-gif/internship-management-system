from flask import Flask, render_template, redirect, request, session   # 1. Imported 'request'
import sqlite3
from datetime import datetime
app = Flask(__name__)
app.secret_key = "internship_admin_secret_key"

def create_database():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            duration TEXT NOT NULL,
            eligibility TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            company TEXT NOT NULL,
            internship TEXT NOT NULL,
            apply_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")
    cursor.execute("""
        INSERT OR IGNORE INTO students
        (id, name, email, course, year)
        VALUES (?, ?, ?, ?, ?)
    """, (
        1,
        "Sample Student",
        "student@gmail.com",
        "B.Sc. Computer Applications",
        "TY"
    ))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        college TEXT NOT NULL,
        password TEXT NOT NULL
    )
""")
   
    cursor.execute("PRAGMA table_info(applications)")
    application_columns = [column[1] for column in cursor.fetchall()]

    if "student_email" not in application_columns:
        cursor.execute(
            "ALTER TABLE applications ADD COLUMN student_email TEXT"
        )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")
@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO admins (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "This email is already registered."

        conn.close()
        return redirect("/admin")

    return render_template("admin_register.html")

@app.route("/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        college = request.form["college"]
        password = request.form["password"]

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO student_accounts
                (name, email, phone, college, password)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, phone, college, password))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "This email is already registered."

        conn.close()
        return redirect("/login")

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("internships.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM student_accounts WHERE email = ? AND password = ?",
            (email, password)
        )

        student = cursor.fetchone()
        conn.close()

        if student:
            session["student_email"] = student["email"]
            session["student"] = dict(student)
            return redirect("/dashboard")

        return "Invalid Student Email or Password"

    return render_template("login.html")
@app.route("/dashboard")
def student_dashboard():
    if "student_email" not in session:
        return redirect("/login")

    return render_template("dashboard.html")
@app.route("/internships")
def student_internships():
    if "student_email" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip()

    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM internships
            WHERE title LIKE ?
               OR company LIKE ?
               OR location LIKE ?
        """, (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))
    else:
        cursor.execute("SELECT * FROM internships")

    internships = cursor.fetchall()

    conn.close()

    return render_template(
        "internships.html",
        internships=internships,
        search=search
    )
@app.route("/internship/<int:internship_id>")
def internship_details(internship_id):
    if "student_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM internships WHERE id = ?",
        (internship_id,)
    )

    internship = cursor.fetchone()
    conn.close()

    if internship is None:
        return "Internship not found"

    return render_template(
        "internship_details.html",
        internship=internship,
        internship_id=internship_id
    )
@app.route("/apply/<int:internship_id>", methods=["GET", "POST"])
def apply(internship_id):
    if "student_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM internships WHERE id = ?",
        (internship_id,)
    )

    internship = cursor.fetchone()

    if internship is None:
        conn.close()
        return "Internship not found"

    if request.method == "POST":
        student = session["student"]

        cursor.execute("""
            INSERT INTO applications
            (student_name, student_email, company, internship, apply_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student["name"],
            student["email"],
            internship["company"],
            internship["title"],
            datetime.now().strftime("%d-%m-%Y"),
            "Pending"
        ))

        conn.commit()
        conn.close()

        return redirect("/applications")

    conn.close()

    return render_template(
        "apply.html",
        internship=internship,
        internship_id=internship_id
    )
@app.route("/applications")
def student_applications():
    if "student_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM applications
        WHERE student_email = ?
        ORDER BY id DESC
    """, (session["student_email"],))

    applications = cursor.fetchall()
    conn.close()

    return render_template(
        "my_applications.html",
        applications=applications
    )
@app.route("/application-status")
def student_application_status():
    if "student_email" not in session:
        return redirect("/login")

    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM applications
        WHERE student_email = ?
        ORDER BY id DESC
    """, (session["student_email"],))

    applications = cursor.fetchall()
    conn.close()

    return render_template(
        "application_status.html",
        applications=applications
    )
@app.route("/profile", methods=["GET", "POST"])
def student_profile():
    if "student_email" not in session:
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        college = request.form["college"]

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE student_accounts
            SET name = ?, phone = ?, college = ?
            WHERE email = ?
        """, (
            name,
            phone,
            college,
            session["student_email"]
        ))

        conn.commit()
        conn.close()

        session["student"]["name"] = name
        session["student"]["phone"] = phone
        session["student"]["college"] = college

        return redirect("/profile")

    return render_template(
        "profile.html",
        student=session["student"]
    )
# Admin Login Page
@app.route("/admin")
def admin_login():
    return render_template("admin_login.html")

# Admin Login Check
@app.route("/admin/login", methods=["POST"])
def admin_login_check():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admins WHERE email = ? AND password = ?",
        (email, password)
    )

    admin = cursor.fetchone()
    conn.close()

    if admin:
        session["admin_email"] = email
        return redirect("/admin/dashboard")
    else:
        return "Invalid Admin Email or Password"

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_email" not in session:
        return redirect("/admin")
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Rejected'")
    rejected = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_applications=total_applications,
        pending=pending,
        approved=approved,
        rejected=rejected
    )

@app.route("/admin/students")
def manage_students():
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()

    return render_template("manage_students.html", students=students)
@app.route("/admin/students/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/students")
@app.route("/admin/students/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]
        year = request.form["year"]

        cursor.execute("""
            UPDATE students
            SET name = ?, email = ?, course = ?, year = ?
            WHERE id = ?
        """, (name, email, course, year, id))

        conn.commit()
        conn.close()

        return redirect("/admin/students")

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    conn.close()

    return render_template("edit_student.html", student=student)

@app.route("/admin/internships")
def manage_internships():
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM internships")
    internships = cursor.fetchall()

    conn.close()

    return render_template("manage_internships.html", internships=internships)
    
@app.route("/admin/internships/add", methods=["GET", "POST"])
def add_internship():
    if request.method == "POST":
        company = request.form["company"]
        title = request.form["title"]
        location = request.form["location"]
        duration = request.form["duration"]
        eligibility = request.form["eligibility"]

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO internships
            (company, title, location, duration, eligibility)
            VALUES (?, ?, ?, ?, ?)
        """, (company, title, location, duration, eligibility))

        conn.commit()
        conn.close()

        return redirect("/admin/internships")

    return render_template("add_internship.html")

@app.route("/admin/internships/delete/<int:id>")
def delete_internship(id):
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM internships WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/internships")

@app.route("/admin/internships/edit/<int:id>", methods=["GET", "POST"])
def edit_internship(id):
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":
        company = request.form["company"]
        title = request.form["title"]
        location = request.form["location"]
        duration = request.form["duration"]
        eligibility = request.form["eligibility"]

        cursor.execute("""
            UPDATE internships
            SET company = ?, title = ?, location = ?, duration = ?, eligibility = ?
            WHERE id = ?
        """, (company, title, location, duration, eligibility, id))

        conn.commit()
        conn.close()

        return redirect("/admin/internships")

    cursor.execute("SELECT * FROM internships WHERE id = ?", (id,))
    internship = cursor.fetchone()

    conn.close()

    return render_template("edit_internship.html", internship=internship)

@app.route("/admin/applications")
def manage_applications():
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM applications")
    applications = cursor.fetchall()

    conn.close()

    return render_template("manage_applications.html", applications=applications)
@app.route("/admin/applications/status/<int:id>", methods=["POST"])
def update_application_status(id):
    status = request.form["status"]

    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/applications")
@app.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        course = request.form["course"]
        year = request.form["year"]

        conn = sqlite3.connect("internships.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO students (name, email, course, year)
            VALUES (?, ?, ?, ?)
        """, (name, email, course, year))

        conn.commit()
        conn.close()

        return redirect("/admin/students")

    return render_template("add_student.html")
@app.route("/admin/reports")
def reports():
    conn = sqlite3.connect("internships.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Rejected'")
    rejected = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected
    )
@app.route("/add-demo-applications")
def add_demo_applications():
    conn = sqlite3.connect("internships.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications
        (student_name, company, internship, apply_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, ("Rahul", "TCS", "Python Intern", "29-09-2026", "Pending"))

    cursor.execute("""
        INSERT INTO applications
        (student_name, company, internship, apply_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, ("Priya", "Infosys", "Web Development Intern", "28-09-2026", "Approved"))

    cursor.execute("""
        INSERT INTO applications
        (student_name, company, internship, apply_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, ("Amit", "Wipro", "Data Science Intern", "27-09-2026", "Rejected"))

    conn.commit()
    conn.close()

    return redirect("/admin/applications")

@app.route("/logout")
def student_logout():
    session.pop("student_email", None)
    session.pop("student", None)
    return redirect("/")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin")

if __name__ == "__main__":
    create_database()
    app.run(debug=True)
