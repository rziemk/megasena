"""
Script para criar view de Score Individual (apenas regras de número)
Considera apenas as 6 regras que analisam cada número individualmente
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🎯 CRIANDO SCORE INDIVIDUAL (Apenas Regras de Número)")
print("=" * 80)

# Pesos das regras individuais (normalizados para somar 100%)
# Original: R1=9%, R2=9%, R3=7%, R10=7%, R11=6%, R15=4% = 42% do total
# Normalizando para 100%: dividir cada peso por 0.42
print("\n📊 Pesos das Regras Individuais (normalizados para 100%):")
print("   R1  - Frequência: 21.43% (9/42)")
print("   R2  - Atraso: 21.43% (9/42)")
print("   R3  - Tendência: 16.67% (7/42)")
print("   R10 - Ciclo: 16.67% (7/42)")
print("   R11 - Poisson: 14.29% (6/42)")
print("   R15 - Pressão: 9.52% (4/42)")
print("   " + "=" * 40)
print("   TOTAL: 100.00%")

# Criar view de score individual
print("\n1️⃣ Criando view v_score_individual...")
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

        -- Score Individual Consolidado (apenas regras de número)
        -- Normalizando os pesos para somar 100%
        round(
            coalesce(score_frequencia, 0) * 0.2143 +  -- 21.43% (9/42)
            coalesce(score_atraso, 0) * 0.2143 +       -- 21.43% (9/42)
            coalesce(score_tendencia, 0) * 0.1667 +    -- 16.67% (7/42)
            coalesce(score_ciclo, 0) * 0.1667 +        -- 16.67% (7/42)
            coalesce(score_poisson, 0) * 0.1429 +      -- 14.29% (6/42)
            coalesce(score_pressao_ciclo, 0) * 0.0952, -- 9.52% (4/42)
        2) as score_individual,

        -- Score Final Completo (todas as 15 regras) para comparação
        round(coalesce(score_final, 0), 2) as score_final_completo

    FROM loterias.v_scores
    ORDER BY score_individual DESC
""")
print("   ✅ View v_score_individual criada!")

# Testar a view
print("\n2️⃣ Testando view - Top 20 números por Score Individual:")
top20 = client.query("""
    SELECT
        numero,
        r1_freq,
        r2_atraso,
        r3_tend,
        r10_ciclo,
        r11_poisson,
        r15_pressao,
        score_individual,
        score_final_completo
    FROM loterias.v_score_individual
    ORDER BY score_individual DESC
    LIMIT 20
""")

print("\n" + "=" * 120)
print(top20.to_string(index=False))
print("=" * 120)

print("\n3️⃣ Comparação: Score Individual vs Score Completo")
comparacao = client.query("""
    SELECT
        numero,
        score_individual,
        score_final_completo,
        score_final_completo - score_individual as diferenca
    FROM loterias.v_score_individual
    ORDER BY score_individual DESC
    LIMIT 10
""")
print("\n" + comparacao.to_string(index=False))

print("\n✅ SCORE INDIVIDUAL CRIADO COM SUCESSO!")
print("\n💡 Uso:")
print("   SELECT * FROM loterias.v_score_individual ORDER BY score_individual DESC")
