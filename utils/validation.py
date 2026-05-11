# utils/validation.py
"""
دوال التحقق من صحة المدخلات
"""
import re
from urllib.parse import urlparse


def is_valid_project_name(name: str) -> bool:
    """
    التحقق من صحة اسم المشروع
    
    المعايير:
    - لا يقل عن 3 أحرف
    - لا يزيد عن 50 حرف
    - يحتوي فقط على أحرف عربية/إنجليزية، أرقام، مسافات، وشرطات سفلية
    - لا يبدأ أو ينتهي بمسافة
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # التحقق من الطول
    if len(name) < 3 or len(name) > 50:
        return False
    
    # التحقق من الأحرف المسموحة (عربية، إنجليزية، أرقام، مسافات، شرطات سفلية)
    pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FFa-zA-Z0-9_ ]+$'
    if not re.match(pattern, name):
        return False
    
    return True


def is_valid_url(url: str) -> bool:
    """
    التحقق من صحة رابط URL
    
    المعايير:
    - يجب أن يبدأ بـ http:// أو https://
    - يجب أن يحتوي على domain صالح
    - لا يحتوي على مسافات
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # التحقق من بداية الرابط
    if not url.startswith(('http://', 'https://')):
        return False
    
    # التحقق من عدم وجود مسافات في الرابط
    if ' ' in url:
        return False
    
    try:
        result = urlparse(url)
        # يجب أن يحتوي على scheme و netloc
        if not all([result.scheme, result.netloc]):
            return False
        
        # التحقق من عدم وجود مسافات في الرابط
        if ' ' in url:
            return False
        
        return True
    except Exception:
        return False


def are_valid_urls(urls: list) -> bool:
    """
    التحقق من صحة قائمة روابط
    
    المعايير:
    - يجب أن تكون قائمة غير فارغة
    - يجب أن يكون كل رابط صالحاً
    """
    if not urls or not isinstance(urls, list):
        return False
    
    if len(urls) == 0:
        return False
    
    return all(is_valid_url(url) for url in urls)


def is_valid_page_count(count: int) -> bool:
    """
    التحقق من صحة عدد الصفحات
    
    المعايير:
    - يجب أن يكون عدداً صحيحاً
    - يجب أن يكون بين 1 و 1000
    """
    if not isinstance(count, int):
        return False
    
    return 1 <= count <= 1000


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    r"""
    تنظيف اسم الملف لإزالة الرموز غير المسموحة
    
    الرموز الممنوعة في ويندوز: < > : " / \ | ? *
    """
    if not filename:
        return "unnamed_project"
    
    # إزالة الرموز غير المسموحة
    sanitized = re.sub(r'[<>:"/\\|?*]', replacement, filename)
    
    # إزالة المسافات الزائدة والنقاط في البداية
    sanitized = sanitized.strip(". ")
    
    # منع الأسماء المحجوزة في ويندوز
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 
                'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    name_part = sanitized.split('.')[0].upper()
    if name_part in reserved:
        sanitized = f"{sanitized}_file"
    
    # منع الاسم الفارغ
    if not sanitized or sanitized == ".":
        sanitized = "unnamed_project"
    
    return sanitized


def is_valid_email(email: str) -> bool:
    """
    التحقق من صحة البريد الإلكتروني
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_delay(delay: float) -> bool:
    """
    التحقق من صحة قيمة التأخير
    
    المعايير:
    - يجب أن يكون رقماً
    - يجب أن يكون بين 0.1 و 60 ثانية
    """
    if not isinstance(delay, (int, float)):
        return False
    
    return 0.1 <= delay <= 60.0
