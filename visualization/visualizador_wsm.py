import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


class VisualizadorScoreFundamentalista:
    def __init__(self, df):
        self.df = df.copy()

    def gerar_grafico_top_empresas(self, top_n=20, figsize=(12, 8)):
        """Gráfico de barras com as top empresas por score"""
        fig, ax = plt.subplots(figsize=figsize)

        # Ordenar e selecionar top N
        df_top = self.df.nlargest(top_n, 'Score_WSM')

        # Criar gráfico de barras
        bars = ax.barh(range(len(df_top)), df_top['Score_WSM'],
                       color='steelblue', alpha=0.7)

        # Adicionar labels
        ax.set_yticks(range(len(df_top)))
        ax.set_yticklabels([f"{row['Papel']} - {row['Empresa'][:20]}..."
                            for _, row in df_top.iterrows()])
        ax.set_xlabel('Score WSM')
        ax.set_title(f'Top {top_n} Empresas por Score Fundamentalista')

        # Adicionar valores nas barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                    f'{width:.1f}', ha='left', va='center', fontsize=9)

        plt.tight_layout()
        return fig

    def gerar_grafico_distribuicao_scores(self, figsize=(10, 6)):
        """Histograma da distribuição dos scores"""
        fig, ax = plt.subplots(figsize=figsize)

        # Histograma
        n, bins, patches = ax.hist(self.df['Score_WSM'].dropna(), bins=20,
                                   color='lightblue', edgecolor='black', alpha=0.7)

        ax.set_xlabel('Score WSM')
        ax.set_ylabel('Frequência')
        ax.set_title('Distribuição dos Scores Fundamentalistas')

        # Adicionar linhas de média e mediana
        media = self.df['Score_WSM'].mean()
        mediana = self.df['Score_WSM'].median()

        ax.axvline(media, color='red', linestyle='--', label=f'Média: {media:.2f}')
        ax.axvline(mediana, color='green', linestyle='--', label=f'Mediana: {mediana:.2f}')
        ax.legend()

        plt.tight_layout()
        return fig

    def gerar_grafico_score_vs_margens(self, figsize=(12, 5)):
        """Scatter plots comparando score com margens Graham e Barsi"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Score vs Margem Graham
        scatter1 = ax1.scatter(self.df['Score_WSM'], self.df['graham_margem'],
                               alpha=0.6, c='blue', s=50)
        ax1.set_xlabel('Score WSM')
        ax1.set_ylabel('Margem Graham (%)')
        ax1.set_title('Score vs Margem Graham')
        ax1.grid(True, alpha=0.3)

        # Score vs Margem Barsi
        scatter2 = ax2.scatter(self.df['Score_WSM'], self.df['barsi_margem'],
                               alpha=0.6, c='green', s=50)
        ax2.set_xlabel('Score WSM')
        ax2.set_ylabel('Margem Barsi (%)')
        ax2.set_title('Score vs Margem Barsi')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def gerar_grafico_heatmap_correlacao(self, figsize=(10, 8)):
        """Heatmap de correlação entre indicadores importantes"""
        # Selecionar colunas para correlação
        cols_correlacao = ['Score_WSM', 'graham_margem', 'barsi_margem', 'PL',
                           'PVP', 'ROE', 'ROIC', 'Div_Yield', 'Marg_Liquida']

        # Filtrar colunas existentes
        cols_existentes = [col for col in cols_correlacao if col in self.df.columns]
        df_corr = self.df[cols_existentes].corr()

        fig, ax = plt.subplots(figsize=figsize)

        # Heatmap
        mask = np.triu(np.ones_like(df_corr, dtype=bool))  # Mascarar triângulo superior
        sns.heatmap(df_corr, mask=mask, annot=True, cmap='coolwarm',
                    center=0, ax=ax, fmt='.2f', square=True)

        ax.set_title('Correlação entre Indicadores Fundamentalistas')
        plt.tight_layout()
        return fig

    def gerar_grafico_score_por_subsetor(self, top_subsetores=15, figsize=(12, 8)):
        """Boxplot dos scores por subsetor"""
        fig, ax = plt.subplots(figsize=figsize)

        # Selecionar subsetores com mais empresas
        subsetor_counts = self.df['Subsetor'].value_counts()
        top_subsetores_list = subsetor_counts.head(top_subsetores).index

        df_filtrado = self.df[self.df['Subsetor'].isin(top_subsetores_list)]

        # Boxplot
        df_filtrado.boxplot(column='Score_WSM', by='Subsetor', ax=ax, rot=45)
        ax.set_title('Distribuição do Score por Subsetor')
        ax.set_ylabel('Score WSM')
        ax.set_xlabel('')

        plt.suptitle('')  # Remove título automático
        plt.tight_layout()
        return fig

    def gerar_relatorio_completo(self, top_n=20, save_path=None):
        """Gera relatório completo com todos os gráficos"""
        figs = []

        print("Gerando relatório de scores fundamentalistas...")

        try:
            # 1. Top empresas
            figs.append(self.gerar_grafico_top_empresas(top_n))

            # 2. Distribuição
            figs.append(self.gerar_grafico_distribuicao_scores())

            # 3. Score vs Margens
            figs.append(self.gerar_grafico_score_vs_margens())

            # 4. Heatmap correlação (só se tiver colunas suficientes)
            if len(self.df.columns) > 5 and 'Score_WSM' in self.df.columns:
                figs.append(self.gerar_grafico_heatmap_correlacao())

            # 5. Score por subsetor
            figs.append(self.gerar_grafico_score_por_subsetor())

            # Salvar gráficos se path for fornecido
            if save_path:
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                for i, fig in enumerate(figs):
                    fig.savefig(f"{save_path}_{i + 1}.png", dpi=300, bbox_inches='tight')
                print(f"Gráficos salvos em: {save_path}_*.png")

        except Exception as e:
            print(f"Erro ao gerar gráficos: {e}")

        return figs


# Função de conveniência para uso rápido
def gerar_graficos_score(df, top_n=20, save_path=None):
    """
    Função rápida para gerar todos os gráficos de score
    """
    visualizador = VisualizadorScoreFundamentalista(df)
    return visualizador.gerar_relatorio_completo(top_n=top_n, save_path=save_path)