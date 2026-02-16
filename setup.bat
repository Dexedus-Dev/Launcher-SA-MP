@echo off
setlocal

set TARGET_VERSION=3.11.5
set INSTALLER=python-3.11.5.exe
set URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe
set VENV_DIR=venv

echo ===============================
echo Checking Python %TARGET_VERSION%
echo ===============================

python -c "import sys; exit(0 if sys.version.startswith('%TARGET_VERSION%') else 1)" >nul 2>&1

if %errorlevel%==0 (
    echo Python OK
) else (
    echo Python not found -> Downloading...

    powershell -Command "Invoke-WebRequest -Uri %URL% -OutFile %INSTALLER%"

    if not exist %INSTALLER% (
        echo Download failed!
        pause
        exit /b
    )

    echo Installing Python...

    %INSTALLER% ^
    /quiet ^
    InstallAllUsers=1 ^
    PrependPath=1 ^
    Include_pip=1 ^
    Include_launcher=1 ^
    Include_test=0 ^
    Include_doc=0 ^
    Include_dev=0 ^
    Include_symbols=0 ^
    Include_debug=0 ^
    SimpleInstall=1

    del %INSTALLER%

    echo Refresh PATH
    set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
)

echo ===============================
echo Creating venv
echo ===============================

if not exist %VENV_DIR% (
    python -m venv %VENV_DIR%
)

echo ===============================
echo Activating venv
echo ===============================

call %VENV_DIR%\Scripts\activate.bat

echo ===============================
echo Installing requirements
echo ===============================

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo ===============================
echo DONE (venv ready)
echo ===============================
pause
