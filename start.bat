@echo off

if exist "packages.zip" (
    tar -xf "packages.zip" -C "."
    del /f packages.zip
)

:: Controllo su ambiente virtuale
if not exist "env" (
    echo [1/3] - Creazione ambiente virtuale...
    python -m venv env

    echo [2/3] - Installazione flask, geoip2...
    call env\Scripts\activate.bat
    pip install --quiet --no-index --find-links./packages flask geoip2
    del /f "packages"
)

:: Avvio
call env\Scripts\python flask\tracert.py