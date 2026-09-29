from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = 'super_secret_security_key'

# تهيئة Cloudinary باستخدام المتغيرات البيئية (للسيرفر والمحلي)
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'd4sxhgoz'),
    api_key = os.environ.get('CLOUDINARY_API_KEY', '291136423786673'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', 'fjOT4UA6rXBomUIJK5xP1RSEq5w') # سيعمل محلياً وسحابياً
)

# تهيئة Firebase Firestore 
firebase_config = os.environ.get('FIREBASE_KEY_JSON')

try:
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate('firebase_key.json')
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🚀 تم الاتصال بـ Firebase بنجاح!")
except Exception as e:
    print(f"❌ فشل الاتصال بـ Firebase: {str(e)}")
    db = None

@app.route('/')
def index():
    return render_template('report.html')

# استقبال وحفظ البلاغات والميديا سحابياً للأبد
@app.route('/submit', methods=['POST'])
def submit_report():
    if not db:
        flash('عذراً، نظام قاعدة البيانات غير متصل حالياً.', 'error')
        return redirect(url_for('index'))

    try:
        file_url = ""
        
        # استلام الملف الحقيقي ورفعه مباشرة إلى سحابة Cloudinary
        if 'evidence_file' in request.files:
            file = request.files['evidence_file']
            if file and file.filename != '':
                # رفع السيرفر للملف مباشرة دون الحاجة لقرص تخزين محلي
                upload_result = cloudinary.uploader.upload(
                    file, 
                    resource_type = "auto", # يتعرف تلقائياً إن كان صورة أو فيديو
                    folder = "secure_reports"
                )
                # الحصول على الرابط السحابي الدائم للملف
                file_url = upload_result.get('secure_url')

        # تجهيز البيانات للحفظ
        report_data = {
            'suspect_name': request.form.get('suspect_name'),
            'report_type': request.form.get('category') or request.form.get('report_type'), 
            'province': request.form.get('province'),
            'combat_history': request.form.get('work_details') or request.form.get('combat_history'),
            'filename': file_url, # الرابط السحابي الآمن والدائم للميديا                                 
            'social_link': request.form.get('social_link'),
            'phone': request.form.get('phone'),
            'current_address': request.form.get('current_address'),
            'nationality': request.form.get('nationality', 'سوري'),
            'details': request.form.get('details'),
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        # حفظ البيانات في Firebase Firestore
        db.collection('reports').add(report_data)
        flash('تم إرسال البلاغ والمرفقات بنجاح وبسرية تامة', 'success')
        
    except Exception as e:
        flash(f'حدث خطأ أثناء الإرسال: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    reports = []
    if db:
        try:
            docs = db.collection('reports').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            for doc in docs:
                r = doc.to_dict()
                r['id'] = doc.id
                reports.append(r)
        except Exception:
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
        flash('تم حذف البلاغ بنجاح', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
