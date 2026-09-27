import os
import json
import base64
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# إعداد مجلد الرفع المحلي (احتياطي)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# تهيئة الاتصال بقاعدة بيانات Firebase (سواء محلياً أو عبر متغيرات البيئة على Render)
if 'FIREBASE_KEY_JSON' in os.environ:
    key_dict = json.loads(os.environ['FIREBASE_KEY_JSON'])
    cred = credentials.Certificate(key_dict)
else:
    cred = credentials.Certificate("firebase_key.json")

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# الدالة المساعدة لتحويل الصورة إلى Base64 لتخزينها مباشرة في Firebase وضمان عدم ضياعها على Render
def handle_file_upload(file_storage):
    if file_storage and file_storage.filename != '':
        filename = secure_filename(file_storage.filename)
        # التأكد من أن اسم الملف ليس مجرد امتداد وهمي
        if filename.lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
            return None
        try:
            file_bytes = file_storage.read()
            if len(file_bytes) > 0:
                encoded_string = base64.b64encode(file_bytes).decode('utf-8')
                ext = filename.split('.')[-1].lower()
                if ext == 'jpg':
                    ext = 'jpeg'
                return f"data:image/{ext};base64,{encoded_string}"
        except Exception:
            pass
    return None

# المسار الرئيسي (يعرض صفحة الإرسال report.html ويستقبل البيانات POST)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        suspect_name = request.form.get('suspect_name')
        governorate = request.form.get('governorate')
        address = request.form.get('address')
        affiliation = request.form.get('affiliation')
        facebook = request.form.get('facebook')
        phone = request.form.get('phone')
        
        # التقاط الملف أو الصورة المرفقة من مختلف الأسماء المحتملة في النموذج
        media_file = (
            request.files.get('media_file') or 
            request.files.get('location_image') or 
            request.files.get('media') or 
            request.files.get('image') or
            request.files.get('file') or
            request.files.get('attachment')
        )
        
        media_data = handle_file_upload(media_file)
        
        report_data = {
            'report_type': report_type,
            'name': suspect_name,
            'governorate': governorate,
            'address': address,
            'affiliation': affiliation,
            'facebook': facebook,
            'phone': phone,
            'media': media_data,       
            'image': media_data,       
            'status': 'قيد المعالجة',
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        # حفظ البيانات في فايربيس
        db.collection('reports').add(report_data)
        return redirect(url_for('index'))
        
    return render_template('report.html')

# لوحة التحكم لجلب وعرض البلاغات
@app.route('/admin')
def admin_panel():
    try:
        reports_ref = db.collection('reports').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        reports = []
        for doc in reports_ref:
            r = doc.to_dict()
            r['id'] = doc.id
            reports.append(r)
    except Exception as e:
        reports = [] 
        
    return render_template('admin.html', reports=reports)

# مسار لتغيير حالة البلاغ إلى "تم التعامل"
@app.route('/resolve/<report_id>')
def resolve_report(report_id):
    db.collection('reports').document(report_id).update({'status': 'تم التعامل'})
    return redirect(url_for('admin_panel'))

# مسار لحذف البلاغ
@app.route('/delete/<report_id>')
def delete_report(report_id):
    db.collection('reports').document(report_id).delete()
    return redirect(url_for('admin_panel'))

# مسار لعرض تفاصيل بلاغ محدد
@app.route('/report/<report_id>')
def report_detail(report_id):
    try:
        doc = db.collection('reports').document(report_id).get()
        if doc.exists:
            report = doc.to_dict()
            report['id'] = doc.id
            
            # جلب البيانات المعالجة للصورة
            raw_media = report.get('media') or report.get('image') or report.get('location_image') or report.get('photo') or report.get('file') or report.get('attachment')
            
            if raw_media and str(raw_media).strip().lower() not in ['none', '', 'jpg', 'jpeg', 'png', 'gif', 'webp']:
                report['clean_media'] = str(raw_media).strip()
            else:
                report['clean_media'] = None
                
            return render_template('report_detail.html', report=report)
        return "البلاغ غير موجود في قاعدة البيانات", 404
    except Exception as e:
        import traceback
        return f"<pre style='color: red; direction: ltr; padding: 20px;'>{traceback.format_exc()}</pre>", 500

# مسار التصدير
@app.route('/export')
def export_reports():
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)