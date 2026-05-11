# utils/i18n_manager.py
import json
from pathlib import Path
from typing import Dict

# مسارات ملفات الترجمة
I18N_DIR = Path(__file__).parent.parent / "i18n"
LANGS = {
    "ar": I18N_DIR / "ar.json",
    "en": I18N_DIR / "en.json"
}

class Translator:
    def __init__(self, lang: str = "ar"):
        self.lang = lang
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        """تحميل ملف الترجمة للغة المحددة"""
        lang_file = LANGS.get(self.lang)
        if lang_file and lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except Exception as e:
                print(f"⚠️ خطأ في تحميل ملف اللغة {self.lang}: {e}")
        else:
            print(f"⚠️ ملف اللغة {self.lang} غير موجود.")

    def t(self, key: str, **kwargs) -> str:
        """
        الترجمة باستخدام المفتاح مع دعم المتغيرات
        مثال: t("welcome_message", name="فارس")
        """
        try:
            text = self._get_translation(key)
            # استبدال المتغيرات إن وجدت
            if kwargs:
                for k, v in kwargs.items():
                    text = text.replace(f"{{{{{k}}}}}", str(v))
            return text
        except:
            # إذا لم يوجد الترجمة أو المفتاح، يعود المفتاح نفسه
            return key

    def _get_translation(self, key: str) -> str:
        """الحصول على الترجمة باستخدام مفتاح متداخل"""
        keys = key.split(".")
        value = self.translations
        for k in keys:
            value = value[k]
        return value