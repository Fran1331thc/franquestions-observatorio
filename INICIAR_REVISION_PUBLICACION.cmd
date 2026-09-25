@echo off
setlocal
cd /d "%~dp0"
title Revision completa de FranQuestions

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_acceptance_review.ps1"
if errorlevel 1 (
    echo.
    echo No se pudo iniciar la revision completa de FranQuestions.
    echo Revise el mensaje anterior o ejecute VERIFICAR_FRANQUESTIONS.cmd.
    echo.
    pause
    exit /b 1
)

exit /b 0
