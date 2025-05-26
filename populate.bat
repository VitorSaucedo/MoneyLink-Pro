@echo off
echo Executando script de população dos módulos TI e Funcionários...
echo.
echo Serão criadas as seguintes configurações:
echo - 5 Lojas: Sede, Salgado Filho, Santa Maria, Cachoeirinha e São Leopoldo
echo - 3 Salas com ilhas e PAs configuradas assim:
echo   * Sala 1: Ilha 1 com 10 PAs, Ilha 2 com 8 PAs
echo   * Sala 2: Ilha 1 com 12 PAs, Ilha 2 com 12 PAs
echo   * Sala 3: Ilha 1 com 6 PAs
echo - Total de 48 PAs com funcionários e periféricos atribuídos
echo.

call venv\Scripts\activate.bat
python populate.py
echo.
pause 