from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
app.secret_key = 'super_secret_security_key'

# إعداد مجلد محلي آمن لحفظ الصور والفيديوهات الحقيقية بأي حجم
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

# استقبال البلاغات بكافة الحقول الستة المحددة دون نسيان أي حقل
@app.route('/submit', methods=['POST'])
def submit_report():
    try:
        file_url = None
        
        # معالجة وحفظ الصور والفيديوهات الحقيقية المرفوعة من الأجهزة مباشرة
        if 'evidence_file' in request.files:
            file = request.files['evidence_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # حفظ الملف بأمان في المجلد المحلي على السيرفر
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_url = f"/static/uploads/{filename}"

        # تسجيل كافة البيانات الستة المطلوبة بدقة في قاعدة البيانات
        report_data = {
            'suspect_name': request.form.get('suspect_name'),   # اسم المشتبه به
            'category': request.form.get('category'),           # أولاً: نوع الجرم
            'province': request.form.get('province'),           # ثانياً: المحافظة السورية
            'work_details': request.form.get('work_details'),   # ثالثاً: أين كان يعمل ومع من
            'media_link': file_url,                             # رابعاً: رابط تحميل الصورة/الفيديو الحقيقي
            'social_link': request.form.get('social_link'),     # خامساً: رابط التواصل الاجتماعي
            'phone': request.form.get('phone'),                 # سادساً: رقم جواله
            'details': request.form.get('details'),             # تفاصيل إضافية
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
        # جلب بيانات البلاغ لحذف الملف المرتبط به من السيرفر لتوفير المساحة
        doc_ref = db.collection('reports').document(report_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('media_link'):
                try:
                    local_path = os.path.join(app.root_path, data['media_link'].lstrip('/'))
                    if os.path.exists(local_path):
                        os.remove(local_path)
                except:
                    pass
        doc_ref.delete()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
