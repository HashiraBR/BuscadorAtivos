@echo off
chcp 65001 > nul

set NO_CACHE=0
set APENAS_GRAFICOS=0

:parse_args
if "%1"=="" goto main
if "%1"=="--no-cache" set NO_CACHE=1
if "%1"=="--apenas-graficos" set APENAS_GRAFICOS=1
shift
goto parse_args

:main
echo =========================================
echo    ANALISADOR DE AÇÕES - INICIANDO
echo =========================================

if not exist "main.py" (
    echo ERRO: Execute este script da pasta raiz do projeto!
    pause
    exit /b 1
)

echo Diretorio atual: %CD%

set COMANDO=python main.py

if "%NO_CACHE%"=="1" set COMANDO=%COMANDO% --no-cache
if "%APENAS_GRAFICOS%"=="1" set COMANDO=%COMANDO% --apenas-graficos

echo Executando: %COMANDO%
%COMANDO%

if %errorlevel% == 0 (
    echo Analise concluida com sucesso!
) else (
    echo ERRO: Houve um problema na execucao.
)

echo =========================================
pause