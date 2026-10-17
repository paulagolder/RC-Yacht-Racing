@echo off
rem Build a single Windows program file: dist\pyraceresults.exe
rem
rem     build_windows.bat
rem
rem Run it on Windows, in the project folder. Needs Python 3.9 or newer from python.org (tick
rem "Add python.exe to PATH"; tkinter is included) and PyInstaller:
rem
rem     py -m pip install pyinstaller
rem
rem Data is not part of the program: each user's competitions stay in
rem C:\Users\<name>\.pyraceresults.

setlocal
cd /d "%~dp0"
rem The Python to use: the py launcher unless PYTHON says otherwise (as on GitHub's machines).
if not defined PYTHON set PYTHON=py

echo Running the tests...
%PYTHON% -m unittest discover -s tests -t . -q
if errorlevel 1 (
    echo The tests failed: not building.
    exit /b 1
)

echo Building...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name pyraceresults ^
    --add-data "%CD%\app\resources;app\resources" ^
    --distpath dist --workpath build --specpath build ^
    main.py
if errorlevel 1 exit /b 1

echo.
echo Done: %CD%\dist\pyraceresults.exe
echo Copy it anywhere and double-click it to run.
