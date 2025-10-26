import os
import pandas as pd
import numpy as np
from scipy import stats
import fundamentus as fd

class DataProviderFundamentus:
    """
    Classe para obtenção e tratamento de dados do Fundamentus
    """

    def __init__(self, data_dir='data/downloads'):
        """
        Construtor da classe
        """
        self.df_papeis = None
        self.data_dir = data_dir
        import os
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"Diretorio de dados: {os.path.abspath(self.data_dir)}")

    def _get_nome_arquivo(self):
        """Gera caminho completo para o arquivo CSV"""
        from datetime import datetime
        nome_arquivo = f"ativos_{datetime.now().strftime('%d_%m_%Y')}.csv"
        caminho_completo = os.path.join(self.data_dir, nome_arquivo)
        return caminho_completo

    def _aplicar_filtros_qualidade(self, df):
        """Aplica filtros básicos de qualidade nos dados"""
        filtros = (
                (df['pl'] > 0) &  # Empresas lucrativas
                (df['c5y'] > 0) &  # Crescimento nos últimos 5 anos
                (df['liq2m'] > 1_000_000)  # Boa liquidez
        )
        return df[filtros]

    def _normalizar_colunas_numericas(self, df):
        """Normaliza colunas numéricas com tratamento de erros"""

        def converter_para_float(valor):
            if pd.isna(valor) or valor is None:
                return np.nan
            try:
                # Se já for numérico, retorna direto
                if isinstance(valor, (int, float, np.number)):
                    return float(valor)

                # Converte para string e limpa
                valor_str = str(valor).strip()

                # Verifica se está vazio ou inválido
                if valor_str in ['-', '', 'nan', 'None', 'NULL', 'N/A']:
                    return np.nan

                # Remove pontos de milhar e converte vírgula decimal
                if '.' in valor_str and ',' in valor_str:
                    # Formato: 1.000,50 → remove ponto milhar, converte vírgula
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                elif ',' in valor_str:
                    # Formato: 1000,50 → converte vírgula para ponto
                    valor_str = valor_str.replace(',', '.')

                # Remove porcentagem
                valor_str = valor_str.replace('%', '')

                # Converte para float
                return float(valor_str)

            except (ValueError, TypeError) as e:
                return np.nan

        # Colunas que precisam de conversão
        colunas_numericas = [
            "Valor_da_firma", "PEBIT", "PSR", "PAtivos", "PCap_Giro",
            "PAtiv_Circ_Liq", "Div_Yield", "EV_EBITDA", "EV_EBIT",
            "Cres_Rec_5a", "Marg_Bruta", "Marg_EBIT", "Marg_Liquida",
            "EBIT_Ativo", "ROIC", "ROE", "Liquidez_Corr", "Div_Br_Patrim",
            "Giro_Ativos", "PL", "LPA", "VPA", "Cotacao", "Nro_Acoes"
        ]

        for coluna in colunas_numericas:
            if coluna in df.columns:
                df[coluna] = df[coluna].apply(converter_para_float)

        return df

    def _ajustar_escala_valores(self, df):
        """Ajusta escala de valores que vem multiplicada por 100 ou 10"""

        # Colunas ÷100
        for coluna in ["PL", "LPA", "VPA"]:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce') / 100.0

        # Colunas ÷10
        for coluna in ["Div_Yield", "Marg_Bruta", "Marg_EBIT", "Marg_Liquida",
                       "EBIT_Ativo", "ROIC", "ROE", "Cres_Rec_5a"]:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce') / 10.0

        # Cotacao e Nro_Acoes não precisam de ajuste de escala, só conversão
        for coluna in ['Cotacao', 'Nro_Acoes']:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors='coerce')

        return df

    def _calcular_payout_medio(self, df):
        """
        Calcula payout médio: Payout = (DY × Cotacao) / LPA
        """
        colunas_necessarias = ['Div_Yield', 'Cotacao', 'LPA']

        if not all(col in df.columns for col in colunas_necessarias):
            print("Colunas necessarias nao encontradas para calcular payout")
            return df

        # Garante que são numéricos
        df['Div_Yield'] = pd.to_numeric(df['Div_Yield'], errors='coerce')
        df['Cotacao'] = pd.to_numeric(df['Cotacao'], errors='coerce')
        df['LPA'] = pd.to_numeric(df['LPA'], errors='coerce')

        # Aplica a fórmula apenas onde todos os valores são válidos
        mask = (
                df['Div_Yield'].notna() &
                df['Cotacao'].notna() &
                df['LPA'].notna() &
                (df['LPA'] > 0)
        )

        df.loc[mask, 'Payout_Medio'] = (
                (df.loc[mask, 'Div_Yield'] / 10 * df.loc[mask, 'Cotacao']) /
                df.loc[mask, 'LPA']
        ).round(5)

        # Limita valores entre 0% e 100% (valores realistas)
        #df['Payout_Medio'] = df['Payout_Medio'].clip(0, 1)

        payout_calculado = df['Payout_Medio'].notna().sum()
        print(f"Payout medio calculado para {payout_calculado} empresas")

        return df

    def _calcular_pl_medio_subsetor(self, df, usar_ponderacao=True):
        """
        Calcula média do P/L por subsetor com consolidacao correta por empresa
        """
        print("Calculando P/L medio por subsetor (consolidando por empresa)...")

        # PASSO 1: Criar codigo base da empresa
        df['Empresa_Base'] = df['Papel'].str[:-1]

        # PASSO 2: Consolidar dados por empresa
        empresas_data = []

        for empresa_base in df['Empresa_Base'].unique():
            mask_empresa = df['Empresa_Base'] == empresa_base
            dados_empresa = df[mask_empresa]

            # Calcular PL medio da empresa (entre ON/PN/etc)
            pl_empresa = dados_empresa['PL'].mean()

            # Calcular valor de mercado TOTAL da empresa
            if 'Cotacao' in df.columns and 'Nro_Acoes' in df.columns:
                # Soma o valor de mercado de todos os papéis da empresa
                valor_mercado_total = (
                        dados_empresa['Cotacao'] * dados_empresa['Nro_Acoes']
                ).sum()
            elif 'Valor_de_mercado' in df.columns:
                # Fallback: usa média dos valores individuais se não tiver Nro_Acoes
                valor_mercado_total = dados_empresa['Valor_de_mercado'].mean()
            else:
                valor_mercado_total = 1  # Fallback para média simples

            # Pegar subsetor (deve ser o mesmo para todos os papéis da mesma empresa)
            subsetor = dados_empresa['Subsetor'].iloc[0] if 'Subsetor' in dados_empresa.columns else None

            if subsetor and pd.notna(pl_empresa):
                empresas_data.append({
                    'Empresa_Base': empresa_base,
                    'Subsetor': subsetor,
                    'PL_Medio_Empresa': pl_empresa,
                    'Valor_Mercado_Total': valor_mercado_total
                })

        if not empresas_data:
            print("Nenhuma empresa valida para calcular PL medio do subsetor")
            return df

        df_empresas = pd.DataFrame(empresas_data)
        print(f"Consolidadas {len(df_empresas)} empresas unicas")

        # PASSO 3: Calcular média por subsetor (usando empresas consolidadas)
        subsetores = df_empresas['Subsetor'].unique()
        medias_subsetor = {}

        for subsetor in subsetores:
            try:
                # Dados do subsetor (já consolidados por empresa)
                mask_subsetor = df_empresas['Subsetor'] == subsetor
                dados_subsetor = df_empresas[mask_subsetor]

                pl_empresas = dados_subsetor['PL_Medio_Empresa'].dropna()
                valores_mercado = dados_subsetor['Valor_Mercado_Total']

                if len(pl_empresas) == 0:
                    medias_subsetor[subsetor] = np.nan
                    continue

                # Caso 1: Apenas 1 empresa no subsetor
                if len(pl_empresas) == 1:
                    media = pl_empresas.iloc[0]
                    metodo = "unica empresa"

                # Caso 2: 2+ empresas com ponderação
                elif len(pl_empresas) >= 2 and usar_ponderacao:
                    # Verifica se temos dados de valor de mercado para todas
                    if (valores_mercado.notna().all() and
                            (valores_mercado > 0).all() and
                            len(valores_mercado) == len(pl_empresas)):

                        media = np.average(pl_empresas, weights=valores_mercado)
                        metodo = "ponderado"
                    else:
                        # Fallback para média simples
                        media = pl_empresas.mean()
                        metodo = "simples (fallback)"

                # Caso 3: 2+ empresas sem ponderação
                else:
                    media = pl_empresas.mean()
                    metodo = "simples"

                medias_subsetor[subsetor] = media
                print(f"  {subsetor}: {len(pl_empresas)} empresas, {metodo}, PL medio = {media:.2f}")

            except Exception as e:
                print(f"  Erro no subsetor {subsetor}: {e}")
                medias_subsetor[subsetor] = np.nan
                continue

        # PASSO 4: Atribuir as médias de volta ao DataFrame original
        df['PL_Medio_Subsetor'] = df['Subsetor'].map(medias_subsetor)
        df['PL_Medio_Subsetor'] = df['PL_Medio_Subsetor'].round(2)

        return df

    def carregar_dados(self, usar_cache=True):
        """
        Carrega dados do Fundamentus com tratamento completo
        """
        try:
            caminho_arquivo = self._get_nome_arquivo()

            if usar_cache and os.path.exists(caminho_arquivo):
                self.df_papeis = pd.read_csv(caminho_arquivo)
                print(f"Dados carregados do cache: {caminho_arquivo}")
                return self.df_papeis

            # Buscar dados frescos do Fundamentus
            df_all = fd.get_resultado()
            df_filtrado = self._aplicar_filtros_qualidade(df_all)

            papeis = df_filtrado.index.tolist()
            self.df_papeis = fd.get_papel(papeis)

            # Adiciona os papeis como coluna
            self.df_papeis['Papel'] = papeis

            # Pipeline de tratamento de dados
            self.df_papeis.columns = self.df_papeis.columns.str.strip()
            self.df_papeis = self._normalizar_colunas_numericas(self.df_papeis)
            self.df_papeis = self._ajustar_escala_valores(self.df_papeis)
            self.df_papeis = self._calcular_payout_medio(self.df_papeis)
            self.df_papeis = self._calcular_pl_medio_subsetor(self.df_papeis)

            # Salvar cache
            self.df_papeis.to_csv(caminho_arquivo, index=False)
            print(f"Dados salvos em: {caminho_arquivo}")
            print(f"Total de ativos: {len(self.df_papeis)}")

            return self.df_papeis

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_dataframe(self):
        """Retorna o dataframe tratado"""
        return self.df_papeis

    def analisar_pl_subsetor(self):
        """
        Mostra análise dos P/L médios por subsetor
        """
        if 'PL_Medio_Subsetor' not in self.df_papeis.columns:
            print("P/L medio por subsetor nao foi calculado")
            return

        print("\nANALISE P/L POR SUBSETOR:")

        # Agrupa por subsetor e mostra estatísticas
        analise = self.df_papeis.groupby('Subsetor').agg({
            'PL': ['count', 'mean', 'std', 'min', 'max'],
            'PL_Medio_Subsetor': 'first'
        }).round(2)

        # Renomeia colunas para melhor visualização
        analise.columns = ['Qtd_Empresas', 'PL_Media', 'PL_Desvio', 'PL_Min', 'PL_Max', 'PL_Medio_Sem_Outliers']

        print(analise.sort_values('Qtd_Empresas', ascending=False))


# import fundamentus as fd
# import os
# from datetime import datetime
# import pandas as pd
# import numpy as np
# from scipy import stats
#
#
# class DataProviderFundamentus:
#     """
#     Classe para obtenção e tratamento de dados do Fundamentus
#     """
#
#     def __init__(self):
#         self.df_papeis = None
#
#     def _aplicar_filtros_qualidade(self, df):
#         """Aplica filtros básicos de qualidade nos dados"""
#         filtros = (
#                 (df['pl'] > 0) &  # Empresas lucrativas
#                 (df['c5y'] > 0) &  # Crescimento nos últimos 5 anos
#                 (df['liq2m'] > 1_000_000)  # Boa liquidez
#         )
#         return df[filtros]
#
#     def _normalizar_colunas_numericas(self, df):
#         """Normaliza colunas numéricas com tratamento de erros"""
#
#         def converter_para_float(valor):
#             if pd.isna(valor):
#                 return np.nan
#             try:
#                 # Remove caracteres especiais e converte vírgula para ponto
#                 valor_str = str(valor).replace('.', '').replace(',', '.').replace('%', '').strip()
#                 return float(valor_str) if valor_str not in ['-', '', 'nan', 'None'] else np.nan
#             except:
#                 return np.nan
#
#         # Colunas que precisam de conversão
#         colunas_numericas = [
#             "Valor_da_firma", "PEBIT", "PSR", "PAtivos", "PCap_Giro",
#             "PAtiv_Circ_Liq", "Div_Yield", "EV_EBITDA", "EV_EBIT",
#             "Cres_Rec_5a", "Marg_Bruta", "Marg_EBIT", "Marg_Liquida",
#             "EBIT_Ativo", "ROIC", "ROE", "Liquidez_Corr", "Div_Br_Patrim",
#             "Giro_Ativos", "Cotacao"
#         ]
#
#         for coluna in colunas_numericas:
#             if coluna in df.columns:
#                 df[coluna] = df[coluna].apply(converter_para_float)
#
#         return df
#
#     def _ajustar_escala_valores(self, df):
#         """Ajusta escala de valores que vem multiplicada por 100 ou 10"""
#         # Colunas que vêm multiplicadas por 100
#
#         colunas_100 = ["PL", "LPA", "VPA", "Cotacao"]
#         for coluna in colunas_100:
#             if coluna in df.columns:
#                 df[coluna] = pd.to_numeric(df[coluna], errors='coerce') / 100.0
#
#         # Colunas que vêm multiplicadas por 10
#         colunas_10 = [
#             "Marg_Bruta", "Marg_EBIT", "Marg_Liquida",
#             "EBIT_Ativo", "ROIC", "ROE", "Div_Yield", "Cres_Rec_5a"
#         ]
#         for coluna in colunas_10:
#             if coluna in df.columns:
#                 df[coluna] = pd.to_numeric(df[coluna], errors='coerce') / 10.0
#
#         return df
#     def _calcular_payout_medio(self, df):
#         """
#         Calcula payout médio: Payout = (DY × Cotacao) / LPA
#         """
#         # Verifica se temos as colunas necessárias
#         colunas_necessarias = ['Div_Yield', 'Cotacao', 'LPA']
#
#         if not all(col in df.columns for col in colunas_necessarias):
#             print("Colunas necessárias não encontradas para calcular payout")
#             return df
#
#         print("Garantindo que colunas são numéricas antes do cálculo...")
#
#         # CONVERTE PARA NUMÉRICO ANTES de qualquer operação
#         # df['Div_Yield'] = pd.to_numeric(df['Div_Yield'], errors='coerce')
#         # df['Cotacao'] = pd.to_numeric(df['Cotacao'], errors='coerce')
#         # df['LPA'] = pd.to_numeric(df['LPA'], errors='coerce')
#
#         # Aplica a fórmula apenas onde todos os valores são válidos
#         mask = (
#                 df['Div_Yield'].notna() &
#                 df['Cotacao'].notna() &
#                 df['LPA'].notna() &
#                 (df['LPA'] > 0)  # Evita divisão por zero
#         )
#
#         df.loc[mask, 'Payout_Medio'] = (
#                 (df.loc[mask, 'Div_Yield'] * df.loc[mask, 'Cotacao']) /
#                 df.loc[mask, 'LPA']
#         ).round(2)
#
#         # Limita valores entre 0% e 100% (valores realistas)
#         # df['Payout_Medio'] = df['Payout_Medio'].clip(0, 1)
#
#         # Estatísticas
#         payout_calculado = df['Payout_Medio'].notna().sum()
#         print(f"Payout médio calculado para {payout_calculado} empresas")
#
#         # Debug: mostra alguns valores
#         if payout_calculado > 0:
#             sample = df[['Empresa', 'Div_Yield', 'Cotacao', 'LPA', 'Payout_Medio']].head(3)
#             print("Amostra de cálculos:")
#             for _, row in sample.iterrows():
#                 if pd.notna(row['Payout_Medio']):
#                     print(
#                         f"  {row['Empresa']}: DY={row['Div_Yield']:.2%} × R${row['Cotacao']} ÷ LPA=R${row['LPA']} = {row['Payout_Medio']:.1%}")
#
#         return df
#
#     def _get_nome_arquivo(self):
#         """Gera caminho completo para o arquivo no diretório data/downloads"""
#         # Cria diretório se não existir
#         os.makedirs('data/downloads', exist_ok=True)
#
#         nome_arquivo = f"ativos_{datetime.now().strftime('%d_%m_%Y')}.csv"
#         return os.path.join('data/downloads', nome_arquivo)
#
#     def _calcular_pl_medio_subsetor(self, df, metodo='iqr', threshold=1.5):
#         """
#         Calcula a média do P/L por subsetor, removendo outliers
#         PRIMEIRO agrupa ON/PN da mesma empresa, DEPOIS calcula média do subsetor
#
#         Args:
#             df (DataFrame): DataFrame com dados
#             metodo (str): 'iqr' (Interquartile Range) ou 'zscore'
#             threshold (float): Limite para identificar outliers
#
#         Returns:
#             DataFrame: DataFrame com nova coluna 'PL_Medio_Subsetor'
#         """
#         if 'Subsetor' not in df.columns or 'PL' not in df.columns or 'Papel' not in df.columns:
#             print("Colunas necessarias nao encontradas")
#             return df
#
#         print("Calculando P/L medio por subsetor (agrupando ON/PN primeiro)...")
#
#         # PASSO 1: Criar codigo base da empresa (PETR3 -> PETR, ITUB4 -> ITUB)
#         df['Empresa_Base'] = df['Papel'].str[:-1]
#
#         # PASSO 2: Calcular P/L medio por empresa (agrupa ON/PN)
#         pl_por_empresa = df.groupby(['Empresa_Base', 'Subsetor'])['PL'].mean().reset_index()
#         pl_por_empresa.columns = ['Empresa_Base', 'Subsetor', 'PL_Medio_Empresa']
#
#         print(f"Agrupadas {len(pl_por_empresa)} empresas unicas (ON/PN consolidados)")
#
#         # PASSO 3: Calcular media por subsetor SEM OUTLIERS (usando empresas unicas)
#         subsetores = pl_por_empresa['Subsetor'].unique()
#         medias_subsetor = {}
#
#         for subsetor in subsetores:
#             try:
#                 # Dados do subsetor (ja consolidados por empresa)
#                 dados_pl = pl_por_empresa.loc[
#                     pl_por_empresa['Subsetor'] == subsetor, 'PL_Medio_Empresa'
#                 ].dropna()
#
#                 if len(dados_pl) < 3:  # Minimo de dados para analise
#                     print(f"  {subsetor}: poucos dados ({len(dados_pl)})")
#                     medias_subsetor[subsetor] = dados_pl.mean() if len(dados_pl) > 0 else np.nan
#                     continue
#
#                 # Identifica outliers
#                 if metodo == 'iqr':
#                     # Metodo IQR (Interquartile Range)
#                     Q1 = dados_pl.quantile(0.25)
#                     Q3 = dados_pl.quantile(0.75)
#                     IQR = Q3 - Q1
#                     limite_inferior = Q1 - threshold * IQR
#                     limite_superior = Q3 + threshold * IQR
#
#                     # Filtra sem outliers
#                     dados_sem_outliers = dados_pl[
#                         (dados_pl >= limite_inferior) &
#                         (dados_pl <= limite_superior)
#                         ]
#
#                 elif metodo == 'zscore':
#                     # Metodo Z-Score
#                     z_scores = np.abs(stats.zscore(dados_pl))
#                     dados_sem_outliers = dados_pl[z_scores < threshold]
#
#                 # Calcula media sem outliers
#                 if len(dados_sem_outliers) > 0:
#                     pl_medio = dados_sem_outliers.mean()
#                     outliers_removidos = len(dados_pl) - len(dados_sem_outliers)
#
#                     medias_subsetor[subsetor] = pl_medio
#
#                     print(f"  {subsetor}: {len(dados_sem_outliers)} empresas, "
#                           f"PL medio = {pl_medio:.2f}, "
#                           f"outliers = {outliers_removidos}")
#                 else:
#                     print(f"  {subsetor}: todos os dados foram considerados outliers")
#                     medias_subsetor[subsetor] = dados_pl.mean()  # Usa media bruta como fallback
#
#             except Exception as e:
#                 print(f"  Erro no subsetor {subsetor}: {e}")
#                 medias_subsetor[subsetor] = np.nan
#                 continue
#
#         # PASSO 4: Atribuir as medias de volta ao DataFrame original
#         df['PL_Medio_Subsetor'] = df['Subsetor'].map(medias_subsetor)
#
#         # Arredonda para 2 casas decimais
#         df['PL_Medio_Subsetor'] = df['PL_Medio_Subsetor'].round(2)
#
#         # PASSO 5: Estatisticas finais
#         subsetores_com_media = df['PL_Medio_Subsetor'].notna().groupby(df['Subsetor']).any()
#         subsetores_validos = subsetores_com_media.sum()
#
#         print(f"Processo concluido: {subsetores_validos} subsetores com media calculada")
#         print(f"Empresas unicas consideradas: {len(pl_por_empresa)}")
#         print(f"Acoes no dataset final: {len(df)}")
#
#         return df
#
#     def carregar_dados(self, usar_cache=True):
#         """
#         Carrega dados do Fundamentus com tratamento completo
#
#         Args:
#             usar_cache (bool): Se True, usa arquivo salvo se existir
#         """
#         try:
#             # Tentar carregar do cache primeiro
#             if usar_cache:
#                 try:
#                     self.df_papeis = pd.read_csv(self._get_nome_arquivo())
#                     print("Dados carregados do cache")
#                     return self.df_papeis
#                 except FileNotFoundError:
#                     print("Cache não encontrado, buscando do Fundamentus...")
#
#             # Buscar dados frescos do Fundamentus
#             df_all = fd.get_resultado()
#             df_filtrado = self._aplicar_filtros_qualidade(df_all)
#
#             papeis = df_filtrado.index.tolist()
#             self.df_papeis = fd.get_papel(papeis)
#             # self.df_papeis = fd.get_papel(papeis[1])
#
#             self.df_papeis['Papel'] = papeis
#
#             # Pipeline de tratamento de dados
#             self.df_papeis.columns = self.df_papeis.columns.str.strip()
#             self.df_papeis = self._normalizar_colunas_numericas(self.df_papeis)
#             self.df_papeis = self._ajustar_escala_valores(self.df_papeis)
#             self.df_papeis = self._calcular_payout_medio(self.df_papeis)
#             self.df_papeis = self._calcular_pl_medio_subsetor(self.df_papeis)
#
#             # Salvar cache
#             self.df_papeis.to_csv(self._get_nome_arquivo(), index=False)
#             print(f"Dados atualizados e salvos: {len(self.df_papeis)} ativos")
#
#             return self.df_papeis
#
#         except Exception as e:
#             print(f"Erro ao carregar dados: {e}")
#             return None
#
#     def get_dataframe(self):
#         """Retorna o dataframe tratado"""
#         return self.df_papeis
#
#     def get_colunas_analise(self):
#         """Retorna colunas principais para análise"""
#         colunas_base = ["Papel", "Cotacao", "PL", "LPA", "VPA", "Div_Yield", "Payout_Medio", "PL_Medio_Subsetor"]
#         return [col for col in colunas_base if col in self.df_papeis.columns]
