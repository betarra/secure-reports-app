from flask import Flask, render_template, request, redirect, url_for, flash
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.secret_key = 'super_secret_security_key'

# تهيئة Firebase Firestore
try:
    cred = credentials.Certificate('firebase_key.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    db = None

@app.route('/')
def index():
    return render_template('report.html')

# المسار العام المعتمد والمنشور للناس لاستقبال البيانات
@app.route('/submit', methods=['POST'])
def submit_report():
    try:
        report_data = {
            'suspect_name': request.form.get('suspect_name'),
            'province': request.form.get('province'),
            'phone': request.form.get('phone'),
            'details': request.form.get('details'),
            'category': request.form.get('category'),
            'created_at': firestore.SERVER_TIMESTAMP
        }
        if db:
            db.collection('reports').add(report_data)
            flash('تم إرسال البلاغ بنجاح وبسرية تامة', 'success')
    except Exception as e:
        flash(f'حدث خطأ أثناء الإرسال: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    reports = []
    if db:
        docs = db.collection('reports').stream()
        for doc in docs:
            r = doc.to_dict()
            r['id'] = doc.id
            reports.append(r)
    return render_template('admin.html', reports=reports)

@app.route('/report/<report_id>')
def report_detail(report_id):
    report = {}
    if db:
        doc = db.collection('reports').document(report_id).get()
        if doc.exists:
            report = doc.to_dict()
            report['id'] = doc.id
    return render_template('report_detail.html', report=report)

@app.route('/delete-report/<report_id>', methods=['POST'])
def delete_report(report_id):
    if db:
        db.collection('reports').document(report_id).delete()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
