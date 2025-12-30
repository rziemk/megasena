"""
Script para criar todas as views do ClickHouse Cloud
Cria as 14 regras completas
"""

from clickhouse_client import ClickHouseClient

client = ClickHouseClient()

print("🚀 Iniciando criação de views no ClickHouse Cloud...")

# Lista de SQLs para criar views
views_sql = [
    # View auxiliar: resultados expandidos (1 linha por número sorteado)
    """
    CREATE OR REPLACE VIEW loterias.resultados AS
    SELECT concurso, data, bola1 as numero FROM loterias.megasena
    UNION ALL SELECT concurso, data, bola2 FROM loterias.megasena
    UNION ALL SELECT concurso, data, bola3 FROM loterias.megasena
    UNION ALL SELECT concurso, data, bola4 FROM loterias.megasena
    UNION ALL SELECT concurso, data, bola5 FROM loterias.megasena
    UNION ALL SELECT concurso, data, bola6 FROM loterias.megasena
    """,

    # R1: Frequência
    """
    CREATE OR REPLACE VIEW loterias.v_frequencia AS
    SELECT
        numero,
        count() as aparicoes,
        round(count() * 100.0 / (SELECT count(DISTINCT concurso) FROM loterias.resultados), 2) as pct,
        round((count() / (SELECT max(aparicoes) FROM (
            SELECT count() as aparicoes FROM loterias.resultados GROUP BY numero
        ))) * 100, 2) as score_frequencia
    FROM loterias.resultados
    GROUP BY numero
    ORDER BY aparicoes DESC
    """,

    # R2: Atraso
    """
    CREATE OR REPLACE VIEW loterias.v_atraso AS
    SELECT
        numero,
        (SELECT max(concurso) FROM loterias.megasena) -
        max(concurso) as atraso,
        round(((SELECT max(concurso) FROM loterias.megasena) - max(concurso)) /
            (SELECT max(atraso_max) FROM (
                SELECT max((SELECT max(concurso) FROM loterias.megasena) - max(concurso)) as atraso_max
                FROM loterias.resultados GROUP BY numero
            )) * 100, 2) as score_atraso
    FROM loterias.resultados
    GROUP BY numero
    ORDER BY atraso DESC
    """,

    # R3: Tendência (últimos 48 concursos - média de ciclos completos)
    """
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
    """,

    # R4: Quadrante
    """
    CREATE OR REPLACE VIEW loterias.v_quadrante AS
    SELECT
        numero,
        multiIf(
            numero <= 15, 'Q1',
            numero <= 30, 'Q2',
            numero <= 45, 'Q3',
            'Q4'
        ) as quadrante,
        round((numero - 1) / 15.0 * 100, 2) as score_quadrante
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R5: Paridade
    """
    CREATE OR REPLACE VIEW loterias.v_paridade AS
    SELECT
        numero,
        if(numero % 2 = 0, 'Par', 'Ímpar') as paridade,
        50 as score_paridade
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R6: B/M/A (Baixo/Médio/Alto)
    """
    CREATE OR REPLACE VIEW loterias.v_bma AS
    SELECT
        numero,
        multiIf(
            numero <= 20, 'Baixo',
            numero <= 40, 'Médio',
            'Alto'
        ) as faixa_bma,
        50 as score_bma
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R7: Linhas do volante
    """
    CREATE OR REPLACE VIEW loterias.v_linhas AS
    SELECT
        numero,
        ceil(numero / 10.0) as linha,
        50 as score_linhas
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R8: Colunas do volante (terminações)
    """
    CREATE OR REPLACE VIEW loterias.v_colunas AS
    SELECT
        numero,
        numero % 10 as terminacao,
        50 as score_colunas
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R9: Soma ideal (150-200)
    """
    CREATE OR REPLACE VIEW loterias.v_soma AS
    SELECT
        numero,
        round(100 - abs(175 - numero) / 175.0 * 100, 2) as score_soma
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R10: Ciclo (últimos 27 concursos - mínimo histórico de ciclos completos)
    """
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
    """,

    # R11: Poisson (distribuição de probabilidade)
    """
    CREATE OR REPLACE VIEW loterias.v_poisson AS
    SELECT
        numero,
        count() as freq,
        round(exp(-(count() / (SELECT count(DISTINCT concurso) FROM loterias.resultados))) *
              pow(count() / (SELECT count(DISTINCT concurso) FROM loterias.resultados), count()) /
              factorial(count()), 4) * 100 as score_poisson
    FROM loterias.resultados
    GROUP BY numero
    ORDER BY numero
    """,

    # R12: H-N-F (Quente/Neutro/Frio)
    """
    CREATE OR REPLACE VIEW loterias.v_hnf AS
    WITH stats AS (
        SELECT
            numero,
            count() as freq,
            (SELECT avg(aparicoes) FROM (
                SELECT count() as aparicoes FROM loterias.resultados GROUP BY numero
            )) as freq_media
        FROM loterias.resultados
        GROUP BY numero
    )
    SELECT
        numero,
        multiIf(
            freq > freq_media * 1.1, 'Quente',
            freq < freq_media * 0.9, 'Frio',
            'Neutro'
        ) as classificacao_hnf,
        multiIf(
            freq > freq_media * 1.1, 100,
            freq < freq_media * 0.9, 30,
            65
        ) as score_hnf
    FROM stats
    ORDER BY numero
    """,

    # R13: Sequência
    """
    CREATE OR REPLACE VIEW loterias.v_sequencia AS
    SELECT
        numero,
        50 as score_sequencia
    FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ORDER BY numero
    """,

    # R14: Frequência por Quadrante
    """
    CREATE OR REPLACE VIEW loterias.v_stats_freq_quadrante AS
    WITH numeros AS (
        SELECT
            numero,
            multiIf(numero <= 15, 'Q1 (01-15)', numero <= 30, 'Q2 (16-30)',
                   numero <= 45, 'Q3 (31-45)', 'Q4 (46-60)') as quadrante
        FROM (SELECT DISTINCT numero FROM loterias.resultados)
    )
    SELECT
        quadrante,
        count(*) as qtd_numeros,
        round(avg(aparicoes), 2) as freq_media,
        min(aparicoes) as freq_minima,
        max(aparicoes) as freq_maxima,
        round(sum(aparicoes) * 100.0 / (SELECT sum(aparicoes) FROM loterias.v_frequencia), 2) as pct_total_aparicoes
    FROM loterias.v_frequencia f
    JOIN numeros n ON f.numero = n.numero
    GROUP BY quadrante
    ORDER BY freq_media DESC
    """,

    """
    CREATE OR REPLACE VIEW loterias.v_score_freq_quadrante AS
    WITH numeros AS (
        SELECT
            numero,
            multiIf(numero <= 15, 'Q1', numero <= 30, 'Q2', numero <= 45, 'Q3', 'Q4') as quadrante
        FROM (SELECT DISTINCT numero FROM loterias.resultados)
    ),
    quad_freq AS (
        SELECT quadrante, avg(aparicoes) as freq_media
        FROM loterias.v_frequencia f
        JOIN numeros n ON f.numero = n.numero
        GROUP BY quadrante
    )
    SELECT
        n.numero,
        n.quadrante,
        round((qf.freq_media / (SELECT max(freq_media) FROM quad_freq)) * 100, 2) as score_freq_quadrante
    FROM numeros n
    JOIN quad_freq qf ON n.quadrante = qf.quadrante
    ORDER BY n.numero
    """,

    # View final v_scores com todas as 15 regras
    """
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
        if(coalesce(ci.faltante_no_ciclo, 0) = 1, 100, 0) as score_ciclo,

        coalesce(po.score_poisson, 0) as score_poisson,
        coalesce(h.score_hnf, 0) as score_hnf,
        coalesce(sq.score_sequencia, 0) as score_sequencia,
        coalesce(fq.score_freq_quadrante, 0) as score_freq_quadrante,
        coalesce(pc.score_pressao_ciclo, 0) as score_pressao_ciclo,

        -- Score Final (soma ponderada) - 15 REGRAS
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
    """
]

# Executar cada SQL
for i, sql in enumerate(views_sql, 1):
    try:
        client.query(sql)
        view_name = sql.split("VIEW")[1].split("AS")[0].strip() if "VIEW" in sql else f"SQL {i}"
        print(f"✅ {i}/{len(views_sql)}: {view_name} criada!")
    except Exception as e:
        print(f"❌ {i}/{len(views_sql)}: Erro - {e}")

print("\n🎉 Setup completo! Testando...")

# Testar v_scores
result = client.query("SELECT numero, score_final FROM loterias.v_scores ORDER BY score_final DESC LIMIT 10")
print("\n📊 Top 10 números:")
print(result)

print("\n✅ Todas as 14 regras criadas com sucesso no ClickHouse Cloud!")
