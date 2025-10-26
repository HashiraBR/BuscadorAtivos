# Analysis of Stock Market Shares

Um analisador fundamentalista de acoes brasileiras que utiliza multiplas metodologias de valuation para identificar oportunidades de investimento.

## Funcionalidades

### Metodologias Implementadas
- **Graham**: Baseado na metodologia de Benjamin Graham
- **Barsi**: Foco em dividendos e preco teto
- **PL Descontado**: Analise setorial comparativa

### Análises Geradas
- Precos teto e margens de seguranca para cada metodologia
- Rankings WSM (Weighted Sum Model) com diferentes ponderacoes
- Graficos comparativos e relatorios visuais
- Filtros personalizaveis por acao

## Instalação

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### Dependências
```pip install pandas numpy matplotlib seaborn fundamentus```

## Estrutura do Projeto

AnalysisOfStockMarketShares/
├── run_analysis.sh
├── run_analysis.bat
├── main.py
├── ignorar_acoes.txt
├── data/
│   └── download/
│   └── analises/
├── methodologies/
│   ├── graham.py
│   ├── barsi.py
│   └── pl_descontado.py
└── visualization/
    └── visualizador.py

## Como Usar

### Execução Rápida
#### Linux/Mac
```./run_analysis.sh```

#### Windows
```run_analysis.bat```

#### Execução Manual
```python main.py```

### Parâmetros Opcionais
#### Atualizar dados (ignorar cache)
```./run_analysis.sh --no-cache```

#### Apenas gerar gráficos (usar dados existentes)
```./run_analysis.sh --apenas-graficos```

## Configuração

### Personalizar Ações Excluídas
Edite o arquivo `ignorar_acoes.txt`:
* Lista de ações para remover da análise
* Use `#` para comentar linhas

```
LIGT3
OIBR3
IRBR3
# MGLU3 - ação comentada (não será removida)
```

## Metodologias

### Graham
- Cálculo: √(22.5 × LPA × VPA)
- Foco: Valor intrinseco e margem de segurança

### Barsi
- Cálculo: (Payout × LPA) / DY_Desejado
- Foco: Dividend yield e pagamento consistente

### PL Descontado
- Cálculo: Comparacao do PL atual com media do subsetor
- Foco: Oportunidades setoriais

## Rankings WSM

O sistema gera dois rankings com ponderações diferentes:

1. **Graham (60%) + Barsi (40%)**
2. **Graham (50%) + Barsi (20%) + PL Descontado (30%)**

## Saídas

### Arquivos Gerados
- data/download/ativos_DD_MM_YYYY.csv: Dataset completo com analises
- data/analises/ranking_metodologias.png: Graficos individuais
- data/analises/ranking_wsm_pesos.png: Comparacao WSM
- data/analises/ranking_consolidado.png: Visao consolidada

### Console
- Ranking das melhores oportunidades por metodologia
- Estatisticas de margens positivas
- Ações removidas por filtro


## Personalização

### Modificar Pesos WSM
Edite o metodo `criar_graficos_wsm_lado_a_lado em visualization/visualizador.py`

### Adicionar Novas Metodologias
1. Crie nova classe em `methodologies/`
2. Importe no `main.py`
3. Adicione na função `adicionar_analises`

## Troubleshooting

### Erro de Dependências
```pip install --upgrade pandas numpy matplotlib seaborn fundamentus```

### Erro de Permissão (Linux)
```chmod +x run_analysis.sh```

### Arquivo de Exclusão Não Encontrado
- Certifique-se que `ignorar_acoes.txt` está na raíz do projeto

## Licença
Projeto para fins educacionais e de pesquisa.