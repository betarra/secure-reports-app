import os
import json
import base64
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# تهيئة الاتصال بقاعدة بيانات Firebase
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

# دالة ذكية لالتقاط الملف وضغط حجمه أو تقليله لتجنب الأخطاء
def handle_file_upload(request_files):
    for field_name in ['media_file', 'location_image', 'media', 'image', 'file', 'attachment']:
        file_storage = request_files.get(field_name)
        if file_storage and file_storage.filename != '':
            filename = secure_filename(file_storage.filename)
            try:
                file_bytes = file_storage.read()
                if len(file_bytes) > 0:
                    # إذا كان الملف كبيراً جداً (أكبر من 500 كيلوبايت)، نتجنب تخزينه كـ Base64 بالكامل لتشغيل السيرفر بسلاسة
                    if len(file_bytes) > 500 * 1024:
                        return None # أو يمكن حفظه بشكل مختصر
                    
                    encoded_string = base64.b64encode(file_bytes).decode('utf-8')
                    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpeg'
                    mime_type = 'image/png' if ext == 'png' else 'image/jpeg'
                    return f"data:{mime_type};base64,{encoded_string}"
            except Exception:
                pass
    return None

# المسار الرئيسي لإرسال البلاغات
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            report_type = request.form.get('report_type')
            suspect_name = request.form.get('suspect_name')
            governorate = request.form.get('governorate')
            address = request.form.get('address')
            affiliation = request.form.get('affiliation')
            facebook = request.form.get('facebook')
            phone = request.form.get('phone')
            
            media_data = handle_file_upload(request.files)
            
            report_data = {
                'report_type': report_type,
                'name': suspect_name,
                'governorate': governorate,
                'address': address,
                'affiliation': affiliation,
                'facebook': facebook,
                'phone': phone,
                'media': media_data if media_data else '',       
                'image': media_data if media_data else '',       
                'status': 'قيد المعالجة',
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            db.collection('reports').add(report_data)
            return redirect(url_for('admin_panel'))
        except Exception as e:
            import traceback
            return f"<pre style='color: red; direction: ltr; padding: 20px;'>{traceback.format_exc()}</pre>", 500
        
    return render_template('report.html')

# لوحة التحكم لعرض البلاغات
@app.route('/admin')
def admin_panel():
    try:
        reports_ref = db.collection('reports').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        reports = []
        for doc in reports_ref:
            r = doc.to_dict()
            r['id'] = doc.id
            # إزالة حقول الوسائط الضخمة من القائمة الرئيسية لمنع أي ضغط على الهيدر أو الرابط
            if 'media' in r:
                r.pop('media', None)
            if 'image' in r:
                r.pop('image', None)
            reports.append(r)
        return render_template('admin.html', reports=reports)
    except Exception as e:
        import traceback
        return f"<pre style='color: red; direction: ltr; padding: 20px;'>{traceback.format_exc()}</pre>", 500

# تغيير حالة البلاغ
@app.route('/resolve/<report_id>')
def resolve_report(report_id):
    db.collection('reports').document(report_id).update({'status': 'تم التعامل'})
    return redirect(url_for('admin_panel'))

# حذف البلاغ
@app.route('/delete/<report_id>')
def delete_report(report_id):
    db.collection('reports').document(report_id).delete()
    return redirect(url_for('admin_panel'))

# تفاصيل البلاغ
@app.route('/report/<report_id>')
def report_detail(report_id):
    try:
        doc = db.collection('reports').document(report_id).get()
        if doc.exists:
            report = doc.to_dict()
            report['id'] = doc.id
            
            raw_media = report.get('media') or report.get('image')
            if raw_media and str(raw_media).startswith('data:image'):
                report['clean_media'] = str(raw_media)
            else:
                report['clean_media'] = None
                
            return render_template('report_detail.html', report=report)
        return "البلاغ غير موجود", 404
    except Exception as e:
        import traceback
        return f"<pre style='color: red; direction: ltr; padding: 20px;'>{traceback.format_exc()}</pre>", 500

@app.route('/export')
def export_reports():
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)