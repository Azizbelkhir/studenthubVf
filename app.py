import os
import json
import csv
import io
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, Response, flash
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "studenthub-cloud-super-secret-key-2026")

# Fichier de persistance des étudiants (JSON local)
DATA_FILE = os.path.join(os.path.dirname(__file__), "students.json")

DEFAULT_STUDENTS = [
    {
        "id": "STU26004",
        "last_name": "belkhir",
        "first_name": "aziz",
        "email": "azizbelkhir@gmail.com",
        "filiere": "Mobile",
        "niveau": "Ing2",
        "inscription_date": "25 nov. 2026",
        "color": "emerald"  # BA
    },
    {
        "id": "STU001",
        "last_name": "Ben Ali",
        "first_name": "Ahmed",
        "email": "ahmed.benali@epi.tn",
        "filiere": "IoT",
        "niveau": "Ing2",
        "inscription_date": "25 nov. 2026",
        "color": "pink"  # AB
    },
    {
        "id": "STU002",
        "last_name": "Mansouri",
        "first_name": "Fatma",
        "email": "fatma.mansouri@epi.tn",
        "filiere": "IoT",
        "niveau": "Ing2",
        "inscription_date": "25 nov. 2026",
        "color": "rose"  # FM
    },
    {
        "id": "STU003",
        "last_name": "Trabelsi",
        "first_name": "Mohamed",
        "email": "mohamed.trabelsi@epi.tn",
        "filiere": "Informatique",
        "niveau": "Ing1",
        "inscription_date": "25 nov. 2026",
        "color": "purple"  # MT
    }
]

def load_students():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_students(DEFAULT_STUDENTS)
    return list(DEFAULT_STUDENTS)

def save_students(students_list):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(students_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur d'écriture JSON: {e}")

# Routes Principales
@app.route("/")
@app.route("/dashboard")
def dashboard():
    students = load_students()
    
    total_students = len(students)
    filieres_set = set(s["filiere"] for s in students)
    total_filieres = len(filieres_set)
    niveaux_set = set(s["niveau"] for s in students)
    total_niveaux = len(niveaux_set)
    
    # Répartition par filière
    filiere_counts = {}
    for s in students:
        f = s["filiere"]
        filiere_counts[f] = filiere_counts.get(f, 0) + 1
        
    # Répartition par niveau
    niveau_counts = {}
    for s in students:
        n = s["niveau"]
        niveau_counts[n] = niveau_counts.get(n, 0) + 1

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        students=students,
        total_students=total_students,
        total_filieres=total_filieres,
        total_niveaux=total_niveaux,
        filiere_counts=filiere_counts,
        niveau_counts=niveau_counts,
        is_admin=session.get("is_admin", False)
    )

@app.route("/students")
def students():
    students = load_students()
    return render_template(
        "students.html",
        active_page="students",
        students=students,
        is_admin=session.get("is_admin", False)
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "admin" and password == "admin123":
            session["is_admin"] = True
            session["username"] = "admin"
            return redirect(url_for("students"))
        else:
            flash("Identifiants invalides. Utilisez admin / admin123", "error")
    return render_template("login.html", is_admin=session.get("is_admin", False))

@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    session.pop("username", None)
    return redirect(url_for("students"))

# Actions CRUD pour l'administrateur
@app.route("/students/add", methods=["POST"])
def add_student():
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "Accès non autorisé"}), 403

    students = load_students()
    
    nom = request.form.get("last_name", "").strip()
    prenom = request.form.get("first_name", "").strip()
    email = request.form.get("email", "").strip()
    filiere = request.form.get("filiere", "Informatique")
    niveau = request.form.get("niveau", "Ing1")
    
    if not nom or not prenom or not email:
        return redirect(url_for("students"))

    # Génération ID étudiant
    next_num = len(students) + 1
    new_id = f"STU{next_num:03d}"
    
    colors = ["emerald", "pink", "rose", "purple", "cyan", "amber", "indigo"]
    assigned_color = colors[len(students) % len(colors)]

    new_student = {
        "id": new_id,
        "last_name": nom,
        "first_name": prenom,
        "email": email,
        "filiere": filiere,
        "niveau": niveau,
        "inscription_date": datetime.now().strftime("%d %b. %Y"),
        "color": assigned_color
    }

    students.append(new_student)
    save_students(students)
    return redirect(url_for("students"))

@app.route("/students/edit/<student_id>", methods=["POST"])
def edit_student(student_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "Accès non autorisé"}), 403

    students = load_students()
    for s in students:
        if s["id"] == student_id:
            s["last_name"] = request.form.get("last_name", s["last_name"]).strip()
            s["first_name"] = request.form.get("first_name", s["first_name"]).strip()
            s["email"] = request.form.get("email", s["email"]).strip()
            s["filiere"] = request.form.get("filiere", s["filiere"])
            s["niveau"] = request.form.get("niveau", s["niveau"])
            break
            
    save_students(students)
    return redirect(url_for("students"))

@app.route("/students/delete/<student_id>", methods=["POST", "DELETE"])
def delete_student(student_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "Accès non autorisé"}), 403

    students = load_students()
    students = [s for s in students if s["id"] != student_id]
    save_students(students)
    
    if request.is_json or request.method == "DELETE":
        return jsonify({"success": True})
    return redirect(url_for("students"))

@app.route("/students/export/csv")
def export_csv():
    students = load_students()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["ID", "Nom", "Prénom", "Email", "Filière", "Niveau", "Date Inscription"])
    for s in students:
        writer.writerow([s["id"], s["last_name"], s["first_name"], s["email"], s["filiere"], s["niveau"], s["inscription_date"]])
    
    response = Response(output.getvalue().encode("utf-8-sig"), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=etudiants_studenthub.csv"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
