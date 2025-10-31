#!/bin/bash

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATUALIZAR_DADOS=false
APENAS_VISUALIZACOES=false
QUANTIDADE_RANKINGS=15
EXPORTAR_DADOS=false

# Processar parâmetros
while [[ $# -gt 0 ]]; do
    case $1 in
        --atualizar-dados)
            ATUALIZAR_DADOS=true
            shift
            ;;
        --apenas-visualizacoes)
            APENAS_VISUALIZACOES=true
            shift
            ;;
        --quantidade-rankings)
            QUANTIDADE_RANKINGS="$2"
            shift 2
            ;;
        --exportar-dados)
            EXPORTAR_DADOS=true
            shift
            ;;
        *)
            echo "Parâmetro desconhecido: $1"
            echo "Parâmetros válidos: --atualizar-dados --apenas-visualizacoes --quantidade-rankings N --exportar-dados"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "  ANALISADOR DE AÇÕES - INICIANDO"
echo "========================================="

# Descobrir o diretório onde o script está localizado
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Entrar no diretório do script
cd "$SCRIPT_DIR" || {
    echo "ERRO: Não foi possível acessar o diretório do script!"
    exit 1
}

# Verificar se o arquivo principal existe
if [ ! -f "main.py" ]; then
    echo "ERRO: Arquivo principal do sistema não encontrado em $SCRIPT_DIR"
    echo "💡 Certifique-se de que o nome do arquivo principal está correto"
    exit 1
fi

# Construir comando
COMANDO="python3 main.py"

if [ "$ATUALIZAR_DADOS" = true ]; then
    COMANDO="$COMANDO --atualizar-dados"
fi

if [ "$APENAS_VISUALIZACOES" = true ]; then
    COMANDO="$COMANDO --apenas-visualizacoes"
fi

if [ "$QUANTIDADE_RANKINGS" != "15" ]; then
    COMANDO="$COMANDO --quantidade-rankings $QUANTIDADE_RANKINGS"
fi

if [ "$EXPORTAR_DADOS" = true ]; then
    COMANDO="$COMANDO --exportar-dados"
fi

echo "Executando: $COMANDO"
echo ""

$COMANDO

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Análise concluída com sucesso!"
else
    echo ""
    echo "❌ ERRO: Houve um problema na execução."
    exit 1
fi