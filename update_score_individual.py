"""
Script para atualizar a view v_score_individual
Remove score_final_completo e adiciona % de contribuição de cada regra
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 ATUALIZANDO VIEW v_score_individual")
print("=" * 80)

# Recriar view com percentuais
print("\n1️⃣ Recriando view com percentuais de contribuição...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_score_individual AS
    SELECT
        numero,

        -- Scores individuais das regras de número
        round(coalesce(score_frequencia, 0), 1) as r1_freq,
        round(coalesce(score_atraso, 0), 1) as r2_atraso,
        round(coalesce(score_tendencia, 0), 1) as r3_tend,
        round(coalesce(score_ciclo, 0), 1) as r10_ciclo,
        round(coalesce(score_poisson, 0), 1) as r11_poisson,
        round(coalesce(score_pressao_ciclo, 0), 1) as r15_pressao,

        -- Percentuais de contribuição (peso × score ÷ 100)
        round(coalesce(score_frequencia, 0) * 0.2143, 2) as pct_r1,    -- 21.43%
        round(coalesce(score_atraso, 0) * 0.2143, 2) as pct_r2,        -- 21.43%
        round(coalesce(score_tendencia, 0) * 0.1667, 2) as pct_r3,     -- 16.67%
        round(coalesce(score_ciclo, 0) * 0.1667, 2) as pct_r10,        -- 16.67%
        round(coalesce(score_poisson, 0) * 0.1429, 2) as pct_r11,      -- 14.29%
        round(coalesce(score_pressao_ciclo, 0) * 0.0952, 2) as pct_r15, -- 9.52%

        -- Score Individual Consolidado (soma dos percentuais)
        round(
            coalesce(score_frequencia, 0) * 0.2143 +
            coalesce(score_atraso, 0) * 0.2143 +
            coalesce(score_tendencia, 0) * 0.1667 +
            coalesce(score_ciclo, 0) * 0.1667 +
            coalesce(score_poisson, 0) * 0.1429 +
            coalesce(score_pressao_ciclo, 0) * 0.0952,
        2) as score_individual

    FROM loterias.v_scores
    ORDER BY score_individual DESC
""")
print("   ✅ View atualizada!")

# Testar a view
print("\n2️⃣ Testando view atualizada - Top 10 números:")
top10 = client.query("""
    SELECT
        numero,
        r1_freq,
        r2_atraso,
        r3_tend,
        r10_ciclo,
        r11_poisson,
        r15_pressao,
        pct_r1,
        pct_r2,
        pct_r3,
        pct_r10,
        pct_r11,
        pct_r15,
        score_individual
    FROM loterias.v_score_individual
    ORDER BY score_individual DESC
    LIMIT 10
""")

print("\n" + "=" * 150)
print(top10.to_string(index=False))
print("=" * 150)

# Verificação: soma dos percentuais
print("\n3️⃣ Verificação: Soma dos percentuais (deve dar ~score_individual)")
verificacao = client.query("""
    SELECT
        numero,
        pct_r1,
        pct_r2,
        pct_r3,
        pct_r10,
        pct_r11,
        pct_r15,
        round(pct_r1 + pct_r2 + pct_r3 + pct_r10 + pct_r11 + pct_r15, 2) as soma_pcts,
        score_individual,
        round(abs((pct_r1 + pct_r2 + pct_r3 + pct_r10 + pct_r11 + pct_r15) - score_individual), 2) as diferenca
    FROM loterias.v_score_individual
    ORDER BY score_individual DESC
    LIMIT 5
""")
print("\n" + verificacao.to_string(index=False))

print("\n✅ VIEW ATUALIZADA COM SUCESSO!")
print("\n📊 Colunas disponíveis:")
print("   - numero: Número da Mega-Sena (1-60)")
print("   - r1_freq, r2_atraso, r3_tend, r10_ciclo, r11_poisson, r15_pressao: Scores (0-100)")
print("   - pct_r1, pct_r2, pct_r3, pct_r10, pct_r11, pct_r15: % de contribuição para o score final")
print("   - score_individual: Score consolidado (soma dos %)")
