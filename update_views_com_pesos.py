"""
Atualiza views para usar pesos da tabela loterias.regras
========================================================
- v_score_individual: usa pesos das regras individuais
- v_concurso_analise: adiciona colunas de peso por regra de conjunto
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 ATUALIZANDO VIEWS COM PESOS DA TABELA REGRAS")
print("=" * 80)

# 1. Buscar pesos da tabela regras
print("\n1️⃣ Buscando pesos da tabela loterias.regras...")
regras = client.query("""
    SELECT codigo, peso, tipo
    FROM loterias.regras
    WHERE ativo = 1
    ORDER BY ordem
""")

print("\n   Pesos encontrados:")
for _, r in regras.iterrows():
    print(f"   {r['codigo']}: {r['peso']}% ({r['tipo']})")

# Separar pesos por tipo
pesos_individual = regras[regras['tipo'] == 'individual']
pesos_conjunto = regras[regras['tipo'] == 'conjunto']

soma_individual = pesos_individual['peso'].sum()
soma_conjunto = pesos_conjunto['peso'].sum()

print(f"\n   Soma Individual: {soma_individual}%")
print(f"   Soma Conjunto: {soma_conjunto}%")

# 2. Criar dicionário de pesos
pesos = {}
for _, r in regras.iterrows():
    pesos[r['codigo']] = float(r['peso'])

# Pesos normalizados para regras individuais (soma = 100%)
pesos_norm = {}
for _, r in pesos_individual.iterrows():
    pesos_norm[r['codigo']] = round(float(r['peso']) / soma_individual, 4)

print("\n   Pesos Individuais Normalizados (para 100%):")
for codigo, peso in pesos_norm.items():
    print(f"   {codigo}: {peso*100:.2f}%")

# =====================================================================
# 2. ATUALIZAR v_score_individual
# =====================================================================
print("\n" + "=" * 80)
print("2️⃣ Atualizando v_score_individual...")

# Criar a view usando os pesos da tabela
client.query(f"""
    CREATE OR REPLACE VIEW loterias.v_score_individual AS
    SELECT
        s.numero,

        -- Scores brutos das 6 regras individuais
        round(coalesce(s.score_frequencia, 0), 1) as r1_freq,
        round(coalesce(s.score_atraso, 0), 1) as r2_atraso,
        round(coalesce(s.score_tendencia, 0), 1) as r3_tend,
        round(coalesce(s.score_ciclo, 0), 1) as r10_ciclo,
        round(coalesce(s.score_poisson, 0), 1) as r11_poisson,
        round(coalesce(s.score_pressao_ciclo, 0), 1) as r15_pressao,

        -- Pesos das regras (da tabela regras, normalizados para 100%)
        {pesos_norm['R1']} as peso_r1,
        {pesos_norm['R2']} as peso_r2,
        {pesos_norm['R3']} as peso_r3,
        {pesos_norm['R10']} as peso_r10,
        {pesos_norm['R11']} as peso_r11,
        {pesos_norm['R15']} as peso_r15,

        -- Contribuição de cada regra (score × peso normalizado)
        round(coalesce(s.score_frequencia, 0) * {pesos_norm['R1']}, 2) as pct_r1,
        round(coalesce(s.score_atraso, 0) * {pesos_norm['R2']}, 2) as pct_r2,
        round(coalesce(s.score_tendencia, 0) * {pesos_norm['R3']}, 2) as pct_r3,
        round(coalesce(s.score_ciclo, 0) * {pesos_norm['R10']}, 2) as pct_r10,
        round(coalesce(s.score_poisson, 0) * {pesos_norm['R11']}, 2) as pct_r11,
        round(coalesce(s.score_pressao_ciclo, 0) * {pesos_norm['R15']}, 2) as pct_r15,

        -- Score Individual (soma ponderada normalizada)
        round(
            coalesce(s.score_frequencia, 0) * {pesos_norm['R1']} +
            coalesce(s.score_atraso, 0) * {pesos_norm['R2']} +
            coalesce(s.score_tendencia, 0) * {pesos_norm['R3']} +
            coalesce(s.score_ciclo, 0) * {pesos_norm['R10']} +
            coalesce(s.score_poisson, 0) * {pesos_norm['R11']} +
            coalesce(s.score_pressao_ciclo, 0) * {pesos_norm['R15']},
        2) as score_individual,

        -- Score Final Completo (todas as 15 regras) para comparação
        round(coalesce(s.score_final, 0), 2) as score_final_completo

    FROM loterias.v_scores s
    ORDER BY score_individual DESC
""")
print("   ✅ v_score_individual atualizada!")

# =====================================================================
# 3. ATUALIZAR v_concurso_analise
# =====================================================================
print("\n" + "=" * 80)
print("3️⃣ Atualizando v_concurso_analise com colunas de peso...")

# Pesos das regras de conjunto
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
        -- R12 - HNF (Hot-Neutral-Frio) - Placeholder
        -- =====================================================================
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
    GROUP BY m.concurso, m.data, m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6
    ORDER BY m.concurso DESC
""")
print("   ✅ v_concurso_analise atualizada!")

# =====================================================================
# 4. TESTAR AS VIEWS
# =====================================================================
print("\n" + "=" * 80)
print("4️⃣ Testando views atualizadas...")

print("\n📊 v_score_individual - Top 10:")
top10_ind = client.query("""
    SELECT
        numero,
        r1_freq, r2_atraso, r3_tend, r10_ciclo, r11_poisson, r15_pressao,
        score_individual
    FROM loterias.v_score_individual
    ORDER BY score_individual DESC
    LIMIT 10
""")
print(top10_ind.to_string(index=False))

print("\n📊 v_concurso_analise - Últimos 3 concursos com pesos:")
ultimos = client.query("""
    SELECT
        concurso,
        concat(toString(q1_count), '-', toString(q2_count), '-', toString(q3_count), '-', toString(q4_count)) as quadrantes,
        r4_peso,
        concat(toString(pares_count), 'P/', toString(impares_count), 'I') as paridade,
        r5_peso,
        soma,
        r9_peso,
        sequencias_consecutivas as seq,
        r13_peso
    FROM loterias.v_concurso_analise
    ORDER BY concurso DESC
    LIMIT 3
""")
print(ultimos.to_string(index=False))

print("\n" + "=" * 80)
print("✅ VIEWS ATUALIZADAS COM PESOS DA TABELA REGRAS!")
print("\n💡 Agora os pesos são lidos da tabela loterias.regras")
print("   Para alterar um peso, basta atualizar a tabela e recriar as views")
