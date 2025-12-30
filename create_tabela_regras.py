"""
Cria tabela loterias.regras
===========================
Cadastro centralizado das 15 regras de análise com:
- Código, nome, peso (%)
- Tipo (individual/conjunto)
- Descrição detalhada do funcionamento
- Fórmula de cálculo
"""

from clickhouse_client import ClickHouseClient
import pandas as pd

client = ClickHouseClient()

print("🔄 CRIANDO TABELA DE REGRAS")
print("=" * 80)

# 1. Dropar e recriar tabela
print("\n1️⃣ Criando tabela loterias.regras...")
client.query("DROP TABLE IF EXISTS loterias.regras")
client.query("""
    CREATE TABLE loterias.regras (
        codigo String,
        nome String,
        peso Float32,
        tipo String,
        descricao_curta String,
        descricao_detalhada String,
        formula String,
        janela_concursos UInt16,
        ativo UInt8,
        ordem UInt8
    ) ENGINE = MergeTree()
    ORDER BY ordem
""")
print("   ✅ Tabela criada!")

# 2. Inserir regras via DataFrame
print("\n2️⃣ Inserindo as 15 regras...")

regras = [
    # ========== REGRAS INDIVIDUAIS (48%) ==========
    {
        "codigo": "R1",
        "nome": "Frequência Histórica",
        "peso": 9.00,
        "tipo": "individual",
        "descricao_curta": "Quantas vezes o número foi sorteado no total",
        "descricao_detalhada": """Analisa a frequência absoluta de cada número em todo o histórico da Mega-Sena.

LÓGICA:
- Conta quantas vezes cada número (1-60) apareceu em todos os concursos
- Números mais frequentes historicamente tendem a manter essa tendência (Lei dos Grandes Números)
- A frequência esperada teórica é igual para todos (1/60), mas na prática há variações

SCORE:
- Normalizado pelo número com maior frequência
- Score = (frequência_do_número / frequência_máxima) × 100

EXEMPLO:
- Se o número 10 apareceu 500 vezes e o máximo é 520
- Score = (500/520) × 100 = 96.15""",
        "formula": "(frequencia / max_frequencia) × 100",
        "janela_concursos": 0,
        "ordem": 1
    },
    {
        "codigo": "R2",
        "nome": "Atraso / Regressão à Média",
        "peso": 9.00,
        "tipo": "individual",
        "descricao_curta": "Há quantos concursos o número não sai",
        "descricao_detalhada": """Mede há quantos concursos consecutivos cada número não foi sorteado.

LÓGICA:
- Baseado na Lei de Regressão à Média: números que estão "atrasados" têm maior pressão estatística para aparecer
- Quanto maior o atraso, maior o score
- Atraso 0 significa que o número saiu no último concurso

SCORE:
- Normalizado pelo maior atraso atual
- Score = min((atraso / atraso_máximo) × 100, 100)
- Limitado a 100 para evitar distorções

EXEMPLO:
- Se o número 33 não sai há 45 concursos e o atraso máximo é 60
- Score = (45/60) × 100 = 75.0""",
        "formula": "min((atraso / atraso_maximo) × 100, 100)",
        "janela_concursos": 0,
        "ordem": 2
    },
    {
        "codigo": "R3",
        "nome": "Tendência Recente",
        "peso": 7.00,
        "tipo": "individual",
        "descricao_curta": "Aparições nos últimos 48 concursos (média de ciclos)",
        "descricao_detalhada": """Analisa o comportamento recente de cada número nos últimos 48 concursos.

LÓGICA:
- 48 concursos = média histórica de duração de um ciclo completo (todos 60 números sorteados)
- Números que aparecem mais frequentemente nesta janela estão "quentes"
- Captura tendências de curto/médio prazo

JANELA: 48 concursos (ajustável com base na análise de ciclos)

SCORE:
- Normalizado pelo número com mais aparições na janela
- Score = (aparições_48 / max_aparições_48) × 100

EXEMPLO:
- Se o número 17 apareceu 8 vezes nos últimos 48 concursos e o máximo é 10
- Score = (8/10) × 100 = 80.0""",
        "formula": "(aparicoes_ultimos_48 / max_aparicoes) × 100",
        "janela_concursos": 48,
        "ordem": 3
    },
    {
        "codigo": "R10",
        "nome": "Ciclo de Renovação",
        "peso": 7.00,
        "tipo": "individual",
        "descricao_curta": "Números faltantes nos últimos 27 concursos (mínimo de ciclo)",
        "descricao_detalhada": """Identifica números que NÃO apareceram nos últimos 27 concursos.

LÓGICA:
- 27 concursos = mínimo histórico de um ciclo completo
- Números faltantes nesta janela têm alta probabilidade de aparecer em breve
- É uma regra binária: ou está faltando (100) ou não (0)

JANELA: 27 concursos (mínimo histórico de ciclos completos)

SCORE:
- Binário: 100 se faltante, 0 se já apareceu
- Score = IF(faltante_no_ciclo = 1, 100, 0)

EXEMPLO:
- Se o número 43 não apareceu nos últimos 27 concursos → Score = 100
- Se o número 10 apareceu pelo menos 1 vez → Score = 0""",
        "formula": "IF(faltante_no_ciclo = 1, 100, 0)",
        "janela_concursos": 27,
        "ordem": 4
    },
    {
        "codigo": "R11",
        "nome": "Distribuição de Poisson",
        "peso": 6.00,
        "tipo": "individual",
        "descricao_curta": "Probabilidade estatística esperada",
        "descricao_detalhada": """Aplica a distribuição de Poisson para calcular a probabilidade esperada de cada número.

LÓGICA:
- Distribuição de Poisson modela eventos raros em intervalos fixos
- λ (lambda) = taxa média de aparição = 6/60 = 0.1 por concurso
- Calcula a probabilidade de o número aparecer dado seu histórico

SCORE:
- Baseado na diferença entre frequência observada e esperada
- Números "devidos" (abaixo da expectativa) recebem scores maiores

FÓRMULA POISSON:
- P(X=k) = (λ^k × e^(-λ)) / k!
- Score normalizado pela probabilidade""",
        "formula": "Baseado em P(X=k) = (λ^k × e^(-λ)) / k!",
        "janela_concursos": 0,
        "ordem": 5
    },
    {
        "codigo": "R15",
        "nome": "Pressão do Ciclo Completo",
        "peso": 4.00,
        "tipo": "individual",
        "descricao_curta": "Pressão dos números faltantes no ciclo de 60 números",
        "descricao_detalhada": """Mede a "pressão" para aparecer dos números que ainda faltam no ciclo atual.

LÓGICA:
- Um ciclo completo = todos os 60 números sorteados pelo menos uma vez
- Histórico: mínimo 27, máximo 83, média 48 concursos para completar
- Quanto mais avançado o ciclo, maior a pressão nos números faltantes

SCORE:
- Só se aplica a números que ainda não saíram no ciclo atual
- Score = ((duração_atual - min) / (max - min)) × 100
- Score = ((duração - 27) / (83 - 27)) × 100

EXEMPLO:
- Ciclo atual com 45 concursos, número 43 ainda não saiu
- Score = ((45 - 27) / (83 - 27)) × 100 = 32.14
- Números que já saíram no ciclo atual: Score = 0""",
        "formula": "((duracao_ciclo_atual - 27) / (83 - 27)) × 100",
        "janela_concursos": 0,
        "ordem": 6
    },

    # ========== REGRAS DE CONJUNTO (52%) ==========
    {
        "codigo": "R4",
        "nome": "Equilíbrio por Quadrantes",
        "peso": 7.00,
        "tipo": "conjunto",
        "descricao_curta": "Distribuição entre Q1(1-15), Q2(16-30), Q3(31-45), Q4(46-60)",
        "descricao_detalhada": """Avalia como os 6 números do jogo se distribuem pelos 4 quadrantes.

QUADRANTES:
- Q1: números 1 a 15 (15 números)
- Q2: números 16 a 30 (15 números)
- Q3: números 31 a 45 (15 números)
- Q4: números 46 a 60 (15 números)

PADRÕES HISTÓRICOS MAIS FREQUENTES:
- 1-1-2-2: 5.62% dos concursos
- 2-1-2-1: 5.42% dos concursos
- 1-2-2-1: 5.15% dos concursos
- 1-2-1-2: 5.08% dos concursos

LÓGICA:
- Jogos com distribuição equilibrada (1-2 números por quadrante) são mais frequentes
- Evita concentração em um único quadrante

SCORE:
- Baseado na proximidade com padrões históricos mais frequentes""",
        "formula": "Proximidade com padrões históricos Q1-Q2-Q3-Q4",
        "janela_concursos": 0,
        "ordem": 7
    },
    {
        "codigo": "R5",
        "nome": "Paridade Par/Ímpar",
        "peso": 6.00,
        "tipo": "conjunto",
        "descricao_curta": "Equilíbrio entre números pares e ímpares",
        "descricao_detalhada": """Avalia a proporção de números pares e ímpares no jogo.

DISTRIBUIÇÃO HISTÓRICA:
- 3P/3I: 30.84% (MAIS FREQUENTE)
- 4P/2I: 24.20%
- 2P/4I: 24.07%
- 5P/1I: 9.48%
- 1P/5I: 8.80%
- 0P/6I: 1.32%
- 6P/0I: 1.29%

LÓGICA:
- Distribuição equilibrada (3-3 ou 4-2/2-4) é muito mais comum
- Extremos (6-0 ou 0-6) são raros (~1.3%)

SCORE:
- Máximo para 3P/3I
- Alto para 4P/2I ou 2P/4I
- Baixo para extremos""",
        "formula": "Score baseado na proximidade com 3P/3I",
        "janela_concursos": 0,
        "ordem": 8
    },
    {
        "codigo": "R6",
        "nome": "Faixas Baixo/Médio/Alto",
        "peso": 6.00,
        "tipo": "conjunto",
        "descricao_curta": "Distribuição em 3 faixas (1-20, 21-40, 41-60)",
        "descricao_detalhada": """Avalia como os números se distribuem em 3 faixas de 20 números.

FAIXAS:
- Baixo (B): 1 a 20 (20 números)
- Médio (M): 21 a 40 (20 números)
- Alto (A): 41 a 60 (20 números)

PADRÕES HISTÓRICOS MAIS FREQUENTES:
- 2-2-2: 13.85% (MAIS EQUILIBRADO)
- 1-3-2: 9.38%
- 2-1-3: 9.28%
- 3-2-1: 8.97%
- 3-1-2: 8.73%

LÓGICA:
- Distribuição 2-2-2 é a mais comum (equilibrada)
- Padrões com 1-3 números por faixa também são frequentes

SCORE:
- Máximo para 2-2-2
- Alto para distribuições equilibradas""",
        "formula": "Proximidade com padrão B-M-A histórico",
        "janela_concursos": 0,
        "ordem": 9
    },
    {
        "codigo": "R7",
        "nome": "Distribuição por Linhas",
        "peso": 7.00,
        "tipo": "conjunto",
        "descricao_curta": "Distribuição pelas 6 linhas do volante",
        "descricao_detalhada": """Avalia como os números se distribuem pelas 6 linhas do volante físico.

LINHAS DO VOLANTE:
- L1: 01-02-03-04-05-06-07-08-09-10
- L2: 11-12-13-14-15-16-17-18-19-20
- L3: 21-22-23-24-25-26-27-28-29-30
- L4: 31-32-33-34-35-36-37-38-39-40
- L5: 41-42-43-44-45-46-47-48-49-50
- L6: 51-52-53-54-55-56-57-58-59-60

PADRÃO MAIS FREQUENTE:
- 1-1-1-1-1-1: 2.03% (1 número por linha)

MÉDIA HISTÓRICA POR LINHA:
- L1: 1.01 | L2: 0.99 | L3: 0.97 | L4: 1.03 | L5: 1.01 | L6: 1.00

LÓGICA:
- Distribuição equilibrada (1 número por linha) é frequente
- Evita concentração em poucas linhas""",
        "formula": "Proximidade com média histórica por linha",
        "janela_concursos": 0,
        "ordem": 10
    },
    {
        "codigo": "R8",
        "nome": "Distribuição por Colunas",
        "peso": 7.00,
        "tipo": "conjunto",
        "descricao_curta": "Distribuição pelas 10 colunas (terminações 0-9)",
        "descricao_detalhada": """Avalia como os números se distribuem pelas terminações (0-9).

COLUNAS (Terminações):
- C0: 10, 20, 30, 40, 50, 60
- C1: 01, 11, 21, 31, 41, 51
- C2: 02, 12, 22, 32, 42, 52
- C3: 03, 13, 23, 33, 43, 53
- C4: 04, 14, 24, 34, 44, 54
- C5: 05, 15, 25, 35, 45, 55
- C6: 06, 16, 26, 36, 46, 56
- C7: 07, 17, 27, 37, 47, 57
- C8: 08, 18, 28, 38, 48, 58
- C9: 09, 19, 29, 39, 49, 59

MÉDIA HISTÓRICA:
- Todas as colunas têm média próxima de 0.6 (6 números / 10 colunas)

LÓGICA:
- Evitar repetição excessiva de terminações
- Distribuir por diferentes terminações""",
        "formula": "Proximidade com média histórica por coluna",
        "janela_concursos": 0,
        "ordem": 11
    },
    {
        "codigo": "R9",
        "nome": "Soma Ideal",
        "peso": 7.00,
        "tipo": "conjunto",
        "descricao_curta": "Soma dos 6 números entre 150-200",
        "descricao_detalhada": """Avalia se a soma dos 6 números está na faixa ideal.

ESTATÍSTICAS HISTÓRICAS:
- Mínimo: 66
- Máximo: 331
- Média: 183.2
- Mediana: 184
- Desvio Padrão: 40

FAIXA IDEAL: 150 a 200 (44.52% dos concursos)

DISTRIBUIÇÃO:
- < 100: 1.73%
- 100-124: 5.59%
- 125-149: 14.01%
- 150-174: 19.87%
- 175-199: 23.53%
- 200-224: 20.01%
- 225-249: 10.53%
- >= 250: 4.74%

LÓGICA:
- Somas entre 150-200 representam quase metade dos sorteios
- Evitar extremos (muito baixo ou muito alto)

SCORE:
- Máximo se soma está entre 150-200
- Decresce conforme se afasta da faixa ideal""",
        "formula": "IF(soma BETWEEN 150 AND 200, 100, penalidade_proporcional)",
        "janela_concursos": 0,
        "ordem": 12
    },
    {
        "codigo": "R12",
        "nome": "Classificação Hot-Neutral-Frio",
        "peso": 6.00,
        "tipo": "conjunto",
        "descricao_curta": "Classificação Quente/Neutro/Frio baseada na frequência",
        "descricao_detalhada": """Classifica cada número em 3 categorias baseadas na frequência recente.

CLASSIFICAÇÃO:
- HOT (Quente): Números com frequência acima da média + 1 desvio padrão
- NEUTRAL (Neutro): Números dentro da faixa média ± 1 desvio padrão
- FRIO (Cold): Números com frequência abaixo da média - 1 desvio padrão

LÓGICA:
- Jogos devem ter um mix de números quentes, neutros e frios
- Não concentrar apenas em números "quentes" ou "frios"

DISTRIBUIÇÃO IDEAL:
- 2 números Hot
- 2-3 números Neutral
- 1-2 números Frio

SCORE:
- Baseado na diversidade de classificações no jogo""",
        "formula": "Mix equilibrado de H-N-F no jogo",
        "janela_concursos": 48,
        "ordem": 13
    },
    {
        "codigo": "R13",
        "nome": "Análise de Sequências Consecutivas",
        "peso": 6.00,
        "tipo": "conjunto",
        "descricao_curta": "Padrões de números consecutivos",
        "descricao_detalhada": """Analisa a presença de números consecutivos no jogo.

DISTRIBUIÇÃO HISTÓRICA:
- 0 consecutivos: 57.92% (MAIS COMUM)
- 1 par consecutivo: 34.97%
- 2 pares consecutivos: 6.84%
- 3 pares consecutivos: 0.24%
- 4 pares consecutivos: 0.03%

EXEMPLOS:
- [5, 12, 23, 34, 45, 56] → 0 consecutivos
- [5, 6, 23, 34, 45, 56] → 1 consecutivo (5-6)
- [5, 6, 23, 24, 45, 56] → 2 consecutivos (5-6 e 23-24)

LÓGICA:
- Maioria dos sorteios não tem números consecutivos
- Ter 1 par consecutivo ainda é comum (~35%)
- 2+ pares é raro (~7%)

SCORE:
- Máximo para 0 consecutivos
- Alto para 1 consecutivo
- Baixo para 2+ consecutivos""",
        "formula": "Score inversamente proporcional à quantidade de consecutivos",
        "janela_concursos": 0,
        "ordem": 14
    },
    {
        "codigo": "R14",
        "nome": "Frequência por Quadrante",
        "peso": 6.00,
        "tipo": "conjunto",
        "descricao_curta": "Combina frequência média do quadrante com padrão histórico",
        "descricao_detalhada": """Avalia a frequência média dos números dentro de cada quadrante.

LÓGICA:
- Cada quadrante (Q1-Q4) tem números com diferentes frequências
- Combina a frequência individual com o padrão de distribuição por quadrante
- Busca selecionar os números mais frequentes de cada quadrante

CÁLCULO:
1. Para cada quadrante, identifica os números mais frequentes
2. Calcula a frequência média dos números selecionados no quadrante
3. Combina com o padrão histórico de distribuição Q1-Q2-Q3-Q4

SCORE:
- Baseado na frequência relativa do número dentro do seu quadrante""",
        "formula": "(freq_no_quadrante / max_freq_quadrante) × peso_quadrante",
        "janela_concursos": 0,
        "ordem": 15
    }
]

