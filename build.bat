@echo off
setlocal

python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

python -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1

python -m nuitka ^
  --onefile ^
  --standalone ^
  --assume-yes-for-downloads ^
  --output-dir=dist ^
  --output-filename=gitee-downloader.exe ^
  --include-package=gitee_downloader ^
  --include-package=yaml ^
  main.py
if errorlevel 1 exit /b 1

endlocal
