import pandas as pd
import numpy as np
from scipy import stats


class AnalisadorFundamentalistaCompleto:
    def __init__(self, df):
        self.df = df.copy()

        # Pesos recomendados incluindo Barsi e Graham
        self.indicadores = {
            # Valuation Tradicional (20%)
            'P_L': {'relacao': 'menor', 'peso': 0.07},
            'P_VP': {'relacao': 'menor', 'peso': 0.06},
            'EV_EBITDA': {'relacao': 'menor', 'peso': 0.05},
            'Div_Yield': {'relacao': 'maior', 'peso': 0.02},

            # Rentabilidade (30%)
            'ROE': {'relacao': 'maior', 'peso': 0.09},
            'ROIC': {'relacao': 'maior', 'peso': 0.08},
            'Marg_Liquida': {'relacao': 'maior', 'peso': 0.07},
            'Marg_EBIT': {'relacao': 'maior', 'peso': 0.06},

            # Crescimento (15%)
            'Cres_Rec_5a': {'relacao': 'maior', 'peso': 0.06},
            'Lucro_Liquido_12m': {'relacao': 'maior', 'peso': 0.05},
            'LPA': {'relacao': 'maior', 'peso': 0.04},

            # Saude Financeira (15%)
            'Div_Liquida': {'relacao': 'menor', 'peso': 0.06},
            'Div_Br_Patrim': {'relacao': 'menor', 'peso': 0.05},
            'EBIT_Ativo': {'relacao': 'maior', 'peso': 0.04},

            # Metodologias de Valuation (20%)
            'graham_margem': {'relacao': 'maior', 'peso': 0.10},
            'barsi_margem': {'relacao': 'maior', 'peso': 0.10}
        }

        # Mapeamento dos nomes para exibicao
        self.nomes_exibicao = {
            'P_L': 'P/L',
            'P_VP': 'P/VP',
            'EV_EBITDA': 'EV/EBITDA',
            'Div_Yield': 'Dividend Yield',
            'ROE': 'ROE',
            'ROIC': 'ROIC',
            'Marg_Liquida': 'Margem Liquida',
            'Marg_EBIT': 'Margem EBIT',
            'Cres_Rec_5a': 'Crescimento Receita 5a',
            'Lucro_Liquido_12m': 'Crescimento Lucro',
            'LPA': 'LPA',
            'Div_Liquida': 'Divida Liquida/EBITDA',
            'Div_Br_Patrim': 'Divida Bruta/Patrimonio',
            'EBIT_Ativo': 'EBIT/Ativo',
            'graham_margem': 'Margem Graham',
            'barsi_margem': 'Margem Barsi'
        }

        # Verificar soma dos pesos
        soma_pesos = sum([info['peso'] for info in self.indicadores.values()])
        print(f"Soma dos pesos: {soma_pesos:.3f}")

    def remover_outliers_tradicionais(self, df_grupo):
        """Remove outliers apenas para indicadores tradicionais (exceto Barsi/Graham)"""
        df_limpo = df_grupo.copy()

        for indicador in self.indicadores.keys():
            if indicador not in ['graham_margem', 'barsi_margem'] and indicador in df_limpo.columns:
                Q1 = df_limpo[indicador].quantile(0.25)
                Q3 = df_limpo[indicador].quantile(0.75)
                IQR = Q3 - Q1
                limite_inferior = Q1 - 1.5 * IQR
                limite_superior = Q3 + 1.5 * IQR

                df_limpo = df_limpo[
                    (df_limpo[indicador] >= limite_inferior) &
                    (df_limpo[indicador] <= limite_superior)
                    ]

        return df_limpo

    def normalizar_margem_barsi_graham(self, valor, indicador):
        """
        Normaliza as margens Barsi e Graham de forma especial
        Valores positivos = preco abaixo do teto (oportunidade)
        Valores negativos = preco acima do teto (sobrevalorizado)
        """
        if pd.isna(valor):
            return 0

        if indicador in ['graham_margem', 'barsi_margem']:
            # Margem positiva = boa (preco abaixo do teto)
            # Margem negativa = ruim (preco acima do teto)
            if valor > 0:
                return min(valor, 100)  # Limita em 100% para nao distorcer
            else:
                return max(valor, -50)  # Penalidade maxima de -50%

        return valor

    def calcular_media_ponderada_grupo(self, df_grupo):
        """Calcula media ponderada para indicadores tradicionais (exceto Barsi/Graham)"""
        medias_ponderadas = {}

        for indicador, config in self.indicadores.items():
            # Nao calcula media para Barsi e Graham (sao individuais)
            if indicador in ['graham_margem', 'barsi_margem']:
                continue

            if indicador in df_grupo.columns:
                peso = df_grupo['Valor_de_mercado']
                valores = df_grupo[indicador]

                mask = ~valores.isna() & ~peso.isna()
                if mask.sum() > 0:
                    valores_clean = valores[mask]
                    peso_clean = peso[mask]

                    media_pond = np.average(valores_clean, weights=peso_clean)
                    medias_ponderadas[indicador] = media_pond
                else:
                    medias_ponderadas[indicador] = np.nan

        return medias_ponderadas

    def calcular_margem_media(self, valor_empresa, media_grupo, indicador):
        """Calcula margem em relacao a media do grupo ou normaliza direto"""
        # Para Barsi e Graham, usa normalizacao direta
        if indicador in ['graham_margem', 'barsi_margem']:
            return self.normalizar_margem_barsi_graham(valor_empresa, indicador)

        # Para outros indicadores, calcula margem relativa ao grupo
        if pd.isna(valor_empresa) or pd.isna(media_grupo) or media_grupo == 0:
            return 0
        return ((valor_empresa - media_grupo) / abs(media_grupo)) * 100

    def normalizar_margem(self, margem, relacao):
        """Normaliza a margem baseado na relacao maior/menor melhor"""
        if relacao == 'maior':
            return max(0, margem)  # Penaliza valores abaixo da media
        else:  # menor
            return max(0, -margem)  # Penaliza valores acima da media

    def calcular_score_empresa(self, empresa, medias_grupo):
        """Calcula score WSM com pesos diferentes"""
        scores_ponderados = []
        pesos_aplicados = []

        for indicador, config in self.indicadores.items():
            relacao = config['relacao']
            peso = config['peso']

            if indicador in empresa and not pd.isna(empresa[indicador]):
                valor_empresa = empresa[indicador]

                # Para Barsi e Graham, media_grupo nao e usado
                if indicador in ['graham_margem', 'barsi_margem']:
                    media_grupo = 0  # Nao usado na normalizacao especial
                else:
                    media_grupo = medias_grupo.get(indicador, 0)

                margem = self.calcular_margem_media(valor_empresa, media_grupo, indicador)
                score_normalizado = self.normalizar_margem(margem, relacao)

                scores_ponderados.append(score_normalizado * peso)
                pesos_aplicados.append(peso)

        # Calcular score final ponderado
        if sum(pesos_aplicados) > 0:
            return sum(scores_ponderados) / sum(pesos_aplicados)
        else:
            return 0

    def analisar(self):
        """Executa analise completa"""
        resultados = []

        print("Iniciando analise fundamentalista...")

        for subsetor, grupo in self.df.groupby('Subsetor'):
            print(f"Processando subsetor: {subsetor} ({len(grupo)} empresas)")

            # Remover outliers apenas para indicadores tradicionais
            grupo_limpo = self.remover_outliers_tradicionais(grupo)

            if len(grupo_limpo) == 0:
                continue

            # Calcular medias ponderadas do grupo (apenas para indicadores tradicionais)
            medias_grupo = self.calcular_media_ponderada_grupo(grupo_limpo)

            # Calcular score para cada empresa do grupo
            for idx, empresa in grupo_limpo.iterrows():
                score = self.calcular_score_empresa(empresa, medias_grupo)

                # Coletar informacoes adicionais para analise
                info_empresa = {
                    'Empresa': empresa.get('Empresa', ''),
                    'Subsetor': subsetor,
                    'Papel': empresa.get('Papel', ''),
                    'Cotacao': empresa.get('Cotacao', 0),
                    'Valor_de_mercado': empresa.get('Valor_de_mercado', 0),
                    'Score_WSM': score,
                    'Margem_Graham': empresa.get('graham_margem', 0),
                    'Margem_Barsi': empresa.get('barsi_margem', 0),
                    'P_L': empresa.get('PL', 0),
                    'ROE': empresa.get('ROE', 0),
                    'ROIC': empresa.get('ROIC', 0)
                }

                resultados.append(info_empresa)

        # Criar dataframe de resultados
        df_resultados = pd.DataFrame(resultados)
        df_resultados = df_resultados.sort_values('Score_WSM', ascending=False)

        print(f"Analise concluida! {len(df_resultados)} empresas avaliadas")

        return df_resultados


