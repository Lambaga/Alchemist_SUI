@echo off
echo Intelligente Python Cache-Bereinigung...
echo.

echo Starte intelligente Analyse...
python smart_cache_cleaner.py --mode=smart

echo.
echo Fallback: Traditionelle Bereinigung...

echo.
echo Lösche .pyc Dateien...
for /r %%i in (*.pyc) do (
    del "%%i" 2>nul
    if exist "%%i" (
        echo Konnte nicht löschen: %%i
    )
)

echo.
echo Lösche __pycache__ Ordner...
for /f "delims=" %%i in ('dir /s /b /ad __pycache__ 2^>nul') do (
    rd /s /q "%%i" 2>nul
    if exist "%%i" (
        echo Konnte nicht löschen: %%i
    )
)

echo.
echo Lösche .pyo Dateien...
for /r %%i in (*.pyo) do (
    del "%%i" 2>nul
)

echo.
echo Cache-Bereinigung abgeschlossen!
echo.
pause
