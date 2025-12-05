@echo off
echo Eliminando reporte anterior...
@REM rmdir /s /q allure-report

echo Ejecutando pruebas...
pytest --alluredir=allure-results

echo Generando reporte Allure 3...
npx allure generate allure-results --clean -o allure-report

echo Abriendo reporte...
npx allure open allure-report

pause
