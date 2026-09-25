@echo off
setlocal
cd /d "%~dp0"

title Verificar FranQuestions antes de publicar
echo Iniciando la verificacion de FranQuestions...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "scripts\verify_release.py"
) else if exist "..\outputs\FranQuestions\Version actual\FranQuestions_Observatorio_v1.1.0\.venv\Scripts\python.exe" (
    "..\outputs\FranQuestions\Version actual\FranQuestions_Observatorio_v1.1.0\.venv\Scripts\python.exe" "scripts\verify_release.py"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 "scripts\verify_release.py"
    ) else (
        python "scripts\verify_release.py"
    )
)

set "FQ_RESULT=%ERRORLEVEL%"
echo.
if "%FQ_RESULT%"=="0" (
    echo FranQuestions supero la verificacion local.
) else (
    echo FranQuestions NO supero la verificacion local.
)
echo.
pause
exit /b %FQ_RESULT%
