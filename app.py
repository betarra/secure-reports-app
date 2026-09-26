import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

reports_db = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        name = request.form.get('suspect_name')
        governorate = request.form.get('governorate')
        address = request.form.get('address')
        affiliation = request.form.get('affiliation')
        facebook = request.form.get('facebook')
        phone = request.form.get('phone')
        
        media_file = request.files.get('media_file')
        location_image = request.files.get('location_image')
        
        media_filename = ''
        if media_file and allowed_file(media_file.filename):
            media_filename = secure_filename(media_file.filename)
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], media_filename))

        loc_filename = ''
        if location_image and allowed_file(location_image.filename):
            loc_filename = secure_filename('loc_' + location_image.filename)
            location_image.save(os.path.join(app.config['UPLOAD_FOLDER'], loc_filename))
            
        report_data = {
            'id': len(reports_db) + 1,
            'report_type': report_type,
            'name': name,
            'governorate': governorate,
            'address': address,
            'affiliation': affiliation,
            'facebook': facebook,
            'phone': phone,
            'media': media_filename,
            'location_image': loc_filename,
            'status': 'قيد المعالجة' # الحالة الافتراضية
        }
        reports_db.append(report_data)

        flash('تم إرسال البلاغ بنجاح وسيحظى بالسرية التامة.', 'success')
        return redirect(url_for('report'))

    return render_template('report.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html', reports=reports_db)

@app.route('/admin/report/<int:report_id>')
def report_detail(report_id):
    single_report = next((r for r in reports_db if r['id'] == report_id), None)
    return render_template('report_detail.html', report=single_report)

# مسار لتصدير البلاغات إلى ملف Excel
@app.route('/export_reports')
def export_reports():
    data = []
    for r in reports_db:
        data.append({
            'رقم البلاغ': r['id'],
            'تصنيف الحالة': r['report_type'],
            'الاسم الثلاثي': r['name'],
            'المحافظة': r['governorate'],
            'مكان السكن': r['address'],
            'الانتماء': r['affiliation'],
            'رابط الفيسبوك': r['facebook'],
            'رقم الهاتف': r['phone'],
            'الحالة': r['status']
        })
        
    if not data:
        df = pd.DataFrame(columns=['رقم البلاغ', 'تصنيف الحالة', 'الاسم الثلاثي', 'المحافظة', 'مكان السكن', 'الانتماء', 'رابط الفيسبوك', 'رقم الهاتف', 'الحالة'])
    else:
        df = pd.DataFrame(data)
        
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Security Reports')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Security_Reports.xlsx'
    )

# مسار لحذف البلاغ
@app.route('/admin/delete/<int:report_id>')
def delete_report(report_id):
    global reports_db
    reports_db = [r for r in reports_db if r['id'] != report_id]
    return redirect(url_for('admin_dashboard'))

# مسار لتغيير حالة البلاغ إلى "تم التعامل"
@app.route('/admin/resolve/<int:report_id>')
def resolve_report(report_id):
    for r in reports_db:
        if r['id'] == report_id:
            r['status'] = 'تم التعامل'
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)