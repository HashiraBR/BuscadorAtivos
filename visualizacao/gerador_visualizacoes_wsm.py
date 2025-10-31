import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import pandas as pd


class GeradorVisualizacoesWSM:
    """
    Gerador de visualizações para análise fundamentalista WSM
    Cria gráficos e relatórios visuais dos scores e indicadores
    """

    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()
        self._configurar_estilo_visualizacoes()
        self._mapear_colunas()

    def _configurar_estilo_visualizacoes(self):
        """Configura o estilo padrão para as visualizações"""
        plt.style.use('default')
        sns.set_palette("husl")

        self.estilo_titulos = {'fontsize': 12, 'fontweight': 'bold', 'pad': 10}
        self.estilo_eixos = {'fontsize': 10}
        self.estilo_legendas = {'fontsize': 9}

    def _mapear_colunas(self):
        """Mapeia os nomes das colunas para lidar com diferentes versões"""
        self.colunas = {
            'score': 'score_wsm' if 'score_wsm' in self.dataframe.columns else 'Score_WSM',
            'score_penalidade': 'score_wsm_penalidade' if 'score_wsm_penalidade' in self.dataframe.columns else 'score_wsm_penalidade',
            'empresa': 'Empresa' if 'Empresa' in self.dataframe.columns else 'Empresa',
            'ticker': 'ticker' if 'ticker' in self.dataframe.columns else 'ticker',
            'subsetor': 'Subsetor' if 'Subsetor' in self.dataframe.columns else 'Subsetor',
            'margem_graham': 'margem_seguranca_graham' if 'margem_seguranca_graham' in self.dataframe.columns else 'graham_margem',
            'margem_barsi': 'margem_seguranca_barsi' if 'margem_seguranca_barsi' in self.dataframe.columns else 'barsi_margem',
            'preco_lucro': 'preco_lucro' if 'preco_lucro' in self.dataframe.columns else 'PL',
            'roe': 'roe' if 'roe' in self.dataframe.columns else 'ROE',
            'roic': 'roic' if 'roic' in self.dataframe.columns else 'ROIC'
        }

    def _obter_coluna(self, nome_coluna):
        """Obtém o nome real da coluna baseado no mapeamento"""
        return self.colunas.get(nome_coluna, nome_coluna)

    def gerar_grafico_top_empresas(self, top_empresas=20, tamanho_figura=(12, 8), penalidade=False):
        """
        Gera gráfico de barras com as melhores empresas por score WSM
        """
        figura, eixo = plt.subplots(figsize=tamanho_figura)
        if penalidade:
            coluna_score = self._obter_coluna('score_penalidade')
            lbl = "WSM (Penalidade)"
        else:
            coluna_score = self._obter_coluna('score')
            lbl = "WSM (Truncado à 0)"

        if coluna_score not in self.dataframe.columns:
            print(f"⚠️ Coluna de score '{coluna_score}' não encontrada")
            return figura

        # Ordenar e selecionar top empresas
        dataframe_top = self.dataframe.nlargest(top_empresas, coluna_score)

        # Criar labels para o eixo Y
        coluna_ticker = self._obter_coluna('ticker')
        coluna_empresa = self._obter_coluna('empresa')

        if coluna_empresa in dataframe_top.columns:
            labels_empresas = [
                f"{linha[coluna_ticker]} - {str(linha[coluna_empresa])[:20]}..."
                for _, linha in dataframe_top.iterrows()
            ]
        else:
            labels_empresas = [
                f"{linha[coluna_ticker]}"
                for _, linha in dataframe_top.iterrows()
            ]

        # Criar gráfico de barras horizontais
        barras = eixo.barh(
            range(len(dataframe_top)),
            dataframe_top[coluna_score],
            color='steelblue',
            alpha=0.7,
            height=0.8
        )

        # Configurar labels e títulos
        eixo.set_yticks(range(len(dataframe_top)))
        eixo.set_yticklabels(labels_empresas)
        eixo.set_xlabel('Score WSM', **self.estilo_eixos)
        eixo.set_title(f'Top {top_empresas} Empresas - Score {lbl} Fundamentalista', **self.estilo_titulos)
        eixo.grid(axis='x', alpha=0.3)

        # Adicionar valores nas barras
        for indice, barra in enumerate(barras):
            largura = barra.get_width()
            eixo.text(
                largura + 0.1,
                barra.get_y() + barra.get_height() / 2,
                f'{largura:.1f}',
                ha='left',
                va='center',
                fontsize=9
            )

        plt.tight_layout()
        return figura

    # def gerar_grafico_top_empresas_com_penalidade(self, top_empresas=20, tamanho_figura=(12, 8)):
    #     """
    #     Gera gráfico de barras com as melhores empresas por score WSM
    #     """
    #     figura, eixo = plt.subplots(figsize=tamanho_figura)
    #
    #     coluna_score = self._obter_coluna('score_penalidade')
    #
    #     if coluna_score not in self.dataframe.columns:
    #         print(f"⚠️ Coluna de score '{coluna_score}' não encontrada")
    #         return figura
    #
    #     # Ordenar e selecionar top empresas
    #     dataframe_top = self.dataframe.nlargest(top_empresas, coluna_score)
    #
    #     # Criar labels para o eixo Y
    #     coluna_ticker = self._obter_coluna('ticker')
    #     coluna_empresa = self._obter_coluna('empresa')
    #
    #     if coluna_empresa in dataframe_top.columns:
    #         labels_empresas = [
    #             f"{linha[coluna_ticker]} - {str(linha[coluna_empresa])[:20]}..."
    #             for _, linha in dataframe_top.iterrows()
    #         ]
    #     else:
    #         labels_empresas = [
    #             f"{linha[coluna_ticker]}"
    #             for _, linha in dataframe_top.iterrows()
    #         ]
    #
    #     # Criar gráfico de barras horizontais
    #     barras = eixo.barh(
    #         range(len(dataframe_top)),
    #         dataframe_top[coluna_score],
    #         color='steelblue',
    #         alpha=0.7,
    #         height=0.8
    #     )
    #
    #     # Configurar labels e títulos
    #     eixo.set_yticks(range(len(dataframe_top)))
    #     eixo.set_yticklabels(labels_empresas)
    #     eixo.set_xlabel('Score WSM', **self.estilo_eixos)
    #     eixo.set_title(f'Top {top_empresas} Empresas - Score Fundamentalista (Penalidade)', **self.estilo_titulos)
    #     eixo.grid(axis='x', alpha=0.3)
    #
    #     # Adicionar valores nas barras
    #     for indice, barra in enumerate(barras):
    #         largura = barra.get_width()
    #         eixo.text(
    #             largura + 0.1,
    #             barra.get_y() + barra.get_height() / 2,
    #             f'{largura:.1f}',
    #             ha='left',
    #             va='center',
    #             fontsize=9
    #         )
    #
    #     plt.tight_layout()
    #     return figura

    def gerar_grafico_distribuicao_scores(self, tamanho_figura=(10, 6), penalidade=False):
        """
        Gera histograma da distribuição dos scores WSM
        """
        figura, eixo = plt.subplots(figsize=tamanho_figura)

        if penalidade:
            coluna_score = self._obter_coluna('score_penalidade')
            lbl = "WSM (Penalidade)"
        else:
            coluna_score = self._obter_coluna('score')
            lbl = "WSM (Truncado à 0)"

        if coluna_score not in self.dataframe.columns:
            eixo.text(0.5, 0.5, 'Dados de score\nnão disponíveis',
                      ha='center', va='center', transform=eixo.transAxes)
            eixo.set_title('Distribuição dos Scores', **self.estilo_titulos)
            return figura

        # Criar histograma
        frequencias, intervalos, patches = eixo.hist(
            self.dataframe[coluna_score].dropna(),
            bins=20,
            color='lightblue',
            edgecolor='black',
            alpha=0.7
        )

        eixo.set_xlabel(f'Score {lbl}', **self.estilo_eixos)
        eixo.set_ylabel('Frequência', **self.estilo_eixos)
        eixo.set_title(f'Distribuição dos Scores {lbl}', **self.estilo_titulos)
        eixo.grid(alpha=0.3)

        # Adicionar linhas de referência
        media = self.dataframe[coluna_score].mean()
        mediana = self.dataframe[coluna_score].median()

        eixo.axvline(media, color='red', linestyle='--', linewidth=2,
                     label=f'Média: {media:.2f}')
        eixo.axvline(mediana, color='green', linestyle='--', linewidth=2,
                     label=f'Mediana: {mediana:.2f}')
        eixo.legend(**self.estilo_legendas)

        plt.tight_layout()
        return figura

    def gerar_grafico_score_vs_margens_seguranca(self, tamanho_figura=(12, 5), penalidade=False):
        """
        Gera scatter plots comparando score com margens de segurança
        """
        figura, (eixo1, eixo2) = plt.subplots(1, 2, figsize=tamanho_figura)

        if penalidade:
            coluna_score = self._obter_coluna('score_penalidade')
            lbl = "WSM (Penalidade)"
        else:
            coluna_score = self._obter_coluna('score')
            lbl = "WSM (Truncado à 0)"

        # coluna_score = self._obter_coluna('score')
        coluna_margem_graham = self._obter_coluna('margem_graham')
        coluna_margem_barsi = self._obter_coluna('margem_barsi')

        # Score vs Margem Graham
        if coluna_score in self.dataframe.columns and coluna_margem_graham in self.dataframe.columns:
            dispersao1 = eixo1.scatter(
                self.dataframe[coluna_score],
                self.dataframe[coluna_margem_graham],
                alpha=0.6,
                c='blue',
                s=50,
                edgecolors='white',
                linewidth=0.5
            )
            eixo1.set_xlabel(f'Score {lbl}', **self.estilo_eixos)
            eixo1.set_ylabel('Margem Segurança Graham (%)', **self.estilo_eixos)
            eixo1.set_title(f'Score {lbl} vs Margem Graham', **self.estilo_titulos)
            eixo1.grid(True, alpha=0.3)
        else:
            eixo1.text(0.5, 0.5, 'Dados Graham\nnão disponíveis',
                       ha='center', va='center', transform=eixo1.transAxes)
            eixo1.set_title(f'Score {lbl} vs Margem Graham', **self.estilo_titulos)

        # Score vs Margem Barsi
        if coluna_score in self.dataframe.columns and coluna_margem_barsi in self.dataframe.columns:
            dispersao2 = eixo2.scatter(
                self.dataframe[coluna_score],
                self.dataframe[coluna_margem_barsi],
                alpha=0.6,
                c='green',
                s=50,
                edgecolors='white',
                linewidth=0.5
            )
            eixo2.set_xlabel(f'Score {lbl}', **self.estilo_eixos)
            eixo2.set_ylabel('Margem Segurança Barsi (%)', **self.estilo_eixos)
            eixo2.set_title(f'Score {lbl} vs Margem Barsi', **self.estilo_titulos)
            eixo2.grid(True, alpha=0.3)
        else:
            eixo2.text(0.5, 0.5, 'Dados Barsi\nnão disponíveis',
                       ha='center', va='center', transform=eixo2.transAxes)
            eixo2.set_title(f'Score {lbl} vs Margem Barsi', **self.estilo_titulos)

        plt.tight_layout()
        return figura

    def gerar_heatmap_correlacao(self, tamanho_figura=(10, 8)):
        """
        Gera heatmap de correlação entre indicadores fundamentais
        """
        # Selecionar colunas para análise de correlação
        colunas_correlacao = [
            self._obter_coluna('score'),
            self._obter_coluna('margem_graham'),
            self._obter_coluna('margem_barsi'),
            self._obter_coluna('preco_lucro'),
            'P_VP', 'Div_Yield', 'Marg_Liquida'
        ]

        # Filtrar colunas existentes no dataframe
        colunas_existentes = [col for col in colunas_correlacao if col in self.dataframe.columns]

        if len(colunas_existentes) < 3:
            print("⚠️ Colunas insuficientes para gerar heatmap de correlação")
            return None

        dataframe_correlacao = self.dataframe[colunas_existentes].corr()

        figura, eixo = plt.subplots(figsize=tamanho_figura)

        # Criar máscara para triângulo superior
        mascara = np.triu(np.ones_like(dataframe_correlacao, dtype=bool))

        # Gerar heatmap
        mapa_calor = sns.heatmap(
            dataframe_correlacao,
            mask=mascara,
            annot=True,
            cmap='coolwarm',
            center=0,
            ax=eixo,
            fmt='.2f',
            square=True,
            cbar_kws={'shrink': 0.8}
        )

        eixo.set_title('Correlação entre Indicadores Fundamentalistas', **self.estilo_titulos)
        plt.tight_layout()
        return figura

    def gerar_grafico_score_por_subsetor(self, top_subsetores=15, tamanho_figura=(14, 8), penalidade=False):
        """
        Gera boxplot da distribuição de scores por subsetor com visual melhorado
        """
        figura, eixo = plt.subplots(figsize=tamanho_figura)

        if penalidade:
            coluna_score = self._obter_coluna('score_penalidade')
            lbl = "WSM (Penalidade)"
        else:
            coluna_score = self._obter_coluna('score')
            lbl = "WSM (Truncado à 0)"

        # coluna_score = self._obter_coluna('score')
        coluna_subsetor = self._obter_coluna('subsetor')

        if coluna_score not in self.dataframe.columns or coluna_subsetor not in self.dataframe.columns:
            eixo.text(0.5, 0.5, 'Dados insuficientes\npara análise por subsetor',
                      ha='center', va='center', transform=eixo.transAxes, fontsize=12)
            eixo.set_title(f'Distribuição do Score {lbl} por Subsetor', **self.estilo_titulos)
            return figura

        # Selecionar subsetores com mais empresas
        contagem_subsetores = self.dataframe[coluna_subsetor].value_counts()
        subsetores_principais = contagem_subsetores.head(top_subsetores).index

        dataframe_filtrado = self.dataframe[self.dataframe[coluna_subsetor].isin(subsetores_principais)]

        # Preparar dados para o boxplot
        dados_plot = []
        nomes_subsetores = []

        for subsetor in subsetores_principais:
            dados_subsetor = dataframe_filtrado[dataframe_filtrado[coluna_subsetor] == subsetor][coluna_score].dropna()
            if len(dados_subsetor) > 0:
                dados_plot.append(dados_subsetor)
                nomes_subsetores.append(f"{subsetor}\n(n={len(dados_subsetor)})")

        if not dados_plot:
            eixo.text(0.5, 0.5, 'Dados insuficientes\npara gerar boxplot',
                      ha='center', va='center', transform=eixo.transAxes, fontsize=12)
            eixo.set_title(f'Distribuição do Score {lbl} por Subsetor', **self.estilo_titulos)
            return figura

        # Criar boxplot com seaborn (mais bonito)
        # Preparar DataFrame para seaborn
        dados_seaborn = []
        for subsetor, nome_formatado in zip(subsetores_principais, nomes_subsetores):
            dados_subsetor = dataframe_filtrado[dataframe_filtrado[coluna_subsetor] == subsetor][coluna_score].dropna()
            for valor in dados_subsetor:
                dados_seaborn.append({'Subsetor': nome_formatado, 'Score': valor})

        df_seaborn = pd.DataFrame(dados_seaborn)

        # Criar palette de cores
        cores = sns.color_palette("husl", len(nomes_subsetores))

        # Plotar com seaborn
        sns.boxplot(data=df_seaborn, x='Subsetor', y='Score', ax=eixo, palette=cores,
                    width=0.7, fliersize=3, linewidth=1.5)

        # Personalizar aparência
        eixo.set_title(f'Distribuição do Score {lbl} por Subsetor', **self.estilo_titulos)
        eixo.set_ylabel('Score WSM', **self.estilo_eixos)
        eixo.set_xlabel('Subsetor', **self.estilo_eixos)

        # Melhorar grade
        eixo.grid(True, alpha=0.3, axis='y')
        eixo.set_axisbelow(True)

        # Rotacionar labels do eixo x para melhor legibilidade
        eixo.tick_params(axis='x', rotation=45, labelsize=9)
        eixo.tick_params(axis='y', labelsize=9)

        # Adicionar linha de média geral
        media_geral = self.dataframe[coluna_score].mean()
        eixo.axhline(y=media_geral, color='red', linestyle='--', alpha=0.8, linewidth=1.5,
                     label=f'Média Geral: {media_geral:.2f}')

        # Adicionar legenda
        eixo.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

        # Ajustar layout
        plt.suptitle('')  # Remove título automático do pandas
        plt.tight_layout()

        return figura

    def gerar_grafico_ranking_penalidade(self, resultados_completos, top_empresas=15, tamanho_figura=(12, 8)):
        """
        Gera gráfico de ranking específico para scores com penalidades
        """
        figura, eixo = plt.subplots(figsize=tamanho_figura)

        # Verificar se a coluna de penalidade existe
        if 'score_wsm_penalidade' not in resultados_completos.columns:
            eixo.text(0.5, 0.5, 'Coluna score_wsm_penalidade não encontrada',
                      ha='center', va='center', transform=eixo.transAxes, fontsize=12)
            eixo.set_title('Ranking com Penalidades', **self.estilo_titulos)
            return figura

        # Ordenar por penalidade (do maior para o menor)
        ranking_penalidade = resultados_completos.nlargest(top_empresas, 'score_wsm_penalidade')

        # Criar labels
        labels_empresas = []
        for _, linha in ranking_penalidade.iterrows():
            ticker = linha.get('ticker', 'N/A')
            empresa = linha.get('Empresa', '')
            if empresa:
                labels_empresas.append(f"{ticker}\n{empresa[:15]}...")
            else:
                labels_empresas.append(ticker)

        # Criar gráfico de barras horizontais
        barras = eixo.barh(
            range(len(ranking_penalidade)),
            ranking_penalidade['score_wsm_penalidade'],
            color='#A23B72',  # Roxo para diferenciar
            alpha=0.8,
            height=0.7
        )

        # Configurações do gráfico
        eixo.set_yticks(range(len(ranking_penalidade)))
        eixo.set_yticklabels(labels_empresas, fontsize=9)
        eixo.set_xlabel('Score WSM com Penalidades', **self.estilo_eixos)
        eixo.set_title(f'Top {top_empresas} Empresas - Score com Penalidades Aplicadas', **self.estilo_titulos)
        eixo.grid(axis='x', alpha=0.3)
        eixo.set_facecolor('#f8f9fa')

        # Adicionar valores nas barras
        for indice, barra in enumerate(barras):
            largura = barra.get_width()
            eixo.text(
                largura + 0.1,
                barra.get_y() + barra.get_height() / 2,
                f'{largura:.1f}',
                ha='left',
                va='center',
                fontsize=8,
                fontweight='bold'
            )

        plt.tight_layout()
        return figura

    def gerar_relatorio_completo(self, top_empresas=20, caminho_salvamento=None, penalidade=False):
        """
        Gera relatório completo com todas as visualizações
        """
        print("📊 Gerando relatório visual completo WSM...")

        figuras_geradas = []

        try:
            # # 1. Gráfico COMPARATIVO dos dois scores (NOVO)
            # print("   🔄 Gerando comparação de scores...")
            # figura_comparativa = self.gerar_grafico_comparativo_scores(top_empresas)
            # if self._verificar_figura_valida(figura_comparativa):
            #     figuras_geradas.append(figura_comparativa)
            # else:
            #     print("   ⚠️ Gráfico comparativo não gerado - dados insuficientes")

            # 2. Gráfico das top empresas (score normal)
            print("   🏆 Gerando ranking das melhores empresas...")
            figura_top = self.gerar_grafico_top_empresas(top_empresas, penalidade=penalidade)
            if self._verificar_figura_valida(figura_top):
                figuras_geradas.append(figura_top)
            else:
                print("   ⚠️ Gráfico de top empresas não gerado - dados insuficientes")

            # erro de proposito para não perder a lógica:
            # tenho que passar um bool para cada método para escolher entre score e score_penalidade. quero gerar 2 gráficos para cada
            # print("   🏆 Gerando ranking das melhores empresas com penalidade...")
            # figura_top_penalidade = self.gerar_grafico_top_empresas_com_penalidade(top_empresas)
            # if self._verificar_figura_valida(figura_top_penalidade):
            #     figuras_geradas.append(figura_top_penalidade)
            # else:
            #     print("   ⚠️ Gráfico de top empresas não gerado - dados insuficientes")

            # 3. Distribuição de scores
            print("   📈 Gerando distribuição de scores...")
            figura_dist = self.gerar_grafico_distribuicao_scores(penalidade=penalidade)
            if self._verificar_figura_valida(figura_dist):
                figuras_geradas.append(figura_dist)
            else:
                print("   ⚠️ Gráfico de distribuição não gerado - dados insuficientes")

            # 4. Comparação com margens de segurança
            print("   🔍 Gerando análise de margens de segurança...")
            figura_margens = self.gerar_grafico_score_vs_margens_seguranca(penalidade=penalidade)
            if self._verificar_figura_valida(figura_margens):
                figuras_geradas.append(figura_margens)
            else:
                print("   ⚠️ Gráfico de margens não gerado - dados insuficientes")

            # 5. Heatmap de correlação
            print("   🎯 Gerando mapa de correlações...")
            heatmap = self.gerar_heatmap_correlacao()
            if heatmap is not None and self._verificar_figura_valida(heatmap):
                figuras_geradas.append(heatmap)
            else:
                print("   ⚠️ Heatmap não gerado - dados insuficientes")

            # 6. Análise por subsetor
            print("   🏢 Gerando análise por subsetor...")
            figura_subsetor = self.gerar_grafico_score_por_subsetor(penalidade=penalidade)
            if self._verificar_figura_valida(figura_subsetor):
                figuras_geradas.append(figura_subsetor)
            else:
                print("   ⚠️ Gráfico por subsetor não gerado - dados insuficientes")

            # Salvar gráficos se solicitado
            if caminho_salvamento and figuras_geradas:
                self._salvar_figuras(figuras_geradas, caminho_salvamento)

            print(f"✅ Relatório WSM gerado: {len(figuras_geradas)} visualizações criadas de 6 possíveis")

        except Exception as erro:
            print(f"❌ Erro ao gerar relatório visual WSM: {erro}")
            import traceback
            traceback.print_exc()

        return figuras_geradas

    def _verificar_figura_valida(self, figura):
        """
        Verifica se uma figura contém dados válidos (não está vazia)
        """
        if figura is None:
            return False

        # Verificar se há eixos com dados
        for ax in figura.get_axes():
            if len(ax.collections) > 0 or len(ax.patches) > 0 or len(ax.lines) > 0:
                return True
            # Verificar se há texto (indicando mensagem de "dados não disponíveis")
            if len(ax.texts) > 0:
                for text in ax.texts:
                    if "não disponíveis" not in text.get_text():
                        return True
        return False

    def _salvar_figuras(self, figuras, caminho_base):
        """
        Salva as figuras em arquivos
        """
        try:
            diretorio = os.path.dirname(caminho_base)
            if diretorio:
                os.makedirs(diretorio, exist_ok=True)

            nomes_arquivos = [
                'ranking_top_empresas',
                'distribuicao_scores',
                'score_vs_margens',
                'heatmap_correlacao',
                'score_por_subsetor'
            ]

            for indice, figura in enumerate(figuras):
                if indice < len(nomes_arquivos):
                    nome_arquivo = f"{caminho_base}_{nomes_arquivos[indice]}.png"
                    figura.savefig(nome_arquivo, dpi=300, bbox_inches='tight', facecolor='white')
                    print(f"   💾 Salvo: {nome_arquivo}")

        except Exception as erro:
            print(f"   ⚠️ Erro ao salvar figuras WSM: {erro}")


def gerar_relatorio_wsm_rapido(dataframe, top_empresas=20, caminho_salvamento=None, penalidade=False):
    """
    Função rápida para gerar relatório completo WSM
    """
    gerador = GeradorVisualizacoesWSM(dataframe)
    return gerador.gerar_relatorio_completo(
        top_empresas=top_empresas,
        caminho_salvamento=caminho_salvamento,
        penalidade=penalidade
    )


