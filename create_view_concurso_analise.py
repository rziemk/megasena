"""
Cria view v_concurso_analise
============================
Analisa cada concurso com as regras de conjunto (R4-R9, R12-R14)
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🔄 CRIANDO VIEW v_concurso_analise")
print("=" * 80)

# Criar a view
print("\n1️⃣ Criando view...")
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

        -- =====================================================================
        -- R5 - PARIDADE (Pares vs Ímpares)
        -- =====================================================================
        countIf(n % 2 = 0) as pares_count,
        countIf(n % 2 = 1) as impares_count,
        round(countIf(n % 2 = 0) / 6.0 * 100, 1) as pares_pct,
        round(countIf(n % 2 = 1) / 6.0 * 100, 1) as impares_pct,

        -- =====================================================================
        -- R6 - FAIXAS B/M/A (Baixo: 1-20, Médio: 21-40, Alto: 41-60)
        -- =====================================================================
        countIf(n >= 1 AND n <= 20) as baixo_count,
        countIf(n >= 21 AND n <= 40) as medio_count,
        countIf(n >= 41 AND n <= 60) as alto_count,
        round(countIf(n >= 1 AND n <= 20) / 6.0 * 100, 1) as baixo_pct,
        round(countIf(n >= 21 AND n <= 40) / 6.0 * 100, 1) as medio_pct,
        round(countIf(n >= 41 AND n <= 60) / 6.0 * 100, 1) as alto_pct,

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

        -- =====================================================================
        -- R9 - SOMA
        -- =====================================================================
        (m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) as soma,
        if((m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) BETWEEN 150 AND 200, 'IDEAL', 'FORA') as soma_faixa,

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

        -- =====================================================================
        -- MÉDIA DOS NÚMEROS
        -- =====================================================================
        round((m.bola1 + m.bola2 + m.bola3 + m.bola4 + m.bola5 + m.bola6) / 6.0, 1) as media_numeros

    FROM loterias.megasena m
    ARRAY JOIN [m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6] AS n
    GROUP BY m.concurso, m.data, m.bola1, m.bola2, m.bola3, m.bola4, m.bola5, m.bola6
    ORDER BY m.concurso DESC
""")
print("   ✅ View criada!")

# Testar a view
print("\n2️⃣ Testando view - Últimos 5 concursos:")
result = client.query("""
    SELECT
        concurso,
        -- Quadrantes
        concat(toString(q1_count), '-', toString(q2_count), '-', toString(q3_count), '-', toString(q4_count)) as quadrantes,
        -- Paridade
        concat(toString(pares_count), 'P/', toString(impares_count), 'I') as paridade,
        concat(toString(pares_pct), '%/', toString(impares_pct), '%') as paridade_pct,
        -- Faixas BMA
        concat(toString(baixo_count), '-', toString(medio_count), '-', toString(alto_count)) as bma,
        -- Soma
        soma,
        soma_faixa,
        -- Sequências
        sequencias_consecutivas as seq
    FROM loterias.v_concurso_analise
    ORDER BY concurso DESC
    LIMIT 5
""")

print("\n" + "=" * 120)
print(result.to_string(index=False))
print("=" * 120)

# Mostrar um concurso detalhado
print("\n3️⃣ Detalhes do último concurso:")
detalhe = client.query("""
    SELECT *
    FROM loterias.v_concurso_analise
    ORDER BY concurso DESC
    LIMIT 1
""")

ultimo = detalhe.iloc[0]
print(f"""
📊 CONCURSO {int(ultimo['concurso'])} - Data: {ultimo['data']}
   Números: {int(ultimo['bola1'])}-{int(ultimo['bola2'])}-{int(ultimo['bola3'])}-{int(ultimo['bola4'])}-{int(ultimo['bola5'])}-{int(ultimo['bola6'])}

   🔲 R4 - QUADRANTES:
      Q1 (1-15):  {int(ultimo['q1_count'])} números ({ultimo['q1_pct']}%)
      Q2 (16-30): {int(ultimo['q2_count'])} números ({ultimo['q2_pct']}%)
      Q3 (31-45): {int(ultimo['q3_count'])} números ({ultimo['q3_pct']}%)
      Q4 (46-60): {int(ultimo['q4_count'])} números ({ultimo['q4_pct']}%)

   ⚖️ R5 - PARIDADE:
      Pares:   {int(ultimo['pares_count'])} ({ultimo['pares_pct']}%)
      Ímpares: {int(ultimo['impares_count'])} ({ultimo['impares_pct']}%)

   📶 R6 - FAIXAS B/M/A:
      Baixo (1-20):  {int(ultimo['baixo_count'])} ({ultimo['baixo_pct']}%)
      Médio (21-40): {int(ultimo['medio_count'])} ({ultimo['medio_pct']}%)
      Alto (41-60):  {int(ultimo['alto_count'])} ({ultimo['alto_pct']}%)

   ➡️ R7 - LINHAS:
      L1 (1-10):  {int(ultimo['l1_count'])} ({ultimo['l1_pct']}%)
      L2 (11-20): {int(ultimo['l2_count'])} ({ultimo['l2_pct']}%)
      L3 (21-30): {int(ultimo['l3_count'])} ({ultimo['l3_pct']}%)
      L4 (31-40): {int(ultimo['l4_count'])} ({ultimo['l4_pct']}%)
      L5 (41-50): {int(ultimo['l5_count'])} ({ultimo['l5_pct']}%)
      L6 (51-60): {int(ultimo['l6_count'])} ({ultimo['l6_pct']}%)

   ⬇️ R8 - COLUNAS (Terminações):
      C0: {int(ultimo['c0_count'])} | C1: {int(ultimo['c1_count'])} | C2: {int(ultimo['c2_count'])} | C3: {int(ultimo['c3_count'])} | C4: {int(ultimo['c4_count'])}
      C5: {int(ultimo['c5_count'])} | C6: {int(ultimo['c6_count'])} | C7: {int(ultimo['c7_count'])} | C8: {int(ultimo['c8_count'])} | C9: {int(ultimo['c9_count'])}

   ➕ R9 - SOMA:
      Soma: {int(ultimo['soma'])} ({ultimo['soma_faixa']})

   🔢 R13 - SEQUÊNCIAS CONSECUTIVAS:
      Quantidade: {int(ultimo['sequencias_consecutivas'])}

   📊 MÉDIA:
      Média dos números: {ultimo['media_numeros']}
""")

print("\n✅ VIEW v_concurso_analise CRIADA COM SUCESSO!")