# Funcao para mostrar os pesos detalhados
def mostrar_pesos_detalhados():
    pesos = {
        'CATEGORIA': [
            'VALUATION TRADICIONAL', 'RENTABILIDADE', 'CRESCIMENTO',
            'SAUDE FINANCEIRA', 'METODOLOGIAS AVANCADAS'
        ],
        'INDICADORES': [
            'PL, PVP, EV_EBITDA, Div_Yield',
            'ROE, ROIC, Marg_Liquida, Marg_EBIT',
            'Cres_Rec_5a, Lucro_Liquido_12m, LPA',
            'Div_Liquida, Div_Br_Patrim, EBIT_Ativo',
            'graham_margem, barsi_margem'
        ],
        'PESO_CATEGORIA': ['20%', '30%', '15%', '15%', '20%'],
        'PESO_INDIVIDUAL': [
            '7%, 6%, 5%, 2%',
            '9%, 8%, 7%, 6%',
            '6%, 5%, 4%',
            '6%, 5%, 4%',
            '10%, 10%'
        ]
    }

    return pd.DataFrame(pesos)


# Exemplo de uso
"""
# Mostrar estrutura de pesos
print(mostrar_pesos_detalhados())

# Executar analise
analisador = AnalisadorFundamentalistaCompleto(df)
resultados = analisador.analisar()

# Top 10 empresas
print(resultados[['Empresa', 'Papel', 'Subsetor', 'Score_WSM', 'Margem_Graham', 'Margem_Barsi']].head(10))
"""