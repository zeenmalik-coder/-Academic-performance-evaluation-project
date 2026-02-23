from flask import Flask, render_template, request, redirect, session, flash, make_response
from io import BytesIO
from xhtml2pdf import pisa

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for sessions

# --- Data storage ---
students = []
subjects = ["Math", "English", "Science", "History",
            "Geography", "Computer", "Physics", "Chemistry"]

# --- Institute info ---
institute_name = "Sunrise International School"
class_name = "12th Grade Science"

# --- Helper functions ---
def calculate_grade(percentage):
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B"
    elif percentage >= 60: return "C"
    elif percentage >= 50: return "D"
    else: return "Fail"

def calculate_gpa(percentage):
    return round(percentage / 10, 2)

def class_average():
    return round(sum(s['percentage'] for s in students)/len(students), 2) if students else 0

def find_topper():
    return max(students, key=lambda s: s['percentage']) if students else None

def average_per_subject():
    averages = []
    for i in range(len(subjects)):
        if students:
            avg = round(sum(s['marks'][i] for s in students)/len(students), 2)
        else:
            avg = 0
        averages.append(avg)
    return averages

# --- Routes ---
@app.route('/')
def home():
    return render_template(
        "index.html",
        students=students,
        institute=institute_name,
        class_name=class_name,
        average=None,
        topper=None,
        subjects=subjects,
        average_per_subject=average_per_subject()
    )

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "teacher" and password == "1234":
            session['logged_in'] = True
            return redirect('/')
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route('/add', methods=['POST'])
def add_student():
    if not session.get('logged_in'):
        return redirect('/login')

    name = request.form['name']
    father = request.form['father']
    roll = request.form['roll']

    # Collect marks safely
    marks = []
    for subj in subjects:
        try:
            marks.append(float(request.form.get(subj, 0)))
        except ValueError:
            marks.append(0)

    total = sum(marks)
    percentage = total / len(subjects)
    grade = calculate_grade(percentage)
    gpa = calculate_gpa(percentage)

    student = {
        "name": name,
        "father": father,
        "roll": roll,
        "marks": marks,
        "total": total,
        "percentage": round(percentage,2),
        "grade": grade,
        "gpa": gpa
    }

    students.append(student)
    return redirect('/')
@app.route('/search', methods=['GET'])
def search_student():
    q_name = request.args.get('name','').lower()
    q_father = request.args.get('father','').lower()
    q_roll = request.args.get('roll','').lower()

    # Mark matching students
    for s in students:
        s['highlight'] = (
            (q_name and q_name in s['name'].lower()) or
            (q_father and q_father in s['father'].lower()) or
            (q_roll and q_roll in s['roll'].lower())
        )

    return render_template(
        "index.html",
        students=students,  # Show all students
        institute=institute_name,
        class_name=class_name,
        average=None,
        topper=None,
        subjects=subjects,
        average_per_subject=average_per_subject(),
        search_query=True
    )



@app.route('/average')
def show_average():
    avg = class_average()
    return render_template(
        "index.html",
        students=students,
        institute=institute_name,
        class_name=class_name,
        average=avg,
        topper=None,
        subjects=subjects,
        average_per_subject=average_per_subject()
    )

@app.route('/topper')
def show_topper():
    top = find_topper()
    return render_template(
        "index.html",
        students=students,
        institute=institute_name,
        class_name=class_name,
        average=None,
        topper=top,
        subjects=subjects,
        average_per_subject=average_per_subject()
    )

@app.route('/report/<roll>')
def student_report(roll):
    student = next((s for s in students if s['roll']==roll), None)
    if not student:
        return f"No student with Roll {roll}", 404
    return render_template(
        "report.html",
        student=student,
        subjects=subjects,
        institute=institute_name,
        class_name=class_name
    )

@app.route('/report/<roll>/pdf')
def report_pdf(roll):
    student = next((s for s in students if s['roll']==roll), None)
    if not student: return "Student not found", 404
    html = render_template(
        'report.html',
        student=student,
        subjects=subjects,
        institute=institute_name,
        class_name=class_name,
        pdf=True
    )
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={student["name"]}_ReportCard.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
