#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                MEGA-SENA - DASHBOARD DE ANÁLISE ESTATÍSTICA                  ║
║                         Interface Web Interativa                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from collections import Counter

from config import BUDGET_TOTAL, TABELA_CUSTOS_OFICIAL, PROBABILIDADES
from data_loader import MegaSenaDataLoader, load_data
from statistical_analysis import MegaSenaAnalyzer

# ============================================================================
# TABELA OFICIAL DA CAIXA
# ============================================================================

TABELA_CAIXA = {
    6: {"valor": 6.00, "prob_sena": "1 em 50.063.860", "prob_quina": "1 em 154.518", "prob_quadra": "1 em 2.332"},
    7: {"valor": 42.00, "prob_sena": "1 em 7.151.980", "prob_quina": "1 em 44.981", "prob_quadra": "1 em 1.038"},
    8: {"valor": 168.00, "prob_sena": "1 em 1.787.995", "prob_quina": "1 em 17.192", "prob_quadra": "1 em 539"},
    9: {"valor": 504.00, "prob_sena": "1 em 595.998", "prob_quina": "1 em 7.791", "prob_quadra": "1 em 312"},
    10: {"valor": 1260.00, "prob_sena": "1 em 238.399", "prob_quina": "1 em 3.973", "prob_quadra": "1 em 195"},
    11: {"valor": 2772.00, "prob_sena": "1 em 108.363", "prob_quina": "1 em 2.211", "prob_quadra": "1 em 129"},
    12: {"valor": 5544.00, "prob_sena": "1 em 54.182", "prob_quina": "1 em 1.317", "prob_quadra": "1 em 90"},
    13: {"valor": 10296.00, "prob_sena": "1 em 29.175", "prob_quina": "1 em 828", "prob_quadra": "1 em 65"},
    14: {"valor": 18018.00, "prob_sena": "1 em 16.671", "prob_quina": "1 em 544", "prob_quadra": "1 em 48"},
    15: {"valor": 30030.00, "prob_sena": "1 em 10.003", "prob_quina": "1 em 370", "prob_quadra": "1 em 37"},
    16: {"valor": 48048.00, "prob_sena": "1 em 6.252", "prob_quina": "1 em 260", "prob_quadra": "1 em 29"},
    17: {"valor": 74256.00, "prob_sena": "1 em 4.045", "prob_quina": "1 em 188", "prob_quadra": "1 em 23"},
    18: {"valor": 111384.00, "prob_sena": "1 em 2.697", "prob_quina": "1 em 139", "prob_quadra": "1 em 19"},
    19: {"valor": 162792.00, "prob_sena": "1 em 1.845", "prob_quina": "1 em 105", "prob_quadra": "1 em 16"},
    20: {"valor": 232560.00, "prob_sena": "1 em 1.292", "prob_quina": "1 em 81", "prob_quadra": "1 em 13"},
}

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Mega-Sena - Análise Estatística",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        padding: 0 2rem;
        font-size: 1.1rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .explicacao-box {
        background-color: #f0f8ff;
        border-left: 5px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .justificativa-box {
        background-color: #fffaf0;
        border-left: 5px solid #ffa500;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def carregar_dados_arquivo(file):
    """Carrega dados de arquivo CSV ou Excel."""
    import tempfile
    import os

    try:
        # Detectar tipo de arquivo pela extensão
        file_name = file.name.lower()

        if file_name.endswith('.csv'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                tmp.write(file.getvalue())
                tmp_path = tmp.name
            df = load_data('csv', tmp_path)
            os.unlink(tmp_path)  # Limpar arquivo temporário
            return df

        elif file_name.endswith(('.xlsx', '.xls')):
            suffix = '.xlsx' if file_name.endswith('.xlsx') else '.xls'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file.getvalue())
                tmp_path = tmp.name
            df = load_data('excel', tmp_path)
            os.unlink(tmp_path)  # Limpar arquivo temporário
            return df
        else:
            st.error("Formato não suportado. Use arquivos .csv, .xlsx ou .xls")
            return None

    except Exception as e:
        st.error(f"""
        ❌ **Erro ao carregar arquivo:**

        {str(e)}

        **Formato esperado:**
        - Colunas: Concurso, Data, D1, D2, D3, D4, D5, D6
        - Ou: Número, Data, Bola1, Bola2, Bola3, Bola4, Bola5, Bola6
        - Valores das dezenas entre 1 e 60

        **Dica:** Use dados de demonstração para testar primeiro!
        """)
        return None

@st.cache_data
def carregar_dados_sinteticos():
    """Carrega dados sintéticos/demonstração com cache."""
    return load_data('synthetic')

def explicar_metrica(metrica):
    """Retorna explicação detalhada de cada métrica."""
    explicacoes = {
        "frequencia": """
        ### 🔢 Como calculamos a Frequência

        **Fórmula:** Contagem simples de aparições de cada número no histórico

        **Interpretação:**
        - Números que aparecem mais = maior frequência histórica
        - Baseado na **Lei dos Grandes Números**: ao longo do tempo, todos os números tendem a aparecer com frequência similar
        - **MAS ATENÇÃO**: cada sorteio é independente!

        **Exemplo:** Se o número 23 apareceu 150 vezes em 1000 sorteios, sua frequência é 15%
        """,

        "hot_cold": """
        ### 🔥❄️ Como calculamos Hot/Cold (Temperatura)

        **Hot Numbers (Quentes):**
        - Contamos quantas vezes cada número apareceu nos **últimos 10 sorteios**
        - Números com 3+ aparições = muito quentes

        **Cold Numbers (Frios/Atrasados):**
        - Calculamos quantos sorteios se passaram desde a última aparição
        - Atraso > 30 concursos = muito frio

        **Por que isso importa?**
        - Hot numbers podem estar em "streak" (sequência)
        - Cold numbers podem estar "devendo" aparecer (regressão à média)

        **Exemplo:** Número 45 apareceu 4 vezes nos últimos 10 jogos = HOT 🔥
        """,

        "paridade": """
        ### ⚖️ Como calculamos Par/Ímpar

        **Método:**
        1. Para cada sorteio, contamos quantos números são pares e ímpares
        2. Identificamos os padrões mais comuns (ex: 3P-3I, 4P-2I, 2P-4I)

        **Padrão Estatisticamente Mais Comum:**
        - **3 Pares + 3 Ímpares** (equilíbrio perfeito)
        - Ocorre em ~32% dos sorteios

        **Por que isso importa?**
        - Jogos com 6 pares ou 6 ímpares são RAROS (< 3% cada)
        - O equilíbrio é a regra, não a exceção

        **Exemplo:** 02, 15, 23, 34, 41, 58 = 3P (02,34,58) + 3I (15,23,41) ✅
        """,

        "alto_baixo": """
        ### 📊 Como calculamos Baixo/Médio/Alto

        **Divisão em 3 Faixas:**
        - **Baixos:** 1 a 20 (primeira faixa)
        - **Médios:** 21 a 40 (faixa intermediária)
        - **Altos:** 41 a 60 (última faixa)

        **Análise:**
        - Contamos quantos números de cada faixa aparecem em cada sorteio
        - Padrão mais comum: **2 de cada faixa** (equilíbrio perfeito: 2B-2M-2A)
        - Também são comuns padrões próximos como 2B-3M-1A, 1B-2M-3A, etc.

        **Por que isso importa?**
        - Extremos (6 números de uma única faixa) são extremamente raros
        - A tendência é distribuição equilibrada entre as 3 faixas
        - Ajuda a evitar concentração em apenas uma parte do volante

        **Exemplo:** 05, 15, 28, 35, 42, 58 = 2 Baixos (05,15) + 2 Médios (28,35) + 2 Altos (42,58) ✅
        """,

        "quadrantes": """
        ### 🎯 Como calculamos os Quadrantes

        **Layout do Volante 6x10:**
        ```
        Q1: 01-05  06-10 :Q2
            11-15  16-20
            21-25  26-30

        Q3: 31-35  36-40 :Q4
            41-45  46-50
            51-55  56-60
        ```

        **Cálculo:**
        - Q1: números de 01-05, 11-15, 21-25
        - Q2: números de 06-10, 16-20, 26-30
        - Q3: números de 31-35, 41-45, 51-55
        - Q4: números de 36-40, 46-50, 56-60

        **Ideal:** ~1.5 números por quadrante (6 números ÷ 4 quadrantes)

        **Por que isso importa?**
        - Evita concentração espacial no volante
        - Promove distribuição visual equilibrada
        """,

        "poisson": """
        ### 🎲 Como calculamos a Probabilidade de Poisson

        **Fórmula:** P(k) = (λ^k × e^-λ) / k!

        Onde:
        - λ = taxa média de aparições por sorteio
        - k = número de aparições esperadas
        - e = constante de Euler (~2.718)

        **Interpretação:**
        - Se um número aparece em média 0.15 vezes por sorteio
        - Podemos calcular a probabilidade dele aparecer 1 vez no próximo

        **Por que isso importa?**
        - Modelo probabilístico para eventos raros
        - Ajuda a identificar números com probabilidade estatisticamente maior
        """,

        "score": """
        ### 🏆 Como calculamos o Score Final (0-100)

        **Fórmula Ponderada Completa (12 Regras):**

        ```
        Score = (Frequência × 0.14) +
                (Atraso × 0.14) +
                (Tendência × 0.09) +
                (Quadrante × 0.09) +
                (Paridade × 0.07) +
                (Baixo/Médio/Alto × 0.07) +
                (Linhas × 0.07) +
                (Colunas × 0.07) +
                (Soma × 0.07) +
                (Ciclo × 0.05) +
                (Poisson × 0.05) +
                (H-N-F × 0.09)  ← NOVA!
        ```

        **12 Componentes do Score:**

        1. **Frequência (14%)**: Baseada em aparições históricas
        2. **Atraso (14%)**: Regressão à média (quanto mais atrasado, maior o score)
        3. **Tendência (9%)**: Desempenho recente (últimos 10/20/50 jogos)
        4. **Quadrante (9%)**: Equilíbrio espacial nos 4 quadrantes do volante
        5. **Paridade (7%)**: Contribuição para balanço par/ímpar (ideal: 3P-3I)
        6. **Baixo/Médio/Alto (7%)**: Contribuição para balanço das 3 faixas (ideal: 2B-2M-2A)
        7. **Linhas (7%)**: Distribuição equilibrada nas 6 linhas do volante
        8. **Colunas (7%)**: Distribuição equilibrada nas 10 colunas do volante
        9. **Soma (7%)**: Contribuição para soma ideal (150-200)
        10. **Ciclo (5%)**: Bônus para números que ainda não apareceram no ciclo atual
        11. **Poisson (5%)**: Probabilidade estatística de aparição
        12. **H-N-F (9%)**: 🆕 Faixas de frequência (Quente/Neutro/Frio) - padrões como 2H-2N-2F

        **Resultado:** Score de 0 a 100 para cada número
        - 70-100: Excelente
        - 50-70: Bom
        - 30-50: Médio
        - 0-30: Baixo
        """
    }
    return explicacoes.get(metrica, "")

def gerar_justificativa_numeros(dezenas, analyzer, scores_df):
    """Gera justificativa cruzada detalhada dos números escolhidos."""
    justificativas = []

    freq = analyzer.calcular_frequencias()
    hot = analyzer.calcular_hot_numbers()
    cold = analyzer.calcular_cold_numbers()

    for num in sorted(dezenas):
        score_num = scores_df[scores_df['numero'] == num].iloc[0]
        razoes = []

        # Razão 1: Score geral
        if score_num['score_final'] >= 70:
            razoes.append(f"**Score excelente ({score_num['score_final']:.1f}/100)**")
        elif score_num['score_final'] >= 50:
            razoes.append(f"**Score bom ({score_num['score_final']:.1f}/100)**")

        # Razão 2: Frequência
        freq_rank = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        posicao = [i for i, (n, _) in enumerate(freq_rank, 1) if n == num][0]
        if posicao <= 15:
            razoes.append(f"Top {posicao} em frequência histórica ({freq[num]} aparições)")

        # Razão 3: Temperatura
        if num in hot and hot[num] >= 2:
            razoes.append(f"🔥 Número QUENTE (apareceu {hot[num]}x nos últimos 10 jogos)")
        elif num in cold and cold[num] >= 20:
            razoes.append(f"❄️ Muito ATRASADO ({cold[num]} concursos sem aparecer - regressão à média)")

        # Razão 4: Tendência
        if score_num['score_tendencia'] >= 70:
            razoes.append("📈 Tendência recente forte")

        # Razão 5: Equilíbrio
        paridade = "par" if num % 2 == 0 else "ímpar"
        faixa = "baixo (1-30)" if num <= 30 else "alto (31-60)"
        razoes.append(f"Contribui para equilíbrio ({paridade}, {faixa})")

        justificativas.append({
            "numero": num,
            "razoes": razoes
        })

    return justificativas

def comparar_com_historico(dezenas, analyzer):
    """Compara o jogo sugerido com padrões históricos vencedores."""
    df = analyzer.df

    # Perfil do jogo sugerido
    dezenas_sorted = sorted(dezenas)
    pares = sum(1 for d in dezenas_sorted if d % 2 == 0)
    impares = len(dezenas_sorted) - pares
    baixos = sum(1 for d in dezenas_sorted if d <= 30)
    altos = len(dezenas_sorted) - baixos
    soma = sum(dezenas_sorted)

    # Buscar jogos similares no histórico
    jogos_similares = []

    for idx, row in df.iterrows():
        jogo_hist = sorted([row['D1'], row['D2'], row['D3'], row['D4'], row['D5'], row['D6']])
        p_hist = sum(1 for d in jogo_hist if d % 2 == 0)
        i_hist = 6 - p_hist
        b_hist = sum(1 for d in jogo_hist if d <= 30)
        a_hist = 6 - b_hist
        s_hist = sum(jogo_hist)

        # Score de similaridade
        similaridade = 0
        if p_hist == pares: similaridade += 2
        if b_hist == baixos: similaridade += 2
        if abs(s_hist - soma) <= 20: similaridade += 1

        if similaridade >= 3:
            jogos_similares.append({
                "concurso": row['Concurso'],
                "dezenas": jogo_hist,
                "similaridade": similaridade,
                "padrao": f"{p_hist}P-{i_hist}I, {b_hist}B-{a_hist}A, Soma={s_hist}"
            })

    # Ordenar por similaridade
    jogos_similares.sort(key=lambda x: x['similaridade'], reverse=True)

    return jogos_similares[:10]  # Top 10 mais similares

def sugerir_jogos_por_budget(budget, analyzer, scores_df):
    """Sugere a melhor combinação de jogos baseado no budget."""
    sugestoes = []

    # Ordenar opções por custo decrescente
    opcoes = sorted(TABELA_CAIXA.items(), key=lambda x: x[1]['valor'], reverse=True)

    for qtd_num, info in opcoes:
        custo = info['valor']
        if custo <= budget:
            qtd_jogos = int(budget // custo)
            resto = budget - (qtd_jogos * custo)

            sugestoes.append({
                "quantidade_numeros": qtd_num,
                "custo_por_jogo": custo,
                "qtd_jogos": qtd_jogos,
                "custo_total": qtd_jogos * custo,
                "resto": resto,
                "prob_sena": info['prob_sena'],
                "prob_quina": info['prob_quina'],
                "prob_quadra": info['prob_quadra']
            })

    return sugestoes

def gerar_jogo_otimizado(qtd_numeros: int, analyzer, scores_df, numeros_ja_usados: set = None) -> dict:
    """
    Gera um jogo otimizado considerando TODAS as 12 análises estatísticas.

    Critérios de seleção (baseados nas 12 análises do score):
    1. Frequência histórica (14%) - números que mais aparecem
    2. Atraso/Regressão à média (14%) - números "atrasados"
    3. Tendência recente (9%) - momentum dos últimos jogos
    4. Equilíbrio por quadrante (9%) - distribuição espacial
    5. Paridade par/ímpar (7%) - equilíbrio 3P-3I
    6. Baixo/Médio/Alto (7%) - equilíbrio 2B-2M-2A
    7. Distribuição por linhas (7%) - ~1 número por linha
    8. Distribuição por colunas (7%) - ~0.6 números por coluna
    9. Soma ideal (7%) - contribuição para soma 150-200
    10. Ciclo atual (5%) - números faltantes no ciclo
    11. Probabilidade Poisson (5%) - expectativa estatística
    12. Faixas H-N-F (9%) - padrões Quente/Neutro/Frio

    Restrições adicionais na geração:
    - Evitar 4+ números na mesma linha
    - Evitar 3+ números na mesma coluna
    - Diversificar entre jogos (evitar repetição)
    """
    if numeros_ja_usados is None:
        numeros_ja_usados = set()

    # Obter dados das análises
    ciclo_atual = analyzer.obter_ciclo_atual()
    numeros_faltantes_ciclo = set(ciclo_atual['numeros_faltantes'])

    # Verificar quantos números ainda estão disponíveis (não usados)
    numeros_disponiveis = set(range(1, 61)) - numeros_ja_usados

    # Criar DUAS listas: candidatos novos (prioridade) e candidatos já usados (backup)
    candidatos_novos = []
    candidatos_usados = []

    for _, row in scores_df.iterrows():
        num = int(row['numero'])
        score_base = row['score_final']

        # Bônus para números faltantes no ciclo (maior em jogos grandes)
        bonus_ciclo = 5 if num in numeros_faltantes_ciclo else 0
        if qtd_numeros > 6 and num in numeros_faltantes_ciclo:
            bonus_ciclo = 8  # Bônus maior para jogos com mais dezenas

        # Classificações
        eh_par = num % 2 == 0
        if 1 <= num <= 20:
            faixa = 'baixo'
        elif 21 <= num <= 40:
            faixa = 'medio'
        else:
            faixa = 'alto'

        # Linha e coluna no volante (0-indexed para contagem)
        linha = (num - 1) // 10  # 0-5
        coluna = (num - 1) % 10  # 0-9

        cand_info = {
            'numero': num,
            'score': score_base + bonus_ciclo,
            'score_original': score_base,
            'eh_par': eh_par,
            'faixa': faixa,
            'linha': linha,
            'coluna': coluna,
            'faltante_ciclo': num in numeros_faltantes_ciclo,
            'ja_usado': num in numeros_ja_usados
        }

        # Separar em duas listas: novos vs já usados
        if num in numeros_ja_usados:
            candidatos_usados.append(cand_info)
        else:
            candidatos_novos.append(cand_info)

    # Ordenar cada lista por score
    candidatos_novos.sort(key=lambda x: x['score'], reverse=True)
    candidatos_usados.sort(key=lambda x: x['score'], reverse=True)

    # Combinar: primeiro os novos, depois os usados (como backup)
    candidatos = candidatos_novos + candidatos_usados

    # Seleção inteligente com equilíbrio
    selecionados = []

    # Metas de equilíbrio (para jogo de 6 números como referência, escalar para outros)
    fator = qtd_numeros / 6
    meta_pares = round(3 * fator)
    meta_impares = qtd_numeros - meta_pares
    meta_baixo = round(2 * fator)
    meta_medio = round(2 * fator)
    meta_alto = qtd_numeros - meta_baixo - meta_medio

    # Limites de concentração linha/coluna (baseado em análise histórica)
    max_mesma_linha = 3  # Evitar 4+ números na mesma linha
    max_mesma_coluna = 2  # Evitar 3+ números na mesma coluna

    # Contadores
    count_pares = 0
    count_impares = 0
    count_baixo = 0
    count_medio = 0
    count_alto = 0
    count_linhas = [0] * 6   # Contagem por linha (0-5)
    count_colunas = [0] * 10  # Contagem por coluna (0-9)

    # Primeira passada: pegar os melhores respeitando todos os limites
    for cand in candidatos:
        if len(selecionados) >= qtd_numeros:
            break

        # Verificar se adicionar este número ultrapassa os limites
        pode_adicionar = True

        # Limite de paridade
        if cand['eh_par'] and count_pares >= meta_pares + 1:
            pode_adicionar = False
        if not cand['eh_par'] and count_impares >= meta_impares + 1:
            pode_adicionar = False

        # Limite de faixa B/M/A
        if cand['faixa'] == 'baixo' and count_baixo >= meta_baixo + 1:
            pode_adicionar = False
        if cand['faixa'] == 'medio' and count_medio >= meta_medio + 1:
            pode_adicionar = False
        if cand['faixa'] == 'alto' and count_alto >= meta_alto + 1:
            pode_adicionar = False

        # Limite de linha (evitar 4+ na mesma linha)
        if count_linhas[cand['linha']] >= max_mesma_linha:
            pode_adicionar = False

        # Limite de coluna (evitar 3+ na mesma coluna)
        if count_colunas[cand['coluna']] >= max_mesma_coluna:
            pode_adicionar = False

        if pode_adicionar:
            selecionados.append(cand)
            if cand['eh_par']:
                count_pares += 1
            else:
                count_impares += 1

            if cand['faixa'] == 'baixo':
                count_baixo += 1
            elif cand['faixa'] == 'medio':
                count_medio += 1
            else:
                count_alto += 1

            count_linhas[cand['linha']] += 1
            count_colunas[cand['coluna']] += 1

    # Segunda passada: se não preencheu, relaxar limites de linha/coluna
    if len(selecionados) < qtd_numeros:
        for cand in candidatos:
            if cand in selecionados:
                continue
            if len(selecionados) >= qtd_numeros:
                break

            # Relaxar: aceitar até 4 na mesma linha, 3 na mesma coluna
            if count_linhas[cand['linha']] >= 4:
                continue
            if count_colunas[cand['coluna']] >= 3:
                continue

            selecionados.append(cand)
            count_linhas[cand['linha']] += 1
            count_colunas[cand['coluna']] += 1

    # Terceira passada: se ainda não preencheu, pegar próximos melhores
    if len(selecionados) < qtd_numeros:
        for cand in candidatos:
            if cand not in selecionados:
                selecionados.append(cand)
                if len(selecionados) >= qtd_numeros:
                    break

    dezenas = sorted([c['numero'] for c in selecionados])

    # Calcular perfil do jogo gerado
    pares = sum(1 for d in dezenas if d % 2 == 0)
    impares = len(dezenas) - pares
    baixos = sum(1 for d in dezenas if 1 <= d <= 20)
    medios = sum(1 for d in dezenas if 21 <= d <= 40)
    altos = sum(1 for d in dezenas if 41 <= d <= 60)
    soma = sum(dezenas)
    faltantes_incluidos = sum(1 for d in dezenas if d in numeros_faltantes_ciclo)

    # Contagem final de linhas e colunas
    linhas_final = [0] * 6
    colunas_final = [0] * 10
    for d in dezenas:
        linhas_final[(d - 1) // 10] += 1
        colunas_final[(d - 1) % 10] += 1

    max_linha = max(linhas_final)
    max_coluna = max(colunas_final)
    linhas_usadas = 6 - linhas_final.count(0)
    colunas_usadas = 10 - colunas_final.count(0)

    # Score médio dos números selecionados
    score_medio = np.mean([c['score_original'] for c in selecionados])

    # Alertas de distribuição
    alertas_dist = []
    if max_linha >= 4:
        alertas_dist.append(f"⚠️ {max_linha} nums mesma linha")
    if max_coluna >= 3:
        alertas_dist.append(f"⚠️ {max_coluna} nums mesma coluna")

    return {
        'dezenas': dezenas,
        'perfil': {
            'pares': pares,
            'impares': impares,
            'baixos': baixos,
            'medios': medios,
            'altos': altos,
            'soma': soma,
            'score_medio': round(score_medio, 2),
            'faltantes_ciclo': faltantes_incluidos,
            'max_linha': max_linha,
            'max_coluna': max_coluna,
            'linhas_usadas': linhas_usadas,
            'colunas_usadas': colunas_usadas,
            'alertas_distribuicao': alertas_dist
        }
    }


def calcular_probabilidade_combinada(jogos):
    """
    Calcula a probabilidade combinada de acertar sena/quina/quadra
    considerando TODOS os jogos juntos.

    A probabilidade de acertar pelo menos uma vez em N jogos independentes:
    P(pelo menos 1) = 1 - P(não acertar nenhum)
    P(pelo menos 1) = 1 - (1-p1) * (1-p2) * ... * (1-pN)
    """
    from config import PROBABILIDADES

    # Inicializar probabilidade de NÃO acertar
    prob_nao_acertar_sena = 1.0
    prob_nao_acertar_quina = 1.0
    prob_nao_acertar_quadra = 1.0

    for jogo in jogos:
        qtd = jogo['quantidade_numeros']
        if qtd in PROBABILIDADES:
            prob_sena, prob_quina, prob_quadra = PROBABILIDADES[qtd]

            # Probabilidade de NÃO acertar este jogo
            prob_nao_acertar_sena *= (1 - 1/prob_sena)
            prob_nao_acertar_quina *= (1 - 1/prob_quina)
            prob_nao_acertar_quadra *= (1 - 1/prob_quadra)

    # Probabilidade de acertar PELO MENOS uma vez
    prob_acertar_sena = 1 - prob_nao_acertar_sena
    prob_acertar_quina = 1 - prob_nao_acertar_quina
    prob_acertar_quadra = 1 - prob_nao_acertar_quadra

    # Converter para "1 em X"
    chance_sena = 1 / prob_acertar_sena if prob_acertar_sena > 0 else float('inf')
    chance_quina = 1 / prob_acertar_quina if prob_acertar_quina > 0 else float('inf')
    chance_quadra = 1 / prob_acertar_quadra if prob_acertar_quadra > 0 else float('inf')

    return {
        'prob_sena': prob_acertar_sena,
        'prob_quina': prob_acertar_quina,
        'prob_quadra': prob_acertar_quadra,
        'chance_sena': chance_sena,
        'chance_quina': chance_quina,
        'chance_quadra': chance_quadra,
        'percentual_sena': prob_acertar_sena * 100,
        'percentual_quina': prob_acertar_quina * 100,
        'percentual_quadra': prob_acertar_quadra * 100
    }


def calcular_indice_perfeicao(jogos):
    """
    Calcula um índice de 0-100% que representa o quão próximo
    os jogos sugeridos estão do "perfil ideal" baseado nos 11 indicadores.

    Critérios avaliados (cada um vale até 100 pontos):
    1. Score médio dos números (vs. máximo teórico)
    2. Equilíbrio par/ímpar (ideal ~50/50)
    3. Equilíbrio baixo/médio/alto (ideal ~33/33/33)
    4. Soma na faixa ideal (150-200 para 6 números, proporcional para mais)
    5. Distribuição de linhas (todas 6 representadas)
    6. Distribuição de colunas (máximo possível representado)
    7. Números do ciclo incluídos
    8. Diversificação entre jogos (números únicos)
    """
    if not jogos:
        return {'indice_total': 0, 'detalhes': {}}

    pontuacoes = []
    detalhes = {}

    # 1. Score médio (quanto maior melhor, max teórico ~100)
    scores_medios = [j.get('perfil', {}).get('score_medio', 50) for j in jogos]
    score_medio_geral = sum(scores_medios) / len(scores_medios) if scores_medios else 50
    # Normalizar: score de 50 = 50%, score de 100 = 100%
    pont_score = min(100, score_medio_geral)
    pontuacoes.append(pont_score)
    detalhes['score_medio'] = {'valor': round(score_medio_geral, 1), 'pontos': round(pont_score, 1)}

    # 2. Equilíbrio par/ímpar (ideal: 50/50, tolerância de 10%)
    desvios_paridade = []
    for jogo in jogos:
        perfil = jogo.get('perfil', {})
        pares = perfil.get('pares', 0)
        total = jogo['quantidade_numeros']
        ideal = total / 2
        desvio = abs(pares - ideal) / ideal if ideal > 0 else 0
        desvios_paridade.append(desvio)
    desvio_medio_paridade = sum(desvios_paridade) / len(desvios_paridade) if desvios_paridade else 0
    pont_paridade = max(0, 100 - desvio_medio_paridade * 200)  # 10% desvio = 80 pontos
    pontuacoes.append(pont_paridade)
    detalhes['paridade'] = {'desvio': f"{desvio_medio_paridade*100:.1f}%", 'pontos': round(pont_paridade, 1)}

    # 3. Equilíbrio baixo/médio/alto (ideal: 33/33/33)
    desvios_bma = []
    for jogo in jogos:
        perfil = jogo.get('perfil', {})
        baixos = perfil.get('baixos', 0)
        medios = perfil.get('medios', 0)
        altos = perfil.get('altos', 0)
        total = jogo['quantidade_numeros']
        ideal = total / 3
        desvio = (abs(baixos - ideal) + abs(medios - ideal) + abs(altos - ideal)) / (3 * ideal) if ideal > 0 else 0
        desvios_bma.append(desvio)
    desvio_medio_bma = sum(desvios_bma) / len(desvios_bma) if desvios_bma else 0
    pont_bma = max(0, 100 - desvio_medio_bma * 150)
    pontuacoes.append(pont_bma)
    detalhes['baixo_medio_alto'] = {'desvio': f"{desvio_medio_bma*100:.1f}%", 'pontos': round(pont_bma, 1)}

    # 4. Soma na faixa ideal (proporcional ao número de dezenas)
    pontos_soma = []
    for jogo in jogos:
        perfil = jogo.get('perfil', {})
        soma = perfil.get('soma', 0)
        qtd = jogo['quantidade_numeros']
        # Soma ideal proporcional: para 6 números = 175 (média), escala linear
        soma_ideal = 175 * qtd / 6
        soma_min = 150 * qtd / 6
        soma_max = 200 * qtd / 6

        if soma_min <= soma <= soma_max:
            pont = 100
        else:
            desvio = min(abs(soma - soma_min), abs(soma - soma_max)) / soma_ideal
            pont = max(0, 100 - desvio * 200)
        pontos_soma.append(pont)
    pont_soma_media = sum(pontos_soma) / len(pontos_soma) if pontos_soma else 0
    pontuacoes.append(pont_soma_media)
    detalhes['soma_ideal'] = {'pontos': round(pont_soma_media, 1)}

    # 5. Distribuição de linhas (usar todas as 6 linhas entre os jogos)
    todas_linhas = set()
    for jogo in jogos:
        dezenas = jogo['dezenas']
        for d in dezenas:
            linha = (d - 1) // 10
            todas_linhas.add(linha)
    pont_linhas = (len(todas_linhas) / 6) * 100
    pontuacoes.append(pont_linhas)
    detalhes['cobertura_linhas'] = {'usadas': len(todas_linhas), 'total': 6, 'pontos': round(pont_linhas, 1)}

    # 6. Distribuição de colunas (usar todas as 10 colunas entre os jogos)
    todas_colunas = set()
    for jogo in jogos:
        dezenas = jogo['dezenas']
        for d in dezenas:
            coluna = (d - 1) % 10
            todas_colunas.add(coluna)
    pont_colunas = (len(todas_colunas) / 10) * 100
    pontuacoes.append(pont_colunas)
    detalhes['cobertura_colunas'] = {'usadas': len(todas_colunas), 'total': 10, 'pontos': round(pont_colunas, 1)}

    # 7. Números do ciclo incluídos
    faltantes_incluidos = []
    for jogo in jogos:
        perfil = jogo.get('perfil', {})
        faltantes = perfil.get('faltantes_ciclo', 0)
        faltantes_incluidos.append(faltantes)
    media_faltantes = sum(faltantes_incluidos) / len(faltantes_incluidos) if faltantes_incluidos else 0
    # Ideal: quanto mais números do ciclo, melhor (max 6 por jogo de 6 dezenas)
    pont_ciclo = min(100, media_faltantes * 20)  # 5+ números = 100 pontos
    pontuacoes.append(pont_ciclo)
    detalhes['numeros_ciclo'] = {'media': round(media_faltantes, 1), 'pontos': round(pont_ciclo, 1)}

    # 8. Diversificação (números únicos vs. total de números jogados)
    todos_numeros = []
    numeros_unicos = set()
    for jogo in jogos:
        dezenas = jogo['dezenas']
        todos_numeros.extend(dezenas)
        numeros_unicos.update(dezenas)
    taxa_diversificacao = len(numeros_unicos) / len(todos_numeros) if todos_numeros else 0
    pont_diversificacao = taxa_diversificacao * 100
    pontuacoes.append(pont_diversificacao)
    detalhes['diversificacao'] = {
        'unicos': len(numeros_unicos),
        'total': len(todos_numeros),
        'taxa': f"{taxa_diversificacao*100:.1f}%",
        'pontos': round(pont_diversificacao, 1)
    }

    # Índice final (média ponderada)
    pesos = [0.20, 0.15, 0.15, 0.10, 0.10, 0.10, 0.10, 0.10]  # Soma = 1.0
    indice_total = sum(p * pont for p, pont in zip(pesos, pontuacoes))

    return {
        'indice_total': round(indice_total, 1),
        'detalhes': detalhes,
        'classificacao': 'Excelente' if indice_total >= 85 else 'Muito Bom' if indice_total >= 70 else 'Bom' if indice_total >= 55 else 'Regular'
    }


def otimizar_budget_completo(budget, analyzer, scores_df):
    """
    Otimiza o uso COMPLETO do budget, gastando TODO o dinheiro disponível
    combinando diferentes tipos de jogos para maximizar cobertura.
    Usa a função gerar_jogo_otimizado para criar jogos inteligentes.
    """
    budget_restante = budget
    jogos_selecionados = []
    numeros_ja_usados = set()

    # Estratégia: começar com jogos maiores e ir preenchendo com menores
    # para gastar TODO o dinheiro

    # Passo 1: Tentar encaixar 1 jogo grande (15-20 números) se o budget permitir
    for qtd_nums in [20, 19, 18, 17, 16, 15]:
        custo = TABELA_CAIXA[qtd_nums]['valor']
        if custo <= budget_restante and custo >= budget_restante * 0.4:  # Usa até 40% do budget em um jogo
            # Gerar jogo otimizado
            jogo = gerar_jogo_otimizado(qtd_nums, analyzer, scores_df, numeros_ja_usados)
            dezenas = jogo['dezenas']
            numeros_ja_usados.update(dezenas)

            jogos_selecionados.append({
                'tipo': f'Jogo Principal ({qtd_nums} números)',
                'quantidade_numeros': qtd_nums,
                'dezenas': dezenas,
                'custo': custo,
                'prob_sena': TABELA_CAIXA[qtd_nums]['prob_sena'],
                'estrategia': 'Otimizado por Score + Ciclo',
                'perfil': jogo['perfil']
            })
            budget_restante -= custo
            break

    # Passo 2: Preencher o resto com jogos médios e pequenos
    while budget_restante >= 6.00:  # Mínimo para um jogo simples
        melhor_opcao = None

        # Tentar jogos de 10-14 números (cobertura média)
        for qtd_nums in [14, 13, 12, 11, 10]:
            custo = TABELA_CAIXA[qtd_nums]['valor']
            if custo <= budget_restante:
                melhor_opcao = qtd_nums
                break

        # Se não couber médio, tentar jogos pequenos (6-9)
        if not melhor_opcao:
            for qtd_nums in [9, 8, 7, 6]:
                custo = TABELA_CAIXA[qtd_nums]['valor']
                if custo <= budget_restante:
                    melhor_opcao = qtd_nums
                    break

        if not melhor_opcao:
            break  # Não consegue encaixar mais nada

        # Gerar jogo otimizado evitando números já usados
        jogo = gerar_jogo_otimizado(melhor_opcao, analyzer, scores_df, numeros_ja_usados)
        dezenas = jogo['dezenas']
        numeros_ja_usados.update(dezenas)

        custo = TABELA_CAIXA[melhor_opcao]['valor']

        jogos_selecionados.append({
            'tipo': f'Jogo Complementar ({melhor_opcao} números)',
            'quantidade_numeros': melhor_opcao,
            'dezenas': dezenas,
            'custo': custo,
            'prob_sena': TABELA_CAIXA[melhor_opcao]['prob_sena'],
            'estrategia': 'Otimizado por Score + Ciclo',
            'perfil': jogo['perfil']
        })

        budget_restante -= custo

    return {
        'jogos': jogos_selecionados,
        'total_gasto': budget - budget_restante,
        'total_jogos': len(jogos_selecionados),
        'resto': budget_restante,
        'aproveitamento': ((budget - budget_restante) / budget) * 100
    }

def criar_grafico_frequencias(analyzer):
    """Cria gráfico de barras de frequências."""
    freq = analyzer.calcular_frequencias()
    freq_sorted = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    numeros = [f"{num:02d}" for num, _ in freq_sorted]
    valores = [count for _, count in freq_sorted]

    cores = []
    for i in range(len(valores)):
        if i < 10:
            cores.append('#00cc44')
        elif i >= len(valores) - 10:
            cores.append('#ff4444')
        else:
            cores.append('#4488ff')

    fig = go.Figure(data=[
        go.Bar(x=numeros, y=valores, marker_color=cores, text=valores, textposition='outside')
    ])

    fig.update_layout(
        title="Frequência de Aparição dos Números",
        xaxis_title="Números",
        yaxis_title="Quantidade de Aparições",
        height=500,
        showlegend=False,
        hovermode='x unified'
    )

    return fig

def criar_grafico_hot_cold(analyzer):
    """Cria gráfico de números hot e cold."""
    hot = analyzer.calcular_hot_numbers()
    cold = analyzer.calcular_cold_numbers()

    hot_sorted = sorted(hot.items(), key=lambda x: x[1], reverse=True)[:15]
    cold_sorted = sorted(cold.items(), key=lambda x: x[1], reverse=True)[:15]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='🔥 Hot (Últimos 10 jogos)',
        x=[f"{num:02d}" for num, _ in hot_sorted],
        y=[count for _, count in hot_sorted],
        marker_color='#ff6b6b',
        text=[count for _, count in hot_sorted],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name='❄️ Cold (Atraso)',
        x=[f"{num:02d}" for num, _ in cold_sorted],
        y=[atraso for _, atraso in cold_sorted],
        marker_color='#4ecdc4',
        text=[atraso for _, atraso in cold_sorted],
        textposition='outside'
    ))

    fig.update_layout(
        title="Análise Hot/Cold - Números Quentes vs. Atrasados",
        xaxis_title="Números",
        yaxis_title="Aparições / Atraso (concursos)",
        height=500,
        barmode='group'
    )

    return fig

def criar_grafico_scores(scores_df):
    """Cria gráfico de scores."""
    top_20 = scores_df.head(20)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[f"{int(num):02d}" for num in top_20['numero']],
        y=top_20['score_final'],
        marker=dict(
            color=top_20['score_final'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Score")
        ),
        text=[f"{score:.1f}" for score in top_20['score_final']],
        textposition='outside'
    ))

    fig.update_layout(
        title="Top 20 Números - Ranking de Scores",
        xaxis_title="Números",
        yaxis_title="Score (0-100)",
        height=500,
        showlegend=False
    )

    return fig

def exibir_volante_interativo(dezenas_selecionadas):
    """Exibe volante visual da Mega-Sena."""
    html = """
    <style>
        .volante {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 5px;
            max-width: 600px;
            margin: 20px auto;
        }
        .numero {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #ddd;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
            background: white;
            color: #333;
        }
        .numero.selecionado {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            transform: scale(1.1);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
    </style>
    <div class="volante">
    """

    for num in range(1, 61):
        classe = "selecionado" if num in dezenas_selecionadas else ""
        html += f'<div class="numero {classe}">{num:02d}</div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def criar_grafico_linhas_volante(analyzer):
    """Cria gráfico de distribuição por linhas do volante."""
    analise_linhas = analyzer.analisar_linhas_volante()

    linhas = list(analise_linhas['medias_por_linha'].keys())
    medias = [analise_linhas['medias_por_linha'][l] for l in linhas]
    desvios = [analise_linhas['desvio_por_linha'][l] for l in linhas]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=linhas,
        y=medias,
        error_y=dict(type='data', array=desvios),
        marker_color='#4ecdc4',
        text=[f"{m:.2f}" for m in medias],
        textposition='outside'
    ))

    # Linha de referência (média ideal = 1.0)
    fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                  annotation_text="Média Ideal (1.0)")

    fig.update_layout(
        title="Distribuição por Linhas do Volante (L1: 01-10, L2: 11-20, ...)",
        xaxis_title="Linhas",
        yaxis_title="Média de Números por Linha",
        height=500,
        showlegend=False
    )

    return fig

