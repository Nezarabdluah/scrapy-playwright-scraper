# -*- coding: utf-8 -*-
"""
تطبيق Flask لمستخرج البيانات الذكي
واجهة ويب بسيطة وسهلة الاستخدام - مجانية ومفتوحة المصدر
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_cors import CORS
import os
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from web_ui.executor import ProjectExecutor
from utils.validation import is_valid_project_name, is_valid_url, are_valid_urls, is_valid_page_count

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

BASE_DIR = Path(__file__).parent.parent
USER_DIR = BASE_DIR / "user"
PROJECTS_DIR = USER_DIR / "projects"
RESULTS_DIR = USER_DIR / "results"
CONFIG_DIR = USER_DIR / "config"

for d in [PROJECTS_DIR, RESULTS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

executors = {}

def load_projects():
    """تحميل المشاريع من ملفات JSON"""
    projects = []
    for project_file in PROJECTS_DIR.glob("*.json"):
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project = json.load(f)
                projects.append(project)
        except Exception:
            continue
    projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return projects

def save_project(project):
    """حفظ المشروع"""
    try:
        project_name = project.get('project_name', 'unknown')
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
        project_file = PROJECTS_DIR / f"{safe_name}.json"
        
        project['updated_at'] = datetime.now().isoformat()
        if 'created_at' not in project:
            project['created_at'] = project['updated_at']
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"خطأ في الحفظ: {e}")
        return False

def delete_project_file(project_name):
    """حذف ملف المشروع"""
    try:
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
        project_file = PROJECTS_DIR / f"{safe_name}.json"
        if project_file.exists():
            project_file.unlink()
        return True
    except Exception:
        return False

def get_project_status(project_name):
    """الحصول على حالة المشروع"""
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
    summary_path = RESULTS_DIR / project_name / "summary.json"
    
    if project_name in executors:
        executor = executors[project_name]
        return executor.get_status()
    
    if summary_path.exists():
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {"status": "pending", "progress": 0}

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    projects = load_projects()
    stats = {
        "total": len(projects),
        "completed": sum(1 for p in projects if get_project_status(p.get('project_name', '')).get('status') == 'success'),
        "running": sum(1 for p in projects if get_project_status(p.get('project_name', '')).get('status') == 'running')
    }
    return render_template('index.html', projects=projects[:5], stats=stats)

@app.route('/projects')
def projects_list():
    """صفحة المشاريع"""
    projects = load_projects()
    projects_with_status = []
    for p in projects:
        status = get_project_status(p.get('project_name', ''))
        p['status_info'] = status
        projects_with_status.append(p)
    return render_template('projects.html', projects=projects_with_status)

@app.route('/new', methods=['GET', 'POST'])
def new_project():
    """إنشاء مشروع جديد"""
    if request.method == 'POST':
        project_name = request.form.get('project_name', '').strip()
        target_url = request.form.get('target_url', '').strip()
        data_type = request.form.get('data_type', 'products')
        export_format = request.form.get('export_format', 'json')
        max_pages = int(request.form.get('max_pages', 10))
        delay = int(request.form.get('delay', 2))
        fields = request.form.get('fields', '').strip()
        
        errors = []
        
        if not project_name:
            errors.append('اسم المشروع مطلوب')
        elif not is_valid_project_name(project_name):
            errors.append('اسم المشروع غير صالح')
        
        if not target_url:
            errors.append('الرابط مطلوب')
        elif not is_valid_url(target_url):
            errors.append('الرابط غير صالح')
        
        if not is_valid_page_count(max_pages):
            errors.append('عدد الصفحات غير صالح')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('new_project.html')
        
        project = {
            'project_name': project_name,
            'target_url': target_url,
            'data_type': data_type,
            'export_format': export_format,
            'max_pages': max_pages,
            'delay': delay,
            'fields': [f.strip() for f in fields.split(',') if f.strip()]
        }
        
        if save_project(project):
            flash('تم إنشاء المشروع بنجاح!', 'success')
            return redirect(url_for('projects_list'))
        else:
            flash('خطأ في حفظ المشروع', 'error')
    
    return render_template('new_project.html')

@app.route('/run/<project_name>')
def run_project(project_name):
    """تشغيل مشروع"""
    project = None
    for p in load_projects():
        if p.get('project_name') == project_name:
            project = p
            break
    
    if not project:
        flash('المشروع غير موجود', 'error')
        return redirect(url_for('projects_list'))
    
    if project_name in executors and executors[project_name].status == 'running':
        flash('المشروع يعمل بالفعل', 'warning')
        return redirect(url_for('projects_list'))
    
    executor = ProjectExecutor(project, str(BASE_DIR / "system"))
    executors[project_name] = executor
    executor.start()
    
    flash(f'تم بدء تشغيل المشروع: {project_name}', 'success')
    return redirect(url_for('project_status', project_name=project_name))

@app.route('/stop/<project_name>')
def stop_project(project_name):
    """إيقاف مشروع"""
    if project_name in executors:
        executors[project_name].stop()
        flash(f'تم إيقاف المشروع: {project_name}', 'success')
    else:
        flash('المشروع غير قيد التشغيل', 'warning')
    
    return redirect(url_for('projects_list'))

@app.route('/status/<project_name>')
def project_status(project_name):
    """صفحة حالة المشروع"""
    project = None
    for p in load_projects():
        if p.get('project_name') == project_name:
            project = p
            break
    
    if not project:
        flash('المشروع غير موجود', 'error')
        return redirect(url_for('projects_list'))
    
    status = get_project_status(project_name)
    return render_template('status.html', project=project, status=status)

@app.route('/api/status/<project_name>')
def api_status(project_name):
    """API للحصول على حالة المشروع"""
    status = get_project_status(project_name)
    return jsonify(status)

@app.route('/delete/<project_name>')
def delete_project_route(project_name):
    """حذف مشروع"""
    if delete_project_file(project_name):
        flash(f'تم حذف المشروع: {project_name}', 'success')
    else:
        flash('خطأ في حذف المشروع', 'error')
    return redirect(url_for('projects_list'))

@app.route('/download/<project_name>')
def download_results(project_name):
    """تحميل نتائج المشروع"""
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
    results_path = RESULTS_DIR / project_name
    
    if not results_path.exists():
        flash('لا توجد نتائج لهذا المشروع', 'warning')
        return redirect(url_for('projects_list'))
    
    json_file = results_path / "results.json"
    if json_file.exists():
        return send_file(json_file, as_attachment=True, download_name=f"{project_name}_results.json")
    
    flash('ملف النتائج غير موجود', 'error')
    return redirect(url_for('projects_list'))

@app.route('/help')
def help_page():
    """صفحة المساعدة"""
    return render_template('help.html')

if __name__ == '__main__':
    print("=" * 60)
    print("🕷️  مستخرج البيانات الذكي - Flask")
    print("=" * 60)
    print(f"📁 مجلد المشاريع: {PROJECTS_DIR}")
    print(f"📁 مجلد النتائج: {RESULTS_DIR}")
    print("=" * 60)
    print("🌐 افتح المتصفح على: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
