"""
Gerador de Jogos Mega-Sena - Maximização de Budget
===================================================
Estratégia: Começar pelo maior jogo possível e ir descendo até consumir o máximo do budget.

FLUXO:
1. Pegar pool de números com melhor score individual (top 30-40)
2. Começar tentando gerar jogo com máximo de dezenas que cabe no budget
3. Ir reduzindo dezenas até 6 (mínimo)
4. Cada jogo deve passar nos filtros de conjunto (R4-R14)
5. Continuar até não caber mais nenhum jogo de 6 dezenas
"""

from clickhouse_client import ClickHouseClient
from config import TABELA_CUSTOS_OFICIAL
from itertools import combinations
import pandas as pd
import random

client = ClickHouseClient()


# =============================================================================
# CONFIGURAÇÕES PADRÃO DOS FILTROS
# =============================================================================
DEFAULT_CONFIG = {
    # Budget
    'budget': 1000.00,

    # R4 - Quadrantes (padrões aceitos)
    # Top 8 padrões mais frequentes historicamente (~65% dos sorteios)
    'quadrantes_aceitos': ['1-1-2-2', '2-1-2-1', '1-2-2-1', '1-2-1-2', '2-1-1-2', '2-2-1-1', '1-1-1-3', '0-2-2-2'],
    'max_quadrantes_vazios': 1,  # Máximo 1 quadrante vazio (mais restrito)
    'max_por_quadrante': 3,

    # R5 - Paridade
    # Top 5 padrões mais frequentes (~95% dos sorteios)
    'min_pares': 2,
    'max_pares': 4,
    'paridade_aceita': ['3P/3I', '4P/2I', '2P/4I', '5P/1I', '1P/5I'],

    # R6 - Faixas BMA
    # Top 8 padrões mais frequentes (~70% dos sorteios)
    'min_por_faixa': 1,
    'max_por_faixa': 4,
    'bma_aceito': ['2-2-2', '2-3-1', '3-2-1', '1-3-2', '2-1-3', '1-2-3', '3-1-2', '1-1-4'],

    # R7 - Linhas
    'min_linhas': 4,

    # R8 - Terminações
    'min_terminacoes': 5,

    # R9 - Soma
    'soma_min': 140,
    'soma_max': 210,
    'validar_soma': True,

    # R12 - H-N-F
    'min_hot': 2,
    'max_hot': 4,
    'min_neutral': 1,
    'max_neutral': 3,
    'min_cold': 0,
    'max_cold': 2,

    # R13 - Consecutivos
    'max_consecutivos': 2,

    # R14 - Freq. Quadrante (quadrantes prioritários)
    'freq_quad_prioritarios': None,

    # Pool e geração
    'pool_size': 35,

    # Pesos para score combinado
    'peso_score_individual': 0.6,
    'peso_aderencia': 0.4
}


# =============================================================================
# CACHE DE PADRÕES HISTÓRICOS
# =============================================================================
_padroes_cache = None

def get_padroes_historicos():
    """Busca e cacheia os padrões históricos mais frequentes."""
    global _padroes_cache

    if _padroes_cache is not None:
        return _padroes_cache

    # Quadrantes - top 10 padrões
    quad = client.query("""
        SELECT
            concat(toString(q1_count), '-', toString(q2_count), '-', toString(q3_count), '-', toString(q4_count)) as padrao,
            count() as freq,
            round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as pct
        FROM loterias.v_concurso_analise
        GROUP BY padrao
        ORDER BY freq DESC
        LIMIT 10
    """)

    # Paridade
    par = client.query("""
        SELECT
            concat(toString(pares_count), 'P/', toString(impares_count), 'I') as padrao,
            count() as freq,
            round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as pct
        FROM loterias.v_concurso_analise
        GROUP BY padrao
        ORDER BY freq DESC
    """)

    # BMA - top 10 padrões
    bma = client.query("""
        SELECT
            concat(toString(baixo_count), '-', toString(medio_count), '-', toString(alto_count)) as padrao,
            count() as freq,
            round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as pct
        FROM loterias.v_concurso_analise
        GROUP BY padrao
        ORDER BY freq DESC
        LIMIT 10
    """)

    # Consecutivos
    seq = client.query("""
        SELECT
            sequencias_consecutivas as padrao,
            count() as freq,
            round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 2) as pct
        FROM loterias.v_concurso_analise
        GROUP BY padrao
        ORDER BY freq DESC
    """)

    # Soma stats
    soma = client.query("""
        SELECT
            round(avg(soma), 1) as media,
            round(median(soma), 1) as mediana
        FROM loterias.v_concurso_analise
    """)

    _padroes_cache = {
        'quadrantes': dict(zip(quad['padrao'], quad['pct'])),
        'paridade': dict(zip(par['padrao'], par['pct'])),
        'bma': dict(zip(bma['padrao'], bma['pct'])),
        'consecutivos': dict(zip(seq['padrao'].astype(str), seq['pct'])),
        'soma_media': float(soma['media'].iloc[0]),
        'soma_mediana': float(soma['mediana'].iloc[0]),
        'top_quadrante': quad['padrao'].iloc[0],
        'top_paridade': par['padrao'].iloc[0],
        'top_bma': bma['padrao'].iloc[0],
        'top_consecutivo': int(seq['padrao'].iloc[0])
    }

    return _padroes_cache


