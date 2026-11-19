@echo off
chcp 936 >nul
cd /d "%~dp0"
echo.
echo   [1/3] 生成网页...
python build.py
if errorlevel 1 goto err

echo.
echo   [2/3] 记录改动...
git add -A
git commit -m "更新网站" >nul 2>&1
if errorlevel 1 echo         (没有需要提交的改动)

echo.
echo   [3/3] 上传到 GitHub...
git push origin main
if errorlevel 1 (
  echo         直连失败，改用代理重试...
  git -c http.proxy=http://127.0.0.1:10389 -c https.proxy=http://127.0.0.1:10389 push origin main
)
if errorlevel 1 goto err

echo.
echo   完成！大约 1 分钟后线上就能看到。
echo   地址：https://yukkof.github.io/
echo.
pause
exit /b 0

:err
echo.
echo   [失败] 把上面的报错信息截图发给我。
echo.
pause
exit /b 1
