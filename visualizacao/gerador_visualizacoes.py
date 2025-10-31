import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


class GeradorVisualizacoes:
    """
    Classe para geração de gráficos e visualizações das análises fundamentalistas
    Gera relatórios visuais comparativos entre diferentes metodologias de valuation
    """

    def __init__(self, dataframe):
        """
        Inicializa o gerador de visualizações

        Args:
            dataframe (pd.DataFrame): DataFrame com os dados das análises
        """
        self.dataframe = dataframe
        self._configurar_estilo_graficos()
        self._criar_diretorio_analises()

    def _configurar_estilo_graficos(self):
        """Configura o estilo padrão para todos os gráficos"""
        plt.style.use('default')
        sns.set_palette("husl")

        # Configurações de estilo consistentes
        self.estilo_titulos = {'fontsize': 12, 'fontweight': 'bold', 'pad': 10}
        self.estilo_eixos = {'fontsize': 10}
        self.estilo_legendas = {'fontsize': 9}

    def _criar_diretorio_analises(self):
        """Cria o diretório para análises se não existir"""
        os.makedirs('output/graficos', exist_ok=True)

    def gerar_graficos_ranking_metodologias(self, top_empresas=15):
        """
        Cria gráficos de ranking comparativo para as três metodologias

        Args:
            top_empresas (int): Número de empresas a mostrar em cada ranking
        """
        # Garantir que as colunas são numéricas
        dataframe_temp = self.dataframe.copy()
        dataframe_temp = self._converter_colunas_numericas(dataframe_temp)

        figura, eixos = plt.subplots(1, 3, figsize=(20, 6))
        figura.suptitle('RANKING COMPARATIVO - METODOLOGIAS DE VALUATION',
                        fontsize=16, fontweight='bold')

        # 1. RANKING GRAHAM
        if 'margem_seguranca_graham' in dataframe_temp.columns:
            dataframe_graham = dataframe_temp[
                dataframe_temp['margem_seguranca_graham'].notna()
            ].nlargest(top_empresas, 'margem_seguranca_graham')

            if not dataframe_graham.empty:
                self._criar_grafico_barras_ranking(
                    eixos[0], dataframe_graham, 'margem_seguranca_graham',
                    f'TOP {top_empresas} - MARGENS GRAHAM'
                )

        # 2. RANKING BARSI
        if 'margem_seguranca_barsi' in dataframe_temp.columns:
            dataframe_barsi = dataframe_temp[
                dataframe_temp['margem_seguranca_barsi'].notna()
            ].nlargest(top_empresas, 'margem_seguranca_barsi')

            if not dataframe_barsi.empty:
                self._criar_grafico_barras_ranking(
                    eixos[1], dataframe_barsi, 'margem_seguranca_barsi',
                    f'TOP {top_empresas} - MARGENS BARSI'
                )

        # 3. RANKING PL DESCONTAO
        if 'margem_seguranca_pl_setor' in dataframe_temp.columns:
            dataframe_pl_desc = dataframe_temp[
                dataframe_temp['margem_seguranca_pl_setor'].notna()
            ].nlargest(top_empresas, 'margem_seguranca_pl_setor')

            if not dataframe_pl_desc.empty:
                self._criar_grafico_barras_ranking(
                    eixos[2], dataframe_pl_desc, 'margem_seguranca_pl_setor',
                    f'TOP {top_empresas} - DESCONTOS P/L SETOR'
                )

        plt.tight_layout()

        # Salvar figura
        caminho_figura = 'output/graficos/ranking_metodologias.png'
        plt.savefig(caminho_figura, dpi=300, bbox_inches='tight')
        print(f"📊 Gráfico de rankings salvo: {caminho_figura}")

        plt.show()
        return figura

    def _converter_colunas_numericas(self, dataframe):
        """
        Converte colunas de margens para formato numérico

        Args:
            dataframe (pd.DataFrame): DataFrame a ser convertido

        Returns:
            pd.DataFrame: DataFrame com colunas convertidas
        """
        colunas_margens = [
            'margem_seguranca_graham',
            'margem_seguranca_barsi',
            'margem_seguranca_pl_setor'
        ]

        for coluna in colunas_margens:
            if coluna in dataframe.columns:
                dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce')

        return dataframe

    def _criar_grafico_barras_ranking(self, eixo, dataframe, coluna_margem, titulo):
        """
        Método auxiliar para criar gráfico de barras de ranking

        Args:
            eixo (matplotlib.axes.Axes): Eixo onde plotar o gráfico
            dataframe (pd.DataFrame): Dados para o ranking
            coluna_margem (str): Coluna com os valores de margem
            titulo (str): Título do gráfico
        """
        barras = eixo.barh(range(len(dataframe)), dataframe[coluna_margem])
        eixo.set_yticks(range(len(dataframe)))
        eixo.set_yticklabels(dataframe['ticker'])
        eixo.set_title(titulo, **self.estilo_titulos)
        eixo.set_xlabel('Margem de Segurança (%)', **self.estilo_eixos)
        eixo.grid(axis='x', alpha=0.3)

        # Adicionar valores nas barras
        for indice, barra in enumerate(barras):
            largura = barra.get_width()
            eixo.text(
                largura + 1,
                barra.get_y() + barra.get_height() / 2,
                f'{largura:.1f}%',
                ha='left',
                va='center',
                fontweight='bold',
                fontsize=9
            )

    def gerar_grafico_consolidado(self, top_empresas=10):
        """
        Cria gráfico consolidado com as melhores oportunidades de todas as metodologias

        Args:
            top_empresas (int): Número de empresas por metodologia
        """
        figura, eixo = plt.subplots(figsize=(12, 8))

        rankings_consolidados = []

        # Coletar top empresas de cada metodologia
        if 'margem_seguranca_graham' in self.dataframe.columns:
            top_graham = self.dataframe.nlargest(top_empresas, 'margem_seguranca_graham')[
                ['ticker', 'margem_seguranca_graham']
            ]
            top_graham['metodologia'] = 'Graham'
            top_graham = top_graham.rename(columns={'margem_seguranca_graham': 'margem'})
            rankings_consolidados.append(top_graham)

        if 'margem_seguranca_barsi' in self.dataframe.columns:
            top_barsi = self.dataframe.nlargest(top_empresas, 'margem_seguranca_barsi')[
                ['ticker', 'margem_seguranca_barsi']
            ]
            top_barsi['metodologia'] = 'Barsi'
            top_barsi = top_barsi.rename(columns={'margem_seguranca_barsi': 'margem'})
            rankings_consolidados.append(top_barsi)

        if 'margem_seguranca_pl_setor' in self.dataframe.columns:
            top_pl_setor = self.dataframe.nlargest(top_empresas, 'margem_seguranca_pl_setor')[
                ['ticker', 'margem_seguranca_pl_setor']
            ]
            top_pl_setor['metodologia'] = 'P/L Descontado'
            top_pl_setor = top_pl_setor.rename(columns={'margem_seguranca_pl_setor': 'margem'})
            rankings_consolidados.append(top_pl_setor)

        if rankings_consolidados:
            dataframe_consolidado = pd.concat(rankings_consolidados, ignore_index=True)

            # Criar gráfico de barras agrupadas
            sns.barplot(
                data=dataframe_consolidado,
                x='margem',
                y='ticker',
                hue='metodologia',
                ax=eixo
            )
            eixo.set_title(
                f'TOP {top_empresas} OPORTUNIDADES - VISÃO CONSOLIDADA',
                **self.estilo_titulos
            )
            eixo.set_xlabel('Margem de Segurança / Desconto (%)', **self.estilo_eixos)
            eixo.set_ylabel('Ticker', **self.estilo_eixos)
            eixo.legend(**self.estilo_legendas)

            plt.tight_layout()

            # Salvar figura
            caminho_figura = 'output/graficos/ranking_consolidado.png'
            plt.savefig(caminho_figura, dpi=300, bbox_inches='tight')
            print(f"📊 Gráfico consolidado salvo: {caminho_figura}")

            plt.show()
            return figura
        else:
            print("⚠️ Nenhum dado disponível para gerar gráfico consolidado")
            return None

    def exibir_tabelas_ranking_console(self, top_empresas=10):
        """
        Exibe tabelas com os rankings formatados no console
        """
        print("\n" + "=" * 80)
        print("📋 RANKING DAS MELHORES OPORTUNIDADES")
        print("=" * 80)

        # CORREÇÃO: Verificar colunas disponíveis
        colunas_disponiveis = self.dataframe.columns

        # Determinar nomes das colunas
        coluna_preco = 'preco_atual' if 'preco_atual' in colunas_disponiveis else 'Cotacao'
        coluna_empresa = 'empresa' if 'empresa' in colunas_disponiveis else 'Empresa'

        # Ranking Graham
        coluna_graham = 'margem_seguranca_graham' if 'margem_seguranca_graham' in colunas_disponiveis else 'graham_margem'
        if coluna_graham in colunas_disponiveis:
            print(f"\n🏆 TOP {top_empresas} - METODOLOGIA GRAHAM:")
            colunas_graham = ['ticker', coluna_empresa, coluna_graham, 'preco_teto_graham', coluna_preco]
            colunas_graham = [col for col in colunas_graham if col in colunas_disponiveis]

            top_graham = self.dataframe.nlargest(top_empresas, coluna_graham)[colunas_graham].round(2)
            print(top_graham.to_string(index=False))
        else:
            print("\n❌ GRAHAM: Nenhum dado disponível")

        # Ranking Barsi
        coluna_barsi = 'margem_seguranca_barsi' if 'margem_seguranca_barsi' in colunas_disponiveis else 'barsi_margem'
        if coluna_barsi in colunas_disponiveis:
            print(f"\n🏆 TOP {top_empresas} - METODOLOGIA BARSI:")
            colunas_barsi = ['ticker', coluna_empresa, coluna_barsi, 'preco_teto_barsi', coluna_preco]
            colunas_barsi = [col for col in colunas_barsi if col in colunas_disponiveis]

            top_barsi = self.dataframe.nlargest(top_empresas, coluna_barsi)[colunas_barsi].round(2)
            print(top_barsi.to_string(index=False))
        else:
            print("\n❌ BARSI: Nenhum dado disponível")

        # Ranking P/L Descontado
        coluna_pl_setor = 'margem_seguranca_pl_setor' if 'margem_seguranca_pl_setor' in colunas_disponiveis else 'pl_subsetor_margem'
        if coluna_pl_setor in colunas_disponiveis:
            print(f"\n🏆 TOP {top_empresas} - P/L DESCONTAO POR SETOR:")
            colunas_pl = ['ticker', coluna_empresa, coluna_pl_setor, 'preco_alvo_pl_setor', coluna_preco]
            colunas_pl = [col for col in colunas_pl if col in colunas_disponiveis]

            top_pl_setor = self.dataframe.nlargest(top_empresas, coluna_pl_setor)[colunas_pl].round(2)
            print(top_pl_setor.to_string(index=False))
        else:
            print("\n❌ P/L DESCONTAO: Nenhum dado disponível")

    def gerar_graficos_comparacao_pesos_wsm(self, top_empresas=15):
        """
        Cria gráficos comparativos WSM com diferentes estruturas de pesos

        Args:
            top_empresas (int): Número de empresas a mostrar
        """
        # Garantir colunas numéricas
        dataframe_temp = self.dataframe.copy()
        dataframe_temp = self._converter_colunas_numericas(dataframe_temp)

        peso_graham_1 = 0.6
        peso_barsi_1 = 0.4

        peso_graham_2 = 0.5
        peso_barsi_2 = 0.2
        peso_pl_setor_2 = 0.3

        # Calcular rankings com diferentes pesos
        ranking_cenario_1 = self._calcular_score_wsm(
            dataframe_temp,
            peso_graham=peso_graham_1,
            peso_barsi=peso_barsi_1
        )
        ranking_cenario_2 = self._calcular_score_wsm(
            dataframe_temp,
            peso_graham=peso_graham_2,
            peso_barsi=peso_barsi_2,
            peso_pl_setor=peso_pl_setor_2
        )

        figura, eixos = plt.subplots(1, 2, figsize=(18, 8))
        figura.suptitle('COMPARAÇÃO WSM - ESTRUTURAS DE PESOS DIFERENTES',
                        fontsize=16, fontweight='bold')

        # Gráfico esquerdo: Graham (0.6) + Barsi (0.4)
        dataframe_esquerdo = ranking_cenario_1.head(top_empresas)
        self._criar_grafico_wsm_individual(
            eixos[0], dataframe_esquerdo,
            f'Cenário 1: Graham ({peso_graham_1}) + Barsi ({peso_barsi_1})'
        )

        # Gráfico direito: Graham (0.5) + Barsi (0.2) + PL Setor (0.3)
        dataframe_direito = ranking_cenario_2.head(top_empresas)
        self._criar_grafico_wsm_individual(
            eixos[1], dataframe_direito,
            f'Cenário 2: Graham ({peso_graham_2}) + Barsi ({peso_barsi_2}) + P/L Setor ({peso_pl_setor_2})'
        )

        plt.tight_layout()

        # Salvar figura
        caminho_figura = 'output/graficos/comparacao_pesos_wsm.png'
        plt.savefig(caminho_figura, dpi=300, bbox_inches='tight')
        print(f"📊 Gráfico WSM comparativo salvo: {caminho_figura}")

        plt.show()
        return figura

    def _calcular_score_wsm(self, dataframe, peso_graham=0.5, peso_barsi=0.5, peso_pl_setor=0.0):
        """
        Calcula score WSM com pesos customizados

        Args:
            dataframe (pd.DataFrame): DataFrame com dados
            peso_graham (float): Peso para margem Graham
            peso_barsi (float): Peso para margem Barsi
            peso_pl_setor (float): Peso para margem P/L setor

        Returns:
            pd.DataFrame: DataFrame ordenado por score WSM
        """
        try:
            # Criar cópia para cálculo
            dataframe_wsm = dataframe.copy()
            dataframe_wsm['score_wsm'] = 0.0

            # Adicionar componentes ao score
            if 'margem_seguranca_graham' in dataframe_wsm.columns:
                dataframe_wsm['score_wsm'] += (
                        dataframe_wsm['margem_seguranca_graham'].fillna(0) * peso_graham
                )

            if 'margem_seguranca_barsi' in dataframe_wsm.columns:
                dataframe_wsm['score_wsm'] += (
                        dataframe_wsm['margem_seguranca_barsi'].fillna(0) * peso_barsi
                )

            if 'margem_seguranca_pl_setor' in dataframe_wsm.columns and peso_pl_setor > 0:
                dataframe_wsm['score_wsm'] += (
                        dataframe_wsm['margem_seguranca_pl_setor'].fillna(0) * peso_pl_setor
                )

            return dataframe_wsm.sort_values('score_wsm', ascending=False)

        except Exception as erro:
            print(f"❌ Erro ao calcular score WSM: {erro}")
            return dataframe

    def _criar_grafico_wsm_individual(self, eixo, dataframe, titulo):
        """
        Cria gráfico individual de ranking WSM

        Args:
            eixo (matplotlib.axes.Axes): Eixo para plotagem
            dataframe (pd.DataFrame): Dados do ranking
            titulo (str): Título do gráfico
        """
        barras = eixo.barh(range(len(dataframe)), dataframe['score_wsm'])
        eixo.set_yticks(range(len(dataframe)))
        eixo.set_yticklabels(dataframe['ticker'])
        eixo.set_title(titulo, **self.estilo_titulos)
        eixo.set_xlabel('Score WSM', **self.estilo_eixos)
        eixo.grid(True, axis='x', alpha=0.3)
        eixo.set_axisbelow(True)

        # Adicionar valores nas barras
        for indice, barra in enumerate(barras):
            largura = barra.get_width()
            eixo.text(
                largura + 0.3,
                barra.get_y() + barra.get_height() / 2,
                f'{largura:.1f}',
                ha='left',
                va='center',
                fontweight='bold',
                fontsize=9
            )

    def gerar_relatorio_completo(self, top_empresas=15):
        """
        Gera relatório completo com todas as visualizações e análises

        Args:
            top_empresas (int): Número de empresas nos rankings
        """
        print("📈 Gerando relatório completo de análises...")

        # Gráficos de ranking por metodologia
        self.gerar_graficos_ranking_metodologias(top_empresas)

        # Gráfico consolidado
        self.gerar_grafico_consolidado(top_empresas // 2)

        # Gráficos comparativos WSM
        self.gerar_graficos_comparacao_pesos_wsm(top_empresas)

        # Tabelas no console
        self.exibir_tabelas_ranking_console(top_empresas)

        print("\n✅ Relatório completo gerado com sucesso!")
        print("📁 Arquivos salvos em: output/graficos/")