from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.secret_key = 'super_secret_security_key'

# إعداد مجلد لرفع وحفظ الملفات الحقيقية
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

# استقبال البلاغات والملفات الحقيقية وحفظها
@app.route('/submit', methods=['POST'])
def submit_report():
    try:
        file_path_url = None
        # التحقق من وجود ملف مرفوع حقيقي
        if 'evidence_file' in request.files:
            file = request.files['evidence_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # حفظ الملف داخل المجلد المحلي
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_path_url = f"/static/uploads/{filename}"

        report_data = {
            'suspect_name': request.form.get('suspect_name'),
            'category': request.form.get('category'),
            'province': request.form.get('province'),
            'work_details': request.form.get('work_details'),
            'media_link': file_path_url, # تخزين مسار الملف المرفوع الحقيقي
            'social_link': request.form.get('social_link'),
            'phone': request.form.get('phone'),
            'details': request.form.get('details'),
            'created_at': firestore.SERVER_TIMESTAMP
        }
        if db:
            db.collection('reports').add(report_data)
            flash('تم إرسال البلاغ والملفات بنجاح وبسرية تامة', 'success')
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
        # يمكنك هنا إضافة كود لحذف الملف من المجلد المحلي إن أردت
        db.collection('reports').document(report_id).delete()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
