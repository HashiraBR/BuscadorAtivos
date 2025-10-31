from data.provedor_dados_fundamentus import ProvedorDadosFundamentus
from metodologias.analisador_graham import AnalisadorGraham
from metodologias.analisador_barsi import AnalisadorBarsi
from metodologias.analisador_pl_descontado import AnalisadorPLDescontado
from metodologias.analisador_fundamentalista_wsm import AnalisadorFundamentalistaWSM, exibir_estrutura_pesos
from visualizacao.gerador_visualizacoes import GeradorVisualizacoes
from visualizacao.gerador_visualizacoes_wsm import GeradorVisualizacoesWSM
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import os
from datetime import datetime


class SistemaAnaliseFundamentalista:
    """
    Sistema principal de análise fundamentalista de ações
    Integra múltiplas metodologias de valuation e gera relatórios completos
    """

    def __init__(self):
        self.provedor_dados = ProvedorDadosFundamentus()
        self._configurar_ambiente()

    def _configurar_ambiente(self):
        """Configura os diretórios e ambiente necessário para a análise"""
        diretorios_necessarios = [
            "output/dados/analises",
            "output/dados/cache",
            "output/graficos"
        ]

        for diretorio in diretorios_necessarios:
            os.makedirs(diretorio, exist_ok=True)

        print("✅ Ambiente configurado com sucesso")

    def _processar_argumentos(self):
        """Processa e valida os argumentos da linha de comando"""
        analisador_argumentos = argparse.ArgumentParser(
            description='Sistema de Análise Fundamentalista - Integração Multi-Metodologias'
        )

        analisador_argumentos.add_argument(
            '--atualizar-dados',
            action='store_true',
            help='Forçar atualização dos dados (ignorar cache)'
        )

        analisador_argumentos.add_argument(
            '--apenas-visualizacoes',
            action='store_true',
            help='Apenas gerar visualizações (usar dados existentes)'
        )

        analisador_argumentos.add_argument(
            '--quantidade-rankings',
            type=int,
            default=15,
            help='Número de ações no ranking final (padrão: 15)'
        )

        analisador_argumentos.add_argument(
            '--exportar-dados',
            action='store_true',
            help='Exportar dados completos para Excel'
        )

        return analisador_argumentos.parse_args()

    def _carregar_lista_exclusoes(self, caminho_arquivo='config/lista_exclusoes.txt'):
        """
        Carrega lista de tickers para exclusão da análise

        Args:
            caminho_arquivo (str): Caminho para o arquivo de exclusões

        Returns:
            list: Lista de tickers a serem excluídos
        """
        tickers_excluir = []

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                for linha in arquivo:
                    linha = linha.strip()
                    # Ignora linhas vazias e comentários
                    if linha and not linha.startswith('#'):
                        tickers_excluir.append(linha.upper())

            print(f"📋 Lista de exclusões carregada: {len(tickers_excluir)} tickers")
            return tickers_excluir

        except FileNotFoundError:
            print(f"⚠️ Arquivo de exclusões não encontrado: {caminho_arquivo}")
            print("   Nenhum ticker será excluído da análise")
            return []
        except Exception as erro:
            print(f"❌ Erro ao carregar lista de exclusões: {erro}")
            return []

    def _aplicar_metodologias_valuation(self, dataframe_original):
        """
        Aplica múltiplas metodologias de valuation ao DataFrame

        Args:
            dataframe_original (pd.DataFrame): DataFrame com dados fundamentais

        Returns:
            pd.DataFrame: DataFrame com colunas de valuation adicionadas
        """
        print("\n🔍 Aplicando metodologias de valuation...")

        dataframe_analise = dataframe_original.copy()

        # Inicializar colunas de valuation
        colunas_valuation = [
            'preco_teto_graham', 'margem_seguranca_graham',
            'preco_teto_barsi', 'margem_seguranca_barsi',
            'preco_alvo_pl_setor', 'margem_seguranca_pl_setor'
        ]

        for coluna in colunas_valuation:
            dataframe_analise[coluna] = None

        total_ativos = len(dataframe_analise)
        ativos_processados = 0

        for indice, linha in dataframe_analise.iterrows():
            try:
                ticker = linha.get('ticker')
                preco_atual = linha.get('Cotacao')
                lucro_por_acao = linha.get('LPA')
                valor_patrimonial_por_acao = linha.get('VPA')
                payout_medio = linha.get('Payout_Medio')
                pl_medio_setor = linha.get('PL_Medio_Subsetor')

                # Converter para numérico
                preco_atual_numerico = pd.to_numeric(preco_atual, errors='coerce')
                lpa_numerico = pd.to_numeric(lucro_por_acao, errors='coerce')
                vpa_numerico = pd.to_numeric(valor_patrimonial_por_acao, errors='coerce')
                payout_numerico = pd.to_numeric(payout_medio, errors='coerce')
                pl_setor_numerico = pd.to_numeric(pl_medio_setor, errors='coerce')

                # Aplicar metodologias
                self._aplicar_metodologia_graham(
                    dataframe_analise, indice, ticker,
                    preco_atual_numerico, lpa_numerico, vpa_numerico
                )

                self._aplicar_metodologia_barsi(
                    dataframe_analise, indice, ticker,
                    preco_atual_numerico, lpa_numerico, payout_numerico
                )

                self._aplicar_metodologia_pl_descontado(
                    dataframe_analise, indice, ticker,
                    preco_atual_numerico, lpa_numerico, pl_setor_numerico
                )

                ativos_processados += 1
                if ativos_processados % 50 == 0:
                    print(f"   📊 Processados {ativos_processados}/{total_ativos} ativos...")

            except Exception as erro:
                print(f"   ⚠️ Erro ao processar {linha.get('ticker', 'Desconhecido')}: {erro}")
                continue

        # Garantir tipos numéricos nas colunas de margem
        colunas_margem = ['margem_seguranca_graham', 'margem_seguranca_barsi', 'margem_seguranca_pl_setor']
        for coluna in colunas_margem:
            dataframe_analise[coluna] = pd.to_numeric(dataframe_analise[coluna], errors='coerce')

        print(f"✅ Metodologias aplicadas: {ativos_processados}/{total_ativos} ativos processados")
        return dataframe_analise

    def _aplicar_metodologia_graham(self, dataframe, indice, ticker, preco_atual, lpa, vpa):
        """Aplica a metodologia de Benjamin Graham para valuation"""
        if (pd.notna(preco_atual) and pd.notna(lpa) and pd.notna(vpa) and
                lpa > 0 and vpa > 0 and preco_atual > 0):

            analisador_graham = AnalisadorGraham(ticker, preco_atual, lpa, vpa)
            preco_teto_graham = analisador_graham.calcular_numero_graham()
            margem_seguranca = analisador_graham.calcular_margem_seguranca()

            if preco_teto_graham is not None:
                dataframe.loc[indice, 'preco_teto_graham'] = float(preco_teto_graham)
            if margem_seguranca is not None:
                dataframe.loc[indice, 'margem_seguranca_graham'] = float(margem_seguranca['percentual'])

    def _aplicar_metodologia_barsi(self, dataframe, indice, ticker, preco_atual, lpa, payout):
        """Aplica a metodologia de Luiz Barsi para valuation"""
        if (pd.notna(preco_atual) and pd.notna(lpa) and pd.notna(payout) and
                lpa > 0 and preco_atual > 0 and payout > 0):

            analisador_barsi = AnalisadorBarsi(ticker, preco_atual, lpa, payout)
            preco_teto_barsi = analisador_barsi.calcular_preco_teto()
            margem_seguranca = analisador_barsi.calcular_margem_seguranca()

            if preco_teto_barsi is not None:
                dataframe.loc[indice, 'preco_teto_barsi'] = float(preco_teto_barsi)
            if margem_seguranca is not None:
                dataframe.loc[indice, 'margem_seguranca_barsi'] = float(margem_seguranca['percentual'])

    def _aplicar_metodologia_pl_descontado(self, dataframe, indice, ticker, preco_atual, lpa, pl_medio_setor):
        """Aplica metodologia de P/L descontado em relação ao setor"""
        if (pd.notna(preco_atual) and pd.notna(lpa) and pd.notna(pl_medio_setor) and
                lpa > 0 and preco_atual > 0):

            analisador_pl_desc = AnalisadorPLDescontado(ticker, preco_atual, lpa, pl_medio_setor)
            resultado_analise = analisador_pl_desc.executar_analise_completa()

            if resultado_analise['preco_alvo'] is not None:
                dataframe.loc[indice, 'preco_alvo_pl_setor'] = float(resultado_analise['preco_alvo'])
            if resultado_analise['margem_seguranca'] is not None:
                dataframe.loc[indice, 'margem_seguranca_pl_setor'] = float(
                    resultado_analise['margem_seguranca']['percentual'])

    def _executar_analise_fundamentalista_wsm(self, dataframe, quantidade_rankings):
        """
        Executa análise fundamentalista completa usando Weighted Scoring Model (WSM)

        Args:
            dataframe (pd.DataFrame): DataFrame com dados fundamentais
            quantidade_rankings (int): Número de empresas no ranking final

        Returns:
            tuple: (DataFrame completo com scores, DataFrame do top ranking)
        """
        print("\n" + "=" * 70)
        print("🎯 ANÁLISE FUNDAMENTALISTA COMPLETA - WSM")
        print("=" * 70)

        # Exibir estrutura de pesos utilizada
        dataframe_pesos = exibir_estrutura_pesos()
        print("\n📊 ESTRUTURA DE PESOS DA ANÁLISE:")
        print(dataframe_pesos.to_string(index=False))

        # Executar análise WSM
        analisador_wsm = AnalisadorFundamentalistaWSM(dataframe)
        resultados_completos = analisador_wsm.executar_analise()

        # Preparar ranking das melhores empresas
        top_empresas = self._preparar_ranking_empresas(resultados_completos, quantidade_rankings)

        # Exibir resultados
        self._apresentar_resultados_analise(resultados_completos, top_empresas)

        return resultados_completos, top_empresas

    def _preparar_ranking_empresas(self, resultados_analise, quantidade_rankings):
        """
        Prepara ranking das melhores empresas baseado no score WSM

        Args:
            resultados_analise (pd.DataFrame): DataFrame com resultados completos
            quantidade_rankings (int): Número de empresas no ranking

        Returns:
            pd.DataFrame: DataFrame com top empresas formatadas
        """
        colunas_ranking = [
            'empresa', 'ticker', 'subsetor', 'score_wsm', 'score_wsm_penalidade',
            'margem_graham', 'margem_barsi', 'preco_lucro', 'roe'
        ]

        ranking_empresas = resultados_analise[colunas_ranking].head(quantidade_rankings)

        # Formatar valores numéricos
        colunas_numericas = ['score_wsm', 'score_wsm_penalidade', 'margem_graham', 'margem_barsi', 'preco_lucro', 'roe']
        for coluna in colunas_numericas:
            ranking_empresas[coluna] = ranking_empresas[coluna].round(2)

        return ranking_empresas

    def _apresentar_resultados_analise(self, resultados_completos, ranking_empresas):
        """
        Apresenta resultados formatados da análise

        Args:
            resultados_completos (pd.DataFrame): DataFrame com todos os resultados
            ranking_empresas (pd.DataFrame): DataFrame com ranking das melhores
        """
        print(f"\n🏆 TOP {len(ranking_empresas)} EMPRESAS - RANKING WSM:")
        print("-" * 80)
        print(ranking_empresas.to_string(index=False))
        print("-" * 80)

        # Estatísticas da análise
        score_wsm = resultados_completos['score_wsm']
        print(f"\n📈 ESTATÍSTICAS DA ANÁLISE:")
        print(f"   • Total de empresas analisadas: {len(resultados_completos):,}")
        print(f"   • Score WSM médio: {score_wsm.mean():.2f}")
        print(f"   • Score WSM máximo: {score_wsm.max():.2f}")
        print(f"   • Score WSM mínimo: {score_wsm.min():.2f}")
        print(f"   • Desvio padrão: {score_wsm.std():.2f}")

    def _gerar_visualizacoes_completas(self, dataframe_visualizacao, quantidade_rankings,
                                       modo_apenas_visualizacoes=False):
        """
        Gera todas as visualizações e relatórios da análise

        Args:
            dataframe_visualizacao (pd.DataFrame): DataFrame preparado para visualização
            quantidade_rankings (int): Número de empresas nos rankings visuais
            modo_apenas_visualizacoes (bool): Modo apenas geração de visualizações

        Returns:
            list: Lista de figuras geradas
        """
        print("\n🎨 Gerando visualizações e relatórios...")

        figuras_geradas = []
        timestamp_analise = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Gerar visualizações WSM
        if 'score_wsm' in dataframe_visualizacao.columns:
            gerador_wsm = GeradorVisualizacoesWSM(dataframe_visualizacao)
            figuras_wsm = gerador_wsm.gerar_relatorio_completo(
                top_empresas=quantidade_rankings,
                caminho_salvamento=f"output/graficos/wsm_truncado_completo_{timestamp_analise}",
                penalidade=False
            )
            figuras_geradas.extend(figuras_wsm)

            figuras_wsm_penalidade = gerador_wsm.gerar_relatorio_completo(
                top_empresas=quantidade_rankings,
                caminho_salvamento=f"output/graficos/wsm_penalizado_completo_{timestamp_analise}",
                penalidade=True
            )
            figuras_geradas.extend(figuras_wsm_penalidade)

            # Salvar resultados completos
            self._exportar_resultados_completos(
                dataframe_visualizacao,
                f"output/dados/analises/resultados_wsm_completo_{timestamp_analise}.csv"
            )
        else:
            print("⚠️ Coluna 'score_wsm' não encontrada para geração de gráficos WSM")

        # Gerar visualizações das metodologias tradicionais
        if not modo_apenas_visualizacoes:
            print("\n📊 Gerando visualizações das metodologias tradicionais...")

            colunas_necessarias = ['margem_seguranca_graham', 'margem_seguranca_barsi', 'margem_seguranca_pl_setor']
            colunas_disponiveis = [col for col in colunas_necessarias if col in dataframe_visualizacao.columns]

            if len(colunas_disponiveis) == len(colunas_necessarias):
                try:
                    gerador_visualizacoes = GeradorVisualizacoes(dataframe_visualizacao)
                    gerador_visualizacoes.gerar_relatorio_completo(
                        top_empresas=quantidade_rankings
                    )
                except Exception as erro:
                    print(f"⚠️ Erro ao gerar visualizações tradicionais: {erro}")
            else:
                print(
                    f"⚠️ Metodologias tradicionais: {len(colunas_disponiveis)}/{len(colunas_necessarias)} colunas disponíveis")

        return figuras_geradas

    def _exportar_resultados_completos(self, dataframe, caminho_arquivo):
        """
        Exporta resultados completos para arquivo CSV

        Args:
            dataframe (pd.DataFrame): DataFrame com resultados
            caminho_arquivo (str): Caminho para salvar o arquivo
        """
        try:
            dataframe.to_csv(caminho_arquivo, index=False, encoding='utf-8')
            print(f"💾 Resultados exportados: {caminho_arquivo}")
        except Exception as erro:
            print(f"❌ Erro ao exportar resultados: {erro}")

    def _exportar_para_excel(self, dataframe, caminho_arquivo):
        """
        Exporta resultados completos para Excel com múltimas abas

        Args:
            dataframe (pd.DataFrame): DataFrame com resultados
            caminho_arquivo (str): Caminho para salvar o arquivo Excel
        """
        try:
            with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as escritor:
                # Aba com todos os dados
                dataframe.to_excel(escritor, sheet_name='Dados_Completos', index=False)

                # Aba com ranking WSM
                if 'score_wsm' in dataframe.columns:
                    ranking_wsm = dataframe.nlargest(50, 'score_wsm')[
                        ['empresa', 'ticker', 'subsetor', 'score_wsm', 'score_wsm_penalidade', 'margem_graham', 'margem_barsi']
                    ]
                    ranking_wsm.to_excel(escritor, sheet_name='Ranking_WSM', index=False)

                # Aba com oportunidades por metodologia
                oportunidades = dataframe[
                    (dataframe['margem_seguranca_graham'] > 0) |
                    (dataframe['margem_seguranca_barsi'] > 0) |
                    (dataframe['margem_seguranca_pl_setor'] > 0)
                    ]
                oportunidades.to_excel(escritor, sheet_name='Oportunidades', index=False)

            print(f"📊 Dados exportados para Excel: {caminho_arquivo}")
        except Exception as erro:
            print(f"❌ Erro ao exportar para Excel: {erro}")

    def _exibir_resumo_execucao(self, dataframe):
        """
        Exibe resumo executivo da análise realizada

        Args:
            dataframe (pd.DataFrame): DataFrame com resultados da análise
        """
        print("\n" + "=" * 60)
        print("📋 RESUMO EXECUTIVO DA ANÁLISE")
        print("=" * 60)

        total_empresas = len(dataframe)
        empresas_margem_graham = (dataframe['margem_seguranca_graham'] > 0).sum()
        empresas_margem_barsi = (dataframe['margem_seguranca_barsi'] > 0).sum()
        empresas_margem_pl_setor = (dataframe['margem_seguranca_pl_setor'] > 0).sum()

        print(f"📊 Total de empresas analisadas: {total_empresas:,}")
        print(f"🎯 Oportunidades identificadas:")
        print(f"   • Metodologia Graham: {empresas_margem_graham} empresas")
        print(f"   • Metodologia Barsi: {empresas_margem_barsi} empresas")
        print(f"   • P/L Descontado: {empresas_margem_pl_setor} empresas")

        # Empresas com múltiplas metodologias indicando oportunidade
        oportunidades_multiplas = (
                (dataframe['margem_seguranca_graham'] > 0) &
                (dataframe['margem_seguranca_barsi'] > 0)
        ).sum()

        if oportunidades_multiplas > 0:
            print(f"💎 Oportunidades consolidadas: {oportunidades_multiplas} empresas")

        print("=" * 60)

    def executar_analise_completa(self):
        """Método principal que executa o fluxo completo de análise"""
        print("🚀 INICIANDO SISTEMA DE ANÁLISE FUNDAMENTALISTA")
        print("=" * 70)

        # Processar argumentos
        argumentos = self._processar_argumentos()
        quantidade_rankings = argumentos.quantidade_rankings

        print("⚙️  Configurações da análise:")
        print(f"   • Atualizar dados: {'SIM' if argumentos.atualizar_dados else 'NÃO'}")
        print(f"   • Apenas visualizações: {'SIM' if argumentos.apenas_visualizacoes else 'NÃO'}")
        print(f"   • Empresas no ranking: {quantidade_rankings}")
        print(f"   • Exportar dados: {'SIM' if argumentos.exportar_dados else 'NÃO'}")

        # Carregar dados fundamentais
        print("\n📥 Carregando dados fundamentais...")
        usar_cache = not argumentos.atualizar_dados
        dados_fundamentais = self.provedor_dados.carregar_dados_fundamentais(usar_cache=usar_cache)

        if dados_fundamentais is None or dados_fundamentais.empty:
            print("❌ ERRO: Não foi possível carregar os dados fundamentais")
            return

        print(f"✅ Dados carregados: {len(dados_fundamentais)} ativos encontrados")

        # Aplicar filtros de exclusão
        tickers_excluir = self._carregar_lista_exclusoes()
        if tickers_excluir:
            dados_fundamentais = dados_fundamentais[~dados_fundamentais['ticker'].isin(tickers_excluir)]
            print(f"✅ Filtros aplicados: {len(dados_fundamentais)} ativos após exclusões")

        # Aplicar metodologias de valuation (se necessário)
        if argumentos.apenas_visualizacoes:
            dados_analise = dados_fundamentais
            print("📊 Modo apenas visualizações - usando dados existentes")
        else:
            dados_analise = self._aplicar_metodologias_valuation(dados_fundamentais)
            # Salvar dataset enriquecido
            caminho_dataset = f"output/dados/analises/dataset_enriquecido_{datetime.now().strftime('%Y%m%d')}.csv"
            dados_analise.to_csv(caminho_dataset, index=False)
            print(f"💾 Dataset enriquecido salvo: {caminho_dataset}")

        # Exibir resumo inicial
        self._exibir_resumo_execucao(dados_analise)

        # Executar análise WSM
        dados_com_scores, ranking_empresas = self._executar_analise_fundamentalista_wsm(
            dados_analise, quantidade_rankings
        )

        # Preparar dados para visualização
        dados_visualizacao = self._preparar_dados_visualizacao(dados_analise, dados_com_scores)

        # Mostra todas as colunas com os primeiros registros
        # pd.set_option('display.max_columns', None)
        # print(dados_visualizacao.head())

        # Gerar visualizações
        figuras = self._gerar_visualizacoes_completas(
            dados_visualizacao, quantidade_rankings, argumentos.apenas_visualizacoes
        )

        # Exportar dados se solicitado
        if argumentos.exportar_dados:
            caminho_excel = f"output/dados/analises/relatorio_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            self._exportar_para_excel(dados_visualizacao, caminho_excel)

        # Finalização
        print("\n" + "=" * 70)
        print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        print("📈 Para visualizar os gráficos, feche as janelas do matplotlib")
        print("💾 Relatórios salvos em: output/dados/analises/")
        print("🖼️  Visualizações salvas em: output/graficos/")

        # Exibir gráficos
        if figuras:
            plt.show()
        else:
            print("⚠️ Nenhuma visualização gerada para exibição")

    def _preparar_dados_visualizacao(self, dados_originais, dados_wsm):
        """
        Prepara DataFrame unificado para visualização

        Args:
            dados_originais (pd.DataFrame): Dados com metodologias tradicionais
            dados_wsm (pd.DataFrame): Dados com scores WSM

        Returns:
            pd.DataFrame: DataFrame unificado para visualização
        """
        dados_visualizacao = dados_originais.copy()

        # Integrar scores WSM se disponíveis
        if 'score_wsm' in dados_wsm.columns:
            scores_wsm = dados_wsm[['ticker', 'score_wsm' ,'score_wsm_penalidade']].drop_duplicates()
            dados_visualizacao = dados_visualizacao.merge(scores_wsm, on='ticker', how='left')
            print("✅ Scores WSM integrados para visualização")

        # Verificar integridade dos dados
        colunas_verificar = [
            'margem_seguranca_graham', 'margem_seguranca_barsi',
            'margem_seguranca_pl_setor', 'score_wsm', 'score_wsm_penalidade'
        ]

        print("\n🔍 VERIFICAÇÃO DE INTEGRIDADE DOS DADOS:")
        for coluna in colunas_verificar:
            if coluna in dados_visualizacao.columns:
                dados_validos = dados_visualizacao[coluna].notna().sum()
                print(f"   ✅ {coluna}: {dados_validos}/{len(dados_visualizacao)} valores válidos")
            else:
                print(f"   ❌ {coluna}: COLUNA AUSENTE")

        return dados_visualizacao


def main():
    """Função principal de inicialização do sistema"""
    try:
        sistema_analise = SistemaAnaliseFundamentalista()
        sistema_analise.executar_analise_completa()
    except KeyboardInterrupt:
        print("\n\n⚠️ Análise interrompida pelo usuário")
    except Exception as erro:
        print(f"\n❌ ERRO CRÍTICO: {erro}")
        print("Por favor, verifique a configuração e tente novamente")


if __name__ == "__main__":
    main()