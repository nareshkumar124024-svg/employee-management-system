from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import (
    users_col,
    employees_col,
    attendance_col,
    leave_col,
    check_connection
)
from bson import ObjectId
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret"

# Create a demo admin only if the users collection is empty
if users_col.count_documents({}) == 0:
    users_col.insert_one({
        "name": "Admin",
        "email": "admin@ems.com",
        "password": generate_password_hash("Admin@123"),
        "role": "admin"
    })


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = users_col.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["name"] = user["name"]
            session["role"] = user.get("role", "employee")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    today = date.today().isoformat()

    # Total employees
    total_employees = employees_col.count_documents({})

    # Today's attendance
    present_today = attendance_col.count_documents({
        "date": today,
        "status": "Present"
    })

    absent_today = attendance_col.count_documents({
        "date": today,
        "status": "Absent"
    })

    late_today = attendance_col.count_documents({
        "date": today,
        "status": "Late"
    })

    # Pending leave requests
    pending_leaves = leave_col.count_documents({
        "status": "Pending"
    })

    return render_template(
        "dashboard.html",
        total_employees=total_employees,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        pending_leaves=pending_leaves,
        today=today,
        name=session.get("name")
    )


@app.route("/employees", methods=["GET", "POST"])
def employees():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            employee = {
                "name": request.form.get("name", "").strip(),
                "email": request.form.get("email", "").strip().lower(),
                "phone": request.form.get("phone", "").strip(),
                "department": request.form.get("department", "").strip(),
                "salary": float(request.form.get("salary", 0))
            }

            if not all([
                employee["name"],
                employee["email"],
                employee["phone"],
                employee["department"]
            ]) or employee["salary"] < 0:
                flash("Please enter valid employee details.")
            elif employees_col.find_one({"email": employee["email"]}):
                flash("An employee with this email already exists.")
            else:
                employees_col.insert_one(employee)
                flash("Employee added successfully!")
                return redirect(url_for("employees"))

        except (ValueError, TypeError):
            flash("Please enter a valid salary.")

    employee_list = list(employees_col.find().sort("name", 1))

    return render_template(
        "employees.html",
        employees=employee_list,
        name=session.get("name", "Admin")
    )


@app.route("/employees/edit/<employee_id>", methods=["POST"])
def edit_employee(employee_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        employee = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "phone": request.form.get("phone", "").strip(),
            "department": request.form.get("department", "").strip(),
            "salary": float(request.form.get("salary", 0))
        }

        if not all([
            employee["name"], employee["email"],
            employee["phone"], employee["department"]
        ]) or employee["salary"] < 0:
            flash("Please enter valid employee details.")
        elif employees_col.find_one({
            "email": employee["email"],
            "_id": {"$ne": ObjectId(employee_id)}
        }):
            flash("Another employee already uses this email.")
        else:
            result = employees_col.update_one(
                {"_id": ObjectId(employee_id)},
                {"$set": employee}
            )
            flash(
                "Employee updated successfully!"
                if result.matched_count
                else "Employee not found."
            )

    except (ValueError, TypeError):
        flash("Invalid employee ID or salary.")

    return redirect(url_for("employees"))


@app.route("/employees/delete/<employee_id>", methods=["POST"])
def delete_employee(employee_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        result = employees_col.delete_one(
            {"_id": ObjectId(employee_id)}
        )
        flash(
            "Employee deleted successfully!"
            if result.deleted_count
            else "Employee not found."
        )
    except Exception:
        flash("Invalid employee ID.")

    return redirect(url_for("employees"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/attendance-leave", methods=["GET", "POST"])
def attendance_leave():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        employee_id = request.form.get("employee_id", "")
        attendance_date = request.form.get("attendance_date", "")
        status = request.form.get("status", "")

        try:
            valid_date = date.fromisoformat(attendance_date)
        except (ValueError, TypeError):
            valid_date = None

        if (not ObjectId.is_valid(employee_id)
                or not valid_date
                or status not in ["Present", "Absent", "Late"]):
            flash("Please enter valid attendance details.")
        else:
            employee = employees_col.find_one({
                "_id": ObjectId(employee_id)
            })

            if not employee:
                flash("Employee not found.")
            else:
                attendance_col.update_one(
                    {
                        "employee_id": ObjectId(employee_id),
                        "date": attendance_date
                    },
                    {"$set": {
                        "status": status,
                        "recorded_by": session["user_id"]
                    }},
                    upsert=True
                )
                flash("Attendance saved successfully!")

        return redirect(url_for("attendance_leave"))

    employee_list = list(employees_col.find().sort("name", 1))
    records = list(
        attendance_col.find().sort("date", -1).limit(100)
    )

    employee_map = {
        str(emp["_id"]): emp["name"]
        for emp in employee_list
    }
    all_employees = list(employees_col.find().sort("name", 1))

    return render_template(
        "attendance_leave.html",
        employees=employee_list,
        attendance_records=records,
        all_employees=all_employees,
        employee_map=employee_map,
        today=date.today().isoformat(),
        name=session.get("name", "Admin")
    )


@app.route("/leave-action/<leave_id>", methods=["POST"])
def leave_action(leave_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Only admin can approve or reject leave requests.", "error")
        return redirect(url_for("attendance_leave"))

    try:
        status = request.form.get("status", "").strip()

        if status not in ["Approved", "Rejected"]:
            flash("Invalid leave status.", "error")
            return redirect(url_for("attendance_leave"))

        result = leave_col.update_one(
            {"_id": ObjectId(leave_id)},
            {"$set": {"status": status}}
        )

        if result.matched_count:
            flash(f"Leave request {status.lower()} successfully!", "success")
        else:
            flash("Leave request not found.", "error")

    except Exception:
        flash("Unable to update leave request.", "error")

    return redirect(url_for("attendance_leave"))

@app.route("/reports")
def reports():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    today = date.today().isoformat()
    records = list(attendance_col.find({"date": today}))
    present_ids = [r["employee_id"] for r in records
                   if r["status"] == "Present"]
    absent_ids = [r["employee_id"] for r in records
                  if r["status"] == "Absent"]

    present = list(employees_col.find({"_id": {"$in": present_ids}}))
    absent = list(employees_col.find({"_id": {"$in": absent_ids}}))
    all_employees = list(employees_col.find().sort("name", 1))
    return render_template(
        "reports.html",
        employees=employees_col.count_documents({}),
        present=present,
        absent=absent,
        all_employees=all_employees,
        leaves=leave_col.count_documents({"status": "Pending"})
    )

if __name__ == "__main__":
    check_connection()
    app.run(debug=True)
