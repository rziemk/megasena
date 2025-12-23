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
from strategies import EstrategiaA, EstrategiaB, ComparadorEstrategias

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

@st.cache_data
def carregar_dados(source='synthetic', file=None):
    """Carrega dados com cache."""
    try:
        if source == 'synthetic':
            return load_data('synthetic')
        elif source == 'excel' and file is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(file.getvalue())
                tmp_path = tmp.name
            return load_data('excel', tmp_path)
        elif source == 'csv' and file is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                tmp.write(file.getvalue())
                tmp_path = tmp.name
            return load_data('csv', tmp_path)
        return load_data('synthetic')
    except Exception as e:
        st.error(f"""
        ❌ **Erro ao carregar arquivo:**

        {str(e)}

        **Formato esperado:**
        - Colunas: Concurso, Data, D1, D2, D3, D4, D5, D6
        - Ou: Número, Data, Bola1, Bola2, Bola3, Bola4, Bola5, Bola6
        - Valores das dezenas entre 1 e 60

        **Dica:** Use dados sintéticos para testar primeiro!
        """)
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
        ### 📊 Como calculamos Alto/Baixo

        **Divisão:**
        - **Baixos:** 1 a 30
        - **Altos:** 31 a 60

        **Análise:**
        - Contamos quantos números de cada faixa aparecem em cada sorteio
        - Padrão mais comum: **3 Baixos + 3 Altos** (~35% dos casos)

        **Por que isso importa?**
        - Extremos (6 baixos ou 6 altos) são raríssimos
        - A tendência é o equilíbrio

        **Exemplo:** 12, 18, 25, 38, 45, 56 = 3 Baixos + 3 Altos ✅
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

        **Fórmula Ponderada:**

        ```
        Score = (Frequência × 0.25) +
                (Atraso × 0.20) +
                (Tendência × 0.15) +
                (Quadrante × 0.15) +
                (Paridade × 0.10) +
                (Alto/Baixo × 0.10) +
                (Poisson × 0.05)
        ```

        **Componentes:**
        1. **Frequência (25%)**: Baseada em aparições históricas
        2. **Atraso (20%)**: Regressão à média (quanto mais atrasado, maior o score)
        3. **Tendência (15%)**: Desempenho recente (últimos 50 jogos)
        4. **Quadrante (15%)**: Equilíbrio espacial no volante
        5. **Paridade (10%)**: Contribuição para balanço par/ímpar
        6. **Alto/Baixo (10%)**: Contribuição para balanço de faixas
        7. **Poisson (5%)**: Probabilidade estatística

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
    # Header
    st.markdown('<div class="main-header">🎰 MEGA-SENA</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Análise Estatística Avançada com IA</div>', unsafe_allow_html=True)

    # ========================================================================
    # SIDEBAR - CONFIGURAÇÕES
    # ========================================================================

    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/lottery.png", width=80)
        st.title("⚙️ Configurações")

        st.markdown("---")

        # Upload de arquivo
        st.subheader("📁 Carregar Dados")
        opcao_dados = st.radio(
            "Fonte dos dados:",
            ["Demonstração (Sintético)", "Upload Excel", "Upload CSV"]
        )

        uploaded_file = None
        if opcao_dados == "Upload Excel":
            uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=['xlsx', 'xls'])
        elif opcao_dados == "Upload CSV":
            uploaded_file = st.file_uploader("Escolha o arquivo CSV", type=['csv'])

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
        1. Carregue seus dados ou use demonstração
        2. Defina seu budget
        3. Explore as análises nas abas
        4. Veja as sugestões personalizadas
        5. Jogue com responsabilidade!
        """)

        st.warning("⚠️ Este é um sistema de análise estatística. NÃO garante ganhos.")

    # ========================================================================
    # CARREGAR DADOS
    # ========================================================================

    with st.spinner("Carregando dados..."):
        if opcao_dados == "Demonstração (Sintético)":
            df = carregar_dados('synthetic')
        elif opcao_dados == "Upload Excel" and uploaded_file:
            df = carregar_dados('excel', uploaded_file)
        elif opcao_dados == "Upload CSV" and uploaded_file:
            df = carregar_dados('csv', uploaded_file)
        else:
            df = carregar_dados('synthetic')

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

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Análises Estatísticas",
        "🏆 Ranking de Scores",
        "🔬 Análises Avançadas",
        "📋 Perfis de Jogos",
        "🎯 Estratégias",
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
        st.write("**Top 5 Padrões Mais Comuns:**")
        for i, (padrao, count) in enumerate(list(paridade.items())[:5], 1):
            porcentagem = (count / len(df)) * 100
            st.write(f"{i}. **{padrao}** - {count} vezes ({porcentagem:.1f}%)")

        st.markdown("---")

        # Alto/Baixo
        st.subheader("4️⃣ Análise Alto/Baixo")

        with st.expander("📖 Como Calculamos esta Métrica", expanded=False):
            st.markdown(explicar_metrica("alto_baixo"))

        alto_baixo = analyzer.analisar_alto_baixo()
        st.write("**Top 5 Padrões Mais Comuns:**")
        for i, (padrao, count) in enumerate(list(alto_baixo.items())[:5], 1):
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

    # ------------------------------------------------------------------------
    # TAB 2: RANKING DE SCORES COM EXPLICAÇÃO
    # ------------------------------------------------------------------------

    with tab2:
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
    # TAB 3: ANÁLISES AVANÇADAS
    # ------------------------------------------------------------------------

    with tab3:
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
    # TAB 5: ESTRATÉGIAS
    # ------------------------------------------------------------------------

    with tab5:
        st.header("🎯 Comparação de Estratégias")

        st.info("""
        Comparamos duas estratégias diferentes de seleção de números baseadas em critérios estatísticos distintos.
        """)

        # Calcular scores
        scores_df = analyzer.calcular_todos_scores()

        # Estratégia A: Sniper (Top scores)
        st.subheader("🎯 Estratégia A: SNIPER (Precisão)")

        with st.expander("📖 Como funciona a Estratégia Sniper", expanded=False):
            st.markdown("""
            ### 🎯 Estratégia SNIPER

            **Filosofia:** "Atire nos alvos certos com precisão matemática"

            **Critérios:**
            - Seleciona os números com **MAIOR score final** (Top performers)
            - Baseado em múltiplos fatores combinados:
              * Frequência histórica
              * Atraso (regressão à média)
              * Tendência recente
              * Equilíbrio espacial no volante

            **Vantagens:**
            - Baseado em análise estatística profunda
            - Maximiza probabilidade teórica
            - Equilibrado e racional

            **Desvantagens:**
            - Pode ser muito "óbvio" (muitas pessoas usam)
            - Menor potencial de premiação exclusiva
            """)

        estrategia_a = EstrategiaA(analyzer)
        jogo_a_obj = estrategia_a.gerar_jogo_principal()
        jogo_a = jogo_a_obj.dezenas[:6]  # Pega apenas 6 números para exibição

        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 15px; text-align: center; color: white;'>
            <h3>Jogo Estratégia A (Sniper)</h3>
            <h1 style='font-size: 2rem; margin: 1rem 0;'>
                {' - '.join([f'{d:02d}' for d in sorted(jogo_a)])}
            </h1>
        </div>
        """, unsafe_allow_html=True)

        exibir_volante_interativo(jogo_a)

        st.markdown("---")

        # Estratégia B: Bomber (Diversificação)
        st.subheader("💣 Estratégia B: BOMBER (Diversificação)")

        with st.expander("📖 Como funciona a Estratégia Bomber", expanded=False):
            st.markdown("""
            ### 💣 Estratégia BOMBER

            **Filosofia:** "Cubra mais área com diversificação inteligente"

            **Critérios:**
            - Combina números de **diferentes perfis**:
              * 40% Top scores (alta probabilidade)
              * 30% Números atrasados (regressão à média)
              * 20% Números quentes (momentum)
              * 10% Zebras (surpresa)
            - Garante equilíbrio par/ímpar e alto/baixo
            - Distribui pelos quadrantes do volante

            **Vantagens:**
            - Maior diversificação
            - Cobre diferentes cenários estatísticos
            - Potencial de premiação exclusiva se acertar

            **Desvantagens:**
            - Menos focado em probabilidade pura
            - Maior variância nos resultados
            """)

        estrategia_b = EstrategiaB(analyzer)
        jogo_b_obj = estrategia_b.gerar_jogo_principal()
        jogo_b = jogo_b_obj.dezenas[:6]  # Pega apenas 6 números para exibição

        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 2rem; border-radius: 15px; text-align: center; color: white;'>
            <h3>Jogo Estratégia B (Bomber)</h3>
            <h1 style='font-size: 2rem; margin: 1rem 0;'>
                {' - '.join([f'{d:02d}' for d in sorted(jogo_b)])}
            </h1>
        </div>
        """, unsafe_allow_html=True)

        exibir_volante_interativo(jogo_b)

        st.markdown("---")

        # Comparação lado a lado
        st.subheader("⚖️ Comparação Lado a Lado")

        comparador = ComparadorEstrategias(analyzer)
        comparacao_result = comparador.comparar()

        col1, col2 = st.columns(2)

        # Calcular perfis dos jogos
        equilibrio_a = analyzer.validar_equilibrio_jogo(jogo_a)
        equilibrio_b = analyzer.validar_equilibrio_jogo(jogo_b)

        with col1:
            st.markdown("### 🎯 Sniper")
            st.write(f"**Dezenas:** {', '.join([f'{d:02d}' for d in sorted(jogo_a)])}")
            st.write(f"**Pares/Ímpares:** {equilibrio_a['pares']}P - {equilibrio_a['impares']}I")
            st.write(f"**Baixos/Altos:** {equilibrio_a['baixos']}B - {equilibrio_a['altos']}A")
            st.write(f"**Soma Total:** {sum(jogo_a)}")

        with col2:
            st.markdown("### 💣 Bomber")
            st.write(f"**Dezenas:** {', '.join([f'{d:02d}' for d in sorted(jogo_b)])}")
            st.write(f"**Pares/Ímpares:** {equilibrio_b['pares']}P - {equilibrio_b['impares']}I")
            st.write(f"**Baixos/Altos:** {equilibrio_b['baixos']}B - {equilibrio_b['altos']}A")
            st.write(f"**Soma Total:** {sum(jogo_b)}")

        st.success(f"""
        💡 **Qual escolher?**

        - **Sniper:** Se você prefere seguir a matemática pura e maximizar probabilidades teóricas
        - **Bomber:** Se você prefere diversificar e cobrir diferentes cenários estatísticos
        - **Ambas:** Jogue as duas e aumente sua cobertura!
        """)

    # ------------------------------------------------------------------------
    # TAB 6: SUGESTÃO PERSONALIZADA POR BUDGET
    # ------------------------------------------------------------------------

    with tab6:
        st.header("🎲 Sugestão Personalizada para seu Budget")

        st.info(f"💰 **Seu Budget:** R$ {budget:,.2f}")

        # Calcular scores
        scores_df = analyzer.calcular_todos_scores()

        # Sugerir jogos baseado no budget
        sugestoes = sugerir_jogos_por_budget(budget, analyzer, scores_df)

        if not sugestoes:
            st.error("Budget insuficiente. Mínimo: R$ 6,00")
            return

        st.subheader("📋 Opções Disponíveis para seu Budget")

        for i, sug in enumerate(sugestoes[:3], 1):  # Top 3 opções
            with st.expander(f"Opção {i}: {sug['qtd_jogos']} jogo(s) de {sug['quantidade_numeros']} números", expanded=(i==1)):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Custo por Jogo", f"R$ {sug['custo_por_jogo']:,.2f}")
                    st.metric("Quantidade de Jogos", sug['qtd_jogos'])

                with col2:
                    st.metric("Custo Total", f"R$ {sug['custo_total']:,.2f}")
                    st.metric("Sobra", f"R$ {sug['resto']:,.2f}")

                with col3:
                    st.metric("Prob. Sena", sug['prob_sena'])
                    st.metric("Prob. Quina", sug['prob_quina'])

                # Gerar jogo sugerido
                st.markdown("---")
                st.markdown("### 🎯 Dezenas Sugeridas")

                qtd_dezenas = sug['quantidade_numeros']
                dezenas_sugeridas = sorted(scores_df.head(qtd_dezenas)['numero'].astype(int).tolist())

                # Exibir dezenas
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 2rem; border-radius: 15px; text-align: center; color: white;'>
                    <h3>Dezenas Selecionadas</h3>
                    <h1 style='font-size: 2rem; margin: 1rem 0;'>
                        {' - '.join([f'{d:02d}' for d in dezenas_sugeridas])}
                    </h1>
                </div>
                """, unsafe_allow_html=True)

                # Volante visual
                exibir_volante_interativo(dezenas_sugeridas)

                # Justificativa detalhada
                st.markdown("---")
                st.markdown("### 🤔 Por que escolhemos estes números?")

                justificativas = gerar_justificativa_numeros(dezenas_sugeridas, analyzer, scores_df)

                for just in justificativas:
                    with st.expander(f"Número {just['numero']:02d}"):
                        for razao in just['razoes']:
                            st.markdown(f"✅ {razao}")

                # Comparação com histórico
                st.markdown("---")
                st.markdown("### 📊 Jogos Similares que já Ganharam")

                jogos_similares = comparar_com_historico(dezenas_sugeridas, analyzer)

                if jogos_similares:
                    st.success(f"Encontramos **{len(jogos_similares)} jogos vencedores** com padrão similar!")

                    for jogo_hist in jogos_similares[:5]:  # Top 5
                        st.write(f"**Concurso {jogo_hist['concurso']}:** {' - '.join([f'{d:02d}' for d in jogo_hist['dezenas']])}")
                        st.write(f"   ↳ Padrão: {jogo_hist['padrao']}")
                else:
                    st.warning("Padrão único - não encontramos jogos similares no histórico.")

        st.markdown("---")
        st.success("""
        💡 **Dica:** Quanto mais números você joga, maior a probabilidade de acerto,
        mas também maior o custo. Encontre o equilíbrio ideal para seu budget!
        """)

    # ------------------------------------------------------------------------
    # TAB 7: TABELA DE CUSTOS OFICIAL
    # ------------------------------------------------------------------------

    with tab7:
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
    # TAB 8: DADOS BRUTOS
    # ------------------------------------------------------------------------

    with tab8:
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
