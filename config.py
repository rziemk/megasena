"""
Configurações do Projeto Mega-Sena
==================================
Parâmetros de orçamento, custos e configurações estatísticas.
"""

# =============================================================================
# CONFIGURAÇÕES DE ORÇAMENTO
# =============================================================================
BUDGET_TOTAL = 180_000.00  # R$ 180.000,00

# Tabela oficial de custos por quantidade de dezenas
TABELA_CUSTOS = {
    6: 5.00,
    7: 35.00,
    8: 140.00,
    9: 420.00,
    10: 1_050.00,
    11: 2_310.00,
    12: 4_620.00,
    13: 8_580.00,
    14: 15_015.00,
    15: 25_025.00,
    16: 40_040.00,
    17: 61_880.00,
    18: 92_820.00,
    19: 135_660.00,
    20: 193_800.00,
}

# Nota: Os custos na imagem do usuário diferem ligeiramente
# Usando valores atualizados conforme imagem fornecida:
TABELA_CUSTOS_OFICIAL = {
    6: 6.00,
    7: 42.00,
    8: 168.00,
    9: 504.00,
    10: 1_260.00,
    11: 2_772.00,
    12: 5_544.00,
    13: 10_296.00,
    14: 18_018.00,
    15: 30_030.00,
    16: 48_048.00,
    17: 74_256.00,
    18: 111_384.00,
    19: 162_792.00,
    20: 232_560.00,
}

# =============================================================================
# PROBABILIDADES OFICIAIS (1 em X)
# =============================================================================
PROBABILIDADES = {
    # dezenas: (sena, quina, quadra)
    6: (50_063_860, 154_518, 2_332),
    7: (7_151_980, 44_981, 1_038),
    8: (1_787_995, 17_192, 539),
    9: (595_998, 7_791, 312),
    10: (238_399, 3_973, 195),
    11: (108_363, 2_211, 129),
    12: (54_182, 1_317, 90),
    13: (29_175, 828, 65),
    14: (16_671, 544, 48),
    15: (10_003, 370, 37),
    16: (6_252, 260, 29),
    17: (4_045, 188, 23),
    18: (2_697, 139, 19),
    19: (1_845, 105, 16),
    20: (1_292, 81, 13),
}

# =============================================================================
# PRÊMIOS MÉDIOS HISTÓRICOS (estimativas)
# =============================================================================
PREMIO_MEDIO_SENA = 50_000_000.00      # R$ 50 milhões (média)
PREMIO_MEDIO_QUINA = 50_000.00          # R$ 50 mil (média)
PREMIO_MEDIO_QUADRA = 1_000.00          # R$ 1 mil (média)

# =============================================================================
# CONFIGURAÇÕES DO VOLANTE MEGA-SENA
# =============================================================================
TOTAL_NUMEROS = 60
NUMEROS_SORTEADOS = 6
NUMEROS_MIN = 1
NUMEROS_MAX = 60

# Mapeamento do Volante 6x10
VOLANTE_LINHAS = 6
VOLANTE_COLUNAS = 10

# Limites para classificação Alto/Baixo
LIMITE_ALTO_BAIXO = 30  # 1-30 = Baixo, 31-60 = Alto

# =============================================================================
# CONFIGURAÇÕES DE ANÁLISE ESTATÍSTICA
# =============================================================================
JANELA_HOT = 10           # Últimos N jogos para análise "Hot"
JANELA_COLD = 50          # Janela para análise "Cold" (atraso)
CICLO_RENOVACAO = 15      # Ciclo médio de renovação (concursos)

# Pesos para cálculo do Score (Total = 1.0) - 13 REGRAS
PESO_FREQUENCIA = 0.09        # Frequência histórica
PESO_ATRASO = 0.09            # Atraso (regressão à média)
PESO_TENDENCIA = 0.08         # Tendência recente
PESO_QUADRANTE = 0.08         # Equilíbrio por quadrante
PESO_PARIDADE = 0.08          # Contribuição par/ímpar
PESO_BAIXO_MEDIO_ALTO = 0.08  # Contribuição Baixo/Médio/Alto (3 faixas)
PESO_LINHAS = 0.08            # Distribuição por linhas do volante
PESO_COLUNAS = 0.08           # Distribuição por colunas do volante
PESO_SOMA = 0.07              # Contribuição para soma ideal (150-200)
PESO_CICLO = 0.07             # Números faltantes no ciclo atual
PESO_POISSON = 0.07           # Probabilidade Poisson
PESO_FREQUENCIA_HNF = 0.07    # Faixas de Frequência H-N-F (Quente/Neutro/Frio)
PESO_SEQUENCIA = 0.06         # Padrões de sequências consecutivas

# Faixa ideal de Soma (onde ~60% dos sorteios caem)
SOMA_IDEAL_MIN = 150
SOMA_IDEAL_MAX = 200
SOMA_IDEAL_MEDIA = 175        # Soma média esperada para 6 números

# Limites para classificação Baixo/Médio/Alto (3 faixas)
LIMITE_BAIXO = 20    # 1-20 = Baixo
LIMITE_MEDIO = 40    # 21-40 = Médio, 41-60 = Alto

# =============================================================================
# CONFIGURAÇÕES DE ESTRATÉGIAS
# =============================================================================

# Estratégia A - "Sniper"
ESTRATEGIA_A_DEZENAS_PRINCIPAL = 19
ESTRATEGIA_A_CUSTO_PRINCIPAL = TABELA_CUSTOS_OFICIAL[19]  # R$ 162.792,00
ESTRATEGIA_A_SOBRA = BUDGET_TOTAL - ESTRATEGIA_A_CUSTO_PRINCIPAL  # R$ 17.208,00

# Estratégia B - "Bomber"
ESTRATEGIA_B_DEZENAS_PRINCIPAL = 18
ESTRATEGIA_B_CUSTO_PRINCIPAL = TABELA_CUSTOS_OFICIAL[18]  # R$ 111.384,00
ESTRATEGIA_B_SOBRA = BUDGET_TOTAL - ESTRATEGIA_B_CUSTO_PRINCIPAL  # R$ 68.616,00
