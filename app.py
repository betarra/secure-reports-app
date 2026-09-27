import os
from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# تهيئة الاتصال بـ Firebase باستخدام ملف المفتاح الذي وضعناه
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# صفحة الرئيسية (إرسال بلاغ)
@app.route('/')
def index():
    return render_template('report.html')

# استقبال البلاغ وتخزينه في سحابة Firebase الأبدية
@app.route('/submit', methods=['POST'])
def submit_report():
    category = request.form.get('category')
    content = request.form.get('content')
    
    # حفظ البيانات في مجموعة 'reports' في قاعدة البيانات
    db.collection('reports').add({
        'category': category,
        'content': content,
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