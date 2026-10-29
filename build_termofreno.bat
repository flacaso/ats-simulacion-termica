@echo off
setlocal
cd /d "%~dp0"

set NAME=Termofreno
set VERSION=1.0.0

if not exist termofreno.pyw (
  echo No encuentro termofreno.pyw. Pon este .bat en la misma carpeta que el programa.
  pause
  exit /b 1
)
if not exist version_info.txt (
  echo Falta version_info.txt en esta carpeta.
  pause
  exit /b 1
)

echo.
echo [1/5] Creando entorno limpio (.venv_build)...
if exist .venv_build rmdir /s /q .venv_build
py -m venv .venv_build || goto :error
call .venv_build\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
pip install pyinstaller pywebview pystray pillow requests pyvjoy inputs segno || goto :error

echo.
echo [2/5] Compilando con PyInstaller (onedir, sin UPX, sin consola)...
pyinstaller --noconfirm --clean --onedir --noconsole --noupx ^
  --name %NAME% ^
  --icon icono_frenos.ico ^
  --version-file version_info.txt ^
  --collect-all pyvjoy ^
  --collect-all webview ^
  --hidden-import pystray._win32 ^
  termofreno.pyw || goto :error

echo.
echo [3/5] Copiando los HTML e imagenes junto al .exe (el programa los busca ahi)...
for %%F in (ventana_principal.html mini_ventana.html movil.html obs_top.html obs_bottom.html sim_panel_button_box.html sim_panel_minimalista.html logo_programa.png icono_frenos.ico) do (
  if exist "%%F" (copy /y "%%F" "dist\%NAME%\" >nul) else (echo AVISO: no encuentro %%F)
)

echo.
echo [4/5] Creando el .zip para GitHub...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%NAME%' -DestinationPath 'dist\%NAME%_v%VERSION%_win64.zip' -Force" || goto :error

echo.
echo [5/5] Hashes SHA-256 (pegalos en la descripcion del release):
certutil -hashfile "dist\%NAME%\%NAME%.exe" SHA256
certutil -hashfile "dist\%NAME%_v%VERSION%_win64.zip" SHA256

echo.
echo LISTO.
echo   Carpeta:  dist\%NAME%\
echo   Zip:      dist\%NAME%_v%VERSION%_win64.zip
echo Sube dist\%NAME%\%NAME%.exe y el .zip a VirusTotal para revisar.
pause
exit /b 0

:error
echo.
echo ERROR: algo fallo. Copia el mensaje de arriba y pasamelo.
pause
exit /b 1
