import os
import json
from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# تهيئة الاتصال بقاعدة بيانات Firebase (سواء محلياً أو عبر متغيرات البيئة على Render)
if 'FIREBASE_KEY_JSON' in os.environ:
    key_dict = json.loads(os.environ['FIREBASE_KEY_JSON'])
    cred = credentials.Certificate(key_dict)
else:
    cred = credentials.Certificate("firebase_key.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

# المسار الرئيسي (يعرض صفحة الإرسال report.html ويستقبل البيانات POST لتجنب خطأ 405)
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
        
        # تخزين البلاغ في قاعدة البيانات مع مطابقة الحقول لتعمل مع لوحة التحكم
        db.collection('reports').add({
            'report_type': report_type,
            'name': suspect_name,  # تتطابق تماماً مع {{ r.name }} في admin.html
            'governorate': governorate,
            'address': address,
            'affiliation': affiliation,
            'facebook': facebook,
            'phone': phone,
            'status': 'قيد المعالجة',  # الحالة الافتراضية للبلاغ الجديد
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return redirect(url_for('index'))
        
    return render_template('report.html')

# مسار إضافي احتياطي لاستقبال الـ submit إذا كان النموذج يوجه إليه
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
        'name': suspect_name,
        'governorate': governorate,
        'address': address,
        'affiliation': affiliation,
        'facebook': facebook,
        'phone': phone,
        'status': 'قيد المعالجة',
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    return redirect(url_for('index'))

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
    doc = db.collection('reports').document(report_id).get()
    if doc.exists:
        r = doc.to_dict()
        r['id'] = doc.id
        return f"""
        <html dir='rtl'><body style='background:#121212; color:#fff; font-family:Tahoma; padding:20px;'>
        <h2>تفاصيل البلاغ: {r.get('name')}</h2>
        <p><b>نوع البلاغ:</b> {r.get('report_type')}</p>
        <p><b>المحافظة:</b> {r.get('governorate')}</p>
        <p><b>العنوان:</b> {r.get('address')}</p>
        <p><b>الجهة / الصفة:</b> {r.get('affiliation')}</p>
        <p><b>رابط الفيسبوك:</b> <a href='{r.get('facebook')}' target='_blank' style='color:#60a5fa;'>{r.get('facebook')}</a></p>
        <p><b>رقم الهاتف:</b> {r.get('phone')}</p>
        <p><b>الحالة:</b> {r.get('status')}</p>
        <br><a href='{url_for('admin_panel')}' style='background:#059669; color:white; padding:10px 15px; text-decoration:none; border-radius:5px;'>العودة لوحة التحكم</a>
        </body></html>
        """
    return "البلاغ غير موجود", 404

# مسار التصدير
@app.route('/export')
def export_reports():
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)