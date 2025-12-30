"""
Atualiza view v_scores para usar as novas estruturas de v_tendencia e v_ciclo
===============================================================================
v_tendencia agora tem: aparicoes_ultimos_48 e taxa_aparicao_pct
v_ciclo agora não tem mais score_ciclo direto
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 ATUALIZANDO VIEW v_scores")
print("=" * 80)

# Recriar view v_scores com cálculos corretos
print("\n1️⃣ Recriando view v_scores...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_scores AS
    SELECT
        n.numero as numero,

        -- Scores individuais
        coalesce(f.score_frequencia, 0) as score_frequencia,
        coalesce(a.score_atraso, 0) as score_atraso,

        -- R3: Calcular score_tendencia a partir de aparicoes_ultimos_48
        -- Score = (aparições / max_aparições) × 100 (normalizado pelo máximo)
        round((coalesce(t.aparicoes_ultimos_48, 0) / (SELECT max(aparicoes_ultimos_48) FROM loterias.v_tendencia)) * 100, 1) as score_tendencia,

        coalesce(q.score_quadrante, 0) as score_quadrante,
        coalesce(p.score_paridade, 0) as score_paridade,
        coalesce(b.score_bma, 0) as score_bma,
        coalesce(l.score_linhas, 0) as score_linhas,
        coalesce(c.score_colunas, 0) as score_colunas,
        coalesce(s.score_soma, 0) as score_soma,

        -- R10: Calcular score_ciclo a partir de faltante_no_ciclo
        -- Se faltante = 1, score = 100; senão score = 0
        if(coalesce(ci.faltante_no_ciclo, 0) = 1, 100, 0) as score_ciclo,

        coalesce(po.score_poisson, 0) as score_poisson,
        coalesce(h.score_hnf, 0) as score_hnf,
        coalesce(sq.score_sequencia, 0) as score_sequencia,
        coalesce(fq.score_freq_quadrante, 0) as score_freq_quadrante,
        coalesce(pc.score_pressao_ciclo, 0) as score_pressao_ciclo,

        -- Score Final (soma ponderada)
        round(
            coalesce(f.score_frequencia, 0) * 0.09 +           -- R1: 9%
            coalesce(a.score_atraso, 0) * 0.09 +                -- R2: 9%
            (coalesce(t.aparicoes_ultimos_48, 0) / (SELECT max(aparicoes_ultimos_48) FROM loterias.v_tendencia)) * 100 * 0.07 +  -- R3: 7%
            coalesce(q.score_quadrante, 0) * 0.07 +             -- R4: 7%
            coalesce(p.score_paridade, 0) * 0.06 +              -- R5: 6%
            coalesce(b.score_bma, 0) * 0.06 +                   -- R6: 6%
            coalesce(l.score_linhas, 0) * 0.07 +                -- R7: 7%
            coalesce(c.score_colunas, 0) * 0.07 +               -- R8: 7%
            coalesce(s.score_soma, 0) * 0.07 +                  -- R9: 7%
            (if(coalesce(ci.faltante_no_ciclo, 0) = 1, 100, 0)) * 0.07 +  -- R10: 7%
            coalesce(po.score_poisson, 0) * 0.06 +              -- R11: 6%
            coalesce(h.score_hnf, 0) * 0.06 +                   -- R12: 6%
            coalesce(sq.score_sequencia, 0) * 0.06 +            -- R13: 6%
            coalesce(fq.score_freq_quadrante, 0) * 0.06 +       -- R14: 6%
            coalesce(pc.score_pressao_ciclo, 0) * 0.04,         -- R15: 4%
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
print("   ✅ View v_scores atualizada!")

# Testar a view
print("\n2️⃣ Testando view - Top 10 números:")
top10 = client.query("""
    SELECT
        numero,
        score_frequencia,
        score_atraso,
        score_tendencia,
        score_ciclo,
        score_final
    FROM loterias.v_scores
    ORDER BY score_final DESC
    LIMIT 10
""")

print("\n" + "=" * 100)
print(top10.to_string(index=False))
print("=" * 100)

print("\n✅ VIEW v_scores ATUALIZADA COM SUCESSO!")
print("📊 Agora usando:")
print("   - R3 (Tendência): aparicoes_ultimos_48 / 8 × 100")
print("   - R10 (Ciclo): if(faltante_no_ciclo = 1, 100, 0)")
