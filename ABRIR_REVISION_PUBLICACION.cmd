@echo off
setlocal
cd /d "%~dp0"
title Revision visual de FranQuestions
if not exist "REVISION_VISUAL_PUBLICACION.md" (
    echo No se encontro la lista REVISION_VISUAL_PUBLICACION.md.
    pause
    exit /b 1
)
start "" notepad.exe "%CD%\REVISION_VISUAL_PUBLICACION.md"
exit /b 0