def criar_grafico_colunas_volante(analyzer):
    """Cria gráfico de distribuição por colunas do volante."""
    analise_colunas = analyzer.analisar_colunas_volante()

    colunas = list(analise_colunas['medias_por_coluna'].keys())
    medias = [analise_colunas['medias_por_coluna'][c] for c in colunas]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=colunas,
        y=medias,
        marker_color='#95e1d3',
        text=[f"{m:.2f}" for m in medias],
        textposition='outside'
    ))

    # Linha de referência (média ideal = 0.6)
    fig.add_hline(y=0.6, line_dash="dash", line_color="red",
                  annotation_text="Média Ideal (0.6)")

    fig.update_layout(
        title="Distribuição por Colunas do Volante (C1: 01,11,21,31,41,51, ...)",
        xaxis_title="Colunas",
        yaxis_title="Média de Números por Coluna",
        height=500,
        showlegend=False
    )

    return fig

def criar_mapa_calor_volante(analyzer):
    """Cria mapa de calor do volante cruzando linhas e colunas."""
    df = analyzer.df

    # Criar matriz 6x10 (6 linhas x 10 colunas)
    matriz_volante = np.zeros((6, 10))

    # Mapear cada número para sua posição no volante
    # Linha = (numero - 1) // 10
    # Coluna = (numero - 1) % 10

    # Contar frequência de cada número
    for idx, row in df.iterrows():
        jogo = [row['D1'], row['D2'], row['D3'], row['D4'], row['D5'], row['D6']]
        for num in jogo:
            linha = (num - 1) // 10  # 0-5
            coluna = (num - 1) % 10   # 0-9
            matriz_volante[linha][coluna] += 1

    # Criar labels das linhas e colunas
    labels_linhas = ['L1 (01-10)', 'L2 (11-20)', 'L3 (21-30)', 'L4 (31-40)', 'L5 (41-50)', 'L6 (51-60)']
    labels_colunas = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10']

    # Criar texto para cada célula (número + frequência)
    texto_celulas = []
    for i in range(6):
        linha_texto = []
        for j in range(10):
            numero = i * 10 + j + 1
            freq = int(matriz_volante[i][j])
            linha_texto.append(f"{numero:02d}<br>({freq})")
        texto_celulas.append(linha_texto)

    # Criar heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matriz_volante,
        x=labels_colunas,
        y=labels_linhas,
        text=texto_celulas,
        texttemplate='%{text}',
        textfont={"size": 10},
        colorscale='RdYlGn',
        colorbar=dict(title="Frequência"),
        hoverongaps=False,
        hovertemplate='<b>%{y} - %{x}</b><br>Frequência: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title="Mapa de Calor do Volante - Cruzamento Linhas × Colunas",
        xaxis_title="Colunas (Vertical)",
        yaxis_title="Linhas (Horizontal)",
        height=600,
        xaxis={'side': 'top'}
    )

    return fig

