from flask import Flask, render_template, request, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secure_admin_key_12345')

# إعداد مجلد حفظ الملفات المرفوعة
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# إعداد اتصال Firebase
if not firebase_admin._apps:
    firebase_key_json = os.environ.get('FIREBASE_KEY_JSON')
    if firebase_key_json:
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate('firebase_key.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

SYRIAN_PROVINCES = [
    "دمشق", "ريف دمشق", "حلب", "حمص", "حماة", "اللاذقية", 
    "طرطوس", "إدلب", "دير الزور", "الرقة", "الحسكة", 
    "درعا", "السويداء", "القنيطرة"
]

@app.route('/', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        try:
            # التعامل مع رفع الملف (صورة أو فيديو)
            file = request.files.get('media_file')
            filename = ''
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            report_data = {
                'report_type': request.form.get('report_type'),
                'suspect_name': request.form.get('suspect_name'),
                'province': request.form.get('province'),
                'nationality': request.form.get('nationality', 'سوري'),
                'current_address': request.form.get('current_address'),
                'combat_history': request.form.get('combat_history'),
                'social_link': request.form.get('social_link'),
                'phone': request.form.get('phone'),
                'media_filename': filename, # تخزين اسم الملف المرفوع
                'created_at': firestore.SERVER_TIMESTAMP
            }
            db.collection('reports').add(report_data)
            flash('تم إرسال بلاغك بنجاح وبسرية تامة.', 'success')
            return redirect(url_for('report'))
        except Exception as e:
            flash(f'حدث خطأ أثناء الإرسال: {str(e)}', 'error')
            
    return render_template('report.html', provinces=SYRIAN_PROVINCES)

@app.route('/admin')
def admin_dashboard():
    try:
        docs = db.collection('reports').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        reports = []
        for doc in docs:
            r = doc.to_dict()
            r['id'] = doc.id
            reports.append(r)
    except Exception as e:
        reports = []

    return render_template('admin.html', reports=reports)

@app.route('/admin/delete/<report_id>', methods=['POST'])
def delete_report(report_id):
    try:
        db.collection('reports').document(report_id).delete()
        flash('تم حذف البلاغ بنجاح', 'success')
    except Exception as e:
        flash('حدث خطأ أثناء الحذف', 'error')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)