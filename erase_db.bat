@echo off
echo Executando script de limpeza dos módulos TI e Funcionários...
echo ATENÇÃO: Este script irá remover dados do banco de dados!
echo.

call venv\Scripts\activate.bat
python erase_db.py
echo.
pause 