def criar_grafico_paridade(analyzer):
    """Cria gráfico de pizza para padrões Par/Ímpar."""
    paridade = analyzer.analisar_paridade()

    # Pegar top 8 padrões
    top_padroes = list(paridade.items())[:8]
    labels = [padrao for padrao, _ in top_padroes]
    values = [count for _, count in top_padroes]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo='label+percent',
        textposition='auto',
        marker=dict(
            colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']
        )
    )])

    fig.update_layout(
        title="Distribuição de Padrões Par/Ímpar",
        height=500,
        showlegend=True
    )

    return fig

def criar_grafico_baixo_medio_alto(analyzer):
    """Cria gráfico de pizza para padrões Baixo/Médio/Alto."""
    df = analyzer.df

    # Analisar padrão Baixo (1-20), Médio (21-40), Alto (41-60)
    padroes = {}

    for idx, row in df.iterrows():
        jogo = [row['D1'], row['D2'], row['D3'], row['D4'], row['D5'], row['D6']]
        baixos = sum(1 for num in jogo if 1 <= num <= 20)
        medios = sum(1 for num in jogo if 21 <= num <= 40)
        altos = sum(1 for num in jogo if 41 <= num <= 60)

        padrao = f"{baixos}B-{medios}M-{altos}A"
        padroes[padrao] = padroes.get(padrao, 0) + 1

    # Ordenar por frequência
    padroes_sorted = sorted(padroes.items(), key=lambda x: x[1], reverse=True)

    # Pegar top 10 padrões
    top_padroes = padroes_sorted[:10]
    labels = [padrao for padrao, _ in top_padroes]
    values = [count for _, count in top_padroes]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo='label+percent',
        textposition='auto',
        marker=dict(
            colors=['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22', '#34495E', '#16A085', '#C0392B']
        )
    )])

    fig.update_layout(
        title="Distribuição de Padrões Baixo/Médio/Alto",
        height=500,
        showlegend=True
    )

    return fig

