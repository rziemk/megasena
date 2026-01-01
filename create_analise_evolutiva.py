#!/usr/bin/env python3
"""
Criação da Tabela de Análise Evolutiva
======================================
Processa todas as 19 regras concurso a concurso, sempre olhando o histórico passado.

Estrutura:
- 6 Regras Individuais (resumo por concurso)
- 13 Regras de Conjunto (padrão do concurso)
- 4 Metadados de Ciclo (números faltantes por ciclo)
"""

from clickhouse_client import ClickHouseClient
from math import comb, factorial, exp
import pandas as pd
from collections import Counter

# Números primos de 1 a 60
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}
PARES = {i for i in range(2, 61, 2)}  # 2, 4, 6, ..., 60
IMPARES = {i for i in range(1, 60, 2)}  # 1, 3, 5, ..., 59
TODOS = set(range(1, 61))

def execute_ddl(sql):
    """Executa DDL no ClickHouse Cloud via curl."""
    import subprocess
    from pathlib import Path

    # Carregar configurações
    dev_vars_path = Path(__file__).parent / 'dev.vars'
    config = {}
    if dev_vars_path.exists():
        with open(dev_vars_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    host = config.get('CLICKHOUSE_HOST', '').replace('https://', '').replace('http://', '')
    port = config.get('CLICKHOUSE_PORT', '8443')
    user = config.get('CLICKHOUSE_USER', 'default')
    password = config.get('CLICKHOUSE_PASSWORD', '')

    url = f"https://{host}:{port}/"

    cmd = [
        'curl', '-s', '--fail-with-body',
        '--user', f"{user}:{password}",
        '--data-binary', sql,
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def create_table():
    """Cria a tabela de análise evolutiva no ClickHouse."""

    # Dropar tabela se existir
    success, out, err = execute_ddl("DROP TABLE IF EXISTS loterias.concurso_analise_evolutiva")
    if success:
        print("Tabela anterior removida.")
    else:
        print(f"Aviso ao remover tabela: {err}")

    create_sql = """
    CREATE TABLE IF NOT EXISTS loterias.concurso_analise_evolutiva (
        -- Identificação
        concurso UInt32,
        data Date,
        numeros Array(UInt8),

        -- =============================================
        -- REGRAS INDIVIDUAIS (resumo do concurso)
        -- =============================================

        -- R1: Frequência - quantos dos 6 estão no top 20 de frequência
        r1_freq_top20 UInt8,

        -- R2: Atraso - atraso médio dos 6 números sorteados
        r2_atraso_medio Float32,
        r2_atraso_max UInt16,

        -- R3: Tendência - quantos dos 6 apareceram 5+ vezes nos últimos 48
        r3_tendencia_quentes UInt8,

        -- R4: Poisson - desvio médio dos 6 números
        r4_poisson_desvio Float32,

        -- R5: Pressão Ciclo 60 - quantos estavam "devendo" (faltantes no ciclo)
        r5_pressao_faltantes UInt8,

        -- R6: HNF - classificação Hot/Neutral/Frio dos 6 números
        r6_hot UInt8,
        r6_neutral UInt8,
        r6_frio UInt8,

        -- =============================================
        -- REGRAS DE CONJUNTO (padrão do concurso)
        -- =============================================

        -- R7: Soma das 6 dezenas
        r7_soma UInt16,
        r7_soma_classe String,  -- 'baixa', 'ideal', 'alta'

        -- R8: Paridade
        r8_pares UInt8,
        r8_impares UInt8,
        r8_padrao String,  -- ex: '3P-3I'

        -- R9: Primos
        r9_primos UInt8,
        r9_nao_primos UInt8,

        -- R10: Quadrantes (Q1: 1-15, Q2: 16-30, Q3: 31-45, Q4: 46-60)
        r10_q1 UInt8,
        r10_q2 UInt8,
        r10_q3 UInt8,
        r10_q4 UInt8,
        r10_padrao String,  -- ex: '2-1-2-1'

        -- R11: BMA (B: 1-20, M: 21-40, A: 41-60)
        r11_baixo UInt8,
        r11_medio UInt8,
        r11_alto UInt8,
        r11_padrao String,  -- ex: '2-2-2'

        -- R12: Linhas (6 linhas de 10 números cada)
        r12_l1 UInt8,
        r12_l2 UInt8,
        r12_l3 UInt8,
        r12_l4 UInt8,
        r12_l5 UInt8,
        r12_l6 UInt8,
        r12_padrao String,  -- ex: '1-2-1-1-1-0'

        -- R13: Colunas/Terminações (0-9)
        r13_t0 UInt8,
        r13_t1 UInt8,
        r13_t2 UInt8,
        r13_t3 UInt8,
        r13_t4 UInt8,
        r13_t5 UInt8,
        r13_t6 UInt8,
        r13_t7 UInt8,
        r13_t8 UInt8,
        r13_t9 UInt8,
        r13_padrao String,  -- ex: '1-0-2-1-0-1-0-1-0-0'

        -- R14: Sequências consecutivas
        r14_tem_sequencia UInt8,  -- 0 ou 1
        r14_maior_sequencia UInt8,  -- tamanho da maior sequência
        r14_total_sequencias UInt8,  -- quantas sequências tem

        -- R15: Ciclo 60 - cobertura do ciclo completo
        r15_ciclo_numero UInt16,  -- em qual ciclo estamos
        r15_faltam_antes UInt8,  -- quantos faltavam ANTES deste sorteio
        r15_novos UInt8,  -- quantos "novos" saíram (não tinham saído neste ciclo)
        r15_repetidos UInt8,  -- quantos já tinham saído neste ciclo
        r15_faltam_depois UInt8,  -- quantos faltam DEPOIS deste sorteio

        -- R16: Ciclo Pares
        r16_ciclo_numero UInt16,
        r16_faltam_antes UInt8,
        r16_novos UInt8,
        r16_repetidos UInt8,
        r16_faltam_depois UInt8,

        -- R17: Ciclo Ímpares
        r17_ciclo_numero UInt16,
        r17_faltam_antes UInt8,
        r17_novos UInt8,
        r17_repetidos UInt8,
        r17_faltam_depois UInt8,

        -- R18: Ciclo Primos
        r18_ciclo_numero UInt16,
        r18_faltam_antes UInt8,
        r18_novos UInt8,
        r18_repetidos UInt8,
        r18_faltam_depois UInt8,

        -- R19: Mix HNF do concurso
        r19_padrao String,  -- ex: '3H-2N-1F'

        -- =============================================
        -- METADADOS - Números faltantes por ciclo
        -- =============================================
        meta_faltam_ciclo60 Array(UInt8),    -- números que ainda faltam no ciclo 60
        meta_faltam_pares Array(UInt8),      -- pares que ainda faltam
        meta_faltam_impares Array(UInt8),    -- ímpares que ainda faltam
        meta_faltam_primos Array(UInt8)      -- primos que ainda faltam

    ) ENGINE = MergeTree()
    ORDER BY concurso
    """

    success, out, err = execute_ddl(create_sql)

    if not success:
        print(f"Erro ao criar tabela: {err}")
        return False

    print("Tabela loterias.concurso_analise_evolutiva criada com sucesso!")
    return True


def processar_concursos():
    """Processa todos os concursos a partir do fim do ciclo 1."""

    ch = ClickHouseClient()

    # Buscar todos os concursos
    df = ch.query('''
        SELECT concurso, data, bola1, bola2, bola3, bola4, bola5, bola6
        FROM loterias.megasena
        ORDER BY concurso ASC
    ''')

    print(f"Total de concursos: {len(df)}")

    # Encontrar fim do ciclo 1
    numeros_vistos = set()
    ciclo1_fim = None

    for idx, row in df.iterrows():
        numeros = {int(row['bola1']), int(row['bola2']), int(row['bola3']),
                   int(row['bola4']), int(row['bola5']), int(row['bola6'])}
        numeros_vistos.update(numeros)

        if len(numeros_vistos) == 60 and ciclo1_fim is None:
            ciclo1_fim = int(row['concurso'])
            break

    print(f"Ciclo 1 termina no concurso: {ciclo1_fim}")
    print(f"Processando a partir do concurso: {ciclo1_fim + 1}")

    # Inicializar estados dos ciclos
    ciclo_60 = {'numero': 2, 'vistos': set()}  # Já estamos no ciclo 2
    ciclo_pares = {'numero': 1, 'vistos': set()}
    ciclo_impares = {'numero': 1, 'vistos': set()}
    ciclo_primos = {'numero': 1, 'vistos': set()}

    # Reconstruir estado dos ciclos até o fim do ciclo 1
    for idx, row in df.iterrows():
        if int(row['concurso']) > ciclo1_fim:
            break

        numeros = {int(row['bola1']), int(row['bola2']), int(row['bola3']),
                   int(row['bola4']), int(row['bola5']), int(row['bola6'])}

        # Atualizar ciclo de pares
        pares_sorteio = numeros & PARES
        ciclo_pares['vistos'].update(pares_sorteio)
        if ciclo_pares['vistos'] == PARES:
            ciclo_pares['numero'] += 1
            ciclo_pares['vistos'] = set()

        # Atualizar ciclo de ímpares
        impares_sorteio = numeros & IMPARES
        ciclo_impares['vistos'].update(impares_sorteio)
        if ciclo_impares['vistos'] == IMPARES:
            ciclo_impares['numero'] += 1
            ciclo_impares['vistos'] = set()

        # Atualizar ciclo de primos
        primos_sorteio = numeros & PRIMOS
        ciclo_primos['vistos'].update(primos_sorteio)
        if ciclo_primos['vistos'] == PRIMOS:
            ciclo_primos['numero'] += 1
            ciclo_primos['vistos'] = set()

    # Histórico acumulado para cálculos
    historico_numeros = []  # Lista de sets, cada um é um sorteio
    frequencia_acumulada = Counter()

    # Reconstruir histórico até ciclo1_fim
    for idx, row in df.iterrows():
        if int(row['concurso']) > ciclo1_fim:
            break
        numeros = {int(row['bola1']), int(row['bola2']), int(row['bola3']),
                   int(row['bola4']), int(row['bola5']), int(row['bola6'])}
        historico_numeros.append(numeros)
        frequencia_acumulada.update(numeros)

    # Processar cada concurso a partir do ciclo1_fim + 1
    resultados = []

    for idx, row in df.iterrows():
        concurso = int(row['concurso'])

        if concurso <= ciclo1_fim:
            continue

        numeros = {int(row['bola1']), int(row['bola2']), int(row['bola3']),
                   int(row['bola4']), int(row['bola5']), int(row['bola6'])}
        numeros_lista = sorted(list(numeros))

        # =============================================
        # CALCULAR TODAS AS REGRAS
        # =============================================

        resultado = calcular_regras(
            concurso=concurso,
            data=row['data'],
            numeros=numeros,
            numeros_lista=numeros_lista,
            historico_numeros=historico_numeros,
            frequencia_acumulada=frequencia_acumulada,
            ciclo_60=ciclo_60,
            ciclo_pares=ciclo_pares,
            ciclo_impares=ciclo_impares,
            ciclo_primos=ciclo_primos
        )

        resultados.append(resultado)

        # Atualizar histórico
        historico_numeros.append(numeros)
        frequencia_acumulada.update(numeros)

        # Atualizar ciclos
        atualizar_ciclos(numeros, ciclo_60, ciclo_pares, ciclo_impares, ciclo_primos)

        # Log de progresso
        if concurso % 500 == 0:
            print(f"Processado: {concurso}")

    print(f"Total processado: {len(resultados)} concursos")

    # Inserir no ClickHouse
    inserir_resultados(resultados)

    return resultados


def calcular_regras(concurso, data, numeros, numeros_lista, historico_numeros,
                    frequencia_acumulada, ciclo_60, ciclo_pares, ciclo_impares, ciclo_primos):
    """Calcula todas as 19 regras para um concurso."""

    resultado = {
        'concurso': concurso,
        'data': str(data),
        'numeros': numeros_lista
    }

    total_concursos = len(historico_numeros)

    # =============================================
    # R1: Frequência - top 20
    # =============================================
    top20 = set([n for n, _ in frequencia_acumulada.most_common(20)])
    r1_count = len(numeros & top20)
    resultado['r1_freq_top20'] = r1_count

    # =============================================
    # R2: Atraso
    # =============================================
    atrasos = []
    for n in numeros:
        atraso = 0
        for i in range(len(historico_numeros) - 1, -1, -1):
            if n in historico_numeros[i]:
                break
            atraso += 1
        atrasos.append(atraso)

    resultado['r2_atraso_medio'] = sum(atrasos) / len(atrasos) if atrasos else 0
    resultado['r2_atraso_max'] = max(atrasos) if atrasos else 0

    # =============================================
    # R3: Tendência (últimos 48 concursos)
    # =============================================
    ultimos_48 = historico_numeros[-48:] if len(historico_numeros) >= 48 else historico_numeros
    freq_recente = Counter()
    for sorteio in ultimos_48:
        freq_recente.update(sorteio)

    # Quentes = apareceram 5+ vezes nos últimos 48
    quentes_recente = {n for n, f in freq_recente.items() if f >= 5}
    resultado['r3_tendencia_quentes'] = len(numeros & quentes_recente)

    # =============================================
    # R4: Poisson
    # =============================================
    if total_concursos > 0:
        freq_esperada = (total_concursos * 6) / 60  # cada número deveria sair essa média
        desvios = []
        for n in numeros:
            freq_real = frequencia_acumulada[n]
            desvio = (freq_real - freq_esperada) / max(freq_esperada, 1)
            desvios.append(abs(desvio))
        resultado['r4_poisson_desvio'] = sum(desvios) / len(desvios)
    else:
        resultado['r4_poisson_desvio'] = 0

    # =============================================
    # R5: Pressão Ciclo 60
    # =============================================
    faltantes_ciclo60 = TODOS - ciclo_60['vistos']
    resultado['r5_pressao_faltantes'] = len(numeros & faltantes_ciclo60)

    # =============================================
    # R6: HNF (Hot/Neutral/Frio)
    # =============================================
    if total_concursos > 0:
        freq_list = [(n, frequencia_acumulada[n]) for n in range(1, 61)]
        freq_list.sort(key=lambda x: x[1], reverse=True)

        hot_nums = {n for n, _ in freq_list[:20]}
        frio_nums = {n for n, _ in freq_list[-20:]}
        neutral_nums = TODOS - hot_nums - frio_nums

        resultado['r6_hot'] = len(numeros & hot_nums)
        resultado['r6_neutral'] = len(numeros & neutral_nums)
        resultado['r6_frio'] = len(numeros & frio_nums)
    else:
        resultado['r6_hot'] = 0
        resultado['r6_neutral'] = 6
        resultado['r6_frio'] = 0

    # =============================================
    # R7: Soma
    # =============================================
    soma = sum(numeros)
    resultado['r7_soma'] = soma
    if soma < 140:
        resultado['r7_soma_classe'] = 'baixa'
    elif soma <= 200:
        resultado['r7_soma_classe'] = 'ideal'
    else:
        resultado['r7_soma_classe'] = 'alta'

    # =============================================
    # R8: Paridade
    # =============================================
    pares = len(numeros & PARES)
    impares = 6 - pares
    resultado['r8_pares'] = pares
    resultado['r8_impares'] = impares
    resultado['r8_padrao'] = f"{pares}P-{impares}I"

    # =============================================
    # R9: Primos
    # =============================================
    primos = len(numeros & PRIMOS)
    resultado['r9_primos'] = primos
    resultado['r9_nao_primos'] = 6 - primos

    # =============================================
    # R10: Quadrantes
    # =============================================
    q1 = len([n for n in numeros if 1 <= n <= 15])
    q2 = len([n for n in numeros if 16 <= n <= 30])
    q3 = len([n for n in numeros if 31 <= n <= 45])
    q4 = len([n for n in numeros if 46 <= n <= 60])
    resultado['r10_q1'] = q1
    resultado['r10_q2'] = q2
    resultado['r10_q3'] = q3
    resultado['r10_q4'] = q4
    resultado['r10_padrao'] = f"{q1}-{q2}-{q3}-{q4}"

    # =============================================
    # R11: BMA
    # =============================================
    baixo = len([n for n in numeros if 1 <= n <= 20])
    medio = len([n for n in numeros if 21 <= n <= 40])
    alto = len([n for n in numeros if 41 <= n <= 60])
    resultado['r11_baixo'] = baixo
    resultado['r11_medio'] = medio
    resultado['r11_alto'] = alto
    resultado['r11_padrao'] = f"{baixo}-{medio}-{alto}"

    # =============================================
    # R12: Linhas
    # =============================================
    linhas = [0] * 6
    for n in numeros:
        linha = (n - 1) // 10
        if linha < 6:
            linhas[linha] += 1

    resultado['r12_l1'] = linhas[0]
    resultado['r12_l2'] = linhas[1]
    resultado['r12_l3'] = linhas[2]
    resultado['r12_l4'] = linhas[3]
    resultado['r12_l5'] = linhas[4]
    resultado['r12_l6'] = linhas[5]
    resultado['r12_padrao'] = '-'.join(map(str, linhas))

    # =============================================
    # R13: Colunas/Terminações
    # =============================================
    terminacoes = [0] * 10
    for n in numeros:
        t = n % 10
        terminacoes[t] += 1

    resultado['r13_t0'] = terminacoes[0]
    resultado['r13_t1'] = terminacoes[1]
    resultado['r13_t2'] = terminacoes[2]
    resultado['r13_t3'] = terminacoes[3]
    resultado['r13_t4'] = terminacoes[4]
    resultado['r13_t5'] = terminacoes[5]
    resultado['r13_t6'] = terminacoes[6]
    resultado['r13_t7'] = terminacoes[7]
    resultado['r13_t8'] = terminacoes[8]
    resultado['r13_t9'] = terminacoes[9]
    resultado['r13_padrao'] = '-'.join(map(str, terminacoes))

    # =============================================
    # R14: Sequências
    # =============================================
    sequencias = contar_sequencias(numeros_lista)
    resultado['r14_tem_sequencia'] = 1 if sequencias['maior'] > 1 else 0
    resultado['r14_maior_sequencia'] = sequencias['maior']
    resultado['r14_total_sequencias'] = sequencias['total']

    # =============================================
    # R15: Ciclo 60
    # =============================================
    faltam_antes_60 = TODOS - ciclo_60['vistos']
    novos_60 = numeros & faltam_antes_60
    repetidos_60 = numeros - novos_60
    faltam_depois_60 = faltam_antes_60 - novos_60

    resultado['r15_ciclo_numero'] = ciclo_60['numero']
    resultado['r15_faltam_antes'] = len(faltam_antes_60)
    resultado['r15_novos'] = len(novos_60)
    resultado['r15_repetidos'] = len(repetidos_60)
    resultado['r15_faltam_depois'] = len(faltam_depois_60)

    # =============================================
    # R16: Ciclo Pares
    # =============================================
    pares_sorteio = numeros & PARES
    faltam_antes_pares = PARES - ciclo_pares['vistos']
    novos_pares = pares_sorteio & faltam_antes_pares
    repetidos_pares = pares_sorteio - novos_pares
    faltam_depois_pares = faltam_antes_pares - novos_pares

    resultado['r16_ciclo_numero'] = ciclo_pares['numero']
    resultado['r16_faltam_antes'] = len(faltam_antes_pares)
    resultado['r16_novos'] = len(novos_pares)
    resultado['r16_repetidos'] = len(repetidos_pares)
    resultado['r16_faltam_depois'] = len(faltam_depois_pares)

    # =============================================
    # R17: Ciclo Ímpares
    # =============================================
    impares_sorteio = numeros & IMPARES
    faltam_antes_impares = IMPARES - ciclo_impares['vistos']
    novos_impares = impares_sorteio & faltam_antes_impares
    repetidos_impares = impares_sorteio - novos_impares
    faltam_depois_impares = faltam_antes_impares - novos_impares

    resultado['r17_ciclo_numero'] = ciclo_impares['numero']
    resultado['r17_faltam_antes'] = len(faltam_antes_impares)
    resultado['r17_novos'] = len(novos_impares)
    resultado['r17_repetidos'] = len(repetidos_impares)
    resultado['r17_faltam_depois'] = len(faltam_depois_impares)

    # =============================================
    # R18: Ciclo Primos
    # =============================================
    primos_sorteio = numeros & PRIMOS
    faltam_antes_primos = PRIMOS - ciclo_primos['vistos']
    novos_primos = primos_sorteio & faltam_antes_primos
    repetidos_primos = primos_sorteio - novos_primos
    faltam_depois_primos = faltam_antes_primos - novos_primos

    resultado['r18_ciclo_numero'] = ciclo_primos['numero']
    resultado['r18_faltam_antes'] = len(faltam_antes_primos)
    resultado['r18_novos'] = len(novos_primos)
    resultado['r18_repetidos'] = len(repetidos_primos)
    resultado['r18_faltam_depois'] = len(faltam_depois_primos)

    # =============================================
    # R19: Mix HNF
    # =============================================
    resultado['r19_padrao'] = f"{resultado['r6_hot']}H-{resultado['r6_neutral']}N-{resultado['r6_frio']}F"

    # =============================================
    # METADADOS - Números faltantes
    # =============================================
    resultado['meta_faltam_ciclo60'] = sorted(list(faltam_depois_60))
    resultado['meta_faltam_pares'] = sorted(list(faltam_depois_pares))
    resultado['meta_faltam_impares'] = sorted(list(faltam_depois_impares))
    resultado['meta_faltam_primos'] = sorted(list(faltam_depois_primos))

    return resultado


def contar_sequencias(numeros_lista):
    """Conta sequências consecutivas nos números sorteados."""
    if len(numeros_lista) < 2:
        return {'maior': 1, 'total': 0}

    sorted_nums = sorted(numeros_lista)
    maior_seq = 1
    seq_atual = 1
    total_seqs = 0

    for i in range(1, len(sorted_nums)):
        if sorted_nums[i] == sorted_nums[i-1] + 1:
            seq_atual += 1
        else:
            if seq_atual > 1:
                total_seqs += 1
                maior_seq = max(maior_seq, seq_atual)
            seq_atual = 1

    if seq_atual > 1:
        total_seqs += 1
        maior_seq = max(maior_seq, seq_atual)

    return {'maior': maior_seq, 'total': total_seqs}


def atualizar_ciclos(numeros, ciclo_60, ciclo_pares, ciclo_impares, ciclo_primos):
    """Atualiza o estado dos 4 ciclos após um sorteio."""

    # Ciclo 60
    ciclo_60['vistos'].update(numeros)
    if ciclo_60['vistos'] == TODOS:
        ciclo_60['numero'] += 1
        ciclo_60['vistos'] = set()

    # Ciclo Pares
    pares_sorteio = numeros & PARES
    ciclo_pares['vistos'].update(pares_sorteio)
    if ciclo_pares['vistos'] == PARES:
        ciclo_pares['numero'] += 1
        ciclo_pares['vistos'] = set()

    # Ciclo Ímpares
    impares_sorteio = numeros & IMPARES
    ciclo_impares['vistos'].update(impares_sorteio)
    if ciclo_impares['vistos'] == IMPARES:
        ciclo_impares['numero'] += 1
        ciclo_impares['vistos'] = set()

    # Ciclo Primos
    primos_sorteio = numeros & PRIMOS
    ciclo_primos['vistos'].update(primos_sorteio)
    if ciclo_primos['vistos'] == PRIMOS:
        ciclo_primos['numero'] += 1
        ciclo_primos['vistos'] = set()


def inserir_resultados(resultados):
    """Insere os resultados no ClickHouse."""

    print(f"Inserindo {len(resultados)} registros...")

    # Preparar dados para inserção em lotes
    batch_size = 100

    for i in range(0, len(resultados), batch_size):
        batch = resultados[i:i+batch_size]

        values = []
        for r in batch:
            # Formatar arrays para ClickHouse
            numeros_str = '[' + ','.join(map(str, r['numeros'])) + ']'
            meta60_str = '[' + ','.join(map(str, r['meta_faltam_ciclo60'])) + ']'
            meta_pares_str = '[' + ','.join(map(str, r['meta_faltam_pares'])) + ']'
            meta_impares_str = '[' + ','.join(map(str, r['meta_faltam_impares'])) + ']'
            meta_primos_str = '[' + ','.join(map(str, r['meta_faltam_primos'])) + ']'

            value = f"""(
                {r['concurso']}, '{r['data']}', {numeros_str},
                {r['r1_freq_top20']},
                {r['r2_atraso_medio']}, {r['r2_atraso_max']},
                {r['r3_tendencia_quentes']},
                {r['r4_poisson_desvio']},
                {r['r5_pressao_faltantes']},
                {r['r6_hot']}, {r['r6_neutral']}, {r['r6_frio']},
                {r['r7_soma']}, '{r['r7_soma_classe']}',
                {r['r8_pares']}, {r['r8_impares']}, '{r['r8_padrao']}',
                {r['r9_primos']}, {r['r9_nao_primos']},
                {r['r10_q1']}, {r['r10_q2']}, {r['r10_q3']}, {r['r10_q4']}, '{r['r10_padrao']}',
                {r['r11_baixo']}, {r['r11_medio']}, {r['r11_alto']}, '{r['r11_padrao']}',
                {r['r12_l1']}, {r['r12_l2']}, {r['r12_l3']}, {r['r12_l4']}, {r['r12_l5']}, {r['r12_l6']}, '{r['r12_padrao']}',
                {r['r13_t0']}, {r['r13_t1']}, {r['r13_t2']}, {r['r13_t3']}, {r['r13_t4']}, {r['r13_t5']}, {r['r13_t6']}, {r['r13_t7']}, {r['r13_t8']}, {r['r13_t9']}, '{r['r13_padrao']}',
                {r['r14_tem_sequencia']}, {r['r14_maior_sequencia']}, {r['r14_total_sequencias']},
                {r['r15_ciclo_numero']}, {r['r15_faltam_antes']}, {r['r15_novos']}, {r['r15_repetidos']}, {r['r15_faltam_depois']},
                {r['r16_ciclo_numero']}, {r['r16_faltam_antes']}, {r['r16_novos']}, {r['r16_repetidos']}, {r['r16_faltam_depois']},
                {r['r17_ciclo_numero']}, {r['r17_faltam_antes']}, {r['r17_novos']}, {r['r17_repetidos']}, {r['r17_faltam_depois']},
                {r['r18_ciclo_numero']}, {r['r18_faltam_antes']}, {r['r18_novos']}, {r['r18_repetidos']}, {r['r18_faltam_depois']},
                '{r['r19_padrao']}',
                {meta60_str}, {meta_pares_str}, {meta_impares_str}, {meta_primos_str}
            )"""
            values.append(value)

        insert_sql = f"""
        INSERT INTO loterias.concurso_analise_evolutiva VALUES
        {','.join(values)}
        """

        success, out, err = execute_ddl(insert_sql)

        if not success:
            print(f"Erro no batch {i}: {err}")
            return False

        if (i + batch_size) % 500 == 0:
            print(f"Inseridos: {i + batch_size}")

    print("Inserção concluída com sucesso!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("CRIANDO TABELA DE ANÁLISE EVOLUTIVA")
    print("=" * 60)

    if create_table():
        print("\n" + "=" * 60)
        print("PROCESSANDO CONCURSOS")
        print("=" * 60)
        processar_concursos()
