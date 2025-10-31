import pandas as pd
import numpy as np
from scipy import stats


class AnalisadorFundamentalistaWSM:
    """
    Sistema de análise fundamentalista usando Weighted Scoring Model (WSM)
    Combina múltiplas metodologias de valuation em um score único
    """

    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()
        self._configurar_estrutura_pesos()
        self._validar_configuracao()

    def _configurar_estrutura_pesos(self):
        """
        Configura a estrutura de pesos e indicadores do modelo WSM
        """
        # Estrutura de pesos por categoria
        self.indicadores = {
            # Valuation Tradicional (20%)
            'PL': {'relacao': 'menor_melhor', 'peso': 0.08, 'categoria': 'valuation'},
            'PVP': {'relacao': 'menor_melhor', 'peso': 0.07, 'categoria': 'valuation'},
            'EV_EBITDA': {'relacao': 'menor_melhor', 'peso': 0.05, 'categoria': 'valuation'},
            'Div_Yield': {'relacao': 'maior_melhor', 'peso': 0.02, 'categoria': 'valuation'},

            # Rentabilidade (30%)
            'ROE': {'relacao': 'maior_melhor', 'peso': 0.09, 'categoria': 'rentabilidade'},
            'ROIC': {'relacao': 'maior_melhor', 'peso': 0.08, 'categoria': 'rentabilidade'},
            'Marg_Liquida': {'relacao': 'maior_melhor', 'peso': 0.09, 'categoria': 'rentabilidade'},
            'Marg_EBIT': {'relacao': 'maior_melhor', 'peso': 0.06, 'categoria': 'rentabilidade'},

            # Crescimento (15%)
            #'Cres_Rec_5a': {'relacao': 'maior_melhor', 'peso': 0.08, 'categoria': 'crescimento'},
            #'Lucro_Liquido_12m': {'relacao': 'maior_melhor', 'peso': 0.00, 'categoria': 'crescimento'},
            'LPA': {'relacao': 'maior_melhor', 'peso': 0.09, 'categoria': 'crescimento'},

            # Saúde Financeira (15%)
            #'Div_Liquida': {'relacao': 'menor_melhor', 'peso': 0.00, 'categoria': 'saude_financeira'},
            #'Div_Br_Patrim': {'relacao': 'menor_melhor', 'peso': 0.00, 'categoria': 'saude_financeira'},
            'EBIT_Ativo': {'relacao': 'maior_melhor', 'peso': 0.09, 'categoria': 'saude_financeira'},

            # Metodologias de Valuation Avançadas (20%)
            'margem_seguranca_graham': {'relacao': 'maior_melhor', 'peso': 0.10, 'categoria': 'valuation_avancado'},
            'margem_seguranca_barsi': {'relacao': 'maior_melhor', 'peso': 0.10, 'categoria': 'valuation_avancado'}
        }

        # Mapeamento para exibição amigável
        self.nomes_amigaveis = {
            'PL': 'P/L',
            'PVP': 'P/VP',
            'EV_EBITDA': 'EV/EBITDA',
            'Div_Yield': 'Dividend Yield',
            'ROE': 'ROE',
            'ROIC': 'ROIC',
            'Marg_Liquida': 'Margem Líquida',
            'Marg_EBIT': 'Margem EBIT',
            'Cres_Rec_5a': 'Crescimento Receita (5a)',
            'Lucro_Liquido_12m': 'Crescimento Lucro Líquido',
            'LPA': 'Lucro por Ação (LPA)',
            'Div_Liquida': 'Dívida Líquida/EBITDA',
            'Div_Br_Patrim': 'Dívida Bruta/Patrimônio',
            'EBIT_Ativo': 'EBIT/Ativo',
            'margem_seguranca_graham': 'Margem Segurança Graham',
            'margem_seguranca_barsi': 'Margem Segurança Barsi'
        }

    def _validar_configuracao(self):
        """
        Valida a configuração do modelo WSM
        """
        soma_pesos = sum([config['peso'] for config in self.indicadores.values()])

        if abs(soma_pesos - 1.0) > 0.001:
            print(f"⚠️ Aviso: Soma dos pesos ({soma_pesos:.3f}) difere de 100%")
        else:
            print(f"✅ Configuração validada: Soma dos pesos = {soma_pesos:.1%}")

        # Verificar indicadores disponíveis no dataframe
        indicadores_disponiveis = [ind for ind in self.indicadores.keys() if ind in self.dataframe.columns]
        indicadores_faltantes = [ind for ind in self.indicadores.keys() if ind not in self.dataframe.columns]

        print(f"📊 Indicadores disponíveis: {len(indicadores_disponiveis)}/{len(self.indicadores)}")
        if indicadores_faltantes:
            print(f"   ⚠️ Indicadores faltantes: {indicadores_faltantes}")

    def _remover_outliers_indicadores_tradicionais(self, dataframe_grupo):
        """
        Remove outliers apenas para indicadores tradicionais usando método IQR

        Args:
            dataframe_grupo (pd.DataFrame): DataFrame do grupo/setor

        Returns:
            pd.DataFrame: DataFrame sem outliers
        """
        # if len(dataframe_grupo) <= 3: # Não remove grupos pequenos
        #     return dataframe_grupo

        dataframe_limpo = dataframe_grupo.copy()

        indicadores_avancados = ['margem_seguranca_graham', 'margem_seguranca_barsi']

        for indicador, config in self.indicadores.items():
            if (indicador not in indicadores_avancados and
                    indicador in dataframe_limpo.columns and
                    dataframe_limpo[indicador].notna().sum() > 0):

                try:
                    Q1 = dataframe_limpo[indicador].quantile(0.25)
                    Q3 = dataframe_limpo[indicador].quantile(0.75)
                    IQR = Q3 - Q1

                    if IQR > 0:  # Só aplica se há variação nos dados
                        limite_inferior = Q1 - 1.5 * IQR
                        limite_superior = Q3 + 1.5 * IQR

                        dataframe_limpo = dataframe_limpo[
                            (dataframe_limpo[indicador] >= limite_inferior) &
                            (dataframe_limpo[indicador] <= limite_superior)
                            ]

                except Exception as erro:
                    print(f"   ⚠️ Erro ao remover outliers para {indicador}: {erro}")
                    continue

        return dataframe_limpo

    def _normalizar_margens_avancadas(self, valor, indicador):
        """
        Normaliza as margens de segurança de forma especial

        Args:
            valor (float): Valor da margem de segurança
            indicador (str): Nome do indicador

        Returns:
            float: Valor normalizado
        """
        if pd.isna(valor):
            return 0.0

        if indicador in ['margem_seguranca_graham', 'margem_seguranca_barsi']:
            # Margem positiva = oportunidade (preço abaixo do teto)
            # Margem negativa = sobrevalorizado (preço acima do teto)
            if valor > 0:
                return min(valor, 100)  # Limita em 100% para não distorcer
            else:
                return max(valor, -50)  # Penalidade máxima de -50%

        return valor

    def _calcular_medias_ponderadas_grupo(self, dataframe_grupo):
        """
        Calcula médias ponderadas para indicadores tradicionais do grupo

        Args:
            dataframe_grupo (pd.DataFrame): DataFrame do grupo/setor

        Returns:
            dict: Dicionário com médias ponderadas por indicador
        """
        medias_ponderadas = {}
        indicadores_avancados = ['margem_seguranca_graham', 'margem_seguranca_barsi']

        for indicador, config in self.indicadores.items():
            # Não calcula média para indicadores avançados
            if indicador in indicadores_avancados:
                continue

            if (indicador in dataframe_grupo.columns and
                    'Valor_de_mercado' in dataframe_grupo.columns):

                pesos = dataframe_grupo['Valor_de_mercado']
                valores = dataframe_grupo[indicador]

                mascara_dados_validos = ~valores.isna() & ~pesos.isna() & (pesos > 0)

                if mascara_dados_validos.sum() > 0:
                    valores_validos = valores[mascara_dados_validos]
                    pesos_validos = pesos[mascara_dados_validos]
                    try:
                        media_ponderada = np.average(valores_validos, weights=pesos_validos)
                        medias_ponderadas[indicador] = media_ponderada
                    except Exception as erro:
                        print(f"   ⚠️ Erro ao calcular média ponderada para {indicador}: {erro}")
                        medias_ponderadas[indicador] = np.nan
                else:
                    medias_ponderadas[indicador] = np.nan

        return medias_ponderadas

    def _calcular_margem_relativa(self, valor_empresa, media_grupo, indicador):
        """
        Calcula margem relativa em relação à média do grupo

        Args:
            valor_empresa (float): Valor da empresa para o indicador
            media_grupo (float): Média do grupo para o indicador
            indicador (str): Nome do indicador

        Returns:
            float: Margem relativa calculada
        """
        # Para indicadores avançados, usa normalização direta
        if indicador in ['margem_seguranca_graham', 'margem_seguranca_barsi']:
            return self._normalizar_margens_avancadas(valor_empresa, indicador)

        # Para outros indicadores, calcula margem relativa ao grupo
        if pd.isna(valor_empresa) or pd.isna(media_grupo) or media_grupo == 0:
            return 0.0

        return ((valor_empresa - media_grupo) / abs(media_grupo)) * 100

    def _normalizar_score_indicador(self, margem, tipo_relacao, penalidade=False):
        """
        Normaliza o score baseado no tipo de relação (maior/menor melhor)

        Args:
            margem (float): Margem calculada
            tipo_relacao (str): 'maior_melhor' ou 'menor_melhor'

        Returns:
            float: Score normalizado
        """
        if penalidade:
            if tipo_relacao == 'maior_melhor':
                return margem  # Penaliza valores abaixo da média
            else:  # menor_melhor
                return -margem  # Penaliza valores acima da média
        else:
            if tipo_relacao == 'maior_melhor':
                return max(0, margem)  # Penaliza valores abaixo da média
            else:  # menor_melhor
                return max(0, -margem)  # Penaliza valores acima da média

    # def _calcular_score_empresa(self, dados_empresa, medias_grupo, penalidade=False):
    #     """
    #     Calcula score WSM individual para uma empresa
    #
    #     Args:
    #         dados_empresa (pd.Series): Dados da empresa
    #         medias_grupo (dict): Médias do grupo/setor
    #
    #     Returns:
    #         float: Score WSM final
    #     """
    #     scores_ponderados = []
    #     pesos_aplicados = []
    #
    #     for indicador, config in self.indicadores.items():
    #         tipo_relacao = config['relacao']
    #         peso = config['peso']
    #
    #         if (indicador in dados_empresa.index and
    #                 not pd.isna(dados_empresa[indicador])):
    #             valor_empresa = dados_empresa[indicador]
    #             media_grupo = medias_grupo.get(indicador, 0)
    #
    #             margem = self._calcular_margem_relativa(valor_empresa, media_grupo, indicador)
    #             score_normalizado = self._normalizar_score_indicador(margem, tipo_relacao, penalidade)
    #
    #             scores_ponderados.append(score_normalizado * peso)
    #             pesos_aplicados.append(peso)
    #
    #     # Calcular score final ponderado
    #     if sum(pesos_aplicados) > 0:
    #         return sum(scores_ponderados) / sum(pesos_aplicados)
    #     else:
    #         return 0.0

    def _calcular_score_empresa(self, dados_empresa, medias_grupo, penalidade=False):
        """
        Calcula score WSM individual para uma empresa
        MODIFICADO: Retorna (score, completude)
        """
        scores_ponderados = []
        pesos_aplicados = []

        for indicador, config in self.indicadores.items():
            tipo_relacao = config['relacao']
            peso = config['peso']

            if (indicador in dados_empresa.index and
                    not pd.isna(dados_empresa[indicador])):
                valor_empresa = dados_empresa[indicador]
                media_grupo = medias_grupo.get(indicador, 0)

                margem = self._calcular_margem_relativa(valor_empresa, media_grupo, indicador)
                score_normalizado = self._normalizar_score_indicador(margem, tipo_relacao, penalidade)

                scores_ponderados.append(score_normalizado * peso)
                pesos_aplicados.append(peso)

        # Calcular score final e completude
        if sum(pesos_aplicados) > 0:
            score_final = sum(scores_ponderados) / sum(pesos_aplicados)

            # Calcular completude (percentual de indicadores disponíveis)
            completude = sum(pesos_aplicados) / sum([config['peso'] for config in self.indicadores.values()])

            # Aplicar ajuste por completude se necessário
            if completude < 0.6:  # Se faltar mais de 40% dos indicadores
                score_final *= completude

            return score_final, completude
        else:
            return 0.0, 0.0  # Score zero, completude zero

    def diagnosticar_empresas_sem_score_detalhado(self, dataframe_resultados):
        """
        Diagnóstico detalhado para identificar exatamente onde as empresas se perdem
        """
        print("\n🔍 DIAGNÓSTICO DETALHADO - EMPRESAS SEM SCORE")
        print("=" * 60)

        # Empresas originais vs empresas com score
        empresas_originais = set(self.dataframe['ticker'].dropna())
        empresas_com_score = set(dataframe_resultados['ticker'].dropna()) if not dataframe_resultados.empty else set()
        empresas_sem_score = empresas_originais - empresas_com_score

        print(f"Empresas originais: {len(empresas_originais)}")
        print(f"Empresas com score: {len(empresas_com_score)}")
        print(f"Empresas sem score: {len(empresas_sem_score)}")

        if not empresas_sem_score:
            print("✅ Todas as empresas têm score!")
            return

        # Analisar por subsetor
        print(f"\n📊 ANÁLISE POR SUBSETOR:")
        for subsetor in self.dataframe['Subsetor'].unique():
            empresas_subsetor = set(self.dataframe[self.dataframe['Subsetor'] == subsetor]['ticker'])
            empresas_subsetor_com_score = empresas_subsetor & empresas_com_score
            empresas_subsetor_sem_score = empresas_subsetor - empresas_com_score

            if empresas_subsetor_sem_score:
                print(
                    f"  {subsetor}: {len(empresas_subsetor_com_score)} com score, {len(empresas_subsetor_sem_score)} sem score")

        # Verificar 5 empresas sem score como exemplo
        print(f"\n🔎 EXEMPLOS DE EMPRESAS SEM SCORE:")
        for ticker in list(empresas_sem_score)[:5]:
            empresa = self.dataframe[self.dataframe['ticker'] == ticker].iloc[0]

            # Verificar dados básicos
            subsetor = empresa.get('Subsetor', 'N/A')
            valor_mercado = empresa.get('Valor_de_mercado', 0)

            # Verificar indicadores
            indicadores_presentes = 0
            for indicador in self.indicadores.keys():
                if indicador in empresa.index and not pd.isna(empresa[indicador]):
                    indicadores_presentes += 1

            print(f"  {ticker} (Subsetor: {subsetor}):")
            print(f"    - Indicadores presentes: {indicadores_presentes}/{len(self.indicadores)}")
            print(f"    - Valor mercado: {valor_mercado}")
            print(f"    - Tem 'Valor_de_mercado'? {'Sim' if 'Valor_de_mercado' in empresa.index else 'Não'}")

    def executar_analise(self):
        """
        Executa análise fundamentalista completa usando WSM
        """
        print("🎯 Iniciando análise fundamentalista WSM...")
        resultados = []

        # Agrupar por subsetor para análise comparativa
        for subsetor, grupo in self.dataframe.groupby('Subsetor'):
            print(f"   📊 Processando subsetor: {subsetor} ({len(grupo)} empresas)")

            # Remover outliers apenas para indicadores tradicionais
            grupo_limpo = self._remover_outliers_indicadores_tradicionais(grupo)

            if len(grupo_limpo) == 0:
                print(f"   ⚠️ Grupo {subsetor} vazio após remoção de outliers")
                continue

            # Calcular médias ponderadas do grupo
            medias_grupo = self._calcular_medias_ponderadas_grupo(grupo_limpo)

            # Calcular score para cada empresa do grupo
            for indice, empresa in grupo_limpo.iterrows():
                score_wsm, completude = self._calcular_score_empresa(empresa, medias_grupo, False)
                score_wsm_penalidade, _ = self._calcular_score_empresa(empresa, medias_grupo, True)

                # Coletar informações para resultado final
                informacoes_empresa = {
                    'empresa': empresa.get('Empresa', ''),
                    'subsetor': subsetor,
                    'ticker': empresa.get('ticker', ''),
                    'preco_atual': empresa.get('Cotacao', 0),
                    'valor_mercado': empresa.get('Valor_de_mercado', 0),
                    'score_wsm': score_wsm,
                    'score_wsm_penalidade': score_wsm_penalidade,
                    'completude_indicadores': completude,
                    'margem_graham': empresa.get('margem_seguranca_graham', 0),
                    'margem_barsi': empresa.get('margem_seguranca_barsi', 0),
                    'preco_lucro': empresa.get('PL', 0),
                    'roe': empresa.get('ROE', 0),
                    'roic': empresa.get('ROIC', 0)
                }

                resultados.append(informacoes_empresa)

        # Criar DataFrame de resultados
        dataframe_resultados = pd.DataFrame(resultados)

        if not dataframe_resultados.empty:
            dataframe_resultados = dataframe_resultados.sort_values('score_wsm', ascending=False)
            print(f"✅ Análise concluída: {len(dataframe_resultados)} empresas avaliadas")

            self.diagnosticar_empresas_sem_score_detalhado(dataframe_resultados)

        else:
            print("❌ Nenhum resultado gerado na análise")

        return dataframe_resultados


