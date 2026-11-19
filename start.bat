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
    call env\Scripts\pip install --quiet --no-index --find-links ./packages -r packages/requirements.txt
    rmdir /s /q "packages"
)

:: Avvio
call env\Scripts\python flask\tracert.py