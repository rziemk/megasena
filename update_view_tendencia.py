"""
Atualiza view v_tendencia para usar janela de 48 concursos
===========================================================
Altera de 10 para 48 concursos (média de duração dos ciclos completos)
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 ATUALIZANDO VIEW v_tendencia")
print("=" * 80)
print("📊 Nova janela: 48 concursos (média de ciclos completos)")

# Recriar view com janela de 48 concursos
print("\n1️⃣ Recriando view v_tendencia...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_tendencia AS
    WITH ultimos_48 AS (
        SELECT concurso
        FROM loterias.megasena
        ORDER BY concurso DESC
        LIMIT 48
    )
    SELECT
        numero,
        countIf(concurso IN (SELECT concurso FROM ultimos_48)) as aparicoes_ultimos_48,
        round(countIf(concurso IN (SELECT concurso FROM ultimos_48)) / 48.0 * 100, 1) as taxa_aparicao_pct
    FROM (
        SELECT concurso, numero
        FROM loterias.megasena
        ARRAY JOIN [bola1, bola2, bola3, bola4, bola5, bola6] AS numero
    )
    GROUP BY numero
    ORDER BY aparicoes_ultimos_48 DESC
""")
print("   ✅ View v_tendencia atualizada!")

# Testar a view
print("\n2️⃣ Testando view - Top 10 números por tendência:")
top10 = client.query("""
    SELECT
        numero,
        aparicoes_ultimos_48,
        taxa_aparicao_pct
    FROM loterias.v_tendencia
    ORDER BY aparicoes_ultimos_48 DESC
    LIMIT 10
""")

print("\n" + "=" * 60)
print(top10.to_string(index=False))
print("=" * 60)

print("\n✅ VIEW v_tendencia ATUALIZADA COM SUCESSO!")
print("📊 Agora usando janela de 48 concursos (média de ciclos completos)")
