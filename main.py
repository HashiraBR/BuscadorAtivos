from data.fundamentus import DataProviderFundamentus
from methodologies.graham import AnalisadorGraham
from methodologies.barsi import AnalisadorBarsi
from methodologies.pl_descontado import AnalisadorPLDescontado
from methodologies.wsm_fundamentalista import AnalisadorFundamentalistaCompleto, mostrar_pesos_detalhados
from visualization.visualizador import VisualizadorAnalises
from visualization.visualizador_wsm import VisualizadorScoreFundamentalista
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import os


class AnalisadorAcoes:
    def __init__(self):
        self.data_provider = DataProviderFundamentus()

    def parse_arguments(self):
        """Configura e parseia os argumentos de linha de comando"""
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

    def carregar_ignorar_acoes(self, arquivo='ignorar_acoes.txt'):
        """Carrega lista de ações para excluir de um arquivo de texto"""
        acoes_excluir = []

        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
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

    def adicionar_analises(self, df_original):
        """Adiciona colunas de análise ao DataFrame"""
        print("Adicionando analises ao dataset...")

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

                # Aplicar metodologias
                self._aplicar_graham(df, index, ticker, cotacao_num, lpa_num, vpa_num)
                self._aplicar_barsi(df, index, ticker, cotacao_num, lpa_num, payout_num)
                self._aplicar_pl_descontado(df, index, ticker, cotacao_num, lpa_num, pl_medio_num)

            except Exception as e:
                print(f"Erro em {row.get('Papel', 'Unknown')}: {e}")
                continue

        # Converter colunas finais para numérico
        colunas_numericas = ['graham_margem', 'barsi_margem', 'pl_subsetor_margem']
        for coluna in colunas_numericas:
            df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

        return df

    def _aplicar_graham(self, df, index, ticker, cotacao, lpa, vpa):
        """Aplica metodologia de Graham"""
        if (pd.notna(cotacao) and pd.notna(lpa) and pd.notna(vpa) and
                lpa > 0 and vpa > 0 and cotacao > 0):

            graham = AnalisadorGraham(ticker, cotacao, lpa, vpa)
            graham_teto = graham.calcular_graham_number()
            margem = graham.calcular_margem_seguranca()

            if graham_teto is not None:
                df.loc[index, 'graham_teto'] = float(graham_teto)
            if margem is not None:
                df.loc[index, 'graham_margem'] = float(margem['percentual'])

    def _aplicar_barsi(self, df, index, ticker, cotacao, lpa, payout):
        """Aplica metodologia de Barsi"""
        if (pd.notna(cotacao) and pd.notna(lpa) and pd.notna(payout) and
                lpa > 0 and cotacao > 0 and payout > 0):

            barsi = AnalisadorBarsi(ticker, cotacao, lpa, payout)
            barsi_teto = barsi.calcular_preco_teto()
            margem = barsi.calcular_margem_seguranca()

            if barsi_teto is not None:
                df.loc[index, 'barsi_teto'] = float(barsi_teto)
            if margem is not None:
                df.loc[index, 'barsi_margem'] = float(margem['percentual'])

    def _aplicar_pl_descontado(self, df, index, ticker, cotacao, lpa, pl_medio):
        """Aplica metodologia de PL Descontado"""
        if (pd.notna(cotacao) and pd.notna(lpa) and pd.notna(pl_medio) and
                lpa > 0 and cotacao > 0):

            pl_desc = AnalisadorPLDescontado(ticker, cotacao, lpa, pl_medio)
            analise = pl_desc.analise_completa()

            if analise['preco_alvo'] is not None:
                df.loc[index, 'pl_subsetor_alvo'] = float(analise['preco_alvo'])
            if analise['margem_seguranca'] is not None:
                df.loc[index, 'pl_subsetor_margem'] = float(analise['margem_seguranca']['percentual'])

    def wsm_analise_completa(self, df, top_n):
        """Executa análise completa WSM e retorna resultados COMPLETOS"""
        print("\n" + "=" * 60)
        print("ANALISE FUNDAMENTALISTA COMPLETA - WSM")
        print("=" * 60)

        # Mostrar estrutura de pesos
        pesos_df = mostrar_pesos_detalhados()
        print("\nESTRUTURA DE PESOS:")
        print(pesos_df.to_string(index=False))

        # Executar análise - isso retorna o DataFrame COMPLETO com scores
        analisador = AnalisadorFundamentalistaCompleto(df)
        resultados_completos = analisador.analisar()  # DataFrame completo com todas as empresas

        print("=" * 80)

        # Preparar apenas as top empresas para exibição no terminal
        top_empresas = self._preparar_top_empresas(resultados_completos, top_n)
        self._exibir_resultados(resultados_completos, top_empresas)

        # CORREÇÃO: Retornar o DataFrame COMPLETO e o top empresas
        return resultados_completos, top_empresas

    def _preparar_top_empresas(self, resultados, top_n):
        """Prepara dataframe com top empresas formatadas"""
        top_empresas = resultados[
            ['Empresa', 'Papel', 'Subsetor', 'Score_WSM', 'Margem_Graham', 'Margem_Barsi', 'P_L', 'ROE']
        ].head(top_n)

        # Formatar números
        colunas_formatar = ['Score_WSM', 'Margem_Graham', 'Margem_Barsi', 'P_L', 'ROE']
        for coluna in colunas_formatar:
            top_empresas[coluna] = top_empresas[coluna].round(2)

        return top_empresas

    def _exibir_resultados(self, resultados, top_empresas):
        """Exibe resultados formatados"""
        print(top_empresas.to_string(index=False))

        print(f"\nESTATISTICAS DA ANALISE:")
        print(f"Total de empresas analisadas: {len(resultados)}")
        print(f"Score medio: {resultados['Score_WSM'].mean():.2f}")
        print(f"Score maximo: {resultados['Score_WSM'].max():.2f}")
        print(f"Score minimo: {resultados['Score_WSM'].min():.2f}")

    def gerar_visualizacoes(self, df_visualizacao, top_n, apenas_graficos=False):
        """Gera todas as visualizações usando o DataFrame preparado"""
        print("\nGerando gráficos da análise WSM...")

        # Verificar se temos dados suficientes para o WSM
        if 'Score_WSM' in df_visualizacao.columns:
            visualizador_wsm = VisualizadorScoreFundamentalista(df_visualizacao)
            figs = visualizador_wsm.gerar_relatorio_completo(
                top_n=top_n,
                save_path="data/analises/wsm_completo"
            )

            # Salvar resultados completos
            self._salvar_resultados(df_visualizacao, "data/analises/resultados_wsm_completo.csv")
        else:
            print("Aviso: Coluna 'Score_WSM' não encontrada para gerar gráficos WSM")
            figs = []

        # Gerar visualizações originais (se não for apenas gráficos)
        if not apenas_graficos:
            print("\nGerando visualizações originais...")

            # Verificar colunas necessárias para o VisualizadorAnalises
            colunas_necessarias = ['graham_margem', 'barsi_margem', 'pl_subsetor_margem']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_visualizacao.columns]

            if colunas_faltantes:
                print(f"Aviso: Colunas faltantes para visualização original: {colunas_faltantes}")
                print("Gerando apenas gráficos disponíveis...")

            try:
                visualizador = VisualizadorAnalises(df_visualizacao)
                visualizador.gerar_relatorio_completo(top_n=top_n)
            except KeyError as e:
                print(f"Erro ao gerar visualizações originais: {e}")
                print("Continuando com outras visualizações...")

        return figs

    def _salvar_resultados(self, df, caminho):
        """Salva resultados em arquivo CSV"""
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            df.to_csv(caminho, index=False)
            print(f"Resultados completos salvos em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar resultados: {e}")

    def exibir_estatisticas_rapidas(self, df):
        """Exibe estatísticas rápidas do dataset"""
        print(f"\nRESUMO:")
        print(f"Margem Graham positiva: {(df['graham_margem'] > 0).sum()}")
        print(f"Margem Barsi positiva: {(df['barsi_margem'] > 0).sum()}")
        print(f"Desconto PL: {(df['pl_subsetor_margem'] > 0).sum()}")

    def executar(self):
        """Método principal que executa toda a análise"""
        args = self.parse_arguments()
        top_n = args.top_n

        print("Argumentos recebidos:")
        print(f"  --no-cache: {args.no_cache}")
        print(f"  --apenas-graficos: {args.apenas_graficos}")
        print(f"  --top-n: {args.top_n}")

        # Carregar dados
        usar_cache = not args.no_cache
        df_original = self.data_provider.carregar_dados(usar_cache=usar_cache)

        if df_original is None:
            print("Erro: Não foi possível carregar os dados.")
            return

        # Processar dados
        acoes_ignorar = self.carregar_ignorar_acoes()
        df_original = df_original[~df_original['Papel'].isin(acoes_ignorar)]
        print(f"Total de ativos: {len(df_original)}")

        # Adicionar análises
        if 'graham_margem' not in df_original.columns:
            df = self.adicionar_analises(df_original)
        else:
            df = df_original

        # Salvar dataset atualizado
        caminho_original = self.data_provider._get_nome_arquivo()
        df.to_csv(caminho_original, index=False)
        print(f"Dataset atualizado: {caminho_original}")

        # Exibir estatísticas
        self.exibir_estatisticas_rapidas(df)

        # Executar análise WSM
        df_completo_com_scores, df_top_empresas = self.wsm_analise_completa(df, top_n)

        # CORREÇÃO: Garantir que todas as colunas necessárias estejam presentes
        df_para_visualizacao = self._preparar_dataframe_visualizacao(df, df_completo_com_scores)

        # Gerar visualizações
        self.gerar_visualizacoes(df_para_visualizacao, top_n, args.apenas_graficos)

        # Mostrar gráficos
        plt.show()

    def _preparar_dataframe_visualizacao(self, df_original, df_wsm):
        """Prepara DataFrame com todas as colunas necessárias para visualização"""
        # Juntar os dados originais com os scores do WSM
        df_visualizacao = df_original.copy()

        # Adicionar coluna de score do WSM se existir no df_wsm
        if 'Score_WSM' in df_wsm.columns:
            # Fazer merge baseado no Papel
            scores = df_wsm[['Papel', 'Score_WSM']].drop_duplicates()
            df_visualizacao = df_visualizacao.merge(scores, on='Papel', how='left')

        # Verificar colunas necessárias para o VisualizadorAnalises
        colunas_necessarias = ['graham_margem', 'barsi_margem', 'pl_subsetor_margem', 'Score_WSM']

        print("\nVERIFICAÇÃO DE COLUNAS PARA VISUALIZAÇÃO:")
        for coluna in colunas_necessarias:
            if coluna in df_visualizacao.columns:
                print(f"✓ {coluna}: presente")
            else:
                print(f"✗ {coluna}: ausente")

        return df_visualizacao


def main():
    """Função principal"""
    analisador = AnalisadorAcoes()
    analisador.executar()


if __name__ == "__main__":
    main()