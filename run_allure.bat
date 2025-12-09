@echo off

:MENU
echo Selecciona el navegador:
echo   1) Google Chrome
echo   2) Microsoft Edge
set /p BROWSER_CHOICE="Ingresa una opcion (1 o 2): "
if "%BROWSER_CHOICE%"=="1" (
    set "BROWSER_FLAG=chrome"
    goto CONTINUE
)
if "%BROWSER_CHOICE%"=="2" (
    set "BROWSER_FLAG=edge"
    goto CONTINUE
)
echo Opcion invalida. Intenta de nuevo.
goto MENU

:CONTINUE
set REPORTFIA_BROWSER=%BROWSER_FLAG%
echo Eliminando reporte anterior...
@REM rmdir /s /q allure-report

echo Ejecutando pruebas...
pytest --browser=%BROWSER_FLAG% --alluredir=allure-results

echo Generando reporte Allure 3...
npx allure generate allure-results --clean -o allure-report

echo Abriendo reporte...
npx allure open allure-report

pause