def limpar_cache():
    """Limpa o cache de padrões históricos."""
    global _padroes_cache
    _padroes_cache = None


# =============================================================================
# FUNÇÕES DE CLASSIFICAÇÃO
# =============================================================================
def classificar_numero(n):
    """Classifica um número em quadrante, faixa e paridade."""
    # Quadrante
    if 1 <= n <= 15:
        quadrante = 'Q1'
    elif 16 <= n <= 30:
        quadrante = 'Q2'
    elif 31 <= n <= 45:
        quadrante = 'Q3'
    else:
        quadrante = 'Q4'

    # Faixa BMA
    if 1 <= n <= 20:
        faixa = 'B'
    elif 21 <= n <= 40:
        faixa = 'M'
    else:
        faixa = 'A'

    # Paridade
    paridade = 'P' if n % 2 == 0 else 'I'

    # Linha (1-10, 11-20, etc)
    linha = (n - 1) // 10 + 1

    # Terminação
    terminacao = n % 10

    return {
        'quadrante': quadrante,
        'faixa': faixa,
        'paridade': paridade,
        'linha': linha,
        'terminacao': terminacao
    }


def get_classificacao_hnf():
    """Busca classificação H-N-F de cada número."""
    try:
        df = client.query("""
            SELECT numero, classificacao, is_hot, is_neutral, is_cold
            FROM loterias.v_classificacao_hnf
        """)
        return {int(row['numero']): row['classificacao'] for _, row in df.iterrows()}
    except:
        return {}


