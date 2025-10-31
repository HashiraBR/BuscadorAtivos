import os
import pandas as pd
import numpy as np
from scipy import stats
import fundamentus as fd
from datetime import datetime


class ProvedorDadosFundamentus:
    """
    Classe para obtenção, tratamento e enriquecimento de dados fundamentais do Fundamentus
    Fornece dados consistentes para análise fundamentalista multi-metodologias
    """

    def __init__(self, diretorio_dados='output/dados/cache'):
        """
        Inicializa o provedor de dados

        Args:
            diretorio_dados (str): Diretório para armazenamento de cache
        """
        self.dataframe_ativos = None
        self.diretorio_dados = diretorio_dados
        os.makedirs(self.diretorio_dados, exist_ok=True)
        print(f"📁 Diretório de dados configurado: {os.path.abspath(self.diretorio_dados)}")

    def _gerar_caminho_arquivo_cache(self):
        """
        Gera caminho completo para arquivo de cache com timestamp

        Returns:
            str: Caminho completo do arquivo de cache
        """
        nome_arquivo = f"dados_fundamentais_{datetime.now().strftime('%Y%m%d')}.csv"
        caminho_completo = os.path.join(self.diretorio_dados, nome_arquivo)
        return caminho_completo

    def _aplicar_filtros_qualidade(self, dataframe):
        """
        Aplica filtros básicos de qualidade para seleção de ativos

        Args:
            dataframe (pd.DataFrame): DataFrame com dados brutos

        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        print("🔍 Aplicando filtros de qualidade...")

        condicoes_filtro = (
            (dataframe['pl'] > 0) &  # Empresas lucrativas
            (dataframe['c5y'] > 0) &  # Crescimento nos últimos 5 anos
            (dataframe['liq2m'] > 1_000_000)  # Liquidez mínima de 1 milhão
        )

        dataframe_filtrado = dataframe[condicoes_filtro]
        print(f"   ✅ Filtros aplicados: {len(dataframe_filtrado)}/{len(dataframe)} ativos atendem aos critérios")

        return dataframe_filtrado

    def _converter_valor_numerico(self, valor):
        """
        Converte valores para formato numérico com tratamento robusto

        Args:
            valor: Valor a ser convertido

        Returns:
            float: Valor convertido ou np.nan em caso de erro
        """
        if pd.isna(valor) or valor is None:
            return np.nan

        try:
            # Retorna direto se já for numérico
            if isinstance(valor, (int, float, np.number)):
                return float(valor)

            # Converte para string e limpa
            valor_str = str(valor).strip()

            # Verifica valores inválidos
            if valor_str in ['-', '', 'nan', 'None', 'NULL', 'N/A']:
                return np.nan

            # Remove pontos de milhar e converte vírgula decimal
            if '.' in valor_str and ',' in valor_str:
                # Formato: 1.000,50 → remove ponto milhar, converte vírgula
                valor_str = valor_str.replace('.', '').replace(',', '.')
            elif ',' in valor_str:
                # Formato: 1000,50 → converte vírgula para ponto
                valor_str = valor_str.replace(',', '.')

            # Remove símbolo de porcentagem
            valor_str = valor_str.replace('%', '')

            return float(valor_str)

        except (ValueError, TypeError) as erro:
            return np.nan

    def _normalizar_colunas_numericas(self, dataframe):
        """
        Normaliza todas as colunas numéricas do DataFrame

        Args:
            dataframe (pd.DataFrame): DataFrame com dados brutos

        Returns:
            pd.DataFrame: DataFrame com colunas normalizadas
        """
        print("🔄 Normalizando colunas numéricas...")

        colunas_para_conversao = [
            "Valor_da_firma", "PEBIT", "PSR", "PAtivos", "PCap_Giro",
            "PAtiv_Circ_Liq", "Div_Yield", "EV_EBITDA", "EV_EBIT",
            "Cres_Rec_5a", "Marg_Bruta", "Marg_EBIT", "Marg_Liquida",
            "EBIT_Ativo", "ROIC", "ROE", "Liquidez_Corr", "Div_Br_Patrim",
            "Giro_Ativos", "PL", "LPA", "VPA", "Cotacao", "Nro_Acoes"
        ]

        colunas_convertidas = 0
        for coluna in colunas_para_conversao:
            if coluna in dataframe.columns:
                dataframe[coluna] = dataframe[coluna].apply(self._converter_valor_numerico)
                colunas_convertidas += 1

        print(f"   ✅ {colunas_convertidas} colunas numéricas normalizadas")
        return dataframe

    def _ajustar_escala_valores(self, dataframe):
        """
        Ajusta escala de valores que vêm multiplicados por 100 ou 10 do Fundamentus

        Args:
            dataframe (pd.DataFrame): DataFrame com dados normalizados

        Returns:
            pd.DataFrame: DataFrame com escalas corrigidas
        """
        print("📏 Ajustando escala de valores...")

        # Colunas que necessitam divisão por 100
        colunas_div_100 = ["PL", "LPA", "VPA"]
        for coluna in colunas_div_100:
            if coluna in dataframe.columns:
                dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce') / 100.0

        # Colunas que necessitam divisão por 10 (normalmente porcentagens)
        colunas_div_10 = [
            "Div_Yield", "Marg_Bruta", "Marg_EBIT", "Marg_Liquida",
            "EBIT_Ativo", "ROIC", "ROE", "Cres_Rec_5a"
        ]
        for coluna in colunas_div_10:
            if coluna in dataframe.columns:
                dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce') / 10.0

        # Colunas que necessitam apenas conversão numérica
        colunas_conversao_simples = ['Cotacao', 'Nro_Acoes']
        for coluna in colunas_conversao_simples:
            if coluna in dataframe.columns:
                dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce')

        print("   ✅ Escala de valores ajustada")
        return dataframe

    def _calcular_payout_medio(self, dataframe):
        """
        Calcula payout médio: Payout = (DY × Cotacao) / LPA

        Args:
            dataframe (pd.DataFrame): DataFrame com dados fundamentais

        Returns:
            pd.DataFrame: DataFrame com coluna de payout adicionada
        """
        print("💰 Calculando payout médio...")

        colunas_necessarias = ['Div_Yield', 'Cotacao', 'LPA']

        if not all(coluna in dataframe.columns for coluna in colunas_necessarias):
            print("   ⚠️ Colunas necessárias não encontradas para cálculo do payout")
            return dataframe

        # Garante que as colunas são numéricas
        for coluna in colunas_necessarias:
            dataframe[coluna] = pd.to_numeric(dataframe[coluna], errors='coerce')

        # Aplica a fórmula apenas onde todos os valores são válidos
        condicoes_validas = (
            dataframe['Div_Yield'].notna() &
            dataframe['Cotacao'].notna() &
            dataframe['LPA'].notna() &
            (dataframe['LPA'] > 0)
        )

        dataframe.loc[condicoes_validas, 'Payout_Medio'] = (
            (dataframe.loc[condicoes_validas, 'Div_Yield'] / 10 *
             dataframe.loc[condicoes_validas, 'Cotacao']) /
            dataframe.loc[condicoes_validas, 'LPA']
        ).round(5)

        quantidade_calculada = dataframe['Payout_Medio'].notna().sum()
        print(f"   ✅ Payout médio calculado para {quantidade_calculada} empresas")

        return dataframe

    def _calcular_pl_medio_subsetor(self, dataframe, usar_ponderacao=True):
        """
        Calcula P/L médio por subsetor com consolidação correta por empresa

        Args:
            dataframe (pd.DataFrame): DataFrame com dados fundamentais
            usar_ponderacao (bool): Se deve usar ponderação por valor de mercado

        Returns:
            pd.DataFrame: DataFrame com coluna de P/L médio do subsetor
        """
        print("🏢 Calculando P/L médio por subsetor...")

        # CORREÇÃO: Usar coluna fixa 'ticker' como no original
        if 'ticker' not in dataframe.columns:
            print("   ❌ Coluna 'ticker' não encontrada no DataFrame")
            return dataframe

        # CORREÇÃO: Voltar ao método original - remove último caractere
        dataframe['Empresa_Base'] = dataframe['ticker'].str[:-1]

        # PASSO 2: Consolidar dados por empresa (manter lógica original)
        dados_empresas = []

        for empresa_base in dataframe['Empresa_Base'].unique():
            mascara_empresa = dataframe['Empresa_Base'] == empresa_base
            dados_empresa = dataframe[mascara_empresa]

            # Calcular P/L médio da empresa (entre ON/PN/etc)
            pl_empresa = dados_empresa['PL'].mean()

            # Calcular valor de mercado TOTAL da empresa (manter lógica original)
            if 'Cotacao' in dataframe.columns and 'Nro_Acoes' in dataframe.columns:
                valor_mercado_total = (
                    dados_empresa['Cotacao'] * dados_empresa['Nro_Acoes']
                ).sum()
            elif 'Valor_de_mercado' in dataframe.columns:
                valor_mercado_total = dados_empresa['Valor_de_mercado'].mean()
            else:
                valor_mercado_total = 1

            # Obter subsetor
            subsetor = dados_empresa['Subsetor'].iloc[0] if 'Subsetor' in dados_empresa.columns else None

            if subsetor and pd.notna(pl_empresa):
                dados_empresas.append({
                    'Empresa_Base': empresa_base,
                    'Subsetor': subsetor,
                    'PL_Medio_Empresa': pl_empresa,
                    'Valor_Mercado_Total': valor_mercado_total
                })

        if not dados_empresas:
            print("   ⚠️ Nenhuma empresa válida para cálculo do P/L médio do subsetor")
            return dataframe

        dataframe_empresas = pd.DataFrame(dados_empresas)
        print(f"   📊 Consolidadas {len(dataframe_empresas)} empresas únicas")

        # PASSO 3: Calcular média por subsetor (manter lógica original)
        subsetores = dataframe_empresas['Subsetor'].unique()
        medias_subsetor = {}

        for subsetor in subsetores:
            try:
                mascara_subsetor = dataframe_empresas['Subsetor'] == subsetor
                dados_subsetor = dataframe_empresas[mascara_subsetor]

                pl_empresas = dados_subsetor['PL_Medio_Empresa'].dropna()
                valores_mercado = dados_subsetor['Valor_Mercado_Total']

                if len(pl_empresas) == 0:
                    medias_subsetor[subsetor] = np.nan
                    continue

                # Manter exatamente a mesma lógica do original
                if len(pl_empresas) == 1:
                    media = pl_empresas.iloc[0]
                    metodo = "única empresa"
                elif len(pl_empresas) >= 2 and usar_ponderacao:
                    if (valores_mercado.notna().all() and
                        (valores_mercado > 0).all() and
                        len(valores_mercado) == len(pl_empresas)):
                        media = np.average(pl_empresas, weights=valores_mercado)
                        metodo = "ponderado"
                    else:
                        media = pl_empresas.mean()
                        metodo = "simples (fallback)"
                else:
                    media = pl_empresas.mean()
                    metodo = "simples"

                medias_subsetor[subsetor] = media
                print(f"   • {subsetor}: {len(pl_empresas)} empresas, {metodo}, P/L médio = {media:.2f}")

            except Exception as erro:
                print(f"   ❌ Erro no subsetor {subsetor}: {erro}")
                medias_subsetor[subsetor] = np.nan
                continue

        # PASSO 4: Atribuir as médias (usar nome original)
        dataframe['PL_Medio_Subsetor'] = dataframe['Subsetor'].map(medias_subsetor)
        dataframe['PL_Medio_Subsetor'] = dataframe['PL_Medio_Subsetor'].round(2)

        # Remover coluna temporária
        dataframe = dataframe.drop('Empresa_Base', axis=1, errors='ignore')

        print("   ✅ P/L médio por subsetor calculado e atribuído")
        return dataframe

    def _verificar_colunas_essenciais(self, dataframe):
        """
        Verifica se as colunas essenciais estão presentes no DataFrame

        Args:
            dataframe (pd.DataFrame): DataFrame a ser verificado

        Returns:
            bool: True se todas as colunas essenciais estão presentes
        """
        colunas_essenciais = ['ticker', 'Subsetor', 'PL', 'Cotacao', 'Nro_Acoes']
        colunas_faltantes = [col for col in colunas_essenciais if col not in dataframe.columns]

        if colunas_faltantes:
            print(f"   ⚠️ Colunas essenciais faltantes: {colunas_faltantes}")
            return False

        print("   ✅ Todas as colunas essenciais presentes")
        return True

    def carregar_dados_fundamentais(self, usar_cache=True):
        """
        Carrega e trata dados fundamentais do Fundamentus

        Args:
            usar_cache (bool): Utilizar arquivo de cache se disponível

        Returns:
            pd.DataFrame: DataFrame com dados tratados ou None em caso de erro
        """
        try:
            caminho_cache = self._gerar_caminho_arquivo_cache()

            # Tentar carregar do cache
            if usar_cache and os.path.exists(caminho_cache):
                self.dataframe_ativos = pd.read_csv(caminho_cache)
                print(f"📂 Dados carregados do cache: {caminho_cache}")

                # VERIFICAR SE AS COLUNAS NECESSÁRIAS EXISTEM
                if not self._verificar_colunas_essenciais(self.dataframe_ativos):
                    print("   ⚠️ Cache incompleto, buscando dados atualizados...")
                    usar_cache = False

            if not usar_cache or not os.path.exists(caminho_cache):
                print("🌐 Buscando dados atualizados do Fundamentus...")

                dados_brutos = fd.get_resultado()
                dados_filtrados = self._aplicar_filtros_qualidade(dados_brutos)

                lista_papeis = dados_filtrados.index.tolist()
                self.dataframe_ativos = fd.get_papel(lista_papeis)

                # CORREÇÃO: Usar 'ticker' (com P maiúsculo) como no original
                self.dataframe_ativos['ticker'] = lista_papeis

                # Pipeline completo de tratamento de dados
                print("🛠️  Executando pipeline de tratamento de dados...")
                self.dataframe_ativos.columns = self.dataframe_ativos.columns.str.strip()
                self.dataframe_ativos = self._normalizar_colunas_numericas(self.dataframe_ativos)
                self.dataframe_ativos = self._ajustar_escala_valores(self.dataframe_ativos)
                self.dataframe_ativos = self._calcular_payout_medio(self.dataframe_ativos)
                self.dataframe_ativos = self._calcular_pl_medio_subsetor(self.dataframe_ativos)

                # Salvar no cache
                self.dataframe_ativos.to_csv(caminho_cache, index=False)
                print(f"💾 Dados salvos no cache: {caminho_cache}")

            print(f"📈 Total de ativos processados: {len(self.dataframe_ativos)}")
            return self.dataframe_ativos

        except Exception as erro:
            print(f"❌ Erro crítico ao carregar dados: {erro}")
            import traceback
            traceback.print_exc()
            return None

    def obter_dataframe(self):
        """
        Retorna o dataframe tratado

        Returns:
            pd.DataFrame: DataFrame com dados fundamentais tratados
        """
        return self.dataframe_ativos

    def gerar_analise_subsetores(self):
        """
        Gera análise detalhada dos P/L médios por subsetor

        Returns:
            pd.DataFrame: DataFrame com análise consolidada por subsetor
        """
        if 'PL_Medio_Subsetor' not in self.dataframe_ativos.columns:
            print("⚠️ P/L médio por subsetor não foi calculado")
            return None

        print("\n📊 ANÁLISE DETALHADA POR SUBSETOR:")
        print("=" * 80)

        # Agrupar por subsetor e calcular estatísticas
        analise_subsetores = self.dataframe_ativos.groupby('Subsetor').agg({
            'PL': ['count', 'mean', 'std', 'min', 'max'],
            'PL_Medio_Subsetor': 'first'
        }).round(2)

        # Renomear colunas para melhor legibilidade
        analise_subsetores.columns = [
            'quantidade_empresas', 'pl_medio', 'pl_desvio_padrao',
            'pl_minimo', 'pl_maximo', 'pl_medio_subsetor_ajustado'
        ]

        # Ordenar por quantidade de empresas
        analise_subsetores = analise_subsetores.sort_values('quantidade_empresas', ascending=False)

        print(analise_subsetores)
        print("=" * 80)

        return analise_subsetores

    def obter_estatisticas_gerais(self):
        """
        Retorna estatísticas gerais do dataset

        Returns:
            dict: Dicionário com estatísticas principais
        """
        if self.dataframe_ativos is None:
            return {}

        estatisticas = {
            'total_ativos': len(self.dataframe_ativos),
            'subsetores_unicos': self.dataframe_ativos['Subsetor'].nunique(),
            'pl_medio_geral': self.dataframe_ativos['PL'].mean(),
            'empresas_com_payout': self.dataframe_ativos['Payout_Medio'].notna().sum()
        }

        print("\n📈 ESTATÍSTICAS GERAIS:")
        for chave, valor in estatisticas.items():
            print(f"   • {chave}: {valor}")

        return estatisticas


# Exemplo de uso
if __name__ == "__main__":
    # Criar instância do provedor
    provedor = ProvedorDadosFundamentus()

    # Carregar dados
    dados = provedor.carregar_dados_fundamentais(usar_cache=True)

    if dados is not None:
        # Gerar análises
        provedor.gerar_analise_subsetores()
        provedor.obter_estatisticas_gerais()

        print("\n✅ Processamento concluído com sucesso!")