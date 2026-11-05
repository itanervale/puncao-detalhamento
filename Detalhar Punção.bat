@echo off
rem Abre a janela do detalhamento de armadura de punção (DWG TQS)
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe" "%~dp0janela_puncao.pyw" %*
) else (
    start "" pythonw "%~dp0janela_puncao.pyw" %*
)
