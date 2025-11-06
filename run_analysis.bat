@echo off
setlocal enabledelayedexpansion

rem =========================================
rem  Configurações iniciais
rem =========================================
set "SCRIPT_DIR=%~dp0"
set "ATUALIZAR_DADOS=false"
set "APENAS_VISUALIZACOES=false"
set "QUANTIDADE_RANKINGS=15"
set "EXPORTAR_DADOS=false"

rem =========================================
rem  Processar parâmetros
rem =========================================
:process_args
if "%~1"=="" goto fim_args

if "%~1"=="--atualizar-dados" (
    set "ATUALIZAR_DADOS=true"
    shift
    goto process_args
)

if "%~1"=="--apenas-visualizacoes" (
    set "APENAS_VISUALIZACOES=true"
    shift
    goto process_args
)

if "%~1"=="--quantidade-rankings" (
    set "QUANTIDADE_RANKINGS=%~2"
    shift
    shift
    goto process_args
)

if "%~1"=="--exportar-dados" (
    set "EXPORTAR_DADOS=true"
    shift
    goto process_args
)

echo Parâmetro desconhecido: %~1
echo Parâmetros válidos: --atualizar-dados --apenas-visualizacoes --quantidade-rankings N --exportar-dados
exit /b 1

:fim_args

rem =========================================
rem  Cabeçalho
rem =========================================
echo =========================================
echo   ANALISADOR DE AÇÕES - INICIANDO
echo =========================================

rem =========================================
rem  Verificar arquivo principal
rem =========================================
cd /d "%SCRIPT_DIR%"
if not exist "main.py" (
    echo ERRO: Arquivo principal do sistema não encontrado em %SCRIPT_DIR%
    echo 💡 Certifique-se de que o nome do arquivo principal está correto
    exit /b 1
)

rem =========================================
rem  Construir comando
rem =========================================
set "COMANDO=python main.py"

if "%ATUALIZAR_DADOS%"=="true" (
    set "COMANDO=!COMANDO! --atualizar-dados"
)

if "%APENAS_VISUALIZACOES%"=="true" (
    set "COMANDO=!COMANDO! --apenas-visualizacoes"
)

if not "%QUANTIDADE_RANKINGS%"=="15" (
    set "COMANDO=!COMANDO! --quantidade-rankings %QUANTIDADE_RANKINGS%"
)

if "%EXPORTAR_DADOS%"=="true" (
    set "COMANDO=!COMANDO! --exportar-dados"
)

echo Executando: !COMANDO!
echo.

rem =========================================
rem  Executar comando
rem =========================================
!COMANDO!
if %errorlevel%==0 (
    echo.
    echo ✅ Análise concluída com sucesso!
) else (
    echo.
    echo ❌ ERRO: Houve um problema na execução.
    exit /b 1
)

endlocal