# =============================================================================
# ANÁLISE DE JOGO
# =============================================================================
def analisar_jogo(numeros, scores_dict, hnf_dict=None):
    """Analisa um conjunto de números e retorna métricas completas."""
    n = sorted(numeros)
    padroes = get_padroes_historicos()

    # Classificar cada número
    classificacoes = [classificar_numero(x) for x in n]

    # R4 - Quadrantes
    quadrantes = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    for c in classificacoes:
        quadrantes[c['quadrante']] += 1
    padrao_quad = f"{quadrantes['Q1']}-{quadrantes['Q2']}-{quadrantes['Q3']}-{quadrantes['Q4']}"

    # R5 - Paridade
    pares = sum(1 for c in classificacoes if c['paridade'] == 'P')
    impares = len(n) - pares
    padrao_par = f"{pares}P/{impares}I"

    # R6 - Faixas BMA
    faixas = {'B': 0, 'M': 0, 'A': 0}
    for c in classificacoes:
        faixas[c['faixa']] += 1
    padrao_bma = f"{faixas['B']}-{faixas['M']}-{faixas['A']}"

    # R7 - Linhas
    linhas = set(c['linha'] for c in classificacoes)
    linhas_usadas = len(linhas)

    # R8 - Terminações
    terminacoes = set(c['terminacao'] for c in classificacoes)
    terminacoes_usadas = len(terminacoes)

    # R9 - Soma
    soma = sum(n)
    soma_ok = 150 <= soma <= 200

    # R12 - H-N-F
    hot_count = 0
    neutral_count = 0
    cold_count = 0
    if hnf_dict:
        for num in n:
            hnf = hnf_dict.get(num, 'N')
            if hnf == 'H':
                hot_count += 1
            elif hnf == 'N':
                neutral_count += 1
            else:
                cold_count += 1

    # R13 - Consecutivos
    consecutivos = sum(1 for i in range(len(n)-1) if n[i+1] == n[i] + 1)

    # Score total individual (soma dos scores individuais)
    score_individual = sum(scores_dict.get(x, 0) for x in n)

    # =========================================================================
    # CÁLCULO DO SCORE DE ADERÊNCIA (funciona para qualquer nº de dezenas)
    # =========================================================================
    n_dezenas = len(n)

    # Aderência Quadrantes (0-100) - baseada em equilíbrio
    # Ideal: distribuição equilibrada entre quadrantes (n_dezenas/4 por quadrante)
    ideal_por_quad = n_dezenas / 4.0
    desvio_quad = sum(abs(quadrantes[q] - ideal_por_quad) for q in quadrantes) / 4
    aderencia_quad = max(0, 100 - desvio_quad * 25)
    # Bonus se padrão existe no histórico
    if n_dezenas == 6 and padrao_quad in padroes['quadrantes']:
        aderencia_quad = max(aderencia_quad, padroes['quadrantes'][padrao_quad])

    # Aderência Paridade (0-100) - baseada em equilíbrio
    # Ideal: metade par, metade ímpar
    ideal_pares = n_dezenas / 2.0
    desvio_par = abs(pares - ideal_pares)
    aderencia_par = max(0, 100 - desvio_par * 30)
    # Bonus se padrão existe no histórico
    if n_dezenas == 6 and padrao_par in padroes['paridade']:
        aderencia_par = max(aderencia_par, padroes['paridade'][padrao_par])

    # Aderência BMA (0-100) - baseada em equilíbrio
    # Ideal: distribuição equilibrada entre faixas (n_dezenas/3 por faixa)
    ideal_por_faixa = n_dezenas / 3.0
    desvio_bma = sum(abs(faixas[f] - ideal_por_faixa) for f in faixas) / 3
    aderencia_bma = max(0, 100 - desvio_bma * 25)
    # Bonus se padrão existe no histórico
    if n_dezenas == 6 and padrao_bma in padroes['bma']:
        aderencia_bma = max(aderencia_bma, padroes['bma'][padrao_bma])

    # Aderência Consecutivos (0-100)
    # Ideal para 6 dez: 0-1 consecutivos, escalar para mais dezenas
    max_consec_ideal = max(1, n_dezenas // 6)
    if consecutivos <= max_consec_ideal:
        aderencia_seq = 100
    elif consecutivos <= max_consec_ideal + 1:
        aderencia_seq = 70
    elif consecutivos <= max_consec_ideal + 2:
        aderencia_seq = 40
    else:
        aderencia_seq = 10

    # Aderência Soma (0-100) - baseada em proximidade à soma ideal
    # Soma ideal escala com número de dezenas: 30.5 * n_dezenas
    soma_ideal = 30.5 * n_dezenas
    soma_mediana_ref = padroes['soma_mediana'] if n_dezenas == 6 else soma_ideal
    distancia_soma = abs(soma - soma_mediana_ref)
    # Normalizar distância pela escala (jogos maiores têm variação maior)
    distancia_normalizada = distancia_soma / (n_dezenas * 2)
    aderencia_soma = max(0, 100 - distancia_normalizada * 10)

    # Score de aderência total
    score_aderencia = (
        aderencia_par * 0.30 +
        aderencia_soma * 0.25 +
        aderencia_bma * 0.20 +
        aderencia_quad * 0.15 +
        aderencia_seq * 0.10
    )

    return {
        'numeros': n,
        'n_dezenas': len(n),
        'padrao_quad': padrao_quad,
        'padrao_par': padrao_par,
        'padrao_bma': padrao_bma,
        'linhas_usadas': linhas_usadas,
        'terminacoes_usadas': terminacoes_usadas,
        'soma': soma,
        'soma_ok': soma_ok,
        'consecutivos': consecutivos,
        'hot_count': hot_count,
        'neutral_count': neutral_count,
        'cold_count': cold_count,
        'score_individual': score_individual,
        'score_aderencia': round(score_aderencia, 2),
        'aderencia_quad': round(aderencia_quad, 2),
        'aderencia_par': round(aderencia_par, 2),
        'aderencia_bma': round(aderencia_bma, 2),
        'aderencia_seq': round(aderencia_seq, 2),
        'aderencia_soma': round(aderencia_soma, 2),
        'quadrantes': quadrantes,
        'faixas': faixas,
        'pares': pares
    }


# =============================================================================
# PADRÕES HISTÓRICOS MAIS FREQUENTES (para escalar filtros)
# =============================================================================
# Top padrões por frequência histórica (ordenados do mais ao menos frequente)
PADROES_QUADRANTES_TOP = ['1-1-2-2', '2-1-2-1', '1-2-2-1', '1-2-1-2', '2-1-1-2', '2-2-1-1', '1-1-1-3', '0-2-2-2']
PADROES_PARIDADE_TOP = ['3P/3I', '4P/2I', '2P/4I', '5P/1I', '1P/5I']
PADROES_BMA_TOP = ['2-2-2', '2-3-1', '3-2-1', '1-3-2', '2-1-3', '1-2-3', '3-1-2', '1-1-4']


def escalar_padrao(padrao, fator, tipo='quadrante'):
    """
    Escala um padrão de 6 dezenas para N dezenas.

    Exemplo: '1-1-2-2' (soma=6) com fator 1.5 (9 dezenas) -> '2-2-3-2' ou '1-2-3-3'
    """
    if tipo == 'quadrante':
        partes = [int(x) for x in padrao.split('-')]
        # Escalar proporcionalmente, arredondando
        escalado = [max(0, round(x * fator)) for x in partes]
        # Ajustar para que a soma seja exata
        n_dezenas = round(sum(partes) * fator)
        diff = n_dezenas - sum(escalado)
        # Distribuir diferença nos maiores valores
        while diff != 0:
            if diff > 0:
                idx = escalado.index(max(escalado))
                escalado[idx] += 1
                diff -= 1
            else:
                idx = escalado.index(max(escalado))
                if escalado[idx] > 0:
                    escalado[idx] -= 1
                    diff += 1
                else:
                    break
        return '-'.join(str(x) for x in escalado)

    elif tipo == 'paridade':
        # '3P/3I' -> escalar pares e ímpares
        pares = int(padrao.split('P')[0])
        impares = int(padrao.split('/')[1].replace('I', ''))
        n_original = pares + impares
        n_novo = round(n_original * fator)
        pares_novo = round(pares * fator)
        impares_novo = n_novo - pares_novo
        return f'{pares_novo}P/{impares_novo}I'

    elif tipo == 'bma':
        partes = [int(x) for x in padrao.split('-')]
        escalado = [max(0, round(x * fator)) for x in partes]
        n_dezenas = round(sum(partes) * fator)
        diff = n_dezenas - sum(escalado)
        while diff != 0:
            if diff > 0:
                idx = escalado.index(max(escalado))
                escalado[idx] += 1
                diff -= 1
            else:
                idx = escalado.index(max(escalado))
                if escalado[idx] > 0:
                    escalado[idx] -= 1
                    diff += 1
                else:
                    break
        return '-'.join(str(x) for x in escalado)

    return padrao


def expandir_padroes_aceitos(padroes_selecionados, n_dezenas, tipo='quadrante'):
    """
    Expande os padrões aceitos baseado no número de dezenas.

    - 6 dezenas: usa apenas os padrões selecionados
    - 7-12 dezenas: adiciona 2º padrão mais frequente
    - 13-15 dezenas: adiciona 3º padrão
    - 16+ dezenas: adiciona 4º padrão

    Também escala os padrões proporcionalmente.
    """
    if not padroes_selecionados:
        return None

    fator = n_dezenas / 6.0

    # Determinar quantos padrões extras liberar
    if n_dezenas <= 6:
        extras = 0
    elif n_dezenas <= 12:
        extras = 1  # Libera 2º colocado
    elif n_dezenas <= 15:
        extras = 2  # Libera 3º colocado
    else:
        extras = 3  # Libera 4º colocado

    # Obter lista de padrões top por tipo
    if tipo == 'quadrante':
        padroes_top = PADROES_QUADRANTES_TOP
    elif tipo == 'paridade':
        padroes_top = PADROES_PARIDADE_TOP
    else:  # bma
        padroes_top = PADROES_BMA_TOP

    # Começar com padrões selecionados pelo usuário
    padroes_expandidos = set(padroes_selecionados)

    # Adicionar padrões extras baseado no ranking
    for padrao in padroes_top:
        if extras <= 0:
            break
        if padrao not in padroes_expandidos:
            padroes_expandidos.add(padrao)
            extras -= 1

    # Escalar todos os padrões para o número de dezenas
    if n_dezenas != 6:
        padroes_escalados = set()
        for padrao in padroes_expandidos:
            escalado = escalar_padrao(padrao, fator, tipo)
            padroes_escalados.add(escalado)
        return list(padroes_escalados)

    return list(padroes_expandidos)


# =============================================================================
# AJUSTE DE FILTROS POR NÚMERO DE DEZENAS
# =============================================================================
def ajustar_config_por_dezenas(config, n_dezenas):
    """
    Ajusta os filtros de config proporcionalmente ao número de dezenas.

    Os filtros padrão são calibrados para 6 dezenas. Esta função escala
    os valores para jogos com mais dezenas.
    """
    config_ajustado = config.copy()

    # Fator de escala baseado em 6 dezenas
    fator = n_dezenas / 6.0

    # R4 - Quadrantes: expandir e escalar padrões aceitos
    if config.get('quadrantes_aceitos'):
        config_ajustado['quadrantes_aceitos'] = expandir_padroes_aceitos(
            config['quadrantes_aceitos'], n_dezenas, 'quadrante'
        )

    # R5 - Paridade: expandir e escalar padrões aceitos
    if config.get('paridade_aceita'):
        config_ajustado['paridade_aceita'] = expandir_padroes_aceitos(
            config['paridade_aceita'], n_dezenas, 'paridade'
        )

    # R6 - BMA: expandir e escalar padrões aceitos
    if config.get('bma_aceito'):
        config_ajustado['bma_aceito'] = expandir_padroes_aceitos(
            config['bma_aceito'], n_dezenas, 'bma'
        )

    # R5 - Paridade: escalar min/max pares proporcionalmente (fallback)
    min_pares_base = config.get('min_pares', 2)
    max_pares_base = config.get('max_pares', 4)
    config_ajustado['min_pares'] = max(1, int(min_pares_base * fator))
    config_ajustado['max_pares'] = min(n_dezenas, int(max_pares_base * fator) + 1)

    # R6 - BMA: escalar max_por_faixa
    max_por_faixa_base = config.get('max_por_faixa', 4)
    config_ajustado['max_por_faixa'] = min(n_dezenas, int(max_por_faixa_base * fator) + 1)

    # R4 - Quadrantes: escalar max_por_quadrante
    max_por_quad_base = config.get('max_por_quadrante', 3)
    config_ajustado['max_por_quadrante'] = min(n_dezenas, int(max_por_quad_base * fator) + 1)

    # R9 - Soma: escalar proporcionalmente
    # Soma média esperada = 30.5 * n_dezenas (média de 1-60)
    soma_media_esperada = 30.5 * n_dezenas
    # Margem de ±25% da média
    margem = soma_media_esperada * 0.25
    config_ajustado['soma_min'] = int(soma_media_esperada - margem)
    config_ajustado['soma_max'] = int(soma_media_esperada + margem)

    # R12 - H-N-F: escalar max valores
    config_ajustado['max_hot'] = min(n_dezenas, int(config.get('max_hot', 6) * fator))
    config_ajustado['max_neutral'] = min(n_dezenas, int(config.get('max_neutral', 6) * fator))
    config_ajustado['max_cold'] = min(n_dezenas, int(config.get('max_cold', 6) * fator))

    # R13 - Consecutivos: permitir mais para jogos maiores
    max_consec_base = config.get('max_consecutivos', 2)
    config_ajustado['max_consecutivos'] = max(max_consec_base, int(max_consec_base * fator))

    return config_ajustado


# =============================================================================
# VALIDAÇÃO DE JOGO COM FILTROS DE CONJUNTO
# =============================================================================
def validar_jogo(analise, config):
    """Valida se um jogo atende aos critérios de conjunto (R4-R14)."""

    # Ajustar config baseado no número de dezenas do jogo
    n_dezenas = analise.get('n_dezenas', 6)
    config_adj = ajustar_config_por_dezenas(config, n_dezenas) if n_dezenas > 6 else config

    # R4 - Quadrantes
    # Usar padrões expandidos e escalados do config_adj
    if config_adj.get('quadrantes_aceitos'):
        if analise['padrao_quad'] not in config_adj['quadrantes_aceitos']:
            return False
    else:
        quadrantes_vazios = sum(1 for v in analise['quadrantes'].values() if v == 0)
        if quadrantes_vazios > config_adj.get('max_quadrantes_vazios', 2):
            return False
        if max(analise['quadrantes'].values()) > config_adj.get('max_por_quadrante', 3):
            return False

    # R5 - Paridade
    # Usar padrões expandidos e escalados do config_adj
    if config_adj.get('paridade_aceita'):
        if analise['padrao_par'] not in config_adj['paridade_aceita']:
            return False
    else:
        if analise['pares'] < config_adj.get('min_pares', 2) or analise['pares'] > config_adj.get('max_pares', 4):
            return False

    # R6 - Faixas BMA
    # Usar padrões expandidos e escalados do config_adj
    if config_adj.get('bma_aceito'):
        if analise['padrao_bma'] not in config_adj['bma_aceito']:
            return False
    else:
        if min(analise['faixas'].values()) < config_adj.get('min_por_faixa', 0):
            return False
        if max(analise['faixas'].values()) > config_adj.get('max_por_faixa', 4):
            return False

    # R7 - Linhas
    if analise['linhas_usadas'] < config_adj.get('min_linhas', 4):
        return False

    # R8 - Terminações
    if analise['terminacoes_usadas'] < config_adj.get('min_terminacoes', 5):
        return False

    # R9 - Soma (usando valores ajustados)
    if config.get('validar_soma', True):
        soma_min = config_adj.get('soma_min', 140)
        soma_max = config_adj.get('soma_max', 210)
        if analise['soma'] < soma_min or analise['soma'] > soma_max:
            return False

    # R12 - H-N-F (usando valores ajustados)
    if analise['hot_count'] < config_adj.get('min_hot', 0) or analise['hot_count'] > config_adj.get('max_hot', 6):
        return False
    if analise['neutral_count'] < config_adj.get('min_neutral', 0) or analise['neutral_count'] > config_adj.get('max_neutral', 6):
        return False
    if analise['cold_count'] < config_adj.get('min_cold', 0) or analise['cold_count'] > config_adj.get('max_cold', 6):
        return False

    # R13 - Consecutivos (usando valor ajustado)
    if analise['consecutivos'] > config_adj.get('max_consecutivos', 2):
        return False

    # R14 - Freq. Quadrante (verificar se tem pelo menos 1 número dos quadrantes prioritários)
    if config.get('freq_quad_prioritarios'):
        quads_prioritarios = config['freq_quad_prioritarios']
        tem_prioritario = False
        for q in quads_prioritarios:
            q_key = q.split(' ')[0] if ' ' in q else q  # Extrair Q1, Q2, etc
            if analise['quadrantes'].get(q_key, 0) > 0:
                tem_prioritario = True
                break
        if not tem_prioritario:
            return False

    return True


# =============================================================================
# GERADOR COM MAXIMIZAÇÃO DE BUDGET
# =============================================================================
def gerar_jogos_budget(budget, config=None, verbose=True):
    """
    Gera jogos maximizando o uso do budget.

    Estratégia:
    1. Começar pelo maior jogo possível (20 dezenas)
    2. Se não cabe, tenta 19, 18, ... até 6
    3. Quando gera um jogo, subtrai do budget e repete
    4. Para até não caber mais jogo de 6 dezenas

    Args:
        budget: Valor total disponível em R$
        config: Configurações de filtros
        verbose: Se True, imprime progresso

    Returns:
        Lista de jogos gerados com análise completa
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()

    if verbose:
        print(f"🎰 GERANDO JOGOS - MAXIMIZAÇÃO DE BUDGET")
        print("=" * 80)
        print(f"   💰 Budget: R$ {budget:,.2f}")

    # 1. Buscar pool de números com melhor score
    # Pool maior para jogos com mais dezenas (mínimo 35, máximo 50)
    # Quanto maior o budget, mais números no pool para diversificar
    base_pool = config.get('pool_size', 35)
    # Se budget permite jogos grandes (>10 dez), aumentar pool
    if budget >= TABELA_CUSTOS_OFICIAL.get(12, 5544):
        pool_size = min(50, base_pool + 10)  # Até 50 números
    elif budget >= TABELA_CUSTOS_OFICIAL.get(9, 504):
        pool_size = min(45, base_pool + 5)   # Até 45 números
    else:
        pool_size = base_pool

    if verbose:
        print(f"\n1️⃣ Buscando top {pool_size} números por score individual...")

    pool_df = client.query(f"""
        SELECT numero, score_individual
        FROM loterias.v_score_individual
        ORDER BY score_individual DESC
        LIMIT {pool_size}
    """)

    pool = [int(x) for x in pool_df['numero'].tolist()]
    scores_dict = {int(k): float(v) for k, v in zip(pool_df['numero'], pool_df['score_individual'])}

    if verbose:
        print(f"   Pool: {sorted(pool)}")

    # 2. Buscar classificação H-N-F
    hnf_dict = get_classificacao_hnf()

    # 3. Gerar jogos maximizando budget
    if verbose:
        print(f"\n2️⃣ Gerando jogos para maximizar budget...")

    jogos_gerados = []
    budget_restante = budget
    numeros_usados_recentemente = set()  # Para evitar repetição excessiva

    while budget_restante >= TABELA_CUSTOS_OFICIAL[6]:  # Mínimo é jogo de 6 dezenas
        jogo_gerado = False

        # Tentar do maior para o menor
        for n_dezenas in range(20, 5, -1):
            custo = TABELA_CUSTOS_OFICIAL.get(n_dezenas, float('inf'))

            if custo > budget_restante:
                continue

            # Tentar gerar um jogo válido com n_dezenas
            # Primeira tentativa: com padrões escalados (mais restrito)
            usou_fallback = False
            jogo = gerar_um_jogo(
                n_dezenas=n_dezenas,
                pool=pool,
                scores_dict=scores_dict,
                hnf_dict=hnf_dict,
                config=config,
                numeros_usados=numeros_usados_recentemente,
                max_tentativas=300
            )

            # Segunda tentativa: sem padrões específicos (só validação por range)
            if not jogo:
                usou_fallback = True
                config_relaxado = config.copy()
                config_relaxado['quadrantes_aceitos'] = None
                config_relaxado['paridade_aceita'] = None
                config_relaxado['bma_aceito'] = None
                jogo = gerar_um_jogo(
                    n_dezenas=n_dezenas,
                    pool=pool,
                    scores_dict=scores_dict,
                    hnf_dict=hnf_dict,
                    config=config_relaxado,
                    numeros_usados=numeros_usados_recentemente,
                    max_tentativas=200
                )

            if jogo:
                jogo['custo'] = custo
                jogo['usou_fallback'] = usou_fallback
                jogos_gerados.append(jogo)
                budget_restante -= custo

                # Marcar números como usados recentemente (para diversificar)
                for num in jogo['numeros']:
                    numeros_usados_recentemente.add(num)

                # Limpar números usados a cada 5 jogos para permitir reuso
                if len(jogos_gerados) % 5 == 0:
                    numeros_usados_recentemente.clear()

                if verbose:
                    print(f"   ✅ Jogo #{len(jogos_gerados)}: {n_dezenas} dezenas | R$ {custo:,.2f} | Restante: R$ {budget_restante:,.2f}")

                jogo_gerado = True
                break

        if not jogo_gerado:
            # Não conseguiu gerar nenhum jogo válido, encerra
            if verbose:
                print(f"   ⚠️ Não foi possível gerar mais jogos válidos com os filtros atuais.")
            break

    # 4. Resumo
    if verbose:
        custo_total = sum(j['custo'] for j in jogos_gerados)
        print(f"\n" + "=" * 80)
        print(f"✅ GERAÇÃO COMPLETA!")
        print(f"   📊 Jogos gerados: {len(jogos_gerados)}")
        print(f"   💰 Custo total: R$ {custo_total:,.2f}")
        print(f"   💵 Sobra: R$ {budget_restante:,.2f}")

        # Distribuição por dezenas
        dist = {}
        for j in jogos_gerados:
            nd = j['n_dezenas']
            dist[nd] = dist.get(nd, 0) + 1
        print(f"   📈 Distribuição: {dict(sorted(dist.items(), reverse=True))}")

    return jogos_gerados


def gerar_um_jogo(n_dezenas, pool, scores_dict, hnf_dict, config, numeros_usados=None, max_tentativas=500):
    """
    Gera um único jogo válido com n_dezenas.

    ESTRATÉGIA CHAVE: O sorteio SEMPRE é de 6 números.
    - Jogo de 6 dezenas: cobre 1 combinação
    - Jogo de 16 dezenas: cobre C(16,6) = 8.008 combinações

    Por isso, jogos maiores DEVEM:
    1. SEMPRE incluir os TOP 6 números (garantir qualidade base)
    2. Adicionar números extras para cobrir mais combinações
    3. Manter boa distribuição para atender filtros

    Score de jogos maiores deve ser >= jogos menores (mais cobertura = melhor)
    """
    if numeros_usados is None:
        numeros_usados = set()

    # Pool disponível (priorizar números não usados recentemente)
    pool_disponivel = [n for n in pool if n not in numeros_usados]
    if len(pool_disponivel) < n_dezenas:
        pool_disponivel = pool  # Se não tem suficiente, usa o pool completo

    # Ordenar pool por score (do maior para menor)
    pool_ordenado = sorted(pool_disponivel, key=lambda x: scores_dict.get(x, 0), reverse=True)

    # Separar pool por quadrante
    pool_por_quad = {
        'Q1': [n for n in pool_disponivel if 1 <= n <= 15],
        'Q2': [n for n in pool_disponivel if 16 <= n <= 30],
        'Q3': [n for n in pool_disponivel if 31 <= n <= 45],
        'Q4': [n for n in pool_disponivel if 46 <= n <= 60],
    }

    for tentativa in range(max_tentativas):
        numeros = []

        # PASSO 1: SEMPRE começar com os TOP 6 números do pool (base de qualidade)
        # Isso garante que o jogo tenha no mínimo a mesma qualidade de um jogo de 6
        top_6 = pool_ordenado[:6]
        numeros.extend(top_6)

        # PASSO 2: Se precisa de mais dezenas, adicionar mantendo distribuição
        if n_dezenas > 6:
            # Verificar quais quadrantes ainda precisam de números
            quads_presentes = {
                'Q1': sum(1 for n in numeros if 1 <= n <= 15),
                'Q2': sum(1 for n in numeros if 16 <= n <= 30),
                'Q3': sum(1 for n in numeros if 31 <= n <= 45),
                'Q4': sum(1 for n in numeros if 46 <= n <= 60),
            }

            # Para jogos grandes, garantir pelo menos 1 número em cada quadrante
            # Priorizar quadrantes vazios
            for quad, count in quads_presentes.items():
                if count == 0 and len(numeros) < n_dezenas:
                    # Pegar o melhor número deste quadrante que não está no jogo
                    candidatos = [n for n in pool_por_quad[quad] if n not in numeros]
                    if candidatos:
                        # Ordenar por score e pegar o melhor
                        candidatos_ord = sorted(candidatos, key=lambda x: scores_dict.get(x, 0), reverse=True)
                        numeros.append(candidatos_ord[0])

            # Completar com próximos melhores números (mantendo diversidade)
            while len(numeros) < n_dezenas:
                # Pegar próximos melhores números que não estão no jogo
                disponiveis = [n for n in pool_ordenado if n not in numeros]
                if not disponiveis:
                    break

                # Adicionar o próximo melhor
                numeros.append(disponiveis[0])

                # A cada 3 números adicionados, verificar distribuição
                if len(numeros) % 3 == 0:
                    # Verificar se algum quadrante está muito vazio
                    quads_atual = {
                        'Q1': sum(1 for n in numeros if 1 <= n <= 15),
                        'Q2': sum(1 for n in numeros if 16 <= n <= 30),
                        'Q3': sum(1 for n in numeros if 31 <= n <= 45),
                        'Q4': sum(1 for n in numeros if 46 <= n <= 60),
                    }
                    # Se algum quadrante está vazio, priorizar
                    for quad, count in quads_atual.items():
                        if count == 0 and len(numeros) < n_dezenas:
                            candidatos = [n for n in pool_por_quad[quad] if n not in numeros]
                            if candidatos:
                                candidatos_ord = sorted(candidatos, key=lambda x: scores_dict.get(x, 0), reverse=True)
                                numeros.append(candidatos_ord[0])
                                break

        if len(numeros) < n_dezenas:
            continue

        numeros = sorted(list(set(numeros))[:n_dezenas])

        if len(numeros) < n_dezenas:
            continue

        # Analisar e validar
        analise = analisar_jogo(numeros, scores_dict, hnf_dict)

        if validar_jogo(analise, config):
            # =================================================================
            # CÁLCULO DO SCORE COMBINADO
            # =================================================================
            # O score deve AUMENTAR com mais dezenas porque:
            # - Mais dezenas = mais combinações de 6 cobertas
            # - C(6,6)=1, C(10,6)=210, C(16,6)=8008, C(20,6)=38760
            #
            # Score = (Qualidade dos números) + (Bônus de cobertura)
            # =================================================================

            peso_ind = config.get('peso_score_individual', 0.5)
            peso_ader = config.get('peso_aderencia', 0.3)
            peso_cobertura = config.get('peso_cobertura', 0.2)

            # 1. Score de qualidade: média do score dos números
            media_score_numeros = analise['score_individual'] / n_dezenas
            max_score_possivel = max(scores_dict.values())
            score_qualidade = (media_score_numeros / max_score_possivel) * 100 if max_score_possivel > 0 else 0

            # 2. Score de aderência (distribuição)
            score_aderencia = analise['score_aderencia']

            # 3. Bônus de cobertura: mais dezenas = mais combinações
            # Escala logarítmica para não explodir
            # C(n,6) para n dezenas vs C(6,6)=1
            from math import comb, log10
            combinacoes = comb(n_dezenas, 6)
            # Bônus: 0 para 6 dez, ~20 para 10 dez, ~40 para 16 dez, ~50 para 20 dez
            bonus_cobertura = min(50, log10(combinacoes) * 15) if combinacoes > 1 else 0

            # Score final: média ponderada + bônus de cobertura
            score_base = score_qualidade * peso_ind + score_aderencia * peso_ader
            # Normalizar para que jogo de 6 com score 70 continue sendo ~70
            # e jogo de 16 com mesma qualidade seja ~70 + bônus
            analise['score_combinado'] = round(
                score_base / (peso_ind + peso_ader) * (1 - peso_cobertura) +
                bonus_cobertura * peso_cobertura +
                score_base / (peso_ind + peso_ader) * peso_cobertura,
                2
            )

            # Simplificando: Score = qualidade_base + pequeno_bonus_por_cobertura
            # Jogo de 6: ~70 + 0 = 70
            # Jogo de 16 com mesmos top números: ~70 + 8 = 78
            analise['score_combinado'] = round(
                (score_qualidade * 0.6 + score_aderencia * 0.4) +
                bonus_cobertura * 0.15,  # Pequeno bônus por cobertura
                2
            )

            analise['bonus_cobertura'] = round(bonus_cobertura, 2)
            analise['combinacoes_6'] = combinacoes

            return analise

    return None


# =============================================================================
# FUNÇÃO WRAPPER PARA COMPATIBILIDADE
# =============================================================================
def gerar_jogos(n_jogos=10, pool_size=25, config=None, verbose=True):
    """
    Wrapper de compatibilidade - agora usa maximização de budget.

    Se config tiver 'budget', usa gerar_jogos_budget.
    Senão, usa lógica antiga de n_jogos fixos.
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()

    # Se tem budget definido, usar nova lógica
    if config.get('budget'):
        return gerar_jogos_budget(config['budget'], config, verbose)

    # Lógica antiga (fallback)
    config['pool_size'] = pool_size

    if verbose:
        print(f"🎰 GERANDO {n_jogos} JOGOS (modo legacy)")

    pool_df = client.query(f"""
        SELECT numero, score_individual
        FROM loterias.v_score_individual
        ORDER BY score_individual DESC
        LIMIT {pool_size}
    """)

    pool = [int(x) for x in pool_df['numero'].tolist()]
    scores_dict = {int(k): float(v) for k, v in zip(pool_df['numero'], pool_df['score_individual'])}
    hnf_dict = get_classificacao_hnf()

    jogos = []
    for i in range(n_jogos):
        jogo = gerar_um_jogo(
            n_dezenas=6,
            pool=pool,
            scores_dict=scores_dict,
            hnf_dict=hnf_dict,
            config=config,
            max_tentativas=1000
        )
        if jogo:
            jogo['custo'] = TABELA_CUSTOS_OFICIAL[6]
            jogos.append(jogo)

    return jogos


# =============================================================================
# FUNÇÕES DE EXIBIÇÃO
# =============================================================================
def exibir_jogos(jogos, mostrar_detalhes=True):
    """Exibe os jogos de forma formatada."""
    print("\n" + "=" * 80)
    print("🎯 JOGOS RECOMENDADOS")
    print("=" * 80)

    custo_total = 0
    jogos_fallback = 0
    for i, jogo in enumerate(jogos, 1):
        numeros_str = '-'.join(f"{n:02d}" for n in jogo['numeros'])
        custo = jogo.get('custo', TABELA_CUSTOS_OFICIAL.get(jogo['n_dezenas'], 0))
        custo_total += custo
        usou_fallback = jogo.get('usou_fallback', False)
        if usou_fallback:
            jogos_fallback += 1

        # Indicador de fallback
        fallback_str = " ⚠️ FALLBACK" if usou_fallback else ""
        print(f"\n🎰 JOGO #{i}: [{numeros_str}] ({jogo['n_dezenas']} dezenas){fallback_str}")
        print(f"   💰 Custo: R$ {custo:,.2f}")
        print(f"   📊 Score Combinado: {jogo['score_combinado']:.2f}")

        if mostrar_detalhes:
            print(f"   📋 Análise:")
            print(f"      R4 Quadrantes: {jogo['padrao_quad']}")
            print(f"      R5 Paridade:   {jogo['padrao_par']}")
            print(f"      R6 Faixas:     {jogo['padrao_bma']}")
            print(f"      R7 Linhas:     {jogo['linhas_usadas']}")
            print(f"      R8 Terminações:{jogo['terminacoes_usadas']}")
            print(f"      R9 Soma:       {jogo['soma']} {'✅' if jogo['soma_ok'] else '⚠️'}")
            print(f"      R12 H-N-F:     {jogo['hot_count']}H-{jogo['neutral_count']}N-{jogo['cold_count']}F")
            print(f"      R13 Consec.:   {jogo['consecutivos']}")

    print(f"\n" + "=" * 80)
    print(f"💰 CUSTO TOTAL: R$ {custo_total:,.2f}")
    if jogos_fallback > 0:
        print(f"⚠️  JOGOS COM FALLBACK: {jogos_fallback} de {len(jogos)} (padrões específicos não atendidos)")


def jogos_para_dataframe(jogos):
    """Converte lista de jogos para DataFrame."""
    rows = []
    for i, jogo in enumerate(jogos, 1):
        row = {
            'rank': i,
            'numeros': '-'.join(f"{n:02d}" for n in jogo['numeros']),
            'n_dezenas': jogo['n_dezenas'],
            'custo': jogo.get('custo', TABELA_CUSTOS_OFICIAL.get(jogo['n_dezenas'], 0)),
            'score_combinado': jogo['score_combinado'],
            'score_individual': jogo['score_individual'],
            'score_aderencia': jogo['score_aderencia'],
            'quadrantes': jogo['padrao_quad'],
            'paridade': jogo['padrao_par'],
            'faixas_bma': jogo['padrao_bma'],
            'linhas': jogo['linhas_usadas'],
            'terminacoes': jogo['terminacoes_usadas'],
            'soma': jogo['soma'],
            'hot': jogo['hot_count'],
            'neutral': jogo['neutral_count'],
            'fallback': jogo.get('usou_fallback', False),
            'cold': jogo['cold_count'],
            'consecutivos': jogo['consecutivos']
        }

        # Adicionar cada número separadamente
        for j, num in enumerate(jogo['numeros'], 1):
            row[f'n{j}'] = num

        rows.append(row)

    return pd.DataFrame(rows)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    # Teste com budget
    config = DEFAULT_CONFIG.copy()
    config['budget'] = 1000.00  # R$ 1.000
    config['pool_size'] = 35

    # Gerar jogos
    jogos = gerar_jogos_budget(
        budget=config['budget'],
        config=config,
        verbose=True
    )

    # Exibir jogos
    exibir_jogos(jogos, mostrar_detalhes=True)
