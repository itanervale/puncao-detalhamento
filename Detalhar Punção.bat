@echo off
rem Abre a janela do detalhamento de armadura de puncao (DWG TQS).
rem Procura o Python 3.13 (o da TQSPythonInterface): instalacao do usuario, de todos os usuarios,
rem lancador "pyw -3.13" e, por ultimo, o pythonw do PATH.
cd /d "%~dp0"
set "PYW=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
if exist "%PYW%" goto abrir
set "PYW=%ProgramFiles%\Python313\pythonw.exe"
if exist "%PYW%" goto abrir
where pyw >nul 2>nul
if errorlevel 1 goto path
start "" pyw -3.13 "%~dp0janela_puncao.pyw" %*
goto :eof
:path
start "" pythonw "%~dp0janela_puncao.pyw" %*
goto :eof
:abrir
start "" "%PYW%" "%~dp0janela_puncao.pyw" %*
