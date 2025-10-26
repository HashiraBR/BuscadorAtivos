class AnalisadorGraham:
    """
    Classe para análise de ações baseada na metodologia de Benjamin Graham
    """

    def __init__(self, ticker, preco_atual, lpa, vpa):
        """
        Construtor da classe

        Args:
            ticker (str): Código da ação (ex: 'PETR4')
            preco_atual (float): Preço atual da ação
            lpa (float): Lucro por Ação
            vpa (float): Valor Patrimonial por Ação
        """
        self.ticker = ticker
        self.preco_atual = preco_atual
        self.lpa = lpa
        self.vpa = vpa

    def calcular_graham_number(self):
        """
        Calcula o Graham Number: √(22.5 × LPA × VPA)
        """
        try:
            # Verificar se LPA e VPA são positivos
            if self.lpa <= 0 or self.vpa <= 0:
                return None

            # Calcular o valor dentro da raiz
            valor = 22.5 * self.lpa * self.vpa

            # Verificar se o valor é positivo antes de calcular a raiz
            if valor < 0:
                return None

            graham_number = valor ** 0.5

            # Verificar se é um número real (não complexo)
            if isinstance(graham_number, complex):
                return None

            return round(graham_number, 2)
        except (TypeError, ValueError) as e:
            print(f"Erro no cálculo do Graham Number: {e}")
            return None

    def calcular_margem_seguranca(self):
        """
        Calcula a margem de segurança em relação ao preço atual

        Returns:
            dict: Dicionário com margem absoluta e percentual
        """
        graham_number = self.calcular_graham_number() # Preço teto = nº de Graham
        if graham_number is None:
            return None

        margem_absoluta = graham_number - self.preco_atual
        margem_percentual = (margem_absoluta / self.preco_atual) * 100

        return {
            'absoluta': round(margem_absoluta, 2),
            'percentual': round(margem_percentual, 2)
        }
