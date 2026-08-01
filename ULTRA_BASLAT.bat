@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ULTRA Finans Ajani v0.3

where py >nul 2>nul
if errorlevel 1 (
  echo Python bulunamadi.
  echo Python kurulumunu kontrol edin.
  pause
  exit /b 1
)

echo ULTRA Finans Ajani baslatiliyor...
py app.py

if errorlevel 1 (
  echo.
  echo Program bir hata nedeniyle kapandi.
  pause
)
