@echo off
setlocal

REM Define the directory where the script is located
set "SCRIPT_DIR=%~dp0"

REM Specify the path to Python located in the same folder as the script
set "C4D_PYTHON_PATH=%SCRIPT_DIR%python.exe"

REM Check if Python exists
if not exist "%C4D_PYTHON_PATH%" (
    echo Python not found in this folder. Please place this script next to the required python.exe.
    pause
    exit /b 1
)

REM Download get-pip.py for Python 2.7
echo Downloading get-pip.py for Python 2.7...
curl -o "%SCRIPT_DIR%get-pip.py" https://bootstrap.pypa.io/pip/2.7/get-pip.py
if errorlevel 1 (
    echo Failed to download get-pip.py. Please check your internet connection.
    pause
    exit /b 1
)

REM Install pip using get-pip.py
echo Installing pip...
"%C4D_PYTHON_PATH%" "%SCRIPT_DIR%get-pip.py"

REM Install numpy
echo Installing numpy...
"%C4D_PYTHON_PATH%" -m pip install numpy

REM Delete get-pip.py
del "%SCRIPT_DIR%get-pip.py"

echo Installation completed.
pause
