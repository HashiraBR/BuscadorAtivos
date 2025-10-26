class AnalisadorPLDescontado:
    """
    Classe para análise de desconto no P/L em relação à média do subsetor
    """

    def __init__(self, ticker, preco_atual, lpa, pl_medio_subsetor):
        """
        Construtor da classe
        """
        self.ticker = ticker
        self.preco_atual = preco_atual
        self.lpa = lpa
        self.pl_medio_subsetor = pl_medio_subsetor

    def calcular_pl_atual(self):
        """
        Calcula o P/L atual da ação: Preço / LPA
        """
        try:
            if self.lpa is None or self.lpa <= 0:
                return None
            pl_atual = self.preco_atual / self.lpa
            return round(pl_atual, 2)
        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro no calculo do PL atual: {e}")
            return None

    def calcular_preco_alvo(self):
        """
        Calcula o preço alvo caso a ação alcance o PL médio do subsetor
        Preço_Alvo = LPA × PL_Medio_Subsetor
        """
        try:
            if self.lpa is None or self.pl_medio_subsetor is None:
                return None

            preco_alvo = self.lpa * self.pl_medio_subsetor
            return round(preco_alvo, 2)
        except (TypeError, ValueError) as e:
            print(f"Erro no calculo do preco alvo: {e}")
            return None

    def calcular_margem_seguranca(self):
        """
        Calcula a margem de segurança (única métrica necessária)
        """
        try:
            preco_alvo = self.calcular_preco_alvo()
            if preco_alvo is None:
                return None

            margem_absoluta = preco_alvo - self.preco_atual
            margem_percentual = (margem_absoluta / self.preco_atual) * 100

            return {
                'absoluta': round(margem_absoluta, 2),
                'percentual': round(margem_percentual, 2)
            }
        except (TypeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro no calculo da margem de seguranca: {e}")
            return None

    def analise_completa(self):
        """
        Executa análise completa do PL descontado
        """
        pl_atual = self.calcular_pl_atual()
        preco_alvo = self.calcular_preco_alvo()
        margem_seguranca = self.calcular_margem_seguranca()

        return {
            'ticker': self.ticker,
            'pl_atual': pl_atual,
            'pl_medio_subsetor': self.pl_medio_subsetor,
            'preco_alvo': preco_alvo,
            'margem_seguranca': margem_seguranca
        }