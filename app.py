import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# إعداد مجلد الرفع للملفات
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# تهيئة اتصال فايربيز (Firebase Firestore)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/')
def index():
    return render_template('report.html')

@app.route('/submit', methods=['POST'])
def submit_report():
    try:
        report_type = request.form.get('report_type')
        suspect_name = request.form.get('suspect_name')
        province = request.form.get('province')
        nationality = request.form.get('nationality')
        current_address = request.form.get('current_address')
        combat_history = request.form.get('combat_history')
        social_link = request.form.get('social_link')
        phone = request.form.get('phone')
        
        file = request.files.get('media_file')
        filename = ""
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # تخزين البيانات في Firestore
        doc_ref = db.collection('reports').document()
        doc_ref.set({
            'id': doc_ref.id,
            'report_type': report_type,
            'suspect_name': suspect_name,
            'province': province,
            'nationality': nationality,
            'current_address': current_address,
            'combat_history': combat_history,
            'social_link': social_link,
            'phone': phone,
            'media_filename': filename
        })
        
        return "تم إرسال البلاغ بنجاح وتشفيره بنجاح!"
    except Exception as e:
        return f"حدث خطأ أثناء الإرسال: {e}"

@app.route('/admin')
def admin_panel():
    try:
        docs = db.collection('reports').stream()
        reports = [doc.to_dict() for doc in docs]
        return render_template('admin.html', reports=reports)
    except Exception as e:
        return f"خطأ في جلب التقارير: {e}"

@app.route('/delete/<report_id>', methods=['POST'])
def delete_report(report_id):
    try:
        db.collection('reports').document(report_id).delete()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"خطأ أثناء الحذف: {e}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)