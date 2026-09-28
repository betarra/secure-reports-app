import os
import json
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
    if 'FIREBASE_KEY_JSON' in os.environ:
        cred_dict = json.loads(os.environ['FIREBASE_KEY_JSON'])
        cred = credentials.Certificate(cred_dict)
    else:
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
            'filename': filename  # تم توحيد اسم الحقل ليتطابق مع القالب
        })
        
        return "تم إرسال البلاغ بنجاح وتشفيره بنجاح!"
    except Exception as e:
        return f"حدث خطأ أثناء الإرسال: {e}"

@app.route('/admin')
def admin_panel():
    try:
        docs = db.collection('reports').stream()
        reports = []
        for doc in docs:
            r_data = doc.to_dict()
            r_data['id'] = doc.id  # ضمان جلب معرف الوثيقة من فايربيز مباشرة
            reports.append(r_data)
        
        # تصنيف التقارير حسب نوع الحالة لتظهر في الخانات الأربع المخصصة
        reports_shabih = [r for r in reports if r.get('report_type') == 'شبيح']
        reports_drugs = [r for r in reports if r.get('report_type') == 'تاجر مخدرات']
        reports_agent = [r for r in reports if r.get('report_type') == 'عميل']
        reports_other = [r for r in reports if r.get('report_type') not in ['شبيح', 'تاجر مخدرات', 'عميل']]

        return render_template('admin.html', 
                               reports_shabih=reports_shabih,
                               reports_drugs=reports_drugs,
                               reports_agent=reports_agent,
                               reports_other=reports_other)
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
