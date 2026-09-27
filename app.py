import os
import json
from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# طريقة آمنة للتعرف على المفتاح سواء محلياً أو على Render
if 'FIREBASE_KEY_JSON' in os.environ:
    # على سيرفر Render: نقرأ المفتاح من متغيرات البيئة
    key_dict = json.loads(os.environ['FIREBASE_KEY_JSON'])
    cred = credentials.Certificate(key_dict)
else:
    # محلياً على جهازك: نقرأه من الملف الموجود بجوار الكود
    cred = credentials.Certificate("firebase_key.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

# صفحة الرئيسية (إرسال بلاغ)
@app.route('/')
def index():
    return render_template('report.html')

# استقبال البلاغ وتخزينه في سحابة Firebase الأبدية
# مسار استقبال البلاغ وتخزينه في سحابة Firebase
@app.route('/submit', methods=['POST'])
def submit_report():
    report_type = request.form.get('report_type')
    suspect_name = request.form.get('suspect_name')
    governorate = request.form.get('governorate')
    address = request.form.get('address')
    affiliation = request.form.get('affiliation')
    facebook = request.form.get('facebook')
    phone = request.form.get('phone')
    
    db.collection('reports').add({
        'report_type': report_type,
        'suspect_name': suspect_name,
        'governorate': governorate,
        'address': address,
        'affiliation': affiliation,
        'facebook': facebook,
        'phone': phone,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    return redirect(url_for('index'))

# لوحة التحكم الخاصة بك (/admin) لجلب البلاغات من السحابة وعرضها
@app.route('/admin')
def admin_panel():
    try:
        # جلب البلاغات مرتبة حسب الأحدث
        reports_ref = db.collection('reports').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        reports = []
        for doc in reports_ref:
            r = doc.to_dict()
            r['id'] = doc.id
            reports.append(r)
    except Exception as e:
        reports = [] # في حال لم تكن هناك بلاغات بعد
        
    return render_template('admin.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=True)