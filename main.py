from data.fundamentus import DataProviderFundamentus
from methodologies.graham import AnalisadorGraham
from methodologies.barsi import AnalisadorBarsi
from methodologies.pl_descontado import AnalisadorPLDescontado
from visualization.visualizador import VisualizadorAnalises
import pandas as pd
import argparse


def parse_arguments():
    """
    Configura e parseia os argumentos de linha de comando
    """
    parser = argparse.ArgumentParser(description='Analisador de Acoes - Multiple Methodologies')

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Forcar atualizacao dos dados (ignorar cache)'
    )

    parser.add_argument(
        '--apenas-graficos',
        action='store_true',
        help='Apenas gerar graficos (usar dados existentes)'
    )

    parser.add_argument(
        '--top-n',
        type=int,
        default=15,
        help='Numero de acoes no ranking (padrao: 15)'
    )

    return parser.parse_args()

def carregar_ignorar_acoes(arquivo='ignorar_acoes.txt'):
    """
    Carrega lista de ações para excluir de um arquivo de texto
    """
    acoes_excluir = []

    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                # Ignorar linhas vazias e comentários
                if linha and not linha.startswith('#'):
                    acoes_excluir.append(linha.upper())

        print(f"Carregadas {len(acoes_excluir)} ações para excluir do arquivo: {arquivo}")
        return acoes_excluir

    except FileNotFoundError:
        print(f"Arquivo de exclusão não encontrado: {arquivo}")
        print("Nenhuma ação será excluída.")
        return []
    except Exception as e:
        print(f"Erro ao carregar arquivo de exclusão: {e}")
        return []

def adicionar_analises(df_original):
    """
    Adiciona colunas de análise ao DataFrame
    """
    print("Adicionando analises ao dataset...")

    # Criar cópia explícita para evitar warnings
    df = df_original.copy()

    # Inicializar novas colunas
    df = df.assign(
        graham_teto=None,
        graham_margem=None,
        barsi_teto=None,
        barsi_margem=None,
        pl_subsetor_alvo=None,
        pl_subsetor_margem=None
    )

    for index, row in df.iterrows():
        try:
            ticker = row.get('Papel')
            cotacao = row.get('Cotacao')
            lpa = row.get('LPA')
            vpa = row.get('VPA')
            payout = row.get('Payout_Medio')
            pl_medio = row.get('PL_Medio_Subsetor')

            # Converter para numérico
            cotacao_num = pd.to_numeric(cotacao, errors='coerce')
            lpa_num = pd.to_numeric(lpa, errors='coerce')
            vpa_num = pd.to_numeric(vpa, errors='coerce')
            payout_num = pd.to_numeric(payout, errors='coerce')
            pl_medio_num = pd.to_numeric(pl_medio, errors='coerce')

            # Graham - apenas se todos os valores forem válidos e positivos
            if (pd.notna(cotacao_num) and pd.notna(lpa_num) and pd.notna(vpa_num) and
                    lpa_num > 0 and vpa_num > 0 and cotacao_num > 0):

                graham = AnalisadorGraham(ticker, cotacao_num, lpa_num, vpa_num)
                graham_teto = graham.calcular_graham_number()
                margem = graham.calcular_margem_seguranca()

                if graham_teto is not None:
                    df.loc[index, 'graham_teto'] = float(graham_teto)
                if margem is not None:
                    df.loc[index, 'graham_margem'] = float(margem['percentual'])

            # Barsi - apenas se todos os valores forem válidos e positivos
            if (pd.notna(cotacao_num) and pd.notna(lpa_num) and pd.notna(payout_num) and
                    lpa_num > 0 and cotacao_num > 0 and payout_num > 0):

                barsi = AnalisadorBarsi(ticker, cotacao_num, lpa_num, payout_num)
                barsi_teto = barsi.calcular_preco_teto()
                margem = barsi.calcular_margem_seguranca()

                if barsi_teto is not None:
                    df.loc[index, 'barsi_teto'] = float(barsi_teto)
                if margem is not None:
                    df.loc[index, 'barsi_margem'] = float(margem['percentual'])

            # PL Descontado - apenas se todos os valores forem válidos e positivos
            if (pd.notna(cotacao_num) and pd.notna(lpa_num) and pd.notna(pl_medio_num) and
                    lpa_num > 0 and cotacao_num > 0):

                pl_desc = AnalisadorPLDescontado(ticker, cotacao_num, lpa_num, pl_medio_num)
                analise = pl_desc.analise_completa()

                if analise['preco_alvo'] is not None:
                    df.loc[index, 'pl_subsetor_alvo'] = float(analise['preco_alvo'])
                if analise['margem_seguranca'] is not None:
                    df.loc[index, 'pl_subsetor_margem'] = float(analise['margem_seguranca']['percentual'])

        except Exception as e:
            print(f"Erro em {row.get('Papel', 'Unknown')}: {e}")
            continue

    # Converter colunas finais para numérico
    df['graham_margem'] = pd.to_numeric(df['graham_margem'], errors='coerce')
    df['barsi_margem'] = pd.to_numeric(df['barsi_margem'], errors='coerce')
    df['pl_subsetor_margem'] = pd.to_numeric(df['pl_subsetor_margem'], errors='coerce')

    return df


def main():
    args = parse_arguments()

    print("Argumentos recebidos:")
    print(f"  --no-cache: {args.no_cache}")
    print(f"  --apenas-graficos: {args.apenas_graficos}")
    print(f"  --top-n: {args.top_n}")

    # Carregar dados
    data_provider = DataProviderFundamentus()

    usar_cache = not args.no_cache
    df_original = data_provider.carregar_dados(usar_cache=usar_cache)

    if df_original is not None:

        acoes_ignorar = carregar_ignorar_acoes()

        # Remover ações da lista de exclusão
        df_original = df_original[~df_original['Papel'].isin(acoes_ignorar)]

        print(f"Total de ativos: {len(df_original)}")

        # Adicionar análises (se ainda não tiver)
        if 'graham_margem' not in df_original.columns:
            df = adicionar_analises(df_original)
        else:
            df = df_original

        # Sobrescrever o arquivo original
        caminho_original = data_provider._get_nome_arquivo()
        df.to_csv(caminho_original, index=False)
        print(f"Dataset atualizado: {caminho_original}")

        # Estatísticas rápidas
        print(f"\nRESUMO:")
        print(f"Margem Graham positiva: {(df['graham_margem'] > 0).sum()}")
        print(f"Margem Barsi positiva: {(df['barsi_margem'] > 0).sum()}")
        print(f"Desconto PL: {(df['pl_subsetor_margem'] > 0).sum()}")

        # Gerar visualizações
        visualizador = VisualizadorAnalises(df)
        visualizador.gerar_relatorio_completo(top_n=15)

if __name__ == "__main__":
    main()