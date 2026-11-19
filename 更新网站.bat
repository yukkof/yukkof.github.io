@echo off
chcp 936 >nul
cd /d "%~dp0"
echo.
echo   正在生成网站，请稍等...
echo.
python build.py
if errorlevel 1 (
  echo.
  echo   [失败] 上面有报错信息，把它发给我就行。
) else (
  echo.
  echo   完成。双击 index.html 就能看效果。
)
echo.
pause
