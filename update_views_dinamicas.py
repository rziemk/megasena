"""
Atualiza views para ler pesos DINAMICAMENTE da tabela loterias.regras
====================================================================
As views usam JOIN com a tabela regras para sempre refletir os pesos atuais.
Ao alterar um peso na tabela, a view automaticamente usa o novo valor.
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 ATUALIZANDO VIEWS COM PESOS DINÂMICOS")
print("=" * 80)

# =====================================================================
# 1. ATUALIZAR v_concurso_analise - COM JOIN NA TABELA REGRAS
# =====================================================================
print("\n1️⃣ Atualizando v_concurso_analise com pesos dinâmicos...")

client.query("""
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
        (SELECT peso FROM loterias.regras WHERE codigo = 'R4') as r4_peso,

        -- =====================================================================
        -- R5 - PARIDADE (Pares vs Ímpares)
        -- =====================================================================
        countIf(n % 2 = 0) as pares_count,
        countIf(n % 2 = 1) as impares_count,
        round(countIf(n % 2 = 0) / 6.0 * 100, 1) as pares_pct,
        round(countIf(n % 2 = 1) / 6.0 * 100, 1) as impares_pct,
        (SELECT peso FROM loterias.regras WHERE codigo = 'R5') as r5_peso,

        -- =====================================================================
        -- R6 - FAIXAS B/M/A (Baixo: 1-20, Médio: 21-40, Alto: 41-60)
        -- =====================================================================
        countIf(n >= 1 AND n <= 20) as baixo_count,
        countIf(n >= 21 AND n <= 40) as medio_count,
        countIf(n >= 41 AND n <= 60) as alto_count,
        round(countIf(n >= 1 AND n <= 20) / 6.0 * 100, 1) as baixo_pct,
        round(countIf(n >= 21 AND n <= 40) / 6.0 * 100, 1) as medio_pct,
        round(countIf(n >= 41 AND n <= 60) / 6.0 * 100, 1) as alto_pct,
        (SELECT peso FROM loterias.regras WHERE codigo = 'R6') as r6_peso,

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
        (SELECT peso FROM loterias.regras WHERE codigo = 'R7') as r7_peso,

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
        (SELECT peso FROM loterias.regras WHERE codigo = 'R8') as r8_peso,

        -- =====================================================================
        -- R9 - SOMA
        -- =====================================================================
        (m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) as soma,
        if((m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) BETWEEN 150 AND 200, 'IDEAL', 'FORA') as soma_faixa,
        (SELECT peso FROM loterias.regras WHERE codigo = 'R9') as r9_peso,

        -- =====================================================================
        -- R12 - HNF (Hot-Neutral-Frio)
        -- =====================================================================
        (SELECT peso FROM loterias.regras WHERE codigo = 'R12') as r12_peso,

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
        (SELECT peso FROM loterias.regras WHERE codigo = 'R13') as r13_peso,

        -- =====================================================================
        -- R14 - Frequência por Quadrante
        -- =====================================================================
        (SELECT peso FROM loterias.regras WHERE codigo = 'R14') as r14_peso,

        -- =====================================================================
        -- MÉDIA DOS NÚMEROS
        -- =====================================================================
        round((m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) / 6.0, 1) as media_numeros

    FROM loterias.megasena m
    ARRAY JOIN [m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6] AS n
    GROUP BY m.concurso, m.data, m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6
    ORDER BY m.concurso DESC
