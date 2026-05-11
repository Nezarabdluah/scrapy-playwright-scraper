# utils/data_manager.py
import os
import json
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

# مسارات النظام
BASE_DIR = Path(__file__).parent.parent
USER_DIR = BASE_DIR / "user"
PROJECTS_DIR = USER_DIR / "projects"
DATA_DIR = USER_DIR / "projects" / "data"
AUTH_DIR = USER_DIR / "auth"
CONFIG_DIR = USER_DIR / "config"

# التأكد من وجود المجلدات الضرورية
for d in [PROJECTS_DIR, DATA_DIR, AUTH_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# إعداد التخزين المؤقت
@st.cache_data(ttl=300)  # التخزين المؤقت لمدة 5 دقائق
def load_projects() -> List[Dict]:
    """تحميل قائمة المشاريع من ملفات JSON مع التخزين المؤقت"""
    projects = []
    for project_file in PROJECTS_DIR.glob("*.json"):
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project = json.load(f)
                projects.append(project)
        except Exception as e:
            print(f"⚠️ خطأ في تحميل المشروع {project_file.name}: {e}")
    # ترتيب المشاريع حسب تاريخ الإنشاء (الأحدث أولاً)
    projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return projects

def save_project(project: Dict) -> bool:
    """حفظ مشروع إلى ملف JSON"""
    try:
        project_name = project.get('project_name', 'unknown')
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
        project_file = PROJECTS_DIR / f"{safe_name}.json"

        # تحديث حقل التاريخ
        project['updated_at'] = datetime.now().isoformat()
        if 'created_at' not in project:
            project['created_at'] = project['updated_at']

        # حفظ المشروع
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

        # إنشاء مجلد البيانات إذا لم يكن موجوداً
        project_data_dir = DATA_DIR / safe_name
        project_data_dir.mkdir(exist_ok=True)

        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ المشروع: {e}")
        return False

def load_project(project_name: str) -> Optional[Dict]:
    """تحميل مشروع محدد من ملف JSON"""
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
    project_file = PROJECTS_DIR / f"{safe_name}.json"
    if project_file.exists():
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطأ في تحميل المشروع {project_name}: {e}")
    return None

def delete_project(project_name: str) -> bool:
    """حذف مشروع ومجلد البيانات المرتبط به"""
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
    project_file = PROJECTS_DIR / f"{safe_name}.json"
    project_data_dir = DATA_DIR / safe_name

    try:
        # حذف ملف المشروع
        if project_file.exists():
            project_file.unlink()
        # حذف مجلد البيانات
        if project_data_dir.exists():
            import shutil
            shutil.rmtree(project_data_dir)
        # إعادة تحميل قائمة المشاريع
        load_projects.clear()  # مسح التخزين المؤقت لإعادة تحميله
        return True
    except Exception as e:
        print(f"❌ خطأ في حذف المشروع {project_name}: {e}")
        return False

@st.cache_data(ttl=600)  # التخزين المؤقت لمدة 10 دقائق
def load_settings() -> Dict:
    """تحميل إعدادات النظام"""
    settings_file = CONFIG_DIR / "settings.json"
    default_settings = {
        "default_delay": 2,
        "default_pages": 10,
        "browser_mode": "خفي",
        "auto_export": True,
        "notify_complete": True
    }
    try:
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                # دمج الإعدادات مع الإعدادات الافتراضية
                default_settings.update(saved_settings)
        return default_settings
    except Exception as e:
        print(f"⚠️ خطأ في تحميل الإعدادات: {e}")
        return default_settings

def save_settings(settings: Dict) -> bool:
    """حفظ إعدادات النظام"""
    settings_file = CONFIG_DIR / "settings.json"
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        load_settings.clear()  # مسح التخزين المؤقت لإعادة تحميله
        return True
    except Exception as e:
        print(f"❌ خطأ في حفظ الإعدادات: {e}")
        return False

def save_result(project_name: str, data: List[Dict], file_type: str = "json") -> bool:
    """حفظ نتيجة بيانات لمشروع"""
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
    project_data_dir = DATA_DIR / safe_name
    project_data_dir.mkdir(exist_ok=True)

    try:
        # حفظ البيانات بتنسيق محدد
        if file_type == "json":
            result_file = project_data_dir / "results.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif file_type == "csv":
            import csv
            result_file = project_data_dir / "results.csv"
            with open(result_file, 'w', encoding='utf-8-sig', newline='') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

        # حفظ الإحصائيات الأساسية
        stats = {
            "items_count": len(data),
            "created_at": datetime.now().isoformat()
        }
        return save_project_stats(project_name, stats)
    except Exception as e:
        print(f"❌ خطأ في حفظ نتيجة المشروع {project_name}: {e}")
        return False

def save_project_stats(project_name: str, stats: Dict) -> bool:
    """تحديث إحصائيات المشروع"""
    project = load_project(project_name)
    if project:
        project['stats'] = stats
        return save_project(project)
    return False

def load_permissions() -> Dict:
    """تحميل إعدادات الصلاحيات"""
    permissions_file = AUTH_DIR / "permissions.json"
    default_permissions = {
        "roles": {
            "admin": {"description": "مدير النظام"},
            "user": {"description": "مستخدم عادي"},
            "guest": {"description": "زائر"}
        },
        "users": {
            "admin": {"role": "admin", "name": "مدير النظام"},
            "test_user": {"role": "user", "name": "مستخدم تجريبي"}
        },
        "current_user": "test_user"
    }
    try:
        if permissions_file.exists():
            with open(permissions_file, 'r', encoding='utf-8') as f:
                saved_perms = json.load(f)
                default_permissions.update(saved_perms)
        return default_permissions
    except Exception as e:
        print(f"⚠️ خطأ في تحميل الصلاحيات: {e}")
        return default_permissions