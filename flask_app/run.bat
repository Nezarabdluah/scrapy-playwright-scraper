>@echo off
chcp 65001 >nul
echo ============================================
echo    🕷️  مستخرج البيانات الذكي - Flask
echo ============================================
echo.

echo [1/3] التحقق من Python...
python --version
if errorlevel 1 (
    echo ❌ Python غير مثبت! قم بتثبيته من https://python.org
    pause
    exit /b 1
)

echo.
echo [2/3] تثبيت المتطلبات...
pip install flask flask-cors -q

echo.
echo [3/3] تشغيل التطبيق...
echo.
echo ============================================
echo  ✅ تم التشغيل بنجاح!
echo  🌐 افتح المتصفح على: http://127.0.0.1:5000
echo ============================================
echo.

cd /d "%~dp0"
python app.py

pause