# Criar DataFrame
df_regras = pd.DataFrame(regras)
df_regras['ativo'] = 1

# Inserir via cliente
client.insert_dataframe('loterias.regras', df_regras)
for r in regras:
    print(f"   ✅ {r['codigo']} - {r['nome']}")

print("\n" + "=" * 80)
print("📊 VERIFICANDO DADOS INSERIDOS")
print("=" * 80)

# Verificar inserção
resultado = client.query("""
    SELECT
        codigo,
        nome,
        peso,
        tipo,
        descricao_curta,
        janela_concursos as janela
    FROM loterias.regras
    ORDER BY ordem
""")

print("\n" + resultado.to_string(index=False))

# Mostrar totais por tipo
totais = client.query("""
    SELECT
        tipo,
        count() as qtd_regras,
        sum(peso) as peso_total
    FROM loterias.regras
    WHERE ativo = 1
    GROUP BY tipo
""")

print("\n" + "-" * 80)
print("RESUMO POR TIPO:")
print(totais.to_string(index=False))

total_geral = client.query("SELECT sum(peso) as total FROM loterias.regras WHERE ativo = 1")
print(f"\n📊 PESO TOTAL: {total_geral['total'].iloc[0]}%")

print("\n✅ TABELA DE REGRAS CRIADA COM SUCESSO!")
