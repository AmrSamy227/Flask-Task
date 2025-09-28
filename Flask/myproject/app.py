from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import or_
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Job Model
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    company = db.Column(db.String(100))
    location = db.Column(db.String(100))
    employees = db.relationship('Employee', backref='job', lazy=True)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))


@app.route("/")
def home():
    jobs = Job.query.all()
    employees = Employee.query.all()
    jobs_count = len(jobs)
    employees_count = len(employees)
    # for chart: employees per job
    labels = [j.title for j in jobs]
    data = [len([e for e in employees if e.job_id == j.id]) for j in jobs]

    return render_template(
        "home.html",
        jobs_count=jobs_count,
        employees_count=employees_count,
        last_jobs=jobs[-5:],             
        last_employees=employees[-5:],     
        chart_labels=labels,
        chart_data=data
    )

@app.route('/search')
def search():
    query = request.args.get('q', '')

    jobs = Job.query.filter(
        or_(
            Job.title.ilike(f'%{query}%'),
            Job.company.ilike(f'%{query}%'),
            Job.location.ilike(f'%{query}%')
        )
    ).all()

    # كل employees في كل job هييجي من العلاقة job.employees
    employees = Employee.query.filter(
        or_(
            Employee.name.ilike(f'%{query}%'),
            Employee.email.ilike(f'%{query}%')
        )
    ).all()

    return render_template('search.html', query=query, jobs=jobs, employees=employees)
@app.route('/jobs')
def jobs():
    jobs = Job.query.all()
    return render_template('jobs.html', jobs=jobs)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        job = Job(title=title, company=company, location=location)
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('jobs'))
    return render_template('create_job.html')

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = Job.query.all()
    data = []
    for job in jobs:
        _job = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location
        }
        data.append(_job)
    return jsonify(data)

@app.route('/api/jobs/<id>', methods=['GET'])
def get_job(id):
    job = Job.query.get_or_404(id)
    data = {'id': job.id, 'title': job.title, 'company': job.company, 'location': job.location}
    return jsonify(data)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_job_html(id):
    job = Job.query.get_or_404(id)
    if request.method == 'POST':
        job.title = request.form['title']
        job.company = request.form['company']
        job.location = request.form['location']
        db.session.commit()
        return redirect(url_for('jobs'))
    return render_template('update.html', job=job)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_job_html(id):
    job = Job.query.get_or_404(id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('jobs'))

# 🟢 إضافة موظف جديد
@app.route('/employees/create', methods=['GET', 'POST'])
def create_employee():
    jobs = Job.query.all()  # لإظهار الوظائف في الـ dropdown
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        job_id = request.form['job_id']

        employee = Employee(name=name, email=email, job_id=job_id)
        db.session.add(employee)
        db.session.commit()

        return redirect(url_for('list_employees'))

    return render_template('create_employee.html', jobs=jobs)

@app.route('/employees')
def list_employees():
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/employees/update/<int:id>', methods=['GET', 'POST'])
def update_employee(id):
    employee = Employee.query.get_or_404(id)
    jobs = Job.query.all()  # علشان الdropdown
    if request.method == 'POST':
        employee.name = request.form['name']
        employee.email = request.form['email']
        employee.job_id = request.form['job_id']
        db.session.commit()
        return redirect(url_for('list_employees'))
    return render_template('update_employee.html', employee=employee, jobs=jobs)

@app.route('/employees/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('list_employees'))

if __name__ == '__main__':
    app.run(debug=True)