def exibir_estrutura_pesos():
    """
    Exibe a estrutura de pesos do modelo WSM de forma organizada

    Returns:
        pd.DataFrame: DataFrame com estrutura de pesos
    """
    estrutura_pesos = {
        'categoria': [
            'VALUATION TRADICIONAL',
            'RENTABILIDADE',
            'CRESCIMENTO',
            'SAÚDE FINANCEIRA',
            'METODOLOGIAS AVANÇADAS'
        ],
        'peso_categoria': ['20%', '30%', '15%', '15%', '20%'],
        'indicadores': [
            'P/L, P/VP, EV/EBITDA, Dividend Yield',
            'ROE, ROIC, Margem Líquida, Margem EBIT',
            'Crescimento Receita (5a), Crescimento Lucro, LPA',
            'Dívida Líquida/EBITDA, Dívida Bruta/Patrimônio, EBIT/Ativo',
            'Margem Segurança Graham, Margem Segurança Barsi'
        ],
        'pesos_indicadores': [
            '7%, 6%, 5%, 2%',
            '9%, 8%, 7%, 6%',
            '6%, 5%, 4%',
            '6%, 5%, 4%',
            '10%, 10%'
        ]
    }

    dataframe_pesos = pd.DataFrame(estrutura_pesos)
    return dataframe_pesos
