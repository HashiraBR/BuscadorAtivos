import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


class VisualizadorAnalises:
    """
    Classe para geração de gráficos e visualizações das análises
    """

    def __init__(self, df):
        """
        Construtor da classe

        Args:
            df (DataFrame): DataFrame com os dados das análises
        """
        self.df = df
        # Configuração do estilo
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Garantir que o diretório de análises existe
        self._criar_diretorio_analises()

    def _criar_diretorio_analises(self):
        """Cria o diretório data/analises se não existir"""
        os.makedirs('data/analises', exist_ok=True)

    def criar_graficos_ranking(self, top_n=15):
        """
        Cria gráficos de ranking para as três metodologias
        """
        # CONVERTER COLUNAS PARA NUMÉRICO ANTES DE USAR nlargest
        df_temp = self.df.copy()

        if 'graham_margem' in df_temp.columns:
            df_temp['graham_margem'] = pd.to_numeric(df_temp['graham_margem'], errors='coerce')
        if 'barsi_margem' in df_temp.columns:
            df_temp['barsi_margem'] = pd.to_numeric(df_temp['barsi_margem'], errors='coerce')
        if 'pl_subsetor_margem' in df_temp.columns:
            df_temp['pl_subsetor_margem'] = pd.to_numeric(df_temp['pl_subsetor_margem'], errors='coerce')

        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        fig.suptitle('RANKING DAS MELHORES OPORTUNIDADES POR METODOLOGIA',
                     fontsize=16, fontweight='bold')

        # 1. RANKING GRAHAM
        if 'graham_margem' in df_temp.columns:
            df_graham = df_temp[df_temp['graham_margem'].notna()].nlargest(top_n, 'graham_margem')
            if not df_graham.empty:
                self._criar_barra_ranking(axes[0], df_graham, 'graham_margem',
                                          f'TOP {top_n} - MAIORES MARGENS GRAHAM')

        # 2. RANKING BARSI
        if 'barsi_margem' in df_temp.columns:
            df_barsi = df_temp[df_temp['barsi_margem'].notna()].nlargest(top_n, 'barsi_margem')
            if not df_barsi.empty:
                self._criar_barra_ranking(axes[1], df_barsi, 'barsi_margem',
                                          f'TOP {top_n} - MAIORES MARGENS BARSI')

        # 3. RANKING PL DESCONTAO
        if 'pl_subsetor_margem' in df_temp.columns:
            df_pl_desc = df_temp[df_temp['pl_subsetor_margem'].notna()].nlargest(top_n, 'pl_subsetor_margem')
            if not df_pl_desc.empty:
                self._criar_barra_ranking(axes[2], df_pl_desc, 'pl_subsetor_margem',
                                          f'TOP {top_n} - MAIORES DESCONTOS NO PL')

        plt.tight_layout()

        # Salvar figura
        caminho_figura = 'data/analises/ranking_metodologias.png'
        plt.savefig(caminho_figura, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo: {caminho_figura}")

        plt.show()

    def _criar_barra_ranking(self, ax, df, coluna_margem, titulo):
        """
        Método auxiliar para criar barras de ranking
        """
        bars = ax.barh(range(len(df)), df[coluna_margem])
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df['Papel'])
        ax.set_title(titulo, fontweight='bold')
        ax.set_xlabel('Margem de Segurança (%)')

        # Adicionar valores nas barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height() / 2,
                    f'{width:.1f}%', ha='left', va='center', fontweight='bold')

    def criar_grafico_consolidado(self, top_n=10):
        """
        Cria um gráfico consolidado com as top empresas de cada metodologia
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        rankings = []

        # Coletar top empresas de cada metodologia
        if 'graham_margem' in self.df.columns:
            graham_top = self.df.nlargest(top_n, 'graham_margem')[['Papel', 'graham_margem']]
            graham_top['Metodologia'] = 'Graham'
            graham_top = graham_top.rename(columns={'graham_margem': 'Margem'})
            rankings.append(graham_top)

        if 'barsi_margem' in self.df.columns:
            barsi_top = self.df.nlargest(top_n, 'barsi_margem')[['Papel', 'barsi_margem']]
            barsi_top['Metodologia'] = 'Barsi'
            barsi_top = barsi_top.rename(columns={'barsi_margem': 'Margem'})
            rankings.append(barsi_top)

        if 'pl_subsetor_margem' in self.df.columns:
            pl_top = self.df.nlargest(top_n, 'pl_subsetor_margem')[['Papel', 'pl_subsetor_margem']]
            pl_top['Metodologia'] = 'PL Descontado'
            pl_top = pl_top.rename(columns={'pl_subsetor_margem': 'Margem'})
            rankings.append(pl_top)

        if rankings:
            df_consolidado = pd.concat(rankings, ignore_index=True)

            # Criar gráfico
            sns.barplot(data=df_consolidado, x='Margem', y='Papel', hue='Metodologia', ax=ax)
            ax.set_title(f'TOP {top_n} OPORTUNIDADES - METODOLOGIAS CONSOLIDADAS', fontweight='bold')
            ax.set_xlabel('Margem de Segurança / Desconto (%)')
            ax.set_ylabel('')

            plt.tight_layout()

            # Salvar figura
            caminho_figura = 'data/analises/ranking_consolidado.png'
            plt.savefig(caminho_figura, dpi=300, bbox_inches='tight')
            print(f"Gráfico salvo: {caminho_figura}")

            plt.show()
        else:
            print("Nenhum dado disponível para gerar gráfico consolidado")

    def mostrar_tabela_ranking(self, top_n=10):
        """
        Mostra tabela com os rankings no console
        """
        print("\n" + "=" * 80)
        print("RANKING DAS MELHORES OPORTUNIDADES")
        print("=" * 80)

        # Graham
        if 'graham_margem' in self.df.columns:
            print(f"\nTOP {top_n} - GRAHAM:")
            graham_top = self.df.nlargest(top_n, 'graham_margem')[
                ['Papel', 'Empresa', 'graham_margem', 'graham_teto', 'Cotacao']
            ].round(2)
            print(graham_top.to_string(index=False))
        else:
            print("\nGRAHAM: Nenhum dado disponível")

        # Barsi
        if 'barsi_margem' in self.df.columns:
            print(f"\nTOP {top_n} - BARSI:")
            barsi_top = self.df.nlargest(top_n, 'barsi_margem')[
                ['Papel', 'Empresa', 'barsi_margem', 'barsi_teto', 'Cotacao']
            ].round(2)
            print(barsi_top.to_string(index=False))
        else:
            print("\nBARSI: Nenhum dado disponível")

        # PL Descontado
        if 'pl_subsetor_margem' in self.df.columns:
            print(f"\nTOP {top_n} - PL DESCONTAO:")
            pl_top = self.df.nlargest(top_n, 'pl_subsetor_margem')[
                ['Papel', 'Empresa', 'pl_subsetor_margem', 'pl_subsetor_alvo', 'Cotacao']
            ].round(2)
            print(pl_top.to_string(index=False))
        else:
            print("\nPL DESCONTAO: Nenhum dado disponível")

    def criar_graficos_wsm_lado_a_lado(self, df, top_n=15):
        """
        Cria dois gráficos WSM lado a lado com pesos diferentes
        """
        # CONVERTER COLUNAS PARA NUMÉRICO
        df_temp = df.copy()

        if 'graham_margem' in df_temp.columns:
            df_temp['graham_margem'] = pd.to_numeric(df_temp['graham_margem'], errors='coerce')
        if 'barsi_margem' in df_temp.columns:
            df_temp['barsi_margem'] = pd.to_numeric(df_temp['barsi_margem'], errors='coerce')
        if 'pl_subsetor_margem' in df_temp.columns:
            df_temp['pl_subsetor_margem'] = pd.to_numeric(df_temp['pl_subsetor_margem'], errors='coerce')

        # Calcular rankings WSM
        ranking_cenario1 = self._calcular_wsm(df_temp, graham_peso=0.6, barsi_peso=0.4)
        ranking_cenario2 = self._calcular_wsm(df_temp, graham_peso=0.5, barsi_peso=0.2, pl_peso=0.3)

        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        fig.suptitle('RANKING WSM - COMPARAÇÃO DE PESOS', fontsize=16, fontweight='bold')

        # Gráfico da esquerda: Graham (0.6) + Barsi (0.4)
        df_left = ranking_cenario1.head(top_n)
        self._criar_grafico_wsm_individual(axes[0], df_left,
                                           'Graham (0.6) + Barsi (0.4)')

        # Gráfico da direita: Graham (0.5) + Barsi (0.2) + PL Descontado (0.3)
        df_right = ranking_cenario2.head(top_n)
        self._criar_grafico_wsm_individual(axes[1], df_right,
                                           'Graham (0.5) + Barsi (0.2) + PL Descontado (0.3)')

        plt.tight_layout()

        # Salvar figura
        caminho_figura = 'data/analises/ranking_wsm_pesos.png'
        plt.savefig(caminho_figura, dpi=300, bbox_inches='tight')
        print(f"Gráfico WSM salvo: {caminho_figura}")

        plt.show()

    def _calcular_wsm(self, df, graham_peso=0.5, barsi_peso=0.5, pl_peso=0.0):
        """Calcula WSM de forma segura, lidando com colunas ausentes"""
        try:
            # Verificar colunas disponíveis
            colunas_disponiveis = df.columns

            # Inicializar score
            df_wsm = df.copy()
            df_wsm['score_temp'] = 0

            # Adicionar Graham se disponível
            if 'graham_margem' in colunas_disponiveis:
                df_wsm['score_temp'] += df_wsm['graham_margem'].fillna(0) * graham_peso

            # Adicionar Barsi se disponível
            if 'barsi_margem' in colunas_disponiveis:
                df_wsm['score_temp'] += df_wsm['barsi_margem'].fillna(0) * barsi_peso

            # Adicionar PL Descontado se disponível
            if 'pl_subsetor_margem' in colunas_disponiveis and pl_peso > 0:
                df_wsm['score_temp'] += df_wsm['pl_subsetor_margem'].fillna(0) * pl_peso

            # Renomear a coluna para wsm_score para compatibilidade
            df_wsm = df_wsm.rename(columns={'score_temp': 'wsm_score'})

            return df_wsm.sort_values('wsm_score', ascending=False)

        except Exception as e:
            print(f"Erro ao calcular WSM: {e}")
            return df

    def _criar_grafico_wsm_individual(self, ax, df, titulo):
        """
        Cria gráfico individual de ranking WSM
        """
        bars = ax.barh(range(len(df)), df['wsm_score'])
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df['Papel'])
        ax.set_title(titulo, fontweight='bold', fontsize=12)
        ax.set_xlabel('Score WSM')

        # Adicionar valores nas barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height() / 2,
                    f'{width:.1f}%', ha='left', va='center', fontweight='bold')

        # Linhas de grade
        ax.grid(True, axis='x', alpha=0.3)
        ax.set_axisbelow(True)

    def gerar_relatorio_completo(self, top_n=15):
        """
        Gera relatório completo com todos os gráficos e tabelas
        """
        print("Gerando relatorio completo de analises...")

        # Gráficos individuais
        self.criar_graficos_ranking(top_n)

        # Gráfico consolidado
        self.criar_grafico_consolidado(top_n // 2)

        # Gráficos WSM lado a lado
        self.criar_graficos_wsm_lado_a_lado(self.df, top_n)

        # Tabelas no console
        self.mostrar_tabela_ranking(top_n)

        print("\nRelatorio completo gerado com sucesso!")
        print("Arquivos salvos em: data/analises/")