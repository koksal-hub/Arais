@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ULTRA Finans Ajani Testleri

where py >nul 2>nul
if errorlevel 1 (
  echo Python bulunamadi.
  echo Python kurulumunu kontrol edin.
  pause
  exit /b 1
)

echo Testler calistiriliyor...
echo.
py -m unittest discover -s tests -v
set TEST_EXIT=%errorlevel%
echo.
if "%TEST_EXIT%"=="0" (
  echo TUM TESTLER BASARILI.
) else (
  echo TESTLERDE HATA VAR. Bu pencerenin ekran goruntusunu gonderin.
)
echo.
pause
exit /b %TEST_EXIT%
