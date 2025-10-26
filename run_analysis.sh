#!/bin/bash

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NO_CACHE=false
APENAS_GRAFICOS=false

# Processar parâmetros
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --apenas-graficos)
            APENAS_GRAFICOS=true
            shift
            ;;
        *)
            echo "Parâmetro desconhecido: $1"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "  ANALISADOR DE AÇÕES - INICIANDO"
echo "========================================="

# Verificar se estamos no diretório correto
if [ ! -f "main.py" ]; then
    echo "ERRO: Execute este script da pasta raiz do projeto!"
    exit 1
fi

# Construir comando
COMANDO="python3 main.py"

if [ "$NO_CACHE" = true ]; then
    COMANDO="$COMANDO --no-cache"
fi

if [ "$APENAS_GRAFICOS" = true ]; then
    COMANDO="$COMANDO --apenas-graficos"
fi

echo "Executando: $COMANDO"
$COMANDO

if [ $? -eq 0 ]; then
    echo "Análise concluída com sucesso!"
else
    echo "ERRO: Houve um problema na execução."
fi