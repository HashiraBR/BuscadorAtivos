@echo off
REM =========================================
REM  ANALISADOR DE AÇÕES - INICIANDO (Windows)
REM =========================================

REM Descobrir o diretório onde o script está localizado
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%" || (
    echo ERRO: Nao foi possivel acessar o diretorio do script!
    exit /b 1
)

REM Verificar se o main.py existe
if not exist "main.py" (
    echo ERRO: Arquivo main.py nao encontrado em "%SCRIPT_DIR%"
    exit /b 1
)

REM Variáveis de controle
set NO_CACHE=false
set APENAS_GRAFICOS=false

REM Processar parâmetros
:parse
if "%~1"=="" goto after_parse
if "%~1"=="--no-cache" (
    set NO_CACHE=true
    shift
    goto parse
)
if "%~1"=="--apenas-graficos" (
    set APENAS_GRAFICOS=true
    shift
    goto parse
)
echo Parametro desconhecido: %~1
exit /b 1
:after_parse

REM Construir comando
set COMANDO=python main.py

if "%NO_CACHE%"=="true" (
    set COMANDO=%COMANDO% --no-cache
)

if "%APENAS_GRAFICOS%"=="true" (
    set COMANDO=%COMANDO% --apenas-graficos
)

echo Executando: %COMANDO%
%COMANDO%

if %ERRORLEVEL%==0 (
    echo Analise concluida com sucesso!
) else (
    echo ERRO: Houve um problema na execucao.
)