def criar_grafico_ciclos(analyzer):
    """Cria gráfico de análise de ciclos de renovação."""
    analise_ciclos = analyzer.analisar_ciclos_renovacao_completa()

    if analise_ciclos['total_ciclos_completos'] == 0:
        # Gráfico vazio se não há ciclos completos
        fig = go.Figure()
        fig.add_annotation(
            text="Dados insuficientes para análise de ciclos completos",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(height=400)
        return fig

    # Top 20 números mais frequentes nos ciclos
    top_nums = analise_ciclos['numeros_mais_frequentes_no_ciclo'][:20]
    numeros = [f"{num:02d}" for num, _ in top_nums]
    frequencias = [freq for _, freq in top_nums]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=numeros,
        y=frequencias,
        marker_color='#f38181',
        text=[f"{f:.2f}" for f in frequencias],
        textposition='outside'
    ))

    fig.update_layout(
        title=f"Top 20 Números - Média de Aparições por Ciclo (Ciclo Médio: {analise_ciclos['ciclo_medio']:.0f} concursos)",
        xaxis_title="Números",
        yaxis_title="Média de Aparições por Ciclo",
        height=500,
        showlegend=False
    )

    return fig

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    # Arquivo padrão com histórico real
    ARQUIVO_PADRAO = "/Users/rz80/Documents/megasena/resultadosmega.xlsx"

    # Inicializar session_state para persistência de dados
    if 'dados_carregados' not in st.session_state:
        # Placeholder para mensagens de status
        status_placeholder = st.empty()

        import os
        if os.path.exists(ARQUIVO_PADRAO):
            try:
                # Feedback visual: Carregando arquivo
                with status_placeholder.container():
                    st.info(f"📂 **Carregando histórico...**")
                    st.caption(f"Arquivo: `{ARQUIVO_PADRAO}`")

                df_padrao = pd.read_excel(ARQUIVO_PADRAO)

                # Feedback visual: Processando
                with status_placeholder.container():
                    st.info(f"🔬 **Processando {len(df_padrao):,} registros...**")

                # Normaliza colunas
                df_padrao.columns = [str(c).strip() for c in df_padrao.columns]

                # Detecta colunas de dezenas (várias variações)
                colunas_dezenas = None
                # Variação 1: "bola 1", "bola 2", etc (com espaço, minúsculo)
                if all(f'bola {i}' in df_padrao.columns for i in range(1, 7)):
                    colunas_dezenas = [f'bola {i}' for i in range(1, 7)]
                # Variação 2: "Bola1", "Bola2", etc (sem espaço)
                elif all(f'Bola{i}' in df_padrao.columns for i in range(1, 7)):
                    colunas_dezenas = [f'Bola{i}' for i in range(1, 7)]
                # Variação 3: "D1", "D2", etc
                elif all(f'D{i}' in df_padrao.columns for i in range(1, 7)):
                    colunas_dezenas = [f'D{i}' for i in range(1, 7)]

                if colunas_dezenas:
                    # Renomeia para padrão D1-D6
                    for i, col in enumerate(colunas_dezenas, 1):
                        df_padrao = df_padrao.rename(columns={col: f'D{i}'})

                    # Garante coluna Concurso
                    if 'Concurso' not in df_padrao.columns:
                        for col in df_padrao.columns:
                            if 'concurso' in col.lower():
                                df_padrao = df_padrao.rename(columns={col: 'Concurso'})
                                break
                        else:
                            df_padrao['Concurso'] = range(1, len(df_padrao) + 1)

                    st.session_state.dados_carregados = df_padrao
                    st.session_state.nome_arquivo = "resultadosmega.xlsx"
                    st.session_state.fonte_dados = "Histórico Oficial"
                    st.session_state.caminho_arquivo = ARQUIVO_PADRAO

                    # Feedback visual: Sucesso
                    status_placeholder.success(f"✅ **Carregado:** {len(df_padrao):,} concursos do histórico oficial")
                else:
                    st.session_state.dados_carregados = None
                    st.session_state.nome_arquivo = None
                    st.session_state.fonte_dados = "Demonstração"
                    st.session_state.caminho_arquivo = None
                    status_placeholder.warning("⚠️ Formato de arquivo não reconhecido. Usando demonstração.")
            except Exception as e:
                st.session_state.dados_carregados = None
                st.session_state.nome_arquivo = None
                st.session_state.fonte_dados = "Demonstração"
                st.session_state.caminho_arquivo = None
                status_placeholder.error(f"❌ Erro ao carregar: {str(e)}")
        else:
            st.session_state.dados_carregados = None
            st.session_state.nome_arquivo = None
            st.session_state.fonte_dados = "Demonstração"
            st.session_state.caminho_arquivo = None

    # Header
    st.markdown('<div class="main-header">🎰 MEGA-SENA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Análise Estatística Avançada com 12 Critérios</div>', unsafe_allow_html=True)

    # Resumo das 12 Análises
    with st.expander("📊 **Sistema de 12 Análises Estatísticas** - Clique para ver detalhes", expanded=False):
        st.markdown("""
        ### Como funciona nosso sistema de análise?

        Cada número de 1 a 60 recebe um **Score de 0 a 100** baseado em **12 critérios estatísticos**:

        | # | Análise | Peso | O que mede |
        |---|---------|------|------------|
        | 1 | **Frequência Histórica** | 14% | Quantas vezes o número apareceu em todos os sorteios |
        | 2 | **Atraso (Regressão à Média)** | 14% | Há quantos sorteios o número não aparece - números "atrasados" tendem a sair |
        | 3 | **Tendência Recente** | 9% | Se o número está "quente" ou "frio" nos últimos 10 jogos |
        | 4 | **Equilíbrio por Quadrante** | 9% | Distribuição espacial no volante (4 quadrantes) |
        | 5 | **Paridade Par/Ímpar** | 7% | Contribuição para equilíbrio 3 pares - 3 ímpares |
        | 6 | **Baixo/Médio/Alto** | 7% | Contribuição para equilíbrio 2B-2M-2A (3 faixas de 20 números) |
        | 7 | **Distribuição por Linhas** | 7% | Equilíbrio entre as 6 linhas do volante (~1 número/linha) |
        | 8 | **Distribuição por Colunas** | 7% | Equilíbrio entre as 10 colunas (~0.6 números/coluna) |
        | 9 | **Soma Ideal** | 7% | Contribuição para soma total entre 150-200 (faixa mais comum) |
        | 10 | **Ciclo Atual** | 5% | Se o número ainda não apareceu no ciclo de renovação atual |
        | 11 | **Probabilidade Poisson** | 5% | Expectativa estatística de aparição baseada em distribuição |
        | 12 | **Faixas H-N-F** 🆕 | 9% | Padrões Quente/Neutro/Frio - equilíbrio 2H-2N-2F mais comum |

        ---

        ### Na geração de jogos, também aplicamos:

        - **Limite de Linha:** Máximo 3 números na mesma linha (4+ é raro: ~5% histórico)
        - **Limite de Coluna:** Máximo 2 números na mesma coluna (3+ é raro: ~8% histórico)
        - **Diversificação:** Penalidade para números repetidos entre jogos
        - **Bônus Ciclo:** Prioridade para números faltantes no ciclo atual

        ---

        💡 **Resultado:** Jogos estatisticamente balanceados que seguem os padrões históricos mais frequentes!
        """, unsafe_allow_html=True)

    # ========================================================================
    # SIDEBAR - CONFIGURAÇÕES
    # ========================================================================

    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/lottery.png", width=80)
        st.title("⚙️ Configurações")

        st.markdown("---")

        # Informações da base de dados
        st.subheader("📁 Base de Dados")

        # Mostrar status dos dados atuais
        if st.session_state.dados_carregados is not None:
            st.success(f"✅ **{st.session_state.fonte_dados}**")
            st.caption(f"📊 **{len(st.session_state.dados_carregados):,} concursos**")
            # Mostrar caminho do arquivo
            if hasattr(st.session_state, 'caminho_arquivo') and st.session_state.caminho_arquivo:
                st.code(st.session_state.caminho_arquivo, language=None)
        else:
            st.warning("⚠️ Usando dados de demonstração")

        st.markdown("---")

        # Budget
        st.subheader("💰 Orçamento")
        budget = st.number_input(
            "Budget Total (R$)",
            min_value=6.0,
            max_value=1000000.0,
            value=1000.0,
            step=10.0,
            format="%.2f"
        )
        st.metric("Budget Disponível", f"R$ {budget:,.2f}")

        st.markdown("---")

        # Info
        st.info("""
        **Como usar:**
        1. Carregue seus dados (fica salvo na sessão!)
        2. Defina seu budget
        3. Explore as análises nas abas
        4. Veja as sugestões personalizadas
        5. Jogue com responsabilidade!
        """)

        st.warning("⚠️ Este é um sistema de análise estatística. NÃO garante ganhos.")

    # ========================================================================
    # CARREGAR DADOS
    # ========================================================================

    with st.spinner("🔬 Processando análises estatísticas..."):
        # Usar dados carregados ou demonstração
        if st.session_state.dados_carregados is not None:
            df = st.session_state.dados_carregados
        else:
            df = carregar_dados_sinteticos()
            st.session_state.fonte_dados = "Demonstração"

        analyzer = MegaSenaAnalyzer(df)

    # ========================================================================
    # MÉTRICAS PRINCIPAIS
    # ========================================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Total de Concursos", f"{len(df):,}")

    with col2:
        loader = MegaSenaDataLoader()
        loader.df = df
        sumario = loader.get_summary()
        st.metric("🎯 Primeiro Concurso", f"#{sumario['primeiro_concurso']}")

    with col3:
        st.metric("🔢 Último Concurso", f"#{sumario['ultimo_concurso']}")

    with col4:
        st.metric("📈 Média Soma", f"{sumario['media_soma_dezenas']:.0f}")

    st.markdown("---")

    # ========================================================================
    # TABS PRINCIPAIS
    # ========================================================================

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Análises Estatísticas",
        "🔬 Análises Avançadas",
        "🏆 Ranking de Scores",
        "📋 Perfis de Jogos",
        "🎲 Sugestão Personalizada",
        "💰 Tabela de Custos",
        "💾 Dados Brutos"
    ])

    # ------------------------------------------------------------------------
    # TAB 1: ANÁLISES ESTATÍSTICAS COM EXPLICAÇÕES
    # ------------------------------------------------------------------------

    with tab1:
        st.header("📊 Análises Estatísticas Completas")

        # Frequências
        st.subheader("1️⃣ Análise de Frequências")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown(explicar_metrica("frequencia"))

        fig_freq = criar_grafico_frequencias(analyzer)
        st.plotly_chart(fig_freq, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"""
            **Número MAIS Frequente:**
            `{sumario['numero_mais_frequente'][0]:02d}` com {sumario['numero_mais_frequente'][1]} aparições
            """)

        with col2:
            st.warning(f"""
            **Número MENOS Frequente:**
            `{sumario['numero_menos_frequente'][0]:02d}` com {sumario['numero_menos_frequente'][1]} aparições
            """)

        st.markdown("---")

        # Hot/Cold
        st.subheader("2️⃣ Análise Hot/Cold (Temperaturas)")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown(explicar_metrica("hot_cold"))

        fig_hot_cold = criar_grafico_hot_cold(analyzer)
        st.plotly_chart(fig_hot_cold, use_container_width=True)

        st.markdown("---")

        # Paridade
        st.subheader("3️⃣ Análise Par/Ímpar")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown(explicar_metrica("paridade"))

        paridade = analyzer.analisar_paridade()

        # Gráfico de pizza
        fig_paridade = criar_grafico_paridade(analyzer)
        st.plotly_chart(fig_paridade, use_container_width=True)

        # Top 5 textual
        st.write("**Top 5 Padrões Mais Comuns:**")
        for i, (padrao, count) in enumerate(list(paridade.items())[:5], 1):
            porcentagem = (count / len(df)) * 100
            st.write(f"{i}. **{padrao}** - {count} vezes ({porcentagem:.1f}%)")

        st.markdown("---")

        # Baixo/Médio/Alto
        st.subheader("4️⃣ Análise Baixo/Médio/Alto")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown(explicar_metrica("alto_baixo"))

        # Gráfico de pizza
        fig_bma = criar_grafico_baixo_medio_alto(analyzer)
        st.plotly_chart(fig_bma, use_container_width=True)

        # Calcular padrões para exibição textual
        df_temp = analyzer.df
        padroes_bma = {}

        for idx, row in df_temp.iterrows():
            jogo = [row['D1'], row['D2'], row['D3'], row['D4'], row['D5'], row['D6']]
            baixos = sum(1 for num in jogo if 1 <= num <= 20)
            medios = sum(1 for num in jogo if 21 <= num <= 40)
            altos = sum(1 for num in jogo if 41 <= num <= 60)
            padrao = f"{baixos}B-{medios}M-{altos}A"
            padroes_bma[padrao] = padroes_bma.get(padrao, 0) + 1

        padroes_bma_sorted = sorted(padroes_bma.items(), key=lambda x: x[1], reverse=True)

        st.write("**Top 5 Padrões Mais Comuns:**")
        for i, (padrao, count) in enumerate(padroes_bma_sorted[:5], 1):
            porcentagem = (count / len(df)) * 100
            st.write(f"{i}. **{padrao}** - {count} vezes ({porcentagem:.1f}%)")

        st.markdown("---")

        # Quadrantes
        st.subheader("5️⃣ Análise de Quadrantes do Volante")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown(explicar_metrica("quadrantes"))

        quadrantes = analyzer.analisar_quadrantes()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Quadrante 1", f"{quadrantes['Q1']['media_aparicoes']:.2f}",
                     delta=f"{quadrantes['Q1']['media_aparicoes']-1.5:.2f}")
        with col2:
            st.metric("Quadrante 2", f"{quadrantes['Q2']['media_aparicoes']:.2f}",
                     delta=f"{quadrantes['Q2']['media_aparicoes']-1.5:.2f}")
        with col3:
            st.metric("Quadrante 3", f"{quadrantes['Q3']['media_aparicoes']:.2f}",
                     delta=f"{quadrantes['Q3']['media_aparicoes']-1.5:.2f}")
        with col4:
            st.metric("Quadrante 4", f"{quadrantes['Q4']['media_aparicoes']:.2f}",
                     delta=f"{quadrantes['Q4']['media_aparicoes']-1.5:.2f}")

        st.markdown("---")

        # Faixas de Frequência H-N-F (NOVA - 12ª regra)
        st.subheader("6️⃣ Análise de Faixas de Frequência (H-N-F)")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown("""
            ### 🔥 Faixas de Frequência: Quente (H), Neutro (N) e Frio (F)

            Esta análise classifica os 60 números em **3 faixas** baseado na frequência histórica:

            | Faixa | Descrição | Números |
            |-------|-----------|---------|
            | **H (Hot/Quente)** | Top 20 mais frequentes | 20 números |
            | **N (Neutro)** | 20 números do meio | 20 números |
            | **F (Frio/Cold)** | 20 menos frequentes | 20 números |

            ### 📊 Padrões de Combinação

            Para cada sorteio, analisamos quantos números de cada faixa foram sorteados:
            - **2H-2N-2F**: 2 quentes, 2 neutros, 2 frios (equilibrado)
            - **3H-2N-1F**: 3 quentes, 2 neutros, 1 frio
            - etc.

            ### 🎯 Por que é importante?

            Os padrões mais frequentes historicamente tendem a se repetir.
            Jogos equilibrados (próximos de 2-2-2) aparecem mais vezes.
            Esta é a **12ª regra** do nosso sistema de análise.
            """)

        # Classificação dos números
        classificacao_hnf = analyzer.classificar_numeros_por_frequencia()
        padroes_hnf = analyzer.analisar_padroes_hnf()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.success(f"""
            **🔥 Números QUENTES (Top 20)**

            {', '.join([f'{n:02d}' for n in classificacao_hnf['quente']])}
            """)

        with col2:
            st.info(f"""
            **⚖️ Números NEUTROS (Meio)**

            {', '.join([f'{n:02d}' for n in classificacao_hnf['neutro']])}
            """)

        with col3:
            st.warning(f"""
            **❄️ Números FRIOS (Bottom 20)**

            {', '.join([f'{n:02d}' for n in classificacao_hnf['frio']])}
            """)

        # Gráfico de pizza dos padrões H-N-F
        padroes_data = padroes_hnf['top_5_padroes']
        fig_hnf = go.Figure(data=[go.Pie(
            labels=[p[0] for p in padroes_data],
            values=[p[1] for p in padroes_data],
            hole=0.4,
            textinfo='label+percent',
            marker_colors=['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#ff9ff3']
        )])
        fig_hnf.update_layout(
            title="Top 5 Padrões H-N-F Mais Comuns",
            showlegend=True
        )
        st.plotly_chart(fig_hnf, use_container_width=True)

        # Top 5 padrões textual
        st.write("**Top 5 Padrões Mais Comuns:**")
        for i, (padrao, pct) in enumerate(padroes_data, 1):
            st.write(f"{i}. **{padrao}** - {pct:.1f}%")

        st.markdown(f"""
        **📌 Padrões Recomendados** (cobrem ~{padroes_hnf['cobertura_recomendados']:.0f}% dos sorteios):
        `{', '.join(padroes_hnf['padroes_recomendados'])}`
        """)

    # ------------------------------------------------------------------------
    # TAB 2: RANKING DE SCORES COM EXPLICAÇÃO
    # ------------------------------------------------------------------------

    with tab3:
        st.header("🏆 Ranking de Scores (0-100)")

        with st.expander("📖 Como Calculamos o Score Final", expanded=True):
            st.markdown(explicar_metrica("score"))

        scores_df = analyzer.calcular_todos_scores()

        # Gráfico
        fig_scores = criar_grafico_scores(scores_df)
        st.plotly_chart(fig_scores, use_container_width=True)

        st.markdown("---")

        # Tabelas
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🥇 TOP 20 Melhores Scores")
            top_20 = scores_df.head(20)[['numero', 'score_final', 'score_frequencia', 'score_atraso', 'score_tendencia']].copy()
            top_20['numero'] = top_20['numero'].astype(int)
            top_20.columns = ['Número', 'Score Final', 'Freq', 'Atraso', 'Tendência']
            st.dataframe(
                top_20.style.background_gradient(subset=['Score Final'], cmap='Greens'),
                use_container_width=True,
                height=600
            )

        with col2:
            st.subheader("🦓 BOTTOM 20 (Zebras)")
            bottom_20 = scores_df.tail(20)[['numero', 'score_final', 'score_frequencia', 'score_atraso', 'score_tendencia']].copy()
            bottom_20['numero'] = bottom_20['numero'].astype(int)
            bottom_20.columns = ['Número', 'Score Final', 'Freq', 'Atraso', 'Tendência']
            st.dataframe(
                bottom_20.style.background_gradient(subset=['Score Final'], cmap='Reds_r'),
                use_container_width=True,
                height=600
            )

    # ------------------------------------------------------------------------
    # TAB 3: ANÁLISES AVANÇADAS (agora é TAB 2)
    # ------------------------------------------------------------------------

    with tab2:
        st.header("🔬 Análises Avançadas do Volante")

        st.info("""
        Análises espaciais e temporais profundas sobre o comportamento dos números no volante da Mega-Sena.
        """)

        # Análise de Linhas
        st.subheader("📐 Análise por Linhas do Volante")

        with st.expander("📖 O que são as Linhas do Volante", expanded=False):
            st.markdown("""
            ### 📐 Linhas do Volante da Mega-Sena

            O volante da Mega-Sena é organizado em **6 linhas horizontais**:

            - **L1:** 01, 02, 03, 04, 05, 06, 07, 08, 09, 10
            - **L2:** 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
            - **L3:** 21, 22, 23, 24, 25, 26, 27, 28, 29, 30
            - **L4:** 31, 32, 33, 34, 35, 36, 37, 38, 39, 40
            - **L5:** 41, 42, 43, 44, 45, 46, 47, 48, 49, 50
            - **L6:** 51, 52, 53, 54, 55, 56, 57, 58, 59, 60

            **Distribuição Ideal:** Como temos 6 números sorteados e 6 linhas, a média ideal é **1 número por linha**.

            **Por que isso importa:**
            - Evita concentração de números em poucas linhas
            - Promove distribuição visual equilibrada no volante
            - Reduz padrões previsíveis
            """)

        fig_linhas = criar_grafico_linhas_volante(analyzer)
        st.plotly_chart(fig_linhas, use_container_width=True)

        analise_linhas = analyzer.analisar_linhas_volante()
        st.write(f"**Padrões de distribuição mais comuns (Top 5):**")
        for i, (padrao, count) in enumerate(analise_linhas['top_padroes'][:5], 1):
            porcentagem = (count / len(df)) * 100
            st.write(f"{i}. `{padrao}` - {count} vezes ({porcentagem:.1f}%)")

        st.markdown("---")

        # Análise de Colunas
        st.subheader("📊 Análise por Colunas do Volante")

        with st.expander("📖 O que são as Colunas do Volante", expanded=False):
            st.markdown("""
            ### 📊 Colunas do Volante da Mega-Sena

            O volante da Mega-Sena é organizado em **10 colunas verticais**:

            - **C1:** 01, 11, 21, 31, 41, 51
            - **C2:** 02, 12, 22, 32, 42, 52
            - **C3:** 03, 13, 23, 33, 43, 53
            - **C4:** 04, 14, 24, 34, 44, 54
            - **C5:** 05, 15, 25, 35, 45, 55
            - **C6:** 06, 16, 26, 36, 46, 56
            - **C7:** 07, 17, 27, 37, 47, 57
            - **C8:** 08, 18, 28, 38, 48, 58
            - **C9:** 09, 19, 29, 39, 49, 59
            - **C10:** 10, 20, 30, 40, 50, 60

            **Distribuição Ideal:** Como temos 6 números sorteados e 10 colunas, a média ideal é **0.6 números por coluna**.

            **Por que isso importa:**
            - É comum ter várias colunas sem números
            - Raramente aparecem 2+ números da mesma coluna
            - Ajuda a evitar padrões verticais
            """)

        fig_colunas = criar_grafico_colunas_volante(analyzer)
        st.plotly_chart(fig_colunas, use_container_width=True)

        analise_colunas = analyzer.analisar_colunas_volante()
        st.write(f"**Padrões de distribuição mais comuns (Top 5):**")
        for i, (padrao, count) in enumerate(analise_colunas['top_padroes'][:5], 1):
            porcentagem = (count / len(df)) * 100
            st.write(f"{i}. `{padrao}` - {count} vezes ({porcentagem:.1f}%)")

        st.markdown("---")

        # NOVO: Padrões a Evitar na Geração de Jogos
        st.subheader("⚠️ Padrões de Concentração a Evitar")

        with st.expander("📖 Por que evitar concentrações", expanded=False):
            st.markdown("""
            ### ⚠️ Concentração de Números

            **Problema:** Jogos com muitos números na mesma linha ou coluna são **estatisticamente raros**.

            **Por que isso importa:**
            - Se 4+ números caem na mesma linha, a probabilidade histórica é muito baixa
            - Se 3+ números caem na mesma coluna, também é raro
            - Evitar esses padrões melhora a "qualidade estatística" do jogo

            **Nossa Estratégia:**
            - Limitar a **máximo 3 números na mesma linha**
            - Limitar a **máximo 2 números na mesma coluna**
            - Garantir boa dispersão pelo volante
            """)

        # Análise de padrões históricos
        padrao_linhas = analyzer.analisar_padrao_linhas_jogo()
        padrao_colunas = analyzer.analisar_padrao_colunas_jogo()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📐 Concentração por Linha")
            st.metric(
                "Jogos com 4+ mesma linha",
                f"{padrao_linhas['evitar_4_ou_mais_mesma_linha']:.1f}%",
                delta="EVITAR",
                delta_color="inverse"
            )
            st.write(f"Média histórica: **{padrao_linhas['media_max_por_linha']:.2f}** números/linha máx")

            st.markdown("**Distribuição histórica:**")
            for k, v in padrao_linhas['max_numeros_mesma_linha'].items():
                emoji = "🟢" if "1_" in k or "2_" in k else ("🟡" if "3_" in k else "🔴")
                st.write(f"{emoji} {k.replace('_', ' ')}: {v:.1f}%")

        with col2:
            st.markdown("### 📊 Concentração por Coluna")
            st.metric(
                "Jogos com 3+ mesma coluna",
                f"{padrao_colunas['evitar_3_ou_mais_mesma_coluna']:.1f}%",
                delta="EVITAR",
                delta_color="inverse"
            )
            st.write(f"Média histórica: **{padrao_colunas['media_max_por_coluna']:.2f}** números/coluna máx")

            st.markdown("**Distribuição histórica:**")
            for k, v in padrao_colunas['max_numeros_mesma_coluna'].items():
                emoji = "🟢" if "0_" in k or "1_" in k else ("🟡" if "2_" in k else "🔴")
                st.write(f"{emoji} {k.replace('_', ' ')}: {v:.1f}%")

        st.success("""
        💡 **Como usamos isso na geração de jogos:**
        - O algoritmo prioriza números dos melhores scores
        - **MAS** rejeita combinações que criariam 4+ números na mesma linha
        - **E** rejeita combinações que criariam 3+ números na mesma coluna
        - Resultado: jogos com boa distribuição pelo volante
        """)

        st.markdown("---")

        # NOVO: Mapa de Calor do Volante
        st.subheader("🗺️ Mapa de Calor do Volante (Linhas × Colunas)")

        with st.expander("📖 Como interpretar o Mapa de Calor", expanded=False):
            st.markdown("""
            ### 🗺️ Mapa de Calor do Volante

            **O que é:**
            Este mapa mostra visualmente a frequência de cada número do volante, organizados em uma grade 6×10.

            **Como ler:**
            - **Verde escuro** = números MUITO frequentes
            - **Amarelo** = frequência média
            - **Vermelho** = números POUCO frequentes

            **Cada célula mostra:**
            - Número da dezena (01-60)
            - Frequência entre parênteses (quantas vezes apareceu)

            **Cruzamento:**
            - **Linhas (horizontal):** L1=01-10, L2=11-20, L3=21-30, L4=31-40, L5=41-50, L6=51-60
            - **Colunas (vertical):** C1=terminados em 1, C2=terminados em 2, ..., C10=terminados em 0

            **Exemplo:**
            - Posição **L3-C5** = Número **25** (linha 3, coluna 5)
            - Posição **L6-C10** = Número **60** (linha 6, coluna 10)

            **Para que serve:**
            - Identificar "pontos quentes" do volante (áreas com números muito sorteados)
            - Evitar concentração em áreas "frias"
            - Distribuir melhor suas apostas pelo volante
            """)

        fig_mapa_calor = criar_mapa_calor_volante(analyzer)
        st.plotly_chart(fig_mapa_calor, use_container_width=True)

        # Análise complementar
        st.markdown("### 📊 Insights do Mapa de Calor")

        # Calcular estatísticas do mapa
        df_temp = analyzer.df
        matriz_freq = np.zeros((6, 10))
        for idx, row in df_temp.iterrows():
            jogo = [row['D1'], row['D2'], row['D3'], row['D4'], row['D5'], row['D6']]
            for num in jogo:
                linha = (num - 1) // 10
                coluna = (num - 1) % 10
                matriz_freq[linha][coluna] += 1

        # Encontrar posições mais e menos frequentes
        max_freq = np.max(matriz_freq)
        min_freq = np.min(matriz_freq)
        pos_max = np.where(matriz_freq == max_freq)
        pos_min = np.where(matriz_freq == min_freq)

        num_max = pos_max[0][0] * 10 + pos_max[1][0] + 1
        num_min = pos_min[0][0] * 10 + pos_min[1][0] + 1

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🔥 Posição Mais Quente", f"{num_max:02d}", delta=f"{int(max_freq)} vezes")

        with col2:
            st.metric("❄️ Posição Mais Fria", f"{num_min:02d}", delta=f"{int(min_freq)} vezes")

        with col3:
            variacao = max_freq - min_freq
            st.metric("📊 Variação", f"{int(variacao)}", delta="diferença")

        st.info("""
        💡 **Interpretação:**
        - Números nas posições "quentes" (verde) aparecem com mais frequência
        - Isso NÃO significa que vão sair mais no próximo sorteio
        - Use para diversificar suas apostas e evitar padrões concentrados
        - Combine números de diferentes regiões do volante (quentes + frios)
        """)

        st.markdown("---")

        # Análise de Ciclos
        st.subheader("🔄 Análise de Ciclos de Renovação Completa")

        with st.expander("📖 O que são Ciclos de Renovação", expanded=False):
            st.markdown("""
            ### 🔄 Ciclos de Renovação Completa

            **Definição:** Um ciclo de renovação completa é o período em que **TODOS os 60 números** aparecem pelo menos 1 vez.

            **Como Calculamos:**
            1. Começamos a contar a partir de um concurso
            2. Marcamos cada número que aparece
            3. Quando todos os 60 números apareceram, o ciclo se completa
            4. Reiniciamos a contagem

            **Por que isso importa:**
            - Ajuda a entender a velocidade de "renovação" dos números
            - Identifica se há números que aparecem mais vezes dentro de um ciclo
            - Baseado na Lei dos Grandes Números (todos os números tendem a aparecer)

            **Teoricamente:** Com 6 números sorteados por vez, esperamos ~10 concursos para cada número aparecer pelo menos 1 vez.
            Então um ciclo completo deveria levar cerca de 60-100 concursos.
            """)

        fig_ciclos = criar_grafico_ciclos(analyzer)
        st.plotly_chart(fig_ciclos, use_container_width=True)

        analise_ciclos = analyzer.analisar_ciclos_renovacao_completa()

        if analise_ciclos['total_ciclos_completos'] > 0:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Ciclo Médio", f"{analise_ciclos['ciclo_medio']:.0f} concursos")
            with col2:
                st.metric("Ciclo Mínimo", f"{analise_ciclos['ciclo_minimo']} concursos")
            with col3:
                st.metric("Ciclo Máximo", f"{analise_ciclos['ciclo_maximo']} concursos")
            with col4:
                st.metric("Total de Ciclos", analise_ciclos['total_ciclos_completos'])

            st.write(f"**Últimos {len(analise_ciclos['ultimos_5_ciclos'])} ciclos:**")
            st.write(", ".join([f"{c:.0f}" for c in analise_ciclos['ultimos_5_ciclos']]))

            st.markdown("---")

            # Status do Ciclo Atual usando o novo método
            st.subheader("🔄 Status do Ciclo Atual")

            # Usar o novo método obter_ciclo_atual()
            ciclo_atual = analyzer.obter_ciclo_atual()

            numero_ciclo = ciclo_atual['numero_ciclo']
            total_ciclos_completos = ciclo_atual['total_ciclos_completos']
            qtd_aparecidos = ciclo_atual['qtd_aparecidos']
            qtd_faltantes = ciclo_atual['qtd_faltantes']
            numeros_faltantes = ciclo_atual['numeros_faltantes']
            progresso_pct = ciclo_atual['progresso_pct']
            concurso_inicio = ciclo_atual['concurso_inicio']
            concurso_atual = ciclo_atual['concurso_atual']
            concursos_no_ciclo = ciclo_atual['concursos_no_ciclo']
            media_concursos = ciclo_atual['media_concursos_por_ciclo']
            estimativa_restante = ciclo_atual['estimativa_concursos_restantes']

            # Header do Ciclo com destaque
            st.markdown(f"## 🎯 CICLO {numero_ciclo}")

            # Info do Ciclo
            if concurso_inicio is not None:
                st.success(f"""
                📍 **Estamos no Ciclo {numero_ciclo}** (após {total_ciclos_completos} ciclos completos)

                🔢 Concurso **{concurso_inicio}** → **{concurso_atual}** ({concursos_no_ciclo} sorteios)

                ✅ Já saíram **{qtd_aparecidos}/60** números ({progresso_pct:.1f}%)

                ❌ Faltam **{qtd_faltantes}** números para completar este ciclo

                📊 Média histórica: **{media_concursos:.1f}** concursos por ciclo

                ⏳ Estimativa: **~{estimativa_restante}** concursos restantes para completar
                """)
            else:
                st.warning("⚠️ Novo ciclo ainda não iniciado (ciclo anterior acabou de completar)")

            # Estimativa de sorteios faltantes
            if qtd_faltantes > 0 and analise_ciclos['ciclo_medio'] > 0:
                sorteios_teoricos_faltantes = int(analise_ciclos['ciclo_medio'] * (qtd_faltantes / 60))
            else:
                sorteios_teoricos_faltantes = 0

            # Métricas do ciclo atual
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Números Aparecidos", f"{qtd_aparecidos}/60", delta=f"{progresso_pct:.1f}%")

            with col2:
                st.metric("Números Faltantes", qtd_faltantes)

            with col3:
                st.metric("Sorteios no Ciclo", concursos_no_ciclo)

            with col4:
                if qtd_faltantes == 0:
                    st.success("✅ CICLO COMPLETO!")
                elif qtd_faltantes <= 5:
                    st.warning("⚠️ Quase completo!")
                elif qtd_faltantes <= 15:
                    st.info("🔄 Avançando...")
                else:
                    st.info(f"🔄 Em progresso")

            # Barra de progresso
            st.progress(progresso_pct / 100)

            # Mostrar números faltantes
            if qtd_faltantes > 0:
                st.markdown("### 🎯 Números que ainda NÃO apareceram no ciclo atual:")

                # Agrupar por dezenas para melhor visualização
                faltantes_formatados = [f"**{num:02d}**" for num in numeros_faltantes]

                # Dividir em linhas de 10 números
                linhas_display = []
                for i in range(0, len(faltantes_formatados), 10):
                    linhas_display.append(" - ".join(faltantes_formatados[i:i+10]))

                for linha in linhas_display:
                    st.markdown(linha)

                # Análise dos faltantes com 3 faixas
                st.markdown("---")
                st.markdown("### 📊 Perfil dos Números Faltantes:")

                pares_faltantes = sum(1 for n in numeros_faltantes if n % 2 == 0)
                impares_faltantes = qtd_faltantes - pares_faltantes
                baixos_faltantes = sum(1 for n in numeros_faltantes if 1 <= n <= 20)
                medios_faltantes = sum(1 for n in numeros_faltantes if 21 <= n <= 40)
                altos_faltantes = sum(1 for n in numeros_faltantes if 41 <= n <= 60)

                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric("Pares", pares_faltantes)
                with col2:
                    st.metric("Ímpares", impares_faltantes)
                with col3:
                    st.metric("Baixos (1-20)", baixos_faltantes)
                with col4:
                    st.metric("Médios (21-40)", medios_faltantes)
                with col5:
                    st.metric("Altos (41-60)", altos_faltantes)

                st.info(f"""
                💡 **Interpretação:**
                - Estes **{qtd_faltantes} números** têm maior chance teórica de aparecer nos próximos sorteios
                - **Ciclo {numero_ciclo}:** {concursos_no_ciclo} sorteios desde o concurso {concurso_inicio}
                - Baseado na **Lei dos Grandes Números**, todos tendem a aparecer ao longo do tempo
                - Estimativa: apareçam nos próximos **~{estimativa_restante} sorteios** (baseado na média de {media_concursos:.1f} concursos/ciclo)
                - **MAS ATENÇÃO:** Cada sorteio é independente! Números "atrasados" não têm garantia de sair
                """)
            else:
                # Ciclo completo - não há números faltantes
                st.success(f"""
                🎉 **CICLO COMPLETO!**

                Todos os 60 números apareceram entre os concursos **{concurso_inicio}** e **{concurso_atual}**!
                Total: **{concursos_no_ciclo} sorteios** para completar o ciclo.

                Um novo ciclo está começando agora!
                """)

            # Histórico de Ciclos (sempre exibido)
            st.markdown("---")
            st.subheader("📅 Histórico de Ciclos Completos")

            todos_ciclos = ciclo_atual.get('todos_ciclos', [])
            ultimos_ciclos = ciclo_atual.get('ultimos_ciclos', [])

            if todos_ciclos:
                # Mostrar últimos 5 ciclos por padrão
                st.markdown(f"**Últimos 5 ciclos (de {len(todos_ciclos)} completos):**")
                for ciclo_info in reversed(ultimos_ciclos):
                    st.write(f"**Ciclo {ciclo_info['numero_ciclo']}:** Concurso {ciclo_info['concurso_inicio']} → {ciclo_info['concurso_fim']} ({ciclo_info['tamanho']} sorteios)")

                # Expander para ver todos os ciclos
                with st.expander(f"📋 Ver todos os {len(todos_ciclos)} ciclos completos", expanded=False):
                    # Criar DataFrame para exibição
                    df_ciclos = pd.DataFrame(todos_ciclos)
                    df_ciclos.columns = ['Ciclo', 'Concurso Início', 'Concurso Fim', 'Duração (sorteios)']
                    st.dataframe(df_ciclos, use_container_width=True, height=400)
            else:
                st.write("Nenhum ciclo completo registrado ainda.")

        else:
            st.warning("⚠️ Não há dados suficientes para completar um ciclo de renovação completa (todos os 60 números).")

    # ------------------------------------------------------------------------
    # TAB 4: PERFIS DE JOGOS
    # ------------------------------------------------------------------------

    with tab4:
        st.header("📋 Perfis Completos de Jogos")

        st.info("""
        Análise detalhada de cada jogo vencedor com todos os padrões estatísticos identificados.
        Use os filtros abaixo para encontrar jogos com características específicas.
        """)

        # Explicação detalhada das métricas
        with st.expander("📖 O que significa cada métrica?", expanded=False):
            st.markdown("""
            ### 📊 Explicação das Métricas de Perfil

            **🔢 SOMA**
            - É a soma de todos os 6 números sorteados
            - Exemplo: 05+12+23+34+45+56 = **175**
            - **Mínimo teórico:** 1+2+3+4+5+6 = 21
            - **Máximo teórico:** 55+56+57+58+59+60 = 345
            - **Faixa mais comum:** Entre **150 e 200** (cerca de 60% dos sorteios)
            - **Por que importa:** Somas muito baixas (<100) ou muito altas (>250) são raras

            ---

            **⚖️ PARES / ÍMPARES**
            - Quantidade de números pares e ímpares no jogo
            - Padrão mais comum: **3 Pares + 3 Ímpares** (~32% dos jogos)
            - Extremos (0P-6I ou 6P-0I) são muito raros (<1%)

            ---

            **📊 BAIXOS (1-30) / ALTOS (31-60)**
            - Divisão dos números em duas faixas
            - Padrão mais comum: **3 Baixos + 3 Altos** (~35% dos jogos)
            - Extremos são raros

            ---

            **📏 GAP (Espaçamento)**
            - Diferença entre números consecutivos do jogo (ordenado)
            - Exemplo: 05, 12, 23, 34, 45, 56 → Gaps: 7, 11, 11, 11, 11 → **Gap Médio: 10.2**
            - **Gap Mínimo:** Menor espaço entre dois números consecutivos
            - **Gap Máximo:** Maior espaço entre dois números consecutivos
            - **Por que importa:** Gaps muito pequenos = números concentrados; Gaps grandes = números espalhados

            ---

            **🔗 SEQUÊNCIAS**
            - Quantidade de números consecutivos no jogo
            - Exemplo: 05, **06, 07**, 23, 34, 45 → **2 sequências** (06-07)
            - A maioria dos jogos tem 0-1 sequências
            - Jogos com 3+ sequências são raros

            ---

            **📍 LINHAS COM NÚMEROS**
            - Quantas das 6 linhas do volante têm pelo menos 1 número
            - Volante: L1 (01-10), L2 (11-20), L3 (21-30), L4 (31-40), L5 (41-50), L6 (51-60)
            - Valor típico: **4-5 linhas** ativas
            - 6 linhas ativas = números muito distribuídos

            ---

            **🎯 Q1, Q2, Q3, Q4 (Quadrantes)**
            - Distribuição pelos 4 quadrantes do volante
            - Q1: Superior Esquerdo (01-05, 11-15, 21-25)
            - Q2: Superior Direito (06-10, 16-20, 26-30)
            - Q3: Inferior Esquerdo (31-35, 41-45, 51-55)
            - Q4: Inferior Direito (36-40, 46-50, 56-60)
            - Distribuição ideal: ~1.5 números por quadrante
            """)

        # Gerar perfis
        perfis_df = analyzer.criar_perfis_de_jogos()

        # Filtros interativos
        st.subheader("🔍 Filtros")

        col1, col2, col3 = st.columns(3)

        with col1:
            filtro_pares = st.multiselect(
                "Quantidade de Pares",
                options=[0, 1, 2, 3, 4, 5, 6],
                default=[2, 3, 4]
            )

        with col2:
            filtro_baixos = st.multiselect(
                "Quantidade de Baixos (1-30)",
                options=[0, 1, 2, 3, 4, 5, 6],
                default=[2, 3, 4]
            )

        with col3:
            soma_min = st.number_input("Soma Mínima", value=100, step=10)
            soma_max = st.number_input("Soma Máxima", value=300, step=10)

        # Aplicar filtros
        perfis_filtrados = perfis_df[
            (perfis_df['Pares'].isin(filtro_pares)) &
            (perfis_df['Baixos_1_30'].isin(filtro_baixos)) &
            (perfis_df['Soma'] >= soma_min) &
            (perfis_df['Soma'] <= soma_max)
        ]

        st.success(f"✅ **{len(perfis_filtrados)}** jogos encontrados com os filtros selecionados (de {len(perfis_df)} totais)")

        # Tabela de perfis
        st.subheader("📊 Tabela de Perfis")

        colunas_exibir = [
            'Concurso', 'Dezenas', 'Soma',
            'Pares', 'Impares',
            'Baixos_1_30', 'Altos_31_60',
            'Linhas_Com_Numeros', 'Gap_Medio', 'Sequencias',
            'Q1', 'Q2', 'Q3', 'Q4'
        ]

        st.dataframe(
            perfis_filtrados[colunas_exibir].head(100),
            use_container_width=True,
            height=600
        )

        # Download CSV
        csv = perfis_filtrados.to_csv(index=False)
        st.download_button(
            label="📥 Download Perfis Filtrados (CSV)",
            data=csv,
            file_name="perfis_megasena_filtrados.csv",
            mime="text/csv"
        )

        st.markdown("---")

        # Estatísticas dos perfis filtrados
        if len(perfis_filtrados) > 0:
            st.subheader("📈 Estatísticas dos Jogos Filtrados")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Soma Média", f"{perfis_filtrados['Soma'].mean():.1f}")
                st.metric("Pares Médio", f"{perfis_filtrados['Pares'].mean():.1f}")

            with col2:
                st.metric("Gap Médio", f"{perfis_filtrados['Gap_Medio'].mean():.2f}")
                st.metric("Sequências Média", f"{perfis_filtrados['Sequencias'].mean():.1f}")

            with col3:
                st.metric("Linhas Ativas", f"{perfis_filtrados['Linhas_Com_Numeros'].mean():.1f}")
                st.metric("Q1 Médio", f"{perfis_filtrados['Q1'].mean():.1f}")

            with col4:
                st.metric("Baixos Médio", f"{perfis_filtrados['Baixos_1_30'].mean():.1f}")
                st.metric("Altos Médio", f"{perfis_filtrados['Altos_31_60'].mean():.1f}")

    # ------------------------------------------------------------------------
    # TAB 5: SUGESTÃO PERSONALIZADA POR BUDGET
    # ------------------------------------------------------------------------

    with tab5:
        st.header("🎲 Sugestão Personalizada - Otimização Completa do Budget")

        st.info(f"""
        💰 **Seu Budget:** R$ {budget:,.2f}

        **Estratégia de Otimização:**
        - Gastar TODO o seu dinheiro disponível
        - Combinar diferentes tipos de jogos (grandes + médios + pequenos)
        - Diversificar estratégias para maximizar cobertura
        - Aproveitar ao máximo cada centavo investido
        """)

        # Calcular scores
        scores_df = analyzer.calcular_todos_scores()

        # Otimizar budget completo
        resultado_otimizacao = otimizar_budget_completo(budget, analyzer, scores_df)

        if not resultado_otimizacao['jogos']:
            st.error("Budget insuficiente. Mínimo: R$ 6,00")
        else:
            # Calcular probabilidades combinadas e índice de perfeição
            prob_combinada = calcular_probabilidade_combinada(resultado_otimizacao['jogos'])
            indice_perf = calcular_indice_perfeicao(resultado_otimizacao['jogos'])

            # Resumo da otimização
            st.markdown("---")
            st.subheader("📊 Resumo da Otimização")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total de Jogos", resultado_otimizacao['total_jogos'])

            with col2:
                st.metric("Total Gasto", f"R$ {resultado_otimizacao['total_gasto']:,.2f}")

            with col3:
                st.metric("Sobra", f"R$ {resultado_otimizacao['resto']:,.2f}")

            with col4:
                st.metric("Aproveitamento", f"{resultado_otimizacao['aproveitamento']:.1f}%")

            # Barra de progresso do aproveitamento
            st.progress(resultado_otimizacao['aproveitamento'] / 100)

            if resultado_otimizacao['aproveitamento'] >= 95:
                st.success(f"✅ **EXCELENTE!** Você está usando {resultado_otimizacao['aproveitamento']:.1f}% do seu budget!")
            elif resultado_otimizacao['aproveitamento'] >= 85:
                st.info(f"👍 **BOM!** Você está usando {resultado_otimizacao['aproveitamento']:.1f}% do seu budget.")
            else:
                st.warning(f"⚠️ Aproveitamento de {resultado_otimizacao['aproveitamento']:.1f}%. Considere ajustar seu budget para melhor aproveitamento.")

            # ============================================
            # PROBABILIDADES COMBINADAS
            # ============================================
            st.markdown("---")
            st.subheader("🎰 Suas Chances Combinadas")

            st.info("""
            **Como funciona:** Combinando todos os seus jogos, calculamos a probabilidade de você
            acertar **pelo menos uma vez** a Sena, Quina ou Quadra.
            """)

            col_p1, col_p2, col_p3 = st.columns(3)

            with col_p1:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                            padding: 1.5rem; border-radius: 15px; text-align: center; color: #333;'>
                    <h3 style='margin: 0; font-size: 1.2rem;'>🏆 SENA</h3>
                    <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>1 em {:,.0f}</p>
                    <p style='font-size: 0.9rem; margin: 0;'>{:.6f}%</p>
                </div>
                """.format(prob_combinada['chance_sena'], prob_combinada['percentual_sena']), unsafe_allow_html=True)

            with col_p2:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #C0C0C0 0%, #A0A0A0 100%);
                            padding: 1.5rem; border-radius: 15px; text-align: center; color: #333;'>
                    <h3 style='margin: 0; font-size: 1.2rem;'>🥈 QUINA</h3>
                    <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>1 em {:,.0f}</p>
                    <p style='font-size: 0.9rem; margin: 0;'>{:.4f}%</p>
                </div>
                """.format(prob_combinada['chance_quina'], prob_combinada['percentual_quina']), unsafe_allow_html=True)

            with col_p3:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%);
                            padding: 1.5rem; border-radius: 15px; text-align: center; color: white;'>
                    <h3 style='margin: 0; font-size: 1.2rem;'>🥉 QUADRA</h3>
                    <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>1 em {:,.0f}</p>
                    <p style='font-size: 0.9rem; margin: 0;'>{:.2f}%</p>
                </div>
                """.format(prob_combinada['chance_quadra'], prob_combinada['percentual_quadra']), unsafe_allow_html=True)

            # ============================================
            # ÍNDICE DE PERFEIÇÃO
            # ============================================
            st.markdown("---")
            st.subheader("📈 Índice de Perfeição dos Indicadores")

            st.info("""
            **O que é:** Medimos o quão próximo seus jogos estão do "perfil ideal" baseado nos 12 critérios
            de análise estatística. Quanto maior, melhor a qualidade dos números selecionados.
            """)

            # Gauge visual do índice
            indice = indice_perf['indice_total']
            classificacao = indice_perf['classificacao']

            # Cor baseada no índice
            if indice >= 85:
                cor_indice = "#00cc44"  # Verde
                emoji_class = "🌟"
            elif indice >= 70:
                cor_indice = "#66bb6a"  # Verde claro
                emoji_class = "✨"
            elif indice >= 55:
                cor_indice = "#ffa726"  # Laranja
                emoji_class = "👍"
            else:
                cor_indice = "#ef5350"  # Vermelho
                emoji_class = "⚠️"

            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {cor_indice}33 0%, {cor_indice}66 100%);
                        padding: 2rem; border-radius: 15px; text-align: center; border: 3px solid {cor_indice};'>
                <h2 style='margin: 0; font-size: 3rem; color: {cor_indice};'>{indice:.1f}%</h2>
                <p style='font-size: 1.5rem; margin: 0.5rem 0;'>{emoji_class} {classificacao}</p>
            </div>
            """, unsafe_allow_html=True)

            st.progress(indice / 100)

            # Detalhes do índice em expander
            with st.expander("📊 Ver Detalhes dos Critérios", expanded=False):
                detalhes = indice_perf['detalhes']

                st.markdown("### Pontuação por Critério (máx. 100 cada)")

                criterios_data = [
                    ("Score Médio", detalhes.get('score_medio', {}).get('pontos', 0), f"Valor: {detalhes.get('score_medio', {}).get('valor', 0)}"),
                    ("Paridade (Par/Ímpar)", detalhes.get('paridade', {}).get('pontos', 0), f"Desvio: {detalhes.get('paridade', {}).get('desvio', '0%')}"),
                    ("Baixo/Médio/Alto", detalhes.get('baixo_medio_alto', {}).get('pontos', 0), f"Desvio: {detalhes.get('baixo_medio_alto', {}).get('desvio', '0%')}"),
                    ("Soma Ideal", detalhes.get('soma_ideal', {}).get('pontos', 0), "Faixa 150-200 proporcional"),
                    ("Cobertura Linhas", detalhes.get('cobertura_linhas', {}).get('pontos', 0), f"Usadas: {detalhes.get('cobertura_linhas', {}).get('usadas', 0)}/6"),
                    ("Cobertura Colunas", detalhes.get('cobertura_colunas', {}).get('pontos', 0), f"Usadas: {detalhes.get('cobertura_colunas', {}).get('usadas', 0)}/10"),
                    ("Números do Ciclo", detalhes.get('numeros_ciclo', {}).get('pontos', 0), f"Média: {detalhes.get('numeros_ciclo', {}).get('media', 0)} por jogo"),
                    ("Diversificação", detalhes.get('diversificacao', {}).get('pontos', 0), f"{detalhes.get('diversificacao', {}).get('unicos', 0)} únicos de {detalhes.get('diversificacao', {}).get('total', 0)} total"),
                ]

                for criterio, pontos, detalhe in criterios_data:
                    col_a, col_b, col_c = st.columns([3, 2, 3])
                    with col_a:
                        st.write(f"**{criterio}**")
                    with col_b:
                        if pontos >= 80:
                            st.success(f"{pontos:.1f}")
                        elif pontos >= 60:
                            st.info(f"{pontos:.1f}")
                        elif pontos >= 40:
                            st.warning(f"{pontos:.1f}")
                        else:
                            st.error(f"{pontos:.1f}")
                    with col_c:
                        st.caption(detalhe)

            st.markdown("---")

            # Exibir todos os jogos sugeridos
            st.subheader(f"🎯 Seus {resultado_otimizacao['total_jogos']} Jogos Otimizados")

            for i, jogo in enumerate(resultado_otimizacao['jogos'], 1):
                perfil = jogo.get('perfil', {})
                dezenas_str = ' - '.join([f'{d:02d}' for d in jogo['dezenas']])
                titulo_jogo = f"Jogo {i} | {jogo['quantidade_numeros']} num | {dezenas_str} | R$ {jogo['custo']:,.2f}"
                with st.expander(titulo_jogo, expanded=False):

                    # Exibir dezenas primeiro (destaque)
                    dezenas = jogo['dezenas']
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                padding: 2rem; border-radius: 15px; text-align: center; color: white;'>
                        <h2 style='font-size: 1.8rem; margin: 0.5rem 0;'>
                            {' - '.join([f'{d:02d}' for d in dezenas])}
                        </h2>
                    </div>
                    """, unsafe_allow_html=True)

                    # Volante visual
                    exibir_volante_interativo(dezenas)

                    st.markdown("---")

                    # Métricas do jogo em 2 linhas
                    st.markdown("### 📊 Perfil do Jogo")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Dezenas", jogo['quantidade_numeros'])
                        st.metric("Custo", f"R$ {jogo['custo']:,.2f}")

                    with col2:
                        pares = perfil.get('pares', sum(1 for d in dezenas if d % 2 == 0))
                        impares = perfil.get('impares', len(dezenas) - pares)
                        st.metric("Par/Ímpar", f"{pares}P - {impares}I")
                        st.metric("Prob. Sena", jogo['prob_sena'])

                    with col3:
                        baixos = perfil.get('baixos', sum(1 for d in dezenas if 1 <= d <= 20))
                        medios = perfil.get('medios', sum(1 for d in dezenas if 21 <= d <= 40))
                        altos = perfil.get('altos', sum(1 for d in dezenas if 41 <= d <= 60))
                        st.metric("Baixo/Médio/Alto", f"{baixos}B-{medios}M-{altos}A")
                        st.metric("Soma Total", perfil.get('soma', sum(dezenas)))

                    with col4:
                        st.metric("Score Médio", f"{perfil.get('score_medio', 0):.1f}")
                        faltantes = perfil.get('faltantes_ciclo', 0)
                        st.metric("Núm. do Ciclo", f"{faltantes} incluídos")

                    # Segunda linha de métricas (linhas/colunas)
                    col5, col6, col7, col8 = st.columns(4)
                    with col5:
                        max_lin = perfil.get('max_linha', '-')
                        linhas_usadas = perfil.get('linhas_usadas', '-')
                        st.metric("Máx. Mesma Linha", f"{max_lin} (usa {linhas_usadas}/6)")
                    with col6:
                        max_col = perfil.get('max_coluna', '-')
                        colunas_usadas = perfil.get('colunas_usadas', '-')
                        st.metric("Máx. Mesma Coluna", f"{max_col} (usa {colunas_usadas}/10)")
                    with col7:
                        soma_val = perfil.get('soma', sum(dezenas))
                        soma_status = "✅" if 150 <= soma_val <= 200 else "⚠️"
                        st.metric("Soma", f"{soma_val} {soma_status}")
                    with col8:
                        alertas = perfil.get('alertas_distribuicao', [])
                        if alertas:
                            st.warning(" | ".join(alertas))
                        else:
                            st.success("✅ Distribuição OK")

                    # Justificativa da estratégia
                    st.markdown("---")
                    st.success(f"""
                    **🎯 Critérios de Seleção Aplicados:**

                    1. ✅ **Ranking de Scores:** Números com melhor pontuação geral (frequência + atraso + tendência + etc.)
                    2. ✅ **Ciclo Atual:** Prioridade para {faltantes} números que ainda não apareceram no ciclo
                    3. ✅ **Equilíbrio Par/Ímpar:** {pares} pares e {impares} ímpares (ideal: ~50/50)
                    4. ✅ **Equilíbrio B/M/A:** {baixos} baixos, {medios} médios, {altos} altos
                    5. ✅ **Soma:** {perfil.get('soma', sum(dezenas))} (faixa ideal: 150-200 para 6 números)
                    6. ✅ **Linhas/Colunas:** Máx {perfil.get('max_linha', '?')} na mesma linha, {perfil.get('max_coluna', '?')} na mesma coluna
                    7. ✅ **Diversificação:** Números diferentes dos outros jogos
                    """)

                    # Justificativa dos números (apenas para jogos menores - até 10 números)
                    if len(dezenas) <= 10:
                        st.markdown("---")
                        st.markdown("### 🤔 Por que cada número?")

                        justificativas = gerar_justificativa_numeros(dezenas, analyzer, scores_df)

                        for just in justificativas:
                            with st.expander(f"Número {just['numero']:02d}"):
                                for razao in just['razoes']:
                                    st.markdown(f"✅ {razao}")

                    # Comparação com histórico (apenas para jogos simples de 6 números)
                    if len(dezenas) == 6:
                        st.markdown("---")
                        st.markdown("### 📊 Jogos Similares que já Ganharam")

                        jogos_similares = comparar_com_historico(dezenas, analyzer)

                        if jogos_similares:
                            st.success(f"Encontramos **{len(jogos_similares)} jogos vencedores** com padrão similar!")

                            for jogo_hist in jogos_similares[:5]:  # Top 5
                                st.write(f"**Concurso {jogo_hist['concurso']}:** {' - '.join([f'{d:02d}' for d in jogo_hist['dezenas']])}")
                                st.write(f"   ↳ Padrão: {jogo_hist['padrao']}")
                        else:
                            st.warning("Padrão único - não encontramos jogos similares no histórico.")

            st.markdown("---")
            st.success(f"""
            🎉 **OTIMIZAÇÃO COMPLETA!**

            Você está investindo R$ {resultado_otimizacao['total_gasto']:,.2f} ({resultado_otimizacao['aproveitamento']:.1f}% do budget)
            em {resultado_otimizacao['total_jogos']} jogos diversificados com diferentes estratégias!

            **Vantagens desta abordagem:**
            - ✅ Maximiza uso do budget disponível
            - ✅ Diversifica estratégias (top scores + cold + balanced + median)
            - ✅ Combina jogos grandes (maior cobertura) + jogos pequenos (maior quantidade)
            - ✅ Aumenta suas chances cobrindo diferentes cenários estatísticos

            💡 **Lembre-se:** Jogue com responsabilidade e nunca aposte mais do que pode perder!
            """)

    # ------------------------------------------------------------------------
    # TAB 6: TABELA DE CUSTOS OFICIAL
    # ------------------------------------------------------------------------

    with tab6:
        st.header("💰 Tabela Oficial de Custos e Probabilidades")

        st.info("Tabela oficial da Caixa Econômica Federal com valores e probabilidades por quantidade de números jogados.")

        # Criar DataFrame
        tabela_df = pd.DataFrame([
            {
                "Números": k,
                "Valor (R$)": f"R$ {v['valor']:,.2f}",
                "Prob. Sena": v['prob_sena'],
                "Prob. Quina": v['prob_quina'],
                "Prob. Quadra": v['prob_quadra']
            }
            for k, v in TABELA_CAIXA.items()
        ])

        st.dataframe(
            tabela_df,
            use_container_width=True,
            height=600
        )

        st.markdown("---")

        st.success("""
        ### 📊 Como Interpretar esta Tabela

        - **Números:** Quantidade de dezenas marcadas no volante
        - **Valor:** Custo do jogo
        - **Prob. Sena:** Probabilidade de acertar as 6 dezenas
        - **Prob. Quina:** Probabilidade de acertar 5 dezenas
        - **Prob. Quadra:** Probabilidade de acertar 4 dezenas

        **Exemplo:** Um jogo de 10 números custa R$ 1.260,00 e tem probabilidade de 1 em 238.399 de ganhar a sena.
        """)

    # ------------------------------------------------------------------------
    # TAB 7: DADOS BRUTOS
    # ------------------------------------------------------------------------

    with tab7:
        st.header("💾 Dados Brutos - Histórico de Sorteios")

        st.info("""
        Acesse os dados históricos completos dos sorteios. Você pode visualizar, filtrar e fazer download para análises próprias.
        """)

        # Opções de visualização
        st.subheader("📊 Visualização dos Dados")

        col1, col2 = st.columns(2)

        with col1:
            qtd_mostrar = st.selectbox(
                "Quantidade de registros",
                options=[50, 100, 200, 500, 1000, "Todos"],
                index=1
            )

        with col2:
            ordem = st.selectbox(
                "Ordenação",
                options=["Mais Recentes Primeiro", "Mais Antigos Primeiro"],
                index=0
            )

        # Preparar DataFrame
        df_mostrar = df.copy()

        if ordem == "Mais Recentes Primeiro":
            df_mostrar = df_mostrar.sort_values('Concurso', ascending=False)
        else:
            df_mostrar = df_mostrar.sort_values('Concurso', ascending=True)

        if qtd_mostrar != "Todos":
            df_mostrar = df_mostrar.head(qtd_mostrar)

        # Mostrar tabela
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            height=600
        )

        st.markdown("---")

        # Estatísticas rápidas
        st.subheader("📈 Estatísticas Rápidas")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total de Registros", len(df))

        with col2:
            todas_dezenas = []
            for col in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']:
                todas_dezenas.extend(df[col].tolist())
            st.metric("Total de Sorteios", len(df) * 6)

        with col3:
            st.metric("Menor Número", min(todas_dezenas))
            st.metric("Maior Número", max(todas_dezenas))

        with col4:
            soma_media = df[['D1', 'D2', 'D3', 'D4', 'D5', 'D6']].sum(axis=1).mean()
            st.metric("Soma Média", f"{soma_media:.1f}")

        st.markdown("---")

        # Download
        st.subheader("📥 Download dos Dados")

        col1, col2 = st.columns(2)

        with col1:
            # CSV
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV Completo",
                data=csv_data,
                file_name="megasena_historico_completo.csv",
                mime="text/csv"
            )

        with col2:
            # Excel
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Mega-Sena')
            buffer.seek(0)

            st.download_button(
                label="📊 Download Excel Completo",
                data=buffer,
                file_name="megasena_historico_completo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.success("""
        💡 **Dica:** Use estes dados para fazer suas próprias análises em ferramentas como Excel, Python, R, ou qualquer software de análise estatística.
        """)

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background-color: #f0f2f6; border-radius: 10px;'>
        <h3>⚠️ DISCLAIMER IMPORTANTE ⚠️</h3>
        <p style='font-size: 1.1rem; color: #666;'>
            Este sistema é uma ferramenta de <b>ANÁLISE ESTATÍSTICA</b> e <b>NÃO garante ganhos</b>.<br>
            A Mega-Sena é um jogo de azar onde cada sorteio é um evento <b>INDEPENDENTE</b>.<br>
            A esperança matemática de qualquer loteria é <b>NEGATIVA</b>.<br><br>
            <b>JOGUE COM RESPONSABILIDADE. NUNCA APOSTE MAIS DO QUE PODE PERDER.</b>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