""")
print("   ✅ v_concurso_analise atualizada com pesos dinâmicos!")

# =====================================================================
# 2. ATUALIZAR v_score_individual - COM SUBQUERIES NA TABELA REGRAS
# =====================================================================
print("\n2️⃣ Atualizando v_score_individual com pesos dinâmicos...")

client.query("""
    CREATE OR REPLACE VIEW loterias.v_score_individual AS
    WITH
        -- Pesos das regras individuais
        peso_r1 AS (SELECT peso FROM loterias.regras WHERE codigo = 'R1'),
        peso_r2 AS (SELECT peso FROM loterias.regras WHERE codigo = 'R2'),
        peso_r3 AS (SELECT peso FROM loterias.regras WHERE codigo = 'R3'),
        peso_r10 AS (SELECT peso FROM loterias.regras WHERE codigo = 'R10'),
        peso_r11 AS (SELECT peso FROM loterias.regras WHERE codigo = 'R11'),
        peso_r15 AS (SELECT peso FROM loterias.regras WHERE codigo = 'R15'),
        -- Soma dos pesos individuais para normalização
        soma_pesos AS (SELECT sum(peso) FROM loterias.regras WHERE tipo = 'individual' AND ativo = 1)
    SELECT
        s.numero,

        -- Scores brutos das 6 regras individuais
        round(coalesce(s.score_frequencia, 0), 1) as r1_freq,
        round(coalesce(s.score_atraso, 0), 1) as r2_atraso,
        round(coalesce(s.score_tendencia, 0), 1) as r3_tend,
        round(coalesce(s.score_ciclo, 0), 1) as r10_ciclo,
        round(coalesce(s.score_poisson, 0), 1) as r11_poisson,
        round(coalesce(s.score_pressao_ciclo, 0), 1) as r15_pressao,

        -- Pesos das regras (da tabela regras)
        (SELECT * FROM peso_r1) as peso_r1,
        (SELECT * FROM peso_r2) as peso_r2,
        (SELECT * FROM peso_r3) as peso_r3,
        (SELECT * FROM peso_r10) as peso_r10,
        (SELECT * FROM peso_r11) as peso_r11,
        (SELECT * FROM peso_r15) as peso_r15,

        -- Pesos normalizados (soma = 100%)
        round((SELECT * FROM peso_r1) / (SELECT * FROM soma_pesos), 4) as peso_norm_r1,
        round((SELECT * FROM peso_r2) / (SELECT * FROM soma_pesos), 4) as peso_norm_r2,
        round((SELECT * FROM peso_r3) / (SELECT * FROM soma_pesos), 4) as peso_norm_r3,
        round((SELECT * FROM peso_r10) / (SELECT * FROM soma_pesos), 4) as peso_norm_r10,
        round((SELECT * FROM peso_r11) / (SELECT * FROM soma_pesos), 4) as peso_norm_r11,
        round((SELECT * FROM peso_r15) / (SELECT * FROM soma_pesos), 4) as peso_norm_r15,

        -- Contribuição de cada regra (score × peso normalizado)
        round(coalesce(s.score_frequencia, 0) * (SELECT * FROM peso_r1) / (SELECT * FROM soma_pesos), 2) as pct_r1,
        round(coalesce(s.score_atraso, 0) * (SELECT * FROM peso_r2) / (SELECT * FROM soma_pesos), 2) as pct_r2,
        round(coalesce(s.score_tendencia, 0) * (SELECT * FROM peso_r3) / (SELECT * FROM soma_pesos), 2) as pct_r3,
        round(coalesce(s.score_ciclo, 0) * (SELECT * FROM peso_r10) / (SELECT * FROM soma_pesos), 2) as pct_r10,
        round(coalesce(s.score_poisson, 0) * (SELECT * FROM peso_r11) / (SELECT * FROM soma_pesos), 2) as pct_r11,
        round(coalesce(s.score_pressao_ciclo, 0) * (SELECT * FROM peso_r15) / (SELECT * FROM soma_pesos), 2) as pct_r15,

        -- Score Individual (soma ponderada normalizada)
        round(
            coalesce(s.score_frequencia, 0) * (SELECT * FROM peso_r1) / (SELECT * FROM soma_pesos) +
            coalesce(s.score_atraso, 0) * (SELECT * FROM peso_r2) / (SELECT * FROM soma_pesos) +
            coalesce(s.score_tendencia, 0) * (SELECT * FROM peso_r3) / (SELECT * FROM soma_pesos) +
            coalesce(s.score_ciclo, 0) * (SELECT * FROM peso_r10) / (SELECT * FROM soma_pesos) +
            coalesce(s.score_poisson, 0) * (SELECT * FROM peso_r11) / (SELECT * FROM soma_pesos) +
            coalesce(s.score_pressao_ciclo, 0) * (SELECT * FROM peso_r15) / (SELECT * FROM soma_pesos),
        2) as score_individual,

        -- Score Final Completo (todas as 15 regras) para comparação
        round(coalesce(s.score_final, 0), 2) as score_final_completo

    FROM loterias.v_scores s
    ORDER BY score_individual DESC
