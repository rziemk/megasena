"""
Backtesting das Regras de Conjunto
===================================
Analisa o histórico de concursos para identificar padrões mais frequentes
"""

from clickhouse_client import ClickHouseClient
import pandas as pd

client = ClickHouseClient()

print("📊 BACKTESTING DAS REGRAS DE CONJUNTO")
print("=" * 100)

# Total de concursos
total = client.query("SELECT count() as total FROM loterias.v_concurso_analise")['total'].iloc[0]
print(f"\n📈 Total de concursos analisados: {total}\n")

# =============================================================================
# R4 - QUADRANTES
# =============================================================================
print("=" * 100)
print("🔲 R4 - DISTRIBUIÇÃO POR QUADRANTES")
print("=" * 100)

quadrantes = client.query("""
    SELECT
        concat(toString(q1_count), '-', toString(q2_count), '-', toString(q3_count), '-', toString(q4_count)) as padrao,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY padrao
    ORDER BY frequencia DESC
    LIMIT 15
""")
print("\nTop 15 padrões de quadrantes (Q1-Q2-Q3-Q4):")
print(quadrantes.to_string(index=False))

# =============================================================================
# R5 - PARIDADE
# =============================================================================
print("\n" + "=" * 100)
print("⚖️ R5 - PARIDADE (Pares/Ímpares)")
print("=" * 100)

paridade = client.query("""
    SELECT
        concat(toString(pares_count), 'P/', toString(impares_count), 'I') as padrao,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY padrao
    ORDER BY frequencia DESC
""")
print("\nDistribuição de paridade:")
print(paridade.to_string(index=False))

# =============================================================================
# R6 - FAIXAS B/M/A
# =============================================================================
print("\n" + "=" * 100)
print("📶 R6 - FAIXAS BAIXO/MÉDIO/ALTO")
print("=" * 100)

bma = client.query("""
    SELECT
        concat(toString(baixo_count), '-', toString(medio_count), '-', toString(alto_count)) as padrao,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY padrao
    ORDER BY frequencia DESC
    LIMIT 15
""")
print("\nTop 15 padrões B-M-A:")
print(bma.to_string(index=False))

# =============================================================================
# R7 - LINHAS
# =============================================================================
print("\n" + "=" * 100)
print("➡️ R7 - DISTRIBUIÇÃO POR LINHAS")
print("=" * 100)

linhas = client.query("""
    SELECT
        concat(toString(l1_count), '-', toString(l2_count), '-', toString(l3_count), '-',
               toString(l4_count), '-', toString(l5_count), '-', toString(l6_count)) as padrao,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY padrao
    ORDER BY frequencia DESC
    LIMIT 15
""")
print("\nTop 15 padrões de linhas (L1-L2-L3-L4-L5-L6):")
print(linhas.to_string(index=False))

# Média por linha
media_linhas = client.query("""
    SELECT
        round(avg(l1_count), 2) as L1,
        round(avg(l2_count), 2) as L2,
        round(avg(l3_count), 2) as L3,
        round(avg(l4_count), 2) as L4,
        round(avg(l5_count), 2) as L5,
        round(avg(l6_count), 2) as L6
    FROM loterias.v_concurso_analise
""")
print("\nMédia histórica por linha:")
print(media_linhas.to_string(index=False))

# =============================================================================
# R8 - COLUNAS (Terminações)
# =============================================================================
print("\n" + "=" * 100)
print("⬇️ R8 - DISTRIBUIÇÃO POR COLUNAS (Terminações)")
print("=" * 100)

media_colunas = client.query("""
    SELECT
        round(avg(c0_count), 2) as C0,
        round(avg(c1_count), 2) as C1,
        round(avg(c2_count), 2) as C2,
        round(avg(c3_count), 2) as C3,
        round(avg(c4_count), 2) as C4,
        round(avg(c5_count), 2) as C5,
        round(avg(c6_count), 2) as C6,
        round(avg(c7_count), 2) as C7,
        round(avg(c8_count), 2) as C8,
        round(avg(c9_count), 2) as C9
    FROM loterias.v_concurso_analise
""")
print("\nMédia histórica por coluna (terminação):")
print(media_colunas.to_string(index=False))

# =============================================================================
# R9 - SOMA
# =============================================================================
print("\n" + "=" * 100)
print("➕ R9 - SOMA DOS NÚMEROS")
print("=" * 100)

soma_stats = client.query("""
    SELECT
        min(soma) as minima,
        max(soma) as maxima,
        round(avg(soma), 1) as media,
        round(median(soma), 1) as mediana,
        round(stddevPop(soma), 1) as desvio_padrao
    FROM loterias.v_concurso_analise
""")
print("\nEstatísticas da soma:")
print(soma_stats.to_string(index=False))

soma_faixas = client.query("""
    SELECT
        soma_faixa,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY soma_faixa
    ORDER BY frequencia DESC
""")
print("\nSoma na faixa ideal (150-200):")
print(soma_faixas.to_string(index=False))

# Distribuição da soma em faixas
soma_distribuicao = client.query("""
    SELECT
        multiIf(
            soma < 100, '< 100',
            soma < 125, '100-124',
            soma < 150, '125-149',
            soma < 175, '150-174',
            soma < 200, '175-199',
            soma < 225, '200-224',
            soma < 250, '225-249',
            '>= 250'
        ) as faixa_soma,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY faixa_soma
    ORDER BY faixa_soma
""")
print("\nDistribuição da soma por faixas:")
print(soma_distribuicao.to_string(index=False))

# =============================================================================
# R13 - SEQUÊNCIAS CONSECUTIVAS
# =============================================================================
print("\n" + "=" * 100)
print("🔢 R13 - SEQUÊNCIAS CONSECUTIVAS")
print("=" * 100)

sequencias = client.query("""
    SELECT
        sequencias_consecutivas as qtd_consecutivos,
        count() as frequencia,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY qtd_consecutivos
    ORDER BY qtd_consecutivos
""")
print("\nQuantidade de números consecutivos por sorteio:")
print(sequencias.to_string(index=False))

# =============================================================================
# RESUMO - PADRÕES MAIS FREQUENTES
# =============================================================================
print("\n" + "=" * 100)
print("🎯 RESUMO - PADRÕES MAIS FREQUENTES (TOP 1 de cada regra)")
print("=" * 100)

print(f"""
📊 Baseado em {total} concursos históricos:

🔲 R4 - Quadrantes:      {quadrantes.iloc[0]['padrao']} ({quadrantes.iloc[0]['percentual']}%)
⚖️ R5 - Paridade:        {paridade.iloc[0]['padrao']} ({paridade.iloc[0]['percentual']}%)
📶 R6 - Faixas B/M/A:    {bma.iloc[0]['padrao']} ({bma.iloc[0]['percentual']}%)
➡️ R7 - Linhas:          {linhas.iloc[0]['padrao']} ({linhas.iloc[0]['percentual']}%)
➕ R9 - Soma:            150-200 ({soma_faixas[soma_faixas['soma_faixa']=='IDEAL']['percentual'].values[0]}% na faixa ideal)
🔢 R13 - Consecutivos:   {sequencias.iloc[0]['qtd_consecutivos']} ({sequencias.iloc[0]['percentual']}%)
""")

# =============================================================================
# ANÁLISE DO ÚLTIMO JOGO SUGERIDO
# =============================================================================
print("=" * 100)
print("🎰 ANÁLISE DO JOGO SUGERIDO ATUAL (Top 6)")
print("=" * 100)

# Pegar top 6 números
top6 = client.query("""
    SELECT numero
    FROM loterias.v_scores
    ORDER BY score_final DESC
    LIMIT 6
""")['numero'].tolist()

top6_sorted = sorted([int(n) for n in top6])
print(f"\nNúmeros sugeridos: {top6_sorted}")

# Analisar o jogo sugerido
def analisar_jogo(numeros):
    n = numeros
    analise = {
        'q1': sum(1 for x in n if 1 <= x <= 15),
        'q2': sum(1 for x in n if 16 <= x <= 30),
        'q3': sum(1 for x in n if 31 <= x <= 45),
        'q4': sum(1 for x in n if 46 <= x <= 60),
        'pares': sum(1 for x in n if x % 2 == 0),
        'impares': sum(1 for x in n if x % 2 == 1),
        'baixo': sum(1 for x in n if 1 <= x <= 20),
        'medio': sum(1 for x in n if 21 <= x <= 40),
        'alto': sum(1 for x in n if 41 <= x <= 60),
        'soma': sum(n),
    }

    # Linhas
    for i in range(1, 7):
        inicio = (i-1) * 10 + 1
        fim = i * 10
        analise[f'l{i}'] = sum(1 for x in n if inicio <= x <= fim)

    # Colunas (terminações)
    for i in range(10):
        analise[f'c{i}'] = sum(1 for x in n if x % 10 == i)

    # Consecutivos
    n_sorted = sorted(n)
    consecutivos = sum(1 for i in range(len(n_sorted)-1) if n_sorted[i+1] == n_sorted[i] + 1)
    analise['consecutivos'] = consecutivos

    return analise

jogo = analisar_jogo(top6_sorted)

print(f"""
🔲 R4 - Quadrantes:      {jogo['q1']}-{jogo['q2']}-{jogo['q3']}-{jogo['q4']}
   Mais frequente:       {quadrantes.iloc[0]['padrao']}
   {'✅ MATCH!' if f"{jogo['q1']}-{jogo['q2']}-{jogo['q3']}-{jogo['q4']}" == quadrantes.iloc[0]['padrao'] else '⚠️ Diferente do padrão mais comum'}

⚖️ R5 - Paridade:        {jogo['pares']}P/{jogo['impares']}I
   Mais frequente:       {paridade.iloc[0]['padrao']}
   {'✅ MATCH!' if f"{jogo['pares']}P/{jogo['impares']}I" == paridade.iloc[0]['padrao'] else '⚠️ Diferente do padrão mais comum'}

📶 R6 - Faixas B/M/A:    {jogo['baixo']}-{jogo['medio']}-{jogo['alto']}
   Mais frequente:       {bma.iloc[0]['padrao']}
   {'✅ MATCH!' if f"{jogo['baixo']}-{jogo['medio']}-{jogo['alto']}" == bma.iloc[0]['padrao'] else '⚠️ Diferente do padrão mais comum'}

➡️ R7 - Linhas:          {jogo['l1']}-{jogo['l2']}-{jogo['l3']}-{jogo['l4']}-{jogo['l5']}-{jogo['l6']}
   Mais frequente:       {linhas.iloc[0]['padrao']}

➕ R9 - Soma:            {jogo['soma']}
   Faixa ideal:          150-200
   {'✅ NA FAIXA IDEAL!' if 150 <= jogo['soma'] <= 200 else '⚠️ FORA da faixa ideal'}

🔢 R13 - Consecutivos:   {jogo['consecutivos']}
   Mais frequente:       {sequencias.iloc[0]['qtd_consecutivos']}
   {'✅ MATCH!' if jogo['consecutivos'] == sequencias.iloc[0]['qtd_consecutivos'] else '⚠️ Diferente do padrão mais comum'}
""")

print("=" * 100)
print("✅ BACKTESTING COMPLETO!")
