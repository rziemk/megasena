"""
Atualiza view v_ciclo para usar janela de 27 concursos
=======================================================
Altera de 15 para 27 concursos (mínimo histórico de ciclos completos)
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 ATUALIZANDO VIEW v_ciclo")
print("=" * 80)
print("📊 Nova janela: 27 concursos (mínimo histórico de ciclos completos)")

# Recriar view com janela de 27 concursos
print("\n1️⃣ Recriando view v_ciclo...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_ciclo AS
    WITH ultimos_27 AS (
        SELECT concurso
        FROM loterias.megasena
        ORDER BY concurso DESC
        LIMIT 27
    ),
    numeros_apareceram AS (
        SELECT DISTINCT numero
        FROM (
            SELECT concurso, numero
            FROM loterias.megasena
            ARRAY JOIN [bola1, bola2, bola3, bola4, bola5, bola6] AS numero
        )
        WHERE concurso IN (SELECT concurso FROM ultimos_27)
    ),
    ultimo_aparecimento AS (
        SELECT
            numero,
            max(concurso) as ultimo_concurso
        FROM (
            SELECT concurso, numero
            FROM loterias.megasena
            ARRAY JOIN [bola1, bola2, bola3, bola4, bola5, bola6] AS numero
        )
        GROUP BY numero
    )
    SELECT
        n.numero,
        if(n.numero IN (SELECT numero FROM numeros_apareceram), 0, 1) as faltante_no_ciclo,
        (SELECT max(concurso) FROM loterias.megasena) - coalesce(ua.ultimo_concurso, 0) as concursos_sem_sair
    FROM (
        SELECT number as numero
        FROM numbers(1, 61)
    ) n
    LEFT JOIN ultimo_aparecimento ua ON n.numero = ua.numero
    ORDER BY faltante_no_ciclo DESC, concursos_sem_sair DESC
""")
print("   ✅ View v_ciclo atualizada!")

# Testar a view
print("\n2️⃣ Testando view - Números faltantes no ciclo de 27:")
faltantes = client.query("""
    SELECT
        numero,
        faltante_no_ciclo,
        concursos_sem_sair
    FROM loterias.v_ciclo
    WHERE faltante_no_ciclo = 1
    ORDER BY concursos_sem_sair DESC
    LIMIT 15
""")

print("\n" + "=" * 60)
if not faltantes.empty:
    print(faltantes.to_string(index=False))
    print("\n📊 Total de números faltantes:", len(faltantes))
else:
    print("✓ Nenhum número faltante (ciclo completo!)")
print("=" * 60)

print("\n✅ VIEW v_ciclo ATUALIZADA COM SUCESSO!")
print("📊 Agora usando janela de 27 concursos (mínimo de ciclos completos)")
