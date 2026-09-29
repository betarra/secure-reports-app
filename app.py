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

# استقبال وحفظ الحقول بناءً على مسميات الفايربيس الخاصة بك
@app.route('/submit', methods=['POST'])
def submit_report():
    try:
        report_data = {
            'suspect_name': request.form.get('suspect_name'),
            'report_type': request.form.get('category'),          # مطابقة لـ report_type
            'province': request.form.get('province'),
            'combat_history': request.form.get('work_details'),    # مطابقة لـ combat_history
            'filename': request.form.get('media_data'),            # مطابقة لـ filename لحفظ الصورة
            'social_link': request.form.get('social_link'),
            'phone': request.form.get('phone'),
            'current_address': request.form.get('current_address'),# مطابقة لـ current_address
            'nationality': request.form.get('nationality', 'سوري'),
            'details': request.form.get('details'),
            'created_at': firestore.SERVER_TIMESTAMP
        }
        if db:
            db.collection('reports').add(report_data)
            flash('تم إرسال البلاغ وكافة المرفقات بنجاح وبسرية تامة', 'success')
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

@app.route('/delete-report/<report_id>', methods=['POST'])
def delete_report(report_id):
    if db:
        db.collection('reports').document(report_id).delete()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