""")
print("   ✅ v_score_individual atualizada com pesos dinâmicos!")

# =====================================================================
# 3. ATUALIZAR v_scores - COM SUBQUERIES NA TABELA REGRAS
# =====================================================================
print("\n3️⃣ Atualizando v_scores com pesos dinâmicos...")

client.query("""
    CREATE OR REPLACE VIEW loterias.v_scores AS
    WITH
        -- Pesos das regras (da tabela regras)
        p_r1 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R1'),
        p_r2 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R2'),
        p_r3 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R3'),
        p_r4 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R4'),
        p_r5 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R5'),
        p_r6 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R6'),
        p_r7 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R7'),
        p_r8 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R8'),
        p_r9 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R9'),
        p_r10 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R10'),
        p_r11 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R11'),
        p_r12 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R12'),
        p_r13 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R13'),
        p_r14 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R14'),
        p_r15 AS (SELECT peso/100 FROM loterias.regras WHERE codigo = 'R15')
    SELECT
        n.numero as numero,

        -- Scores individuais
        coalesce(f.score_frequencia, 0) as score_frequencia,
        coalesce(a.score_atraso, 0) as score_atraso,

        -- R3: Calcular score_tendencia a partir de aparicoes_ultimos_48
        round((coalesce(t.aparicoes_ultimos_48, 0) / (SELECT max(aparicoes_ultimos_48) FROM loterias.v_tendencia)) * 100, 1) as score_tendencia,

        coalesce(q.score_quadrante, 0) as score_quadrante,
        coalesce(p.score_paridade, 0) as score_paridade,
        coalesce(b.score_bma, 0) as score_bma,
        coalesce(l.score_linhas, 0) as score_linhas,
        coalesce(c.score_colunas, 0) as score_colunas,
        coalesce(s.score_soma, 0) as score_soma,

        -- R10: Calcular score_ciclo a partir de faltante_no_ciclo
        if(coalesce(ci.faltante_no_ciclo, 0) = 1, 100, 0) as score_ciclo,

        coalesce(po.score_poisson, 0) as score_poisson,
        coalesce(h.score_hnf, 0) as score_hnf,
        coalesce(sq.score_sequencia, 0) as score_sequencia,
        coalesce(fq.score_freq_quadrante, 0) as score_freq_quadrante,
        coalesce(pc.score_pressao_ciclo, 0) as score_pressao_ciclo,

        -- Score Final (soma ponderada com pesos dinâmicos)
        round(
            coalesce(f.score_frequencia, 0) * (SELECT * FROM p_r1) +
            coalesce(a.score_atraso, 0) * (SELECT * FROM p_r2) +
            (coalesce(t.aparicoes_ultimos_48, 0) / (SELECT max(aparicoes_ultimos_48) FROM loterias.v_tendencia)) * 100 * (SELECT * FROM p_r3) +
            coalesce(q.score_quadrante, 0) * (SELECT * FROM p_r4) +
            coalesce(p.score_paridade, 0) * (SELECT * FROM p_r5) +
            coalesce(b.score_bma, 0) * (SELECT * FROM p_r6) +
            coalesce(l.score_linhas, 0) * (SELECT * FROM p_r7) +
            coalesce(c.score_colunas, 0) * (SELECT * FROM p_r8) +
            coalesce(s.score_soma, 0) * (SELECT * FROM p_r9) +
            (if(coalesce(ci.faltante_no_ciclo, 0) = 1, 100, 0)) * (SELECT * FROM p_r10) +
            coalesce(po.score_poisson, 0) * (SELECT * FROM p_r11) +
            coalesce(h.score_hnf, 0) * (SELECT * FROM p_r12) +
            coalesce(sq.score_sequencia, 0) * (SELECT * FROM p_r13) +
            coalesce(fq.score_freq_quadrante, 0) * (SELECT * FROM p_r14) +
            coalesce(pc.score_pressao_ciclo, 0) * (SELECT * FROM p_r15),
        2) as score_final

    FROM (
        SELECT number as numero
        FROM numbers(1, 60)
        WHERE numero > 0 AND numero <= 60
    ) n
    LEFT JOIN loterias.v_frequencia f ON n.numero = f.numero
    LEFT JOIN loterias.v_atraso a ON n.numero = a.numero
    LEFT JOIN loterias.v_tendencia t ON n.numero = t.numero
    LEFT JOIN loterias.v_quadrante q ON n.numero = q.numero
    LEFT JOIN loterias.v_paridade p ON n.numero = p.numero
    LEFT JOIN loterias.v_bma b ON n.numero = b.numero
    LEFT JOIN loterias.v_linhas l ON n.numero = l.numero
    LEFT JOIN loterias.v_colunas c ON n.numero = c.numero
    LEFT JOIN loterias.v_soma s ON n.numero = s.numero
    LEFT JOIN loterias.v_ciclo ci ON n.numero = ci.numero
    LEFT JOIN loterias.v_poisson po ON n.numero = po.numero
    LEFT JOIN loterias.v_hnf h ON n.numero = h.numero
    LEFT JOIN loterias.v_sequencia sq ON n.numero = sq.numero
    LEFT JOIN loterias.v_score_freq_quadrante fq ON n.numero = fq.numero
    LEFT JOIN loterias.v_pressao_ciclo pc ON n.numero = pc.numero
    ORDER BY score_final DESC
""")
print("   ✅ v_scores atualizada com pesos dinâmicos!")

# =====================================================================
# 4. TESTAR - VERIFICAR SE PESOS SÃO LIDOS DINAMICAMENTE
# =====================================================================
print("\n" + "=" * 80)
print("4️⃣ Testando pesos dinâmicos...")

# Verificar peso atual de R7
peso_r7_antes = client.query("SELECT peso FROM loterias.regras WHERE codigo = 'R7'")
print(f"\n   Peso atual de R7 na tabela: {peso_r7_antes['peso'].iloc[0]}%")

# Verificar na view
peso_view = client.query("SELECT r7_peso FROM loterias.v_concurso_analise LIMIT 1")
print(f"   Peso de R7 na view v_concurso_analise: {peso_view['r7_peso'].iloc[0]}%")

print("\n" + "=" * 80)
print("✅ TODAS AS VIEWS AGORA USAM PESOS DINÂMICOS!")
print("\n💡 Para alterar um peso:")
print("   1. ALTER TABLE loterias.regras UPDATE peso = X WHERE codigo = 'RN'")
print("   2. A view automaticamente refletirá o novo valor!")
