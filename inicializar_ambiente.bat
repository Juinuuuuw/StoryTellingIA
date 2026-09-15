@echo off

echo Iniciando o ambiente do projeto...

:: 0. Ollama
curl.exe -s http://127.0.0.1:11434/api/version >nul 2>&1
if %errorlevel% neq 0 (
    echo Iniciando o Ollama...
    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
    timeout /t 3 /nobreak >nul
)

:: 1. Servidor IA
start "Servidor IA" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && cd servidor && python servidor_ia.py"

:: 2. Forge
if exist "D:\Forge\run.bat" (
    start "Forge WebUI" cmd /k "cd /d D:\Forge && call run.bat"
) else if exist "C:\Users\%USERNAME%\Forge\webui-user.bat" (
    start "Forge WebUI" cmd /k "cd /d C:\Users\%USERNAME%\Forge && webui-user.bat"
) else (
    echo [AVISO] Forge WebUI nao encontrado no caminho padrao.
)

:: 3. Story Client
start "Story Client" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && node story_client.js"

echo Todos os terminais foram abertos!