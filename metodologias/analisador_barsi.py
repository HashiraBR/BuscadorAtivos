class AnalisadorBarsi:
    """
    Classe para análise de ações baseada na metodologia de Luiz Barsi
    Foco em preço teto baseado em dividendos
    """

    def __init__(self, ticker, preco_atual, lpa, payout_medio, pct=0.06):
        """
        Construtor da classe

        Args:
            ticker (str): Código da ação (ex: 'PETR4')
            preco_atual (float): Preço atual da ação
            lpa (float): Lucro por Ação
            payout_medio (float): Payout médio histórico (ex: 0.70 para 70%)
        """
        self.ticker = ticker
        self.preco_atual = preco_atual
        self.lpa = lpa
        self.payout_medio = payout_medio
        self.pct = pct

    def calcular_dpa(self):
        """
        Calcula o Dividendos por Ação esperado: DPA = Payout × LPA

        Returns:
            float: DPA (Dividendos por Ação)
        """
        try:
            dpa = self.payout_medio * self.lpa
            return round(dpa, 2)
        except (TypeError, ValueError) as e:
            print(f"Erro no cálculo do DPA: {e}")
            return None

    def calcular_preco_teto(self):
        """
        Calcula o preço teto a 6%: PTP6% = DPA / 0,06

        Returns:
            float: Preço teto para DY default
        """
        try:
            dpa = self.calcular_dpa()
            if dpa is None:
                return None

            preco_teto = dpa / self.pct
            return round(preco_teto, 2)
        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro no cálculo do preço teto: {e}")
            return None

    def calcular_margem_seguranca(self):
        """
        Calcula a margem de segurança em relação ao preço atual
        usando o preço teto a 6%

        Returns:
            dict: Dicionário com margem absoluta e percentual
        """
        preco_teto = self.calcular_preco_teto()
        if preco_teto is None:
            return None

        margem_absoluta = preco_teto - self.preco_atual
        margem_percentual = (margem_absoluta / self.preco_atual) * 100

        return {
            'absoluta': round(margem_absoluta, 2),
            'percentual': round(margem_percentual, 2)
        }

    def calcular_variacoes_dy(self):
        """
        Calcula preços tetos para diferentes DYs alvo

        Returns:
            dict: Preços tetos para DYs de 5%, 6%, 7% e 8%
        """
        dpa = self.calcular_dpa()
        if dpa is None:
            return None

        return {
            'dy_5pct': round(dpa / 0.05, 2),  # Mais conservador
            'dy_6pct': round(dpa / 0.06, 2),  # Padrão Barsi
            'dy_7pct': round(dpa / 0.07, 2),  # Menos conservador
            'dy_8pct': round(dpa / 0.08, 2),
        }

    def calcular_dy_atual(self):
        """
        Calcula o Dividend Yield atual baseado no DPA esperado

        Returns:
            float: DY atual em percentual
        """
        try:
            dpa = self.calcular_dpa()
            if dpa is None or self.preco_atual <= 0:
                return None

            dy_atual = (dpa / self.preco_atual) * 100
            return round(dy_atual, 2)
        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro no cálculo do DY atual: {e}")
            return None