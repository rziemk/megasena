"""
Implementa R12 - H-N-F (Hot-Neutral-Frio) na view v_concurso_analise
====================================================================
Classificação baseada em aparições nos últimos 48 concursos:
- HOT: >= 6 aparições (>= 120% da média esperada de 4.8)
- NEUTRAL: 4-5 aparições (80-120% da média)
- COLD: 0-3 aparições (< 80% da média)
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔥 IMPLEMENTANDO R12 - H-N-F (Hot-Neutral-Frio)")
print("=" * 80)

# 1. Primeiro, criar uma view auxiliar que classifica cada número como H/N/F
print("\n1️⃣ Criando view auxiliar v_classificacao_hnf...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_classificacao_hnf AS
    SELECT
        numero,
        aparicoes_ultimos_48,
        CASE
            WHEN aparicoes_ultimos_48 >= 6 THEN 'H'
            WHEN aparicoes_ultimos_48 >= 4 THEN 'N'
            ELSE 'F'
        END as classificacao,
        CASE
            WHEN aparicoes_ultimos_48 >= 6 THEN 1
            ELSE 0
        END as is_hot,
        CASE
            WHEN aparicoes_ultimos_48 >= 4 AND aparicoes_ultimos_48 < 6 THEN 1
            ELSE 0
        END as is_neutral,
        CASE
            WHEN aparicoes_ultimos_48 < 4 THEN 1
            ELSE 0
        END as is_cold
    FROM loterias.v_tendencia
""")
print("   ✅ v_classificacao_hnf criada!")

# Verificar classificação
print("\n   Classificação atual dos números:")
classificacao = client.query("""
    SELECT classificacao, count() as qtd
    FROM loterias.v_classificacao_hnf
    GROUP BY classificacao
    ORDER BY classificacao
""")
print(f"   {classificacao.to_string(index=False)}")

# 2. Buscar pesos da tabela regras
print("\n2️⃣ Buscando pesos da tabela loterias.regras...")
regras = client.query("""
    SELECT codigo, peso, tipo
    FROM loterias.regras
    WHERE ativo = 1
    ORDER BY ordem
""")

pesos = {}
for _, r in regras.iterrows():
    pesos[r['codigo']] = float(r['peso'])

print(f"   R12 peso: {pesos['R12']}%")

# 3. Atualizar v_concurso_analise com R12 completo
print("\n3️⃣ Atualizando v_concurso_analise com R12...")

# Usando JOINs diretos para cada bola (ClickHouse não suporta subqueries correlacionadas com ARRAY JOIN)
client.query(f"""
    CREATE OR REPLACE VIEW loterias.v_concurso_analise AS
    SELECT
        m.concurso,
        m.data,
        m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6,

        -- =====================================================================
        -- R4 - QUADRANTES (Q1: 1-15, Q2: 16-30, Q3: 31-45, Q4: 46-60)
        -- =====================================================================
        countIf(n IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)) as q1_count,
        countIf(n IN (16,17,18,19,20,21,22,23,24,25,26,27,28,29,30)) as q2_count,
        countIf(n IN (31,32,33,34,35,36,37,38,39,40,41,42,43,44,45)) as q3_count,
        countIf(n IN (46,47,48,49,50,51,52,53,54,55,56,57,58,59,60)) as q4_count,
        round(countIf(n IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)) / 6.0 * 100, 1) as q1_pct,
        round(countIf(n IN (16,17,18,19,20,21,22,23,24,25,26,27,28,29,30)) / 6.0 * 100, 1) as q2_pct,
        round(countIf(n IN (31,32,33,34,35,36,37,38,39,40,41,42,43,44,45)) / 6.0 * 100, 1) as q3_pct,
        round(countIf(n IN (46,47,48,49,50,51,52,53,54,55,56,57,58,59,60)) / 6.0 * 100, 1) as q4_pct,
        {pesos['R4']} as r4_peso,

        -- =====================================================================
        -- R5 - PARIDADE (Pares vs Ímpares)
        -- =====================================================================
        countIf(n % 2 = 0) as pares_count,
        countIf(n % 2 = 1) as impares_count,
        round(countIf(n % 2 = 0) / 6.0 * 100, 1) as pares_pct,
        round(countIf(n % 2 = 1) / 6.0 * 100, 1) as impares_pct,
        {pesos['R5']} as r5_peso,

        -- =====================================================================
        -- R6 - FAIXAS B/M/A (Baixo: 1-20, Médio: 21-40, Alto: 41-60)
        -- =====================================================================
        countIf(n >= 1 AND n <= 20) as baixo_count,
        countIf(n >= 21 AND n <= 40) as medio_count,
        countIf(n >= 41 AND n <= 60) as alto_count,
        round(countIf(n >= 1 AND n <= 20) / 6.0 * 100, 1) as baixo_pct,
        round(countIf(n >= 21 AND n <= 40) / 6.0 * 100, 1) as medio_pct,
        round(countIf(n >= 41 AND n <= 60) / 6.0 * 100, 1) as alto_pct,
        {pesos['R6']} as r6_peso,

        -- =====================================================================
        -- R7 - LINHAS (L1: 1-10, L2: 11-20, L3: 21-30, L4: 31-40, L5: 41-50, L6: 51-60)
        -- =====================================================================
        countIf(n >= 1 AND n <= 10) as l1_count,
        countIf(n >= 11 AND n <= 20) as l2_count,
        countIf(n >= 21 AND n <= 30) as l3_count,
        countIf(n >= 31 AND n <= 40) as l4_count,
        countIf(n >= 41 AND n <= 50) as l5_count,
        countIf(n >= 51 AND n <= 60) as l6_count,
        round(countIf(n >= 1 AND n <= 10) / 6.0 * 100, 1) as l1_pct,
        round(countIf(n >= 11 AND n <= 20) / 6.0 * 100, 1) as l2_pct,
        round(countIf(n >= 21 AND n <= 30) / 6.0 * 100, 1) as l3_pct,
        round(countIf(n >= 31 AND n <= 40) / 6.0 * 100, 1) as l4_pct,
        round(countIf(n >= 41 AND n <= 50) / 6.0 * 100, 1) as l5_pct,
        round(countIf(n >= 51 AND n <= 60) / 6.0 * 100, 1) as l6_pct,
        {pesos['R7']} as r7_peso,

        -- =====================================================================
        -- R8 - COLUNAS (Terminação 0-9)
        -- =====================================================================
        countIf(n % 10 = 0) as c0_count,
        countIf(n % 10 = 1) as c1_count,
        countIf(n % 10 = 2) as c2_count,
        countIf(n % 10 = 3) as c3_count,
        countIf(n % 10 = 4) as c4_count,
        countIf(n % 10 = 5) as c5_count,
        countIf(n % 10 = 6) as c6_count,
        countIf(n % 10 = 7) as c7_count,
        countIf(n % 10 = 8) as c8_count,
        countIf(n % 10 = 9) as c9_count,
        round(countIf(n % 10 = 0) / 6.0 * 100, 1) as c0_pct,
        round(countIf(n % 10 = 1) / 6.0 * 100, 1) as c1_pct,
        round(countIf(n % 10 = 2) / 6.0 * 100, 1) as c2_pct,
        round(countIf(n % 10 = 3) / 6.0 * 100, 1) as c3_pct,
        round(countIf(n % 10 = 4) / 6.0 * 100, 1) as c4_pct,
        round(countIf(n % 10 = 5) / 6.0 * 100, 1) as c5_pct,
        round(countIf(n % 10 = 6) / 6.0 * 100, 1) as c6_pct,
        round(countIf(n % 10 = 7) / 6.0 * 100, 1) as c7_pct,
        round(countIf(n % 10 = 8) / 6.0 * 100, 1) as c8_pct,
        round(countIf(n % 10 = 9) / 6.0 * 100, 1) as c9_pct,
        {pesos['R8']} as r8_peso,

        -- =====================================================================
        -- R9 - SOMA
        -- =====================================================================
        (m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) as soma,
        if((m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) BETWEEN 150 AND 200, 'IDEAL', 'FORA') as soma_faixa,
        {pesos['R9']} as r9_peso,

        -- =====================================================================
        -- R12 - HNF (Hot-Neutral-Frio) - IMPLEMENTADO!
        -- Baseado em aparições nos últimos 48 concursos:
        -- HOT: >= 6 aparições | NEUTRAL: 4-5 | COLD: 0-3
        -- Usando JOINs para cada bola
        -- =====================================================================
        (h1.is_hot + h2.is_hot + h3.is_hot + h4.is_hot + h5.is_hot + h6.is_hot) as hot_count,
        (h1.is_neutral + h2.is_neutral + h3.is_neutral + h4.is_neutral + h5.is_neutral + h6.is_neutral) as neutral_count,
        (h1.is_cold + h2.is_cold + h3.is_cold + h4.is_cold + h5.is_cold + h6.is_cold) as cold_count,
        {pesos['R12']} as r12_peso,

        -- =====================================================================
        -- R13 - SEQUÊNCIAS CONSECUTIVAS
        -- =====================================================================
        (
            if(m.bola2 = m.bola1 + 1, 1, 0) +
            if(m.bola3 = m.bola2 + 1, 1, 0) +
            if(m.bola4 = m.bola3 + 1, 1, 0) +
            if(m.bola5 = m.bola4 + 1, 1, 0) +
            if(m.bola6 = m.bola5 + 1, 1, 0)
        ) as sequencias_consecutivas,
        {pesos['R13']} as r13_peso,

        -- =====================================================================
        -- R14 - Frequência por Quadrante - Placeholder
        -- =====================================================================
        {pesos['R14']} as r14_peso,

        -- =====================================================================
        -- MÉDIA DOS NÚMEROS
        -- =====================================================================
        round((m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) / 6.0, 1) as media_numeros

    FROM loterias.megasena m
    ARRAY JOIN [m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6] AS n
    -- JOINs para R12 H-N-F
    LEFT JOIN loterias.v_classificacao_hnf h1 ON h1.numero = m.bola1
    LEFT JOIN loterias.v_classificacao_hnf h2 ON h2.numero = m.bola2
    LEFT JOIN loterias.v_classificacao_hnf h3 ON h3.numero = m.bola3
    LEFT JOIN loterias.v_classificacao_hnf h4 ON h4.numero = m.bola4
    LEFT JOIN loterias.v_classificacao_hnf h5 ON h5.numero = m.bola5
    LEFT JOIN loterias.v_classificacao_hnf h6 ON h6.numero = m.bola6
    GROUP BY m.concurso, m.data, m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6,
             h1.is_hot, h2.is_hot, h3.is_hot, h4.is_hot, h5.is_hot, h6.is_hot,
             h1.is_neutral, h2.is_neutral, h3.is_neutral, h4.is_neutral, h5.is_neutral, h6.is_neutral,
             h1.is_cold, h2.is_cold, h3.is_cold, h4.is_cold, h5.is_cold, h6.is_cold
    ORDER BY m.concurso DESC
""")
print("   ✅ v_concurso_analise atualizada com R12!")

# 4. Testar a view
print("\n4️⃣ Testando view - Últimos 5 concursos com H-N-F:")
ultimos = client.query("""
    SELECT
        concurso,
        bola1, bola2, bola3, bola4, bola5, bola6,
        hot_count as H,
        neutral_count as N,
        cold_count as F,
        concat(toString(hot_count), 'H-', toString(neutral_count), 'N-', toString(cold_count), 'F') as hnf_pattern
    FROM loterias.v_concurso_analise
    ORDER BY concurso DESC
    LIMIT 5
""")
print("\n" + ultimos.to_string(index=False))

# 5. Estatísticas H-N-F
print("\n5️⃣ Distribuição H-N-F histórica:")
stats_hnf = client.query("""
    SELECT
        concat(toString(hot_count), 'H-', toString(neutral_count), 'N-', toString(cold_count), 'F') as pattern,
        count() as ocorrencias,
        round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as percentual
    FROM loterias.v_concurso_analise
    GROUP BY hot_count, neutral_count, cold_count
    ORDER BY ocorrencias DESC
    LIMIT 15
""")
print("\n" + stats_hnf.to_string(index=False))

print("\n" + "=" * 80)
print("✅ R12 - H-N-F IMPLEMENTADO COM SUCESSO!")
print("\n💡 Classificação:")
print("   🔥 HOT (H): >= 6 aparições nos últimos 48 concursos")
print("   ⚖️ NEUTRAL (N): 4-5 aparições")
print("   ❄️ COLD (F): 0-3 aparições")
print("\n📊 Ideal para geração: 2-3H, 2-3N, 0-2F")
