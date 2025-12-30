#!/usr/bin/env python3
"""
MEGA-SENA - Dashboard Visual de Análise Estatística
====================================================
Interface rica com volante visual, gráficos e cores.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from clickhouse_client import ClickHouseClient
from config import BUDGET_TOTAL, TABELA_CUSTOS_OFICIAL, PROBABILIDADES
from gerador_jogos import gerar_jogos, DEFAULT_CONFIG, get_padroes_historicos, jogos_para_dataframe, limpar_cache

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Mega-Sena - Análise Visual",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado
st.markdown("""
<style>
    /* Reset e Base */
    .block-container { padding-top: 1rem; }

    /* Título Principal */
    .main-header {
        background: linear-gradient(135deg, #1a5f2a 0%, #28a745 50%, #1a5f2a 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .main-header h1 { margin: 0; font-size: 2.5rem; }
    .main-header p { margin: 0.5rem 0 0 0; opacity: 0.9; }

    /* Cards de Número */
    .numero-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .numero-card:hover { transform: translateY(-5px); }

    .numero-grande {
        font-size: 2.5rem;
        font-weight: bold;
        color: white;
        background: linear-gradient(135deg, #28a745 0%, #1a5f2a 100%);
        border-radius: 50%;
        width: 70px;
        height: 70px;
        line-height: 70px;
        margin: 0 auto 0.5rem;
        box-shadow: 0 4px 15px rgba(40,167,69,0.4);
    }

    /* Seções */
    .section-header {
        background: linear-gradient(90deg, #28a745 0%, transparent 100%);
        padding: 0.8rem 1.5rem;
        border-radius: 10px 10px 0 0;
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 1.5rem;
    }

    /* Jogo Card */
    .jogo-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }

    .jogo-numeros {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin: 1rem 0;
    }

    .jogo-numero {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.1rem;
        background: linear-gradient(135deg, #28a745 0%, #1a5f2a 100%);
        color: white;
        box-shadow: 0 3px 10px rgba(40,167,69,0.3);
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .stat-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    .stat-value { font-size: 1.8rem; font-weight: bold; color: #28a745; }
    .stat-label { font-size: 0.8rem; color: #666; }

    /* Loading Overlay */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }

    .loading-spinner {
        width: 80px;
        height: 80px;
        border: 8px solid rgba(255, 255, 255, 0.3);
        border-top: 8px solid #28a745;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-text {
        color: white;
        font-size: 1.2rem;
        margin-top: 20px;
        font-weight: 500;
    }

    .loading-subtext {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        margin-top: 8px;
    }

    /* Hide default streamlit spinner */
    .stSpinner > div {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


def mostrar_loading(mensagem="Carregando...", submensagem=""):
    """Mostra overlay de loading centralizado."""
    return st.markdown(f"""
    <div class="loading-overlay" id="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">{mensagem}</div>
        <div class="loading-subtext">{submensagem}</div>
    </div>
    """, unsafe_allow_html=True)


def esconder_loading():
    """Esconde o overlay de loading via JavaScript."""
    st.markdown("""
    <script>
        var overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    </script>
    """, unsafe_allow_html=True)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

@st.cache_resource
def get_clickhouse_client():
    """Retorna cliente ClickHouse com cache de sessão."""
    return ClickHouseClient()


@st.cache_data(ttl=60)
def carregar_dados():
    """Carrega todos os dados do ClickHouse."""
    client = get_clickhouse_client()

    scores = client.get_detailed_scores()
    frequencia = client.query("SELECT numero, aparicoes as frequencia FROM loterias.v_frequencia ORDER BY numero")
    atraso = client.query("SELECT numero, atraso FROM loterias.v_atraso ORDER BY numero")
    tendencia = client.query("SELECT numero, aparicoes_ultimos_48 FROM loterias.v_tendencia ORDER BY numero")

    return {
        'scores': scores,
        'frequencia': frequencia,
        'atraso': atraso,
        'tendencia': tendencia,
        'top_numeros': client.get_top_numbers(20),
        'faltantes': client.get_numeros_faltantes_ciclo(),
        'ultimo_concurso': client.get_ultimo_concurso(),
        'total_concursos': client.get_total_concursos(),
    }


@st.cache_data(ttl=60)
def carregar_regras():
    """Carrega regras do banco de dados com cache."""
    client = get_clickhouse_client()
    return client.get_regras()


@st.cache_data(ttl=60)
def carregar_score_individual():
    """Carrega score individual com cache."""
    client = get_clickhouse_client()
    return client.get_score_individual()


@st.cache_data(ttl=60)
def executar_query_cached(query_key: str):
    """Executa queries específicas com cache."""
    client = get_clickhouse_client()

    queries = {
        'r1_stats': '''
            SELECT
                multiIf(r1_freq >= 90, '90+ (Muito Alta)', r1_freq >= 80, '80-89 (Alta)',
                        r1_freq >= 70, '70-79 (Média-Alta)', '< 70 (Média)') as faixa,
                count() as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''',
        'r3_stats': '''
            SELECT
                multiIf(r3_tend >= 80, 'Quente (80+)', r3_tend >= 60, 'Morno (60-79)',
                        r3_tend >= 40, 'Neutro (40-59)', 'Frio (< 40)') as faixa,
                count() as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''',
        'r11_stats': '''
            SELECT
                multiIf(r11_poisson >= 80, 'Alta (80+)', r11_poisson >= 60, 'Média (60-79)',
                        r11_poisson >= 40, 'Baixa (40-59)', 'Muito Baixa (< 40)') as faixa,
                count() as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''',
        'r2_stats': '''
            SELECT
                multiIf(r2_atraso >= 80, '80+ (Muito Atrasado)', r2_atraso >= 60, '60-79 (Atrasado)',
                        r2_atraso >= 40, '40-59 (Normal)', '< 40 (Recente)') as faixa,
                count() as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''',
        'r10_stats': '''
            SELECT
                multiIf(r10_ciclo >= 80, 'Muito Atrasado (80+)', r10_ciclo >= 60, 'Atrasado (60-79)',
                        r10_ciclo >= 40, 'Normal (40-59)', 'Recente (< 40)') as faixa,
                count() as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''',
        'r15_stats': '''
            SELECT
                multiIf(r15_pressao >= 80, 'Alta Pressão (80+)', r15_pressao >= 60, 'Média (60-79)',
                        r15_pressao >= 40, 'Baixa (40-59)', 'Mínima (< 40)') as faixa,
                count() as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''',
        'quadrantes': '''
            SELECT
                'Q1 (1-15)' as quadrante, round(avg(q1_count), 2) as media, round(avg(q1_pct), 1) as pct_medio
            FROM loterias.v_concurso_analise
            UNION ALL
            SELECT 'Q2 (16-30)', round(avg(q2_count), 2), round(avg(q2_pct), 1) FROM loterias.v_concurso_analise
            UNION ALL
            SELECT 'Q3 (31-45)', round(avg(q3_count), 2), round(avg(q3_pct), 1) FROM loterias.v_concurso_analise
            UNION ALL
            SELECT 'Q4 (46-60)', round(avg(q4_count), 2), round(avg(q4_pct), 1) FROM loterias.v_concurso_analise
        ''',
        'paridade': '''
            SELECT
                concat(toString(pares_count), '-', toString(impares_count)) as pattern,
                count() as ocorrencias,
                round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY pares_count, impares_count
            ORDER BY ocorrencias DESC
            LIMIT 5
        ''',
        'bma': '''
            SELECT
                concat(toString(baixo_count), '-', toString(medio_count), '-', toString(alto_count)) as pattern,
                count() as ocorrencias,
                round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY baixo_count, medio_count, alto_count
            ORDER BY ocorrencias DESC
            LIMIT 6
        ''',
        'linhas': '''
            SELECT
                arrayStringConcat(arrayMap(x -> toString(x), [l1_count, l2_count, l3_count, l4_count, l5_count, l6_count]), '-') as pattern,
                count() as ocorrencias
            FROM loterias.v_concurso_analise
            GROUP BY l1_count, l2_count, l3_count, l4_count, l5_count, l6_count
            ORDER BY ocorrencias DESC
            LIMIT 5
        ''',
        'colunas': '''
            SELECT
                c0_count + c1_count + c2_count + c3_count + c4_count as low_cols,
                c5_count + c6_count + c7_count + c8_count + c9_count as high_cols,
                count() as ocorrencias
            FROM loterias.v_concurso_analise
            GROUP BY low_cols, high_cols
            ORDER BY ocorrencias DESC
            LIMIT 5
        ''',
        'soma': '''
            SELECT
                multiIf(soma < 150, 'Baixa (<150)', soma <= 200, 'Ideal (150-200)', 'Alta (>200)') as faixa,
                count() as ocorrencias,
                round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY faixa
            ORDER BY ocorrencias DESC
        ''',
        'hnf': '''
            SELECT
                concat(toString(hot_count), 'H-', toString(neutral_count), 'N-', toString(cold_count), 'F') as pattern,
                count() as ocorrencias,
                round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY hot_count, neutral_count, cold_count
            ORDER BY ocorrencias DESC
            LIMIT 8
        ''',
        'sequencias': '''
            SELECT
                sequencias_consecutivas as seq_count,
                count() as ocorrencias,
                round(count() * 100.0 / (SELECT count() FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY sequencias_consecutivas
            ORDER BY seq_count
        ''',
        'freq_quadrante': '''
            SELECT
                quadrante,
                round(avg(score_freq_quadrante), 1) as avg_score,
                count() as total_numeros
            FROM loterias.v_score_freq_quadrante
            GROUP BY quadrante
            ORDER BY quadrante
        ''',
    }

    if query_key in queries:
        return client.query(queries[query_key])
    return None


def classificar_numero(score, atraso, tendencia):
    """Classifica número em categoria de temperatura."""
    # Combina score, atraso e tendência para classificar
    if score >= 75 and tendencia >= 3:
        return 'muito-quente'
    elif score >= 65 and tendencia >= 2:
        return 'quente'
    elif score >= 55:
        return 'morno'
    elif score >= 45:
        return 'neutro'
    elif score >= 35:
        return 'frio'
    else:
        return 'muito-frio'


def score_to_heatmap_color(score, min_score, max_score):
    """Converte score em cor do mapa de calor com 10+ variações."""
    if max_score == min_score:
        ratio = 0.5
    else:
        ratio = (score - min_score) / (max_score - min_score)

    # 10 faixas de cores: Verde Escuro -> Verde -> Verde Claro -> Amarelo -> Laranja -> Vermelho
    # Cada faixa tem 10% do range
    colors = [
        (0, 100, 0),      # 0-10%: Verde muito escuro
        (0, 128, 0),      # 10-20%: Verde escuro
        (34, 139, 34),    # 20-30%: Verde floresta
        (50, 205, 50),    # 30-40%: Verde limão
        (144, 238, 144),  # 40-50%: Verde claro
        (255, 255, 150),  # 50-60%: Amarelo claro
        (255, 255, 0),    # 60-70%: Amarelo
        (255, 200, 0),    # 70-80%: Amarelo dourado
        (255, 140, 0),    # 80-90%: Laranja
        (255, 69, 0),     # 90-100%: Vermelho laranja
        (255, 0, 0),      # 100%: Vermelho puro
    ]

    # Determina qual faixa e interpola
    idx = min(int(ratio * 10), 9)
    next_idx = min(idx + 1, 10)
    local_ratio = (ratio * 10) - idx

    r1, g1, b1 = colors[idx]
    r2, g2, b2 = colors[next_idx]

    r = int(r1 + (r2 - r1) * local_ratio)
    g = int(g1 + (g2 - g1) * local_ratio)
    b = int(b1 + (b2 - b1) * local_ratio)

    return f'rgb({r},{g},{b})'


def criar_volante_mini(valores_dict, titulo, legenda_min, legenda_max, usar_cores_discretas=False, cores_discretas=None):
    """
    Cria um volante mini 6x10 para demonstrar uma regra específica.

    Args:
        valores_dict: {numero: valor} - valores para cada número (1-60)
        titulo: Título do volante
        legenda_min: Texto da legenda mínima
        legenda_max: Texto da legenda máxima
        usar_cores_discretas: Se True, usa cores_discretas ao invés de gradiente
        cores_discretas: {numero: cor_hex} - cores específicas por número
    """
    html = '<div style="background:#f8f9fa;border-radius:10px;padding:15px;margin:15px 0;">'
    html += f'<h5 style="text-align:center;color:#495057;margin:0 0 10px 0;font-size:0.9rem;">{titulo}</h5>'

    # Grid 6x10 compacto
    html += '<div style="display:grid;grid-template-columns:repeat(10, 1fr);gap:2px;max-width:600px;margin:0 auto;background:#dee2e6;padding:2px;border-radius:8px;">'

    if usar_cores_discretas and cores_discretas:
        # Cores específicas (ex: pares/ímpares, linhas, colunas)
        for linha in range(6):
            for col in range(10):
                num = linha * 10 + col + 1
                bg_color = cores_discretas.get(num, '#e9ecef')
                html += f'<div style="aspect-ratio:1;background:{bg_color};color:#2c3e50;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:11px;border-radius:4px;border:1px solid rgba(255,255,255,0.5);" title="Número {num:02d}">{num:02d}</div>'
    else:
        # Gradiente baseado em valores
        min_val = min(valores_dict.values()) if valores_dict else 0
        max_val = max(valores_dict.values()) if valores_dict else 100

        for linha in range(6):
            for col in range(10):
                num = linha * 10 + col + 1
                valor = valores_dict.get(num, 0)

                # Normalizar
                if max_val > min_val:
                    normalized = (valor - min_val) / (max_val - min_val)
                else:
                    normalized = 0.5

                # Cores suaves
                if normalized < 0.5:
                    r = int(144 + (255 - 144) * (normalized / 0.5))
                    g = int(238)
                    b = int(144)
                else:
                    r = int(255)
                    g = int(238 - 138 * ((normalized - 0.5) / 0.5))
                    b = int(144 - 104 * ((normalized - 0.5) / 0.5))

                bg_color = f'rgb({r},{g},{b})'
                html += f'<div style="aspect-ratio:1;background:{bg_color};color:#2c3e50;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:11px;border-radius:4px;border:1px solid rgba(255,255,255,0.5);" title="Número {num:02d}: {valor}">{num:02d}</div>'

    html += '</div>'

    # Legenda mini
    html += '<div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-top:10px;">'
    html += f'<span style="color:#28a745;font-size:11px;font-weight:600;">{legenda_min}</span>'
    html += '<div style="width:150px;height:12px;border-radius:6px;background:linear-gradient(to right, rgb(144,238,144), rgb(255,238,144), rgb(255,100,40));border:1px solid rgba(0,0,0,0.1);"></div>'
    html += f'<span style="color:#dc3545;font-size:11px;font-weight:600;">{legenda_max}</span>'
    html += '</div>'

    html += '</div>'
    return html


def criar_volante_html(scores_df, atraso_df, tendencia_df, top6_numeros):
    """Cria HTML do volante visual em grade retangular 6x10."""

    # Pega scores de todos os números
    scores_dict = dict(zip(scores_df['numero'].astype(int), scores_df['score_final']))
    min_score = scores_df['score_final'].min()
    max_score = scores_df['score_final'].max()

    # Container principal
    html = '<div style="background:linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);border-radius:15px;padding:30px;margin:10px 0;box-shadow:0 4px 20px rgba(0,0,0,0.1);">'

    # Título
    html += '<h3 style="text-align:center;color:#2c3e50;margin:0 0 5px 0;font-size:1.5rem;font-weight:700;">🎰 Volante da Mega-Sena</h3>'
    html += '<p style="text-align:center;color:#6c757d;margin:0 0 25px 0;font-size:0.95rem;">Mapa de Calor por Score | Verde = Baixo → Vermelho = Alto</p>'

    # Grid retangular 6 linhas x 10 colunas
    html += '<div style="display:grid;grid-template-columns:repeat(10, 1fr);gap:3px;max-width:900px;margin:0 auto;background:#dee2e6;padding:3px;border-radius:10px;box-shadow:inset 0 2px 4px rgba(0,0,0,0.1);">'

    for linha in range(6):
        for col in range(10):
            num = linha * 10 + col + 1
            score = scores_dict.get(num, 50)

            # Cores mais suaves - escala verde claro a amarelo suave a laranja suave
            normalized = (score - min_score) / (max_score - min_score) if max_score > min_score else 0.5

            if normalized < 0.33:
                # Verde claro
                r = int(144 + (255 - 144) * (normalized / 0.33))
                g = int(238)
                b = int(144)
            elif normalized < 0.66:
                # Amarelo claro
                r = int(255)
                g = int(238 - 68 * ((normalized - 0.33) / 0.33))
                b = int(144 - 44 * ((normalized - 0.33) / 0.33))
            else:
                # Laranja suave
                r = int(255)
                g = int(170 - 70 * ((normalized - 0.66) / 0.34))
                b = int(100 - 60 * ((normalized - 0.66) / 0.34))

            bg_color = f"rgb({r},{g},{b})"

            is_top6 = num in top6_numeros

            # Top 6: anel dourado e destaque
            if is_top6:
                border = "3px solid #FFD700"
                shadow = "0 0 10px rgba(255,215,0,0.6), inset 0 1px 3px rgba(255,255,255,0.3)"
                font_weight = "900"
                font_size = "18px"
            else:
                border = "1px solid rgba(255,255,255,0.5)"
                shadow = "0 1px 3px rgba(0,0,0,0.15), inset 0 1px 1px rgba(255,255,255,0.3)"
                font_weight = "700"
                font_size = "16px"

            html += f'''<div style="
                aspect-ratio:1;
                background:{bg_color};
                color:#2c3e50;
                display:flex;
                align-items:center;
                justify-content:center;
                font-weight:{font_weight};
                font-size:{font_size};
                border:{border};
                box-shadow:{shadow};
                cursor:pointer;
                transition:all 0.2s ease;
                border-radius:6px;
            " title="Número {num:02d} - Score: {score:.1f}">{num:02d}</div>'''

    html += '</div>'

    # Legenda
    html += '<div style="margin-top:25px;padding-top:20px;border-top:2px solid #dee2e6;">'

    # Barra de gradiente suave
    html += '<div style="display:flex;align-items:center;justify-content:center;gap:15px;margin-bottom:15px;">'
    html += '<span style="color:#28a745;font-size:13px;font-weight:600;">🟢 Baixo</span>'
    html += '<div style="width:300px;height:20px;border-radius:10px;background:linear-gradient(to right, rgb(144,238,144), rgb(255,255,144), rgb(255,170,100));box-shadow:0 2px 6px rgba(0,0,0,0.15);border:1px solid rgba(0,0,0,0.1);"></div>'
    html += '<span style="color:#dc3545;font-size:13px;font-weight:600;">Alto 🔴</span>'
    html += '</div>'

    # Indicador Top 6
    html += '<div style="display:flex;justify-content:center;align-items:center;gap:10px;">'
    html += '<div style="width:32px;height:32px;border:3px solid #FFD700;border-radius:6px;box-shadow:0 0 10px rgba(255,215,0,0.4);background:rgba(255,215,0,0.1);"></div>'
    html += '<span style="color:#FFD700;font-size:14px;font-weight:700;text-shadow:0 1px 2px rgba(0,0,0,0.2);">★ TOP 6 RECOMENDADOS</span>'
    html += '</div>'

    html += '</div></div>'

    return html


def criar_grafico_pizza_paridade(scores_df):
    """Gráfico de pizza: distribuição par/ímpar nos top 20."""
    top20 = scores_df.head(20)['numero'].tolist()
    pares = sum(1 for n in top20 if n % 2 == 0)
    impares = 20 - pares

    fig = go.Figure(data=[go.Pie(
        labels=['Pares', 'Ímpares'],
        values=[pares, impares],
        hole=0.4,
        marker_colors=['#28a745', '#17a2b8'],
        textinfo='label+percent',
        textfont_size=14,
    )])
    fig.update_layout(
        title=dict(text='Paridade nos Top 20', x=0.5, font=dict(size=16)),
        showlegend=True,
        height=300,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def criar_grafico_pizza_bma(scores_df):
    """Gráfico de pizza: distribuição Baixo/Médio/Alto nos top 20."""
    top20 = scores_df.head(20)['numero'].tolist()
    baixo = sum(1 for n in top20 if n <= 20)
    medio = sum(1 for n in top20 if 21 <= n <= 40)
    alto = sum(1 for n in top20 if n > 40)

    fig = go.Figure(data=[go.Pie(
        labels=['Baixo (1-20)', 'Médio (21-40)', 'Alto (41-60)'],
        values=[baixo, medio, alto],
        hole=0.4,
        marker_colors=['#ffc107', '#28a745', '#dc3545'],
        textinfo='label+percent',
        textfont_size=12,
    )])
    fig.update_layout(
        title=dict(text='Faixas B/M/A nos Top 20', x=0.5, font=dict(size=16)),
        showlegend=True,
        height=300,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def criar_grafico_pizza_quadrante(scores_df):
    """Gráfico de pizza: quadrantes nos top 20."""
    top20 = scores_df.head(20)['numero'].tolist()
    q1 = sum(1 for n in top20 if n <= 15)
    q2 = sum(1 for n in top20 if 16 <= n <= 30)
    q3 = sum(1 for n in top20 if 31 <= n <= 45)
    q4 = sum(1 for n in top20 if n > 45)

    fig = go.Figure(data=[go.Pie(
        labels=['Q1 (1-15)', 'Q2 (16-30)', 'Q3 (31-45)', 'Q4 (46-60)'],
        values=[q1, q2, q3, q4],
        hole=0.4,
        marker_colors=['#28a745', '#17a2b8', '#ffc107', '#dc3545'],
        textinfo='label+percent',
        textfont_size=11,
    )])
    fig.update_layout(
        title=dict(text='Quadrantes nos Top 20', x=0.5, font=dict(size=16)),
        showlegend=True,
        height=300,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def criar_grafico_barras_scores(scores_df):
    """Gráfico de barras: top 15 números por score."""
    top15 = scores_df.head(15)

    colors = ['#28a745' if i < 6 else '#17a2b8' for i in range(15)]

    fig = go.Figure(data=[go.Bar(
        x=[f"{int(n):02d}" for n in top15['numero']],
        y=top15['score_final'],
        marker_color=colors,
        text=[f"{s:.1f}" for s in top15['score_final']],
        textposition='outside',
    )])
    fig.update_layout(
        title=dict(text='Top 15 Números por Score Final', x=0.5, font=dict(size=16)),
        xaxis_title='Número',
        yaxis_title='Score',
        height=350,
        margin=dict(t=50, b=50, l=50, r=20),
        yaxis=dict(range=[0, 100]),
    )
    return fig


def criar_grafico_barras_frequencia(freq_df):
    """Gráfico de barras: frequência de todos os 60 números."""
    # Ordena por número
    freq_sorted = freq_df.sort_values('numero')

    # Cores baseadas na frequência
    max_freq = freq_sorted['frequencia'].max()
    min_freq = freq_sorted['frequencia'].min()

    colors = []
    for f in freq_sorted['frequencia']:
        ratio = (f - min_freq) / (max_freq - min_freq) if max_freq > min_freq else 0.5
        if ratio > 0.7:
            colors.append('#dc3545')  # Vermelho - muito frequente
        elif ratio > 0.4:
            colors.append('#ffc107')  # Amarelo - médio
        else:
            colors.append('#17a2b8')  # Azul - pouco frequente

    fig = go.Figure(data=[go.Bar(
        x=[f"{int(n):02d}" for n in freq_sorted['numero']],
        y=freq_sorted['frequencia'],
        marker_color=colors,
    )])
    fig.update_layout(
        title=dict(text='Frequência Histórica de Cada Número', x=0.5, font=dict(size=16)),
        xaxis_title='Número',
        yaxis_title='Vezes Sorteado',
        height=300,
        margin=dict(t=50, b=50, l=50, r=20),
    )
    return fig


def criar_grafico_radar(row):
    """Gráfico radar profissional para um número específico."""
    # Categorias numeradas para referência
    categorias = [
        'R1-Freq',      # Regra 1: Frequência
        'R2-Atraso',    # Regra 2: Atraso
        'R3-Tend',      # Regra 3: Tendência
        'R4-Quad',      # Regra 4: Quadrante
        'R5-Par',       # Regra 5: Paridade
        'R6-BMA',       # Regra 6: Baixo/Médio/Alto
        'R7-Lin',       # Regra 7: Linhas
        'R8-Col',       # Regra 8: Colunas
        'R9-Soma',      # Regra 9: Soma
        'R10-Ciclo',    # Regra 10: Ciclo
        'R11-Poiss',    # Regra 11: Poisson
        'R12-HNF',      # Regra 12: Hot/Neutro/Frio
        'R13-Seq',      # Regra 13: Sequência
        'R14-FQuad',    # Regra 14: Freq. Quadrante
        'R15-Press',    # Regra 15: Pressão Ciclo
    ]
    valores = [row['freq'], row['atraso'], row['tend'], row['quad'], row['parid'],
               row['bma'], row['linhas'], row['cols'], row['soma'], row['ciclo'],
               row['poisson'], row['hnf'], row['seq'], row['freq_quad'], row['pressao']]

    fig = go.Figure(data=go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        fillcolor='rgba(0, 255, 127, 0.25)',
        line=dict(color='#00FF7F', width=3),
        marker=dict(size=6, color='#00FF7F'),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color='#888'),
                gridcolor='rgba(255,255,255,0.2)',
                linecolor='rgba(255,255,255,0.3)',
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#FFD700', family='Arial Black'),
                gridcolor='rgba(255,255,255,0.15)',
                linecolor='rgba(255,255,255,0.3)',
            ),
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=300,
        margin=dict(t=50, b=50, l=60, r=60),
    )
    return fig


def criar_grafico_atraso_vs_frequencia(scores_df, atraso_df, freq_df):
    """Scatter plot: Atraso vs Frequência."""
    merged = scores_df[['numero', 'score_final']].merge(atraso_df, on='numero').merge(freq_df[['numero', 'frequencia']], on='numero')

    fig = go.Figure(data=go.Scatter(
        x=merged['frequencia'],
        y=merged['atraso'],
        mode='markers+text',
        marker=dict(
            size=merged['score_final'] / 5,
            color=merged['score_final'],
            colorscale='Greens',
            showscale=True,
            colorbar=dict(title='Score'),
        ),
        text=[f"{int(n):02d}" for n in merged['numero']],
        textposition='top center',
        textfont=dict(size=8),
        hovertemplate='Número: %{text}<br>Frequência: %{x}<br>Atraso: %{y}<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Atraso vs Frequência (tamanho = score)', x=0.5, font=dict(size=16)),
        xaxis_title='Frequência Histórica',
        yaxis_title='Atraso (concursos sem sair)',
        height=400,
        margin=dict(t=50, b=50, l=50, r=20),
    )
    return fig


def criar_jogo_html(jogo, titulo, custo, prob):
    """Cria HTML para exibir um jogo."""
    numeros_html = ''.join([f'<div class="jogo-numero">{n:02d}</div>' for n in jogo])

    return f'''
    <div class="jogo-card">
        <h4 style="color:#1a5f2a; margin:0 0 0.5rem 0;">{titulo}</h4>
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:0.5rem; margin-bottom:1rem;">
            <span><strong>Dezenas:</strong> {len(jogo)}</span>
            <span><strong>Custo:</strong> R$ {custo:,.2f}</span>
            <span><strong>Prob. Sena:</strong> 1 em {prob[0]:,}</span>
        </div>
        <div class="jogo-numeros">{numeros_html}</div>
    </div>
    '''


def gerar_jogos_otimizados(scores_df, num_jogos=3, dezenas_por_jogo=6):
    """Gera jogos otimizados garantindo diversidade."""
    jogos = []
    numeros_usados = set()

    scores_sorted = scores_df.sort_values('score_final', ascending=False)

    for _ in range(num_jogos):
        jogo = []
        candidatos = scores_sorted[~scores_sorted['numero'].isin(numeros_usados)]

        for _, row in candidatos.iterrows():
            if len(jogo) >= dezenas_por_jogo:
                break
            num = int(row['numero'])
            # Evita sequências longas
            if len(jogo) >= 2:
                if not (abs(num - jogo[-1]) == 1 and abs(jogo[-1] - jogo[-2]) == 1):
                    jogo.append(num)
            else:
                jogo.append(num)

        # Completa se necessário
        for _, row in candidatos.iterrows():
            if len(jogo) >= dezenas_por_jogo:
                break
            num = int(row['numero'])
            if num not in jogo:
                jogo.append(num)

        jogo = sorted(jogo[:dezenas_por_jogo])
        jogos.append(jogo)
        numeros_usados.update(jogo[:3])

    return jogos


def get_regras():
    """Retorna as 15 regras com descrições, numeração e classificação."""
    return [
        ('R1', '📊', 'Frequência Histórica', 9, 'Quantas vezes cada número foi sorteado no total', 'numero'),
        ('R2', '⏰', 'Atraso', 9, 'Há quantos concursos o número não sai (regressão à média)', 'numero'),
        ('R3', '🔥', 'Tendência Recente', 7, 'Aparições nos últimos 48 concursos', 'numero'),
        ('R4', '🔲', 'Quadrantes', 7, 'Equilíbrio entre Q1, Q2, Q3, Q4', 'conjunto'),
        ('R5', '⚖️', 'Paridade', 6, 'Equilíbrio entre pares e ímpares', 'conjunto'),
        ('R6', '📶', 'Faixas B/M/A', 6, 'Equilíbrio Baixo/Médio/Alto', 'conjunto'),
        ('R7', '➡️', 'Linhas', 7, 'Distribuição pelas 6 linhas do volante', 'conjunto'),
        ('R8', '⬇️', 'Colunas', 7, 'Distribuição pelas 10 colunas', 'conjunto'),
        ('R9', '➕', 'Soma Ideal', 7, 'Contribuição para soma 150-200', 'conjunto'),
        ('R10', '🔄', 'Ciclo', 7, 'Números faltantes nos últimos 27 concursos', 'numero'),
        ('R11', '📈', 'Poisson', 6, 'Probabilidade estatística esperada', 'numero'),
        ('R12', '🌡️', 'H-N-F', 6, 'Classificação Quente/Neutro/Frio', 'conjunto'),
        ('R13', '🔢', 'Sequências', 6, 'Análise de números consecutivos', 'conjunto'),
        ('R14', '🗺️', 'Freq. Quadrante', 6, 'Análise de frequência por quadrante', 'conjunto'),
        ('R15', '🔄', 'Pressão Ciclo', 4, 'Pressão do ciclo completo (60 números)', 'numero'),
    ]


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    # Inicializar session_state para controle de carregamento
    if 'dados_carregados' not in st.session_state:
        st.session_state.dados_carregados = False
    if 'dados' not in st.session_state:
        st.session_state.dados = None
    if 'ja_verificou_update' not in st.session_state:
        st.session_state.ja_verificou_update = False

    # Placeholder para loading - só mostra se dados ainda não carregados
    loading_placeholder = st.empty()

    # Mostrar loading apenas no primeiro carregamento
    if not st.session_state.dados_carregados:
        with loading_placeholder.container():
            st.markdown("""
            <div class="loading-overlay">
                <div class="loading-spinner"></div>
                <div class="loading-text">Carregando dados...</div>
                <div class="loading-subtext">Conectando ao banco de dados</div>
            </div>
            """, unsafe_allow_html=True)

        # Auto-atualizar dados apenas uma vez por sessão
        if not st.session_state.ja_verificou_update:
            from auto_update_data import verificar_e_atualizar
            verificar_e_atualizar()
            st.session_state.ja_verificou_update = True

    # Carregar dados (usa cache do @st.cache_data ou session_state)
    try:
        if st.session_state.dados is None:
            st.session_state.dados = carregar_dados()
            st.session_state.dados_carregados = True

        dados = st.session_state.dados
        scores = dados['scores']

        # Remover loading após carregar
        loading_placeholder.empty()

    except Exception as e:
        loading_placeholder.empty()
        st.error(f"❌ Erro ao conectar ao ClickHouse: {e}")
        st.info("Verifique se o ClickHouse está rodando: `clickhouse server`")
        return

    # Header
    st.markdown('''
    <div class="main-header">
        <h1>🎰 MEGA-SENA</h1>
        <p>Sistema de Análise Estatística com 15 Regras Inteligentes</p>
    </div>
    ''', unsafe_allow_html=True)

    # Stats rápidos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Total de Concursos", f"{dados['total_concursos']:,}")
    with col2:
        st.metric("📅 Último Concurso", dados['ultimo_concurso'])
    with col3:
        st.metric("🔄 Faltantes no Ciclo", len(dados['faltantes']))
    with col4:
        top_num = int(scores.iloc[0]['numero'])
        st.metric("🏆 Número #1", f"{top_num:02d}")

    st.markdown("---")

    # ==========================================================================
    # SEÇÃO 1: JOGOS INTELIGENTES
    # ==========================================================================
    st.markdown("## 🎲 Gerador de Jogos Inteligentes")
    st.markdown("*Gera jogos otimizados com base nas 15 regras estatísticas*")

    # ==============================================================
    # 1. VALOR DA APOSTA
    # ==============================================================
    st.markdown("#### 💰 Valor da Aposta")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a5f2a 0%, #28a745 100%); padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;">
        <span style="color: white; font-size: 0.9rem;">Informe quanto deseja investir (mínimo R$ 1.000,00)</span>
    </div>
    """, unsafe_allow_html=True)

    valor_aposta = st.number_input(
        "Valor total da aposta (R$)",
        min_value=1000.0,
        max_value=10000000.0,
        value=11000.0,
        step=100.0,
        format="%.2f",
        help="Mínimo de R$ 1.000,00 para garantir diversificação adequada"
    )

    # Calcular melhor combinação de jogos para o budget
    def calcular_melhor_combinacao(budget):
        """Calcula a melhor combinação de jogos que maximiza o uso do budget."""
        melhor_combo = []
        budget_restante = budget

        # Tentar do maior para o menor (greedy)
        for n_dez in range(20, 5, -1):
            custo = TABELA_CUSTOS_OFICIAL.get(n_dez)
            if custo and custo <= budget_restante:
                qtd = int(budget_restante / custo)
                if qtd > 0:
                    melhor_combo.append((n_dez, qtd, custo * qtd))
                    budget_restante -= custo * qtd

        return melhor_combo, budget - budget_restante, budget_restante

    combo, valor_usado, sobra = calcular_melhor_combinacao(valor_aposta)

    # Formatar a combinação como texto
    if combo:
        combo_texto = " + ".join([f"{qtd}x{dez}dez" for dez, qtd, _ in combo])
        # Calcular total de combinações de 6 cobertas
        from math import comb
        total_combinacoes = sum(comb(dez, 6) * qtd for dez, qtd, _ in combo)
    else:
        combo_texto = "Nenhuma combinação possível"
        total_combinacoes = 0

    # Mostrar card com a melhor combinação
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px; border-radius: 12px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="color: #ffc107; font-size: 0.8rem;">💡 MELHOR COMBINAÇÃO</span>
                <div style="color: white; font-size: 1.1rem; font-weight: bold; margin-top: 3px;">{combo_texto}</div>
            </div>
            <div style="text-align: right;">
                <div style="color: #28a745; font-size: 0.9rem;">✅ R$ {valor_usado:,.2f} usado</div>
                <div style="color: #6c757d; font-size: 0.75rem;">Sobra: R$ {sobra:,.2f}</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 8px; text-align: center;">
                <div style="color: #667eea; font-size: 0.7rem;">COMBINAÇÕES DE 6</div>
                <div style="color: white; font-size: 1rem; font-weight: bold;">{total_combinacoes:,}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ==============================================================
    # 2. FILTROS BASEADOS NAS REGRAS DE CONJUNTO (ordem: R4-R14)
    # ==============================================================
    st.markdown("#### 🎯 Filtros de Conjunto (R4, R5, R6, R7, R8, R9, R12, R13, R14)")
    st.markdown("*Valores pré-configurados com base nos padrões históricos mais frequentes*")

    # Linha 1: R4 Quadrantes, R5 Paridade, R6 Faixas BMA
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### 🔲 R4 - Quadrantes")
        st.caption("Q1(1-15), Q2(16-30), Q3(31-45), Q4(46-60)")
        opcoes_quadrantes = ["1-1-2-2", "2-1-2-1", "1-2-2-1", "1-2-1-2", "2-1-1-2", "2-2-1-1", "1-1-1-3", "0-2-2-2", "Qualquer"]
        quadrantes_selecionados = st.multiselect(
            "Padrões aceitos",
            opcoes_quadrantes,
            default=["1-1-2-2", "2-1-2-1", "1-2-2-1", "1-2-1-2", "2-1-1-2", "2-2-1-1"],  # Top 6 mais frequentes (~60%)
            key="filtro_quadrantes"
        )

    with col2:
        st.markdown("##### ⚖️ R5 - Paridade")
        st.caption("Equilíbrio pares/ímpares")
        opcoes_paridade = ["3P/3I", "4P/2I", "2P/4I", "5P/1I", "1P/5I", "Qualquer"]
        paridade_selecionada = st.multiselect(
            "Padrões aceitos",
            opcoes_paridade,
            default=["3P/3I", "4P/2I", "2P/4I"],  # Top 3 mais frequentes (~85%)
            key="filtro_paridade"
        )

    with col3:
        st.markdown("##### 📶 R6 - Faixas B/M/A")
        st.caption("Baixo(1-20)/Médio(21-40)/Alto(41-60)")
        opcoes_bma = ["2-2-2", "2-3-1", "3-2-1", "1-3-2", "2-1-3", "1-2-3", "3-1-2", "1-1-4", "Qualquer"]
        bma_selecionado = st.multiselect(
            "Padrões aceitos",
            opcoes_bma,
            default=["2-2-2", "2-3-1", "3-2-1", "1-3-2", "2-1-3", "1-2-3"],  # Top 6 mais frequentes (~60%)
            key="filtro_bma"
        )

    # Linha 2: R7 Linhas, R8 Terminações, R9 Soma
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("##### ➡️ R7 - Linhas")
        st.caption("Distribuição nas 6 linhas do volante")
        min_linhas = st.slider("Mínimo de linhas", 3, 6, 4, key="min_linhas")  # 4+ = ~95%

    with col5:
        st.markdown("##### ⬇️ R8 - Terminações")
        st.caption("Terminações diferentes (0-9)")
        min_terminacoes = st.slider("Mínimo de terminações", 3, 10, 4, key="min_terminacoes")  # 4+ = ~90%

    with col6:
        st.markdown("##### ➕ R9 - Soma")
        st.caption("Soma dos 6 números (ideal: 150-210)")
        soma_min = st.slider("Soma mínima", 100, 200, 140, key="soma_min")  # 140-220 abrange ~80%
        soma_max = st.slider("Soma máxima", 180, 270, 220, key="soma_max")

    # Linha 3: R12 H-N-F, R13 Consecutivos, R14 Freq. Quadrante
    col7, col8, col9 = st.columns(3)

    with col7:
        st.markdown("##### 🔥 R12 - H-N-F")
        st.caption("Ideal: 2-3H, 2-3N, 0-2F")
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            min_hot = st.number_input("Mín H", 0, 6, 1, key="min_hot")
            max_hot = st.number_input("Máx H", 0, 6, 4, key="max_hot")
        with col_h2:
            min_neutral = st.number_input("Mín N", 0, 6, 1, key="min_neutral")
            max_neutral = st.number_input("Máx N", 0, 6, 4, key="max_neutral")
        with col_h3:
            min_cold = st.number_input("Mín F", 0, 6, 0, key="min_cold")
            max_cold = st.number_input("Máx F", 0, 6, 3, key="max_cold")

    with col8:
        st.markdown("##### 🔢 R13 - Consecutivos")
        st.caption("Números consecutivos (ideal: 0-2)")
        max_consecutivos = st.slider("Máximo de consecutivos", 0, 4, 2, key="max_consecutivos")

    with col9:
        st.markdown("##### 🗺️ R14 - Freq. Quadrante")
        st.caption("Priorizar quadrantes por frequência")
        opcoes_freq_quad = ["Q3 (31-45)", "Q1 (1-15)", "Q4 (46-60)", "Q2 (16-30)", "Qualquer"]
        freq_quad_selecionado = st.multiselect(
            "Quadrantes prioritários",
            opcoes_freq_quad,
            default=["Qualquer"],  # Aceitar qualquer - mais flexível
            key="filtro_freq_quad"
        )

    # Mostrar resumo dos filtros
    st.markdown("---")
    st.markdown("##### 📋 Resumo dos Filtros Aplicados")
    filtros_html = f"""
    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">🔲 R4 - Quadrantes</div>
            <div style="font-weight: bold; color: #667eea;">{', '.join(quadrantes_selecionados) if quadrantes_selecionados else 'Qualquer'}</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">⚖️ R5 - Paridade</div>
            <div style="font-weight: bold; color: #4169E1;">{', '.join(paridade_selecionada) if paridade_selecionada else 'Qualquer'}</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">📶 R6 - Faixas BMA</div>
            <div style="font-weight: bold; color: #FF8C00;">{', '.join(bma_selecionado) if bma_selecionado else 'Qualquer'}</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">➡️ R7 - Linhas</div>
            <div style="font-weight: bold; color: #17a2b8;">{min_linhas}+ linhas</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">⬇️ R8 - Terminações</div>
            <div style="font-weight: bold; color: #e83e8c;">{min_terminacoes}+ diferentes</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">➕ R9 - Soma</div>
            <div style="font-weight: bold; color: #ffc107;">{soma_min} - {soma_max}</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">🔥 R12 - H-N-F</div>
            <div style="font-weight: bold; color: #ff6b6b;">{min_hot}-{max_hot}H, {min_neutral}-{max_neutral}N, {min_cold}-{max_cold}F</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">🔢 R13 - Consecutivos</div>
            <div style="font-weight: bold; color: #28a745;">0 a {max_consecutivos}</div>
        </div>
        <div style="text-align: center; padding: 8px; background: white; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #666;">🗺️ R14 - Freq. Quad.</div>
            <div style="font-weight: bold; color: #9b59b6;">{', '.join([q.split(' ')[0] for q in freq_quad_selecionado]) if freq_quad_selecionado else 'Qualquer'}</div>
        </div>
    </div>
    """
    st.markdown(filtros_html, unsafe_allow_html=True)

    # ==============================================================
    # 2.5 FILTROS IDEAIS RECOMENDADOS (Layout Visual)
    # ==============================================================
    st.markdown("---")
    st.markdown("#### 💡 Filtros Ideais para Geração de Jogos")
    st.markdown("*Valores pré-populados no gerador de jogos*")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 15px; color: #fff;">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #667eea; font-weight: bold; font-size: 0.75rem;">🔲 R4 - Quadrantes</div>
                <div style="font-size: 1.1rem;">1-1-2-2</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">ou 2-1-2-1, 1-2-2-1</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #4169E1; font-weight: bold; font-size: 0.75rem;">⚖️ R5 - Paridade</div>
                <div style="font-size: 1.1rem;">3P/3I</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">ou 4P/2I, 2P/4I</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #FF8C00; font-weight: bold; font-size: 0.75rem;">📶 R6 - Faixas BMA</div>
                <div style="font-size: 1.1rem;">2-2-2</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">ou 2-3-1, 3-2-1</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px;">
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #17a2b8; font-weight: bold; font-size: 0.75rem;">➡️ R7 - Linhas</div>
                <div style="font-size: 1.1rem;">5 ou 6</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">~85% sorteios</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #e83e8c; font-weight: bold; font-size: 0.75rem;">⬇️ R8 - Terminações</div>
                <div style="font-size: 1.1rem;">5 ou 6</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">~68% sorteios</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #ffc107; font-weight: bold; font-size: 0.75rem;">➕ R9 - Soma</div>
                <div style="font-size: 1.1rem;">180-209</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">28.3% | ou 150-179 (24.2%)</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #ff6b6b; font-weight: bold; font-size: 0.75rem;">🔥 R12 - H-N-F</div>
                <div style="font-size: 1.1rem;">2H-3N-1F</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">15.3% | ou 1H-4N-1F (10.9%)</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #28a745; font-weight: bold; font-size: 0.75rem;">🔢 R13 - Consecutivos</div>
                <div style="font-size: 1.1rem;">0 ou 1</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">92.9% sorteios</div>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                <div style="color: #9b59b6; font-weight: bold; font-size: 0.75rem;">🗺️ R14 - Freq. Quadrante</div>
                <div style="font-size: 1.1rem;">Q3 (31-45)</div>
                <div style="font-size: 0.65rem; opacity: 0.7;">Score 100 (maior freq.)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ==============================================================
    # 2.6 TABELA DE CUSTOS E PROBABILIDADES
    # ==============================================================
    with st.expander("📊 Ver Tabela de Custos e Probabilidades", expanded=False):
        st.info("💡 **Dica:** Quanto mais dezenas você jogar, maior o custo mas também maior a chance de acertar!")

        # Montar DataFrame com custos e probabilidades
        tabela_data = []
        for dezenas in range(6, 21):
            custo = TABELA_CUSTOS_OFICIAL.get(dezenas, 0)
            prob = PROBABILIDADES.get(dezenas, (0, 0, 0))
            tabela_data.append({
                '🎯 Dezenas': dezenas,
                '💰 Custo': f"R$ {custo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                '🏆 Sena (6)': f"1 em {prob[0]:,}".replace(',', '.'),
                '⭐ Quina (5)': f"1 em {prob[1]:,}".replace(',', '.'),
                '✅ Quadra (4)': f"1 em {prob[2]:,}".replace(',', '.')
            })

        df_custos = pd.DataFrame(tabela_data)

        # Usar st.dataframe com configuração de colunas
        st.dataframe(
            df_custos,
            use_container_width=True,
            hide_index=True,
            column_config={
                '🎯 Dezenas': st.column_config.NumberColumn(
                    '🎯 Dezenas',
                    help='Quantidade de dezenas na aposta',
                    format='%d'
                ),
                '💰 Custo': st.column_config.TextColumn(
                    '💰 Custo',
                    help='Valor da aposta em Reais'
                ),
                '🏆 Sena (6)': st.column_config.TextColumn(
                    '🏆 Sena (6)',
                    help='Probabilidade de acertar 6 números'
                ),
                '⭐ Quina (5)': st.column_config.TextColumn(
                    '⭐ Quina (5)',
                    help='Probabilidade de acertar 5 números'
                ),
                '✅ Quadra (4)': st.column_config.TextColumn(
                    '✅ Quadra (4)',
                    help='Probabilidade de acertar 4 números'
                )
            }
        )

        st.warning("⚠️ **Nota:** Probabilidades são '1 em X' - quanto menor o número, maior a chance! Com 20 dezenas, a chance de Sena é 1 em 1.292 (vs 1 em 50 milhões com 6 dezenas).")

    # ==============================================================
    # 3. BOTÃO GERAR JOGOS
    # ==============================================================
    st.markdown("#### 🎰 Gerar Jogos")

    # Montar config com os filtros (ordem: R4, R5, R6, R7, R8, R9, R12, R13, R14)
    config = DEFAULT_CONFIG.copy()
    config['valor_aposta'] = valor_aposta
    # Número total de jogos da combinação calculada
    config['n_jogos'] = sum(qtd for _, qtd, _ in combo) if combo else 0

    # R4 - Quadrantes - filtrar "Qualquer" e se vazio, usar None (aceita tudo)
    quadrantes_filtrados = [q for q in quadrantes_selecionados if q != "Qualquer"]
    config['quadrantes_aceitos'] = quadrantes_filtrados if quadrantes_filtrados else None

    # R5 - Paridade - extrair min/max pares, filtrar "Qualquer"
    paridade_filtrada = [p for p in paridade_selecionada if p != "Qualquer"]
    if paridade_filtrada:
        pares_vals = [int(p.split('P')[0]) for p in paridade_filtrada]
        config['min_pares'] = min(pares_vals)
        config['max_pares'] = max(pares_vals)
    else:
        config['min_pares'] = 0
        config['max_pares'] = 6

    # R6 - Faixas BMA - filtrar "Qualquer"
    bma_filtrado = [b for b in bma_selecionado if b != "Qualquer"]
    config['bma_aceito'] = bma_filtrado if bma_filtrado else None

    # R7 - Linhas
    config['min_linhas'] = min_linhas
    # R8 - Terminações
    config['min_terminacoes'] = min_terminacoes
    # R9 - Soma
    config['soma_min'] = soma_min
    config['soma_max'] = soma_max
    config['validar_soma'] = True
    # R12 - H-N-F
    config['min_hot'] = min_hot
    config['max_hot'] = max_hot
    config['min_neutral'] = min_neutral
    config['max_neutral'] = max_neutral
    config['min_cold'] = min_cold
    config['max_cold'] = max_cold
    # R13 - Consecutivos
    config['max_consecutivos'] = max_consecutivos

    # R14 - Freq. Quadrante - filtrar "Qualquer"
    freq_quad_filtrado = [q for q in freq_quad_selecionado if q != "Qualquer"]
    config['freq_quad_prioritarios'] = freq_quad_filtrado if freq_quad_filtrado else None

    # Pool size - maior para mais diversidade
    config['pool_size'] = 40

    # Inicializar session_state para jogos
    if 'jogos_gerados' not in st.session_state:
        st.session_state.jogos_gerados = None

    # Adicionar budget ao config (valor_aposta é o budget do usuário)
    config['budget'] = valor_aposta

    gerar_clicked = st.button("🎰 Gerar Jogos Otimizados", type="primary", use_container_width=True, key="btn_gerar")

    if gerar_clicked:
        with st.spinner("🔄 Gerando jogos otimizados... Aguarde!"):
            try:
                jogos = gerar_jogos(
                    config=config,
                    verbose=False
                )
                if jogos and len(jogos) > 0:
                    st.session_state.jogos_gerados = jogos
                    st.session_state.config_usado = config
                    st.session_state.budget_usado = valor_aposta
                    st.success(f"✅ {len(jogos)} jogos gerados com sucesso!")
                else:
                    st.warning("⚠️ Nenhum jogo foi gerado. Tente selecionar 'Qualquer' nos filtros de Quadrantes, BMA e Freq. Quadrante.")
            except Exception as e:
                st.error(f"❌ Erro ao gerar jogos: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    # Exibir jogos gerados se existirem
    if st.session_state.jogos_gerados:
        jogos_list = st.session_state.jogos_gerados

        # Calcular custos reais
        custo_total = sum(j.get('custo', 0) for j in jogos_list)
        budget_usado = st.session_state.get('budget_usado', valor_aposta)
        sobra = budget_usado - custo_total

        # Distribuição por dezenas
        dist_dezenas = {}
        for j in jogos_list:
            nd = j.get('n_dezenas', 6)
            dist_dezenas[nd] = dist_dezenas.get(nd, 0) + 1

        st.success(f"✅ {len(jogos_list)} jogos gerados com sucesso!")

        # Converter para DataFrame
        df_jogos = jogos_para_dataframe(jogos_list)

        # Card de resumo
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a5f2a 0%, #28a745 100%); padding: 20px; border-radius: 15px; margin: 15px 0;">
            <h3 style="color: white; margin: 0 0 15px 0; text-align: center;">🎯 Resumo da Geração</h3>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; text-align: center;">
                <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px;">
                    <div style="color: #ccc; font-size: 0.8rem;">Jogos Gerados</div>
                    <div style="color: white; font-size: 1.5rem; font-weight: bold;">{len(jogos_list)}</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px;">
                    <div style="color: #ccc; font-size: 0.8rem;">Custo Total</div>
                    <div style="color: white; font-size: 1.5rem; font-weight: bold;">R$ {custo_total:,.2f}</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px;">
                    <div style="color: #ccc; font-size: 0.8rem;">Sobra</div>
                    <div style="color: white; font-size: 1.5rem; font-weight: bold;">R$ {sobra:,.2f}</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px;">
                    <div style="color: #ccc; font-size: 0.8rem;">Score Médio</div>
                    <div style="color: white; font-size: 1.5rem; font-weight: bold;">{df_jogos['score_combinado'].mean():.1f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ========================================
        # CÁLCULO DE PROBABILIDADE
        # ========================================
        from math import comb

        # Total de combinações possíveis na Mega-Sena: C(60,6)
        TOTAL_COMBINACOES_MEGA = comb(60, 6)  # 50.063.860

        # Calcular combinações cobertas por cada jogo
        # Jogo de N dezenas cobre C(N,6) combinações de sena
        combinacoes_por_jogo = []
        for j in jogos_list:
            n_dez = j.get('n_dezenas', len(j['numeros']))
            comb_jogo = comb(n_dez, 6)
            combinacoes_por_jogo.append({
                'n_dezenas': n_dez,
                'combinacoes': comb_jogo
            })

        # Soma total de combinações (nota: pode haver sobreposição entre jogos)
        total_combinacoes_cobertas = sum(c['combinacoes'] for c in combinacoes_por_jogo)

        # Probabilidade de acertar a sena (assumindo sem sobreposição significativa)
        probabilidade = total_combinacoes_cobertas / TOTAL_COMBINACOES_MEGA
        probabilidade_pct = probabilidade * 100

        # Chance 1 em X
        if probabilidade > 0:
            chance_1_em = int(1 / probabilidade)
        else:
            chance_1_em = TOTAL_COMBINACOES_MEGA

        # Card de probabilidade
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); padding: 20px; border-radius: 15px; margin: 15px 0;">
            <h3 style="color: white; margin: 0 0 15px 0; text-align: center;">🎲 Análise de Probabilidade</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center;">
                <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px;">
                    <div style="color: #bdc3c7; font-size: 0.85rem;">Combinações Cobertas</div>
                    <div style="color: white; font-size: 1.4rem; font-weight: bold;">{total_combinacoes_cobertas:,}</div>
                    <div style="color: #bdc3c7; font-size: 0.75rem;">de {TOTAL_COMBINACOES_MEGA:,} possíveis</div>
                </div>
                <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px;">
                    <div style="color: #bdc3c7; font-size: 0.85rem;">Probabilidade de Sena</div>
                    <div style="color: #2ecc71; font-size: 1.4rem; font-weight: bold;">{probabilidade_pct:.6f}%</div>
                    <div style="color: #bdc3c7; font-size: 0.75rem;">com todos os jogos</div>
                </div>
                <div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px;">
                    <div style="color: #bdc3c7; font-size: 0.85rem;">Chance</div>
                    <div style="color: #f39c12; font-size: 1.4rem; font-weight: bold;">1 em {chance_1_em:,}</div>
                    <div style="color: #bdc3c7; font-size: 0.75rem;">aproximadamente</div>
                </div>
            </div>
            <div style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                <div style="color: #ecf0f1; font-size: 0.85rem; text-align: center;">
                    📊 <b>Combinações por tipo:</b> {' | '.join([f"{nd}dez: {comb(nd,6):,}" for nd in sorted(dist_dezenas.keys(), reverse=True)])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Distribuição de dezenas
        dist_html = " | ".join([f"<b>{nd}dez:</b> {qtd}x" for nd, qtd in sorted(dist_dezenas.items(), reverse=True)])
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 12px 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #28a745;">
            <span style="color: #666;">📊 <b>Distribuição:</b></span> {dist_html}
        </div>
        """, unsafe_allow_html=True)

        # Tabela de jogos
        st.markdown("##### 📋 Jogos Gerados")

        # Contar jogos com fallback
        jogos_fallback = sum(1 for j in jogos_list if j.get('usou_fallback', False))
        if jogos_fallback > 0:
            st.warning(f"⚠️ **{jogos_fallback} jogo(s)** foram gerados com fallback (padrões específicos não atendidos, usou validação por range)")

        # Exibir cada jogo como card
        for i, jogo in enumerate(jogos_list, 1):
            numeros = jogo['numeros']
            n_dezenas = jogo.get('n_dezenas', len(numeros))
            custo_jogo = jogo.get('custo', TABELA_CUSTOS_OFICIAL.get(n_dezenas, 0))
            usou_fallback = jogo.get('usou_fallback', False)

            # Título com indicador de fallback
            titulo_fallback = " ⚠️" if usou_fallback else ""
            with st.expander(f"🎰 Jogo #{i}: {'-'.join(f'{n:02d}' for n in numeros)} | {n_dezenas} dez | R$ {custo_jogo:,.2f} | Score: {jogo['score_combinado']:.1f}{titulo_fallback}", expanded=(i <= 3)):
                col1_j, col2_j, col3_j = st.columns([2, 1.2, 1.3])

                with col1_j:
                    # Aviso de fallback
                    if usou_fallback:
                        st.caption("⚠️ Gerado com fallback (padrões relaxados)")

                    # Volante visual mini
                    html_nums = ""
                    for n in range(1, 61):
                        bg = "#28a745" if n in numeros else "#f0f0f0"
                        color = "white" if n in numeros else "#333"
                        html_nums += f'<span style="display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;margin:2px;border-radius:50%;background:{bg};color:{color};font-size:0.75rem;font-weight:bold;">{n:02d}</span>'
                        if n % 10 == 0:
                            html_nums += "<br>"

                    st.markdown(f'<div style="font-family:monospace;">{html_nums}</div>', unsafe_allow_html=True)

                with col2_j:
                    st.markdown(f"""
                    **📋 Análise:**
                    - 🎯 Dezenas: `{n_dezenas}`
                    - 💰 Custo: `R$ {custo_jogo:,.2f}`
                    - 🔲 Quadrantes: `{jogo['padrao_quad']}`
                    - ⚖️ Paridade: `{jogo['padrao_par']}`
                    - 📶 Faixas: `{jogo['padrao_bma']}`
                    - 📏 Linhas: `{jogo.get('linhas_usadas', '-')}`
                    - 🔢 Terminações: `{jogo.get('terminacoes_usadas', '-')}`
                    - ➕ Soma: `{jogo['soma']}`
                    - 🔥 H-N-F: `{jogo.get('hot_count', 0)}H-{jogo.get('neutral_count', 0)}N-{jogo.get('cold_count', 0)}F`
                    - 🔗 Consecutivos: `{jogo['consecutivos']}`
                    """)

                with col3_j:
                    # Painel de Notas por Regra
                    st.markdown("**📊 Notas:**")

                    # Função para emoji/letra baseado na nota
                    def get_nota_label(nota):
                        if nota >= 90:
                            return "A+", "🟢"
                        elif nota >= 80:
                            return "A", "🟢"
                        elif nota >= 70:
                            return "B", "🟡"
                        elif nota >= 60:
                            return "C", "🟡"
                        elif nota >= 50:
                            return "D", "🟠"
                        else:
                            return "E", "🔴"

                    # Notas das regras de conjunto (usando aderências)
                    notas = {
                        'Quadrantes': jogo.get('aderencia_quad', 50),
                        'Paridade': jogo.get('aderencia_par', 50),
                        'Faixas': jogo.get('aderencia_bma', 50),
                        'Soma': jogo.get('aderencia_soma', 50),
                        'Sequências': jogo.get('aderencia_seq', 50),
                    }

                    # Calcular notas adicionais
                    linhas_jogo = jogo.get('linhas_usadas', 4)
                    linhas_ideal = min(6, max(4, n_dezenas * 0.6))
                    notas['Linhas'] = min(100, (linhas_jogo / linhas_ideal) * 100)

                    terminacoes_jogo = jogo.get('terminacoes_usadas', 5)
                    terminacoes_ideal = min(10, max(5, n_dezenas * 0.7))
                    notas['Terminações'] = min(100, (terminacoes_jogo / terminacoes_ideal) * 100)

                    hot = jogo.get('hot_count', 0)
                    neutral = jogo.get('neutral_count', 0)
                    cold = jogo.get('cold_count', 0)
                    hot_ideal = n_dezenas * 0.4
                    neutral_ideal = n_dezenas * 0.35
                    cold_ideal = n_dezenas * 0.25
                    desvio_hnf = (abs(hot - hot_ideal) + abs(neutral - neutral_ideal) + abs(cold - cold_ideal)) / 3
                    notas['H-N-F'] = max(0, 100 - desvio_hnf * 30)

                    # Exibir notas usando st.progress
                    for regra, nota in notas.items():
                        letra, emoji = get_nota_label(nota)
                        col_label, col_bar, col_nota = st.columns([1.2, 1.5, 0.5])
                        with col_label:
                            st.caption(regra)
                        with col_bar:
                            st.progress(min(100, int(nota)) / 100)
                        with col_nota:
                            st.caption(f"{emoji}{letra}")

                    # Nota final (média ponderada)
                    nota_final = (
                        notas.get('Quadrantes', 0) * 0.15 +
                        notas.get('Paridade', 0) * 0.20 +
                        notas.get('Faixas', 0) * 0.15 +
                        notas.get('Linhas', 0) * 0.10 +
                        notas.get('Terminações', 0) * 0.10 +
                        notas.get('Soma', 0) * 0.15 +
                        notas.get('H-N-F', 0) * 0.10 +
                        notas.get('Sequências', 0) * 0.05
                    )
                    letra_final, emoji_final = get_nota_label(nota_final)

                    st.markdown("---")
                    col_f1, col_f2, col_f3 = st.columns([1.2, 1.5, 0.5])
                    with col_f1:
                        st.markdown("**FINAL**")
                    with col_f2:
                        st.progress(min(100, int(nota_final)) / 100)
                    with col_f3:
                        st.markdown(f"**{emoji_final}{letra_final}**")

        # Botão para exportar
        st.markdown("---")
        csv = df_jogos.to_csv(index=False)
        st.download_button(
            label="📥 Baixar Jogos (CSV)",
            data=csv,
            file_name="megasena_jogos.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Botão para limpar
        if st.button("🗑️ Limpar Jogos", use_container_width=True):
            st.session_state.jogos_gerados = None
            st.rerun()

    st.markdown("---")

    # ==========================================================================
    # SEÇÃO 2: QUADRO DE REGRAS (COMPACTO)
    # ==========================================================================
    try:
        regras_df = carregar_regras()
        regras_individual = regras_df[regras_df['tipo'] == 'individual']
        regras_conjunto = regras_df[regras_df['tipo'] == 'conjunto']
        peso_ind = regras_individual['peso'].sum()
        peso_conj = regras_conjunto['peso'].sum()

        # Header compacto com resumo inline
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 15px; margin: 10px 0 15px 0;">
            <span style="font-size: 1.3rem; font-weight: bold;">📋 Regras do Sistema</span>
            <span style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.8rem;">15 Regras</span>
            <span style="background: #4169E1; color: white; padding: 4px 10px; border-radius: 15px; font-size: 0.75rem;">📍 6 Individuais ({peso_ind:.0f}%)</span>
            <span style="background: #FF8C00; color: white; padding: 4px 10px; border-radius: 15px; font-size: 0.75rem;">🎯 9 Conjunto ({peso_conj:.0f}%)</span>
        </div>
        """, unsafe_allow_html=True)

        # Grid compacto com todas as regras
        # Individuais (R1-R6) + Conjunto (R4-R15)
        regras_ind_html = ' '.join([
            f'<span style="background: rgba(65,105,225,0.15); color: #4169E1; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; white-space: nowrap;"><b>{r["codigo"]}</b> {r["nome"]} <span style="opacity:0.7;">({r["peso"]:.0f}%)</span></span>'
            for _, r in regras_individual.iterrows()
        ])
        regras_conj_html = ' '.join([
            f'<span style="background: rgba(255,140,0,0.15); color: #FF8C00; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; white-space: nowrap;"><b>{r["codigo"]}</b> {r["nome"]} <span style="opacity:0.7;">({r["peso"]:.0f}%)</span></span>'
            for _, r in regras_conjunto.iterrows()
        ])

        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">
                {regras_ind_html}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                {regras_conj_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao carregar regras: {e}")

    st.markdown("---")

    # ==========================================================================
    # SEÇÃO 3: ANÁLISE & SCORES
    # ==========================================================================
    st.markdown("## 📊 Análise Estatística & Scores")

    # Usar funções cacheadas para evitar recarregamento
    score_ind = carregar_score_individual()
    ch_client = get_clickhouse_client()  # Cliente cacheado para queries restantes

    # =================================================================
    # SEÇÃO 1: REGRAS INDIVIDUAIS (v_score_individual)
    # =================================================================
    st.markdown("#### 📍 Regras Individuais (R1, R2, R3, R10, R11, R15)")
    st.markdown("*Análise de cada número de 1 a 60*")

    # Top 6 números
    st.markdown("##### 🏆 Top 6 por Score Individual")
    cols = st.columns(6)
    for i, (_, row) in enumerate(score_ind.head(6).iterrows()):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4169E1 0%, #1e40af 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: white;">
                <div style="font-size: 1.8rem; font-weight: bold;">{int(row['numero']):02d}</div>
                <div style="font-size: 1rem;">{row['score_individual']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    # Estatísticas das regras individuais em 2 colunas
    col1, col2 = st.columns(2)

    with col1:
        # R1 - Frequência
        st.markdown("##### 📊 R1 - Frequência Histórica")
        st.caption("Quantas vezes cada número foi sorteado")
        r1_stats = ch_client.query('''
            SELECT
                multiIf(r1_freq >= 90, '90+ (Muito Alta)', r1_freq >= 80, '80-89 (Alta)',
                        r1_freq >= 70, '70-79 (Média-Alta)', '< 70 (Média)') as faixa,
                count(*) as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''')
        for _, r in r1_stats.iterrows():
            pct = float(r['qtd']) / 60 * 100
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span>{r['faixa']}</span><span>{int(r['qtd'])} números</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: #4169E1; width: {pct}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # R3 - Tendência
        st.markdown("##### 🔥 R3 - Tendência Recente (48 concursos)")
        st.caption("Aparições nos últimos 48 concursos")
        r3_stats = ch_client.query('''
            SELECT
                multiIf(r3_tend >= 80, 'Quente (80+)', r3_tend >= 50, 'Morno (50-79)',
                        r3_tend >= 20, 'Frio (20-49)', 'Gelado (<20)') as faixa,
                count(*) as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''')
        for _, r in r3_stats.iterrows():
            pct = float(r['qtd']) / 60 * 100
            cor = '#dc3545' if 'Quente' in r['faixa'] else '#ffc107' if 'Morno' in r['faixa'] else '#17a2b8'
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span>{r['faixa']}</span><span>{int(r['qtd'])} números</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: {cor}; width: {pct}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # R11 - Poisson
        st.markdown("##### 📈 R11 - Distribuição de Poisson")
        st.caption("Probabilidade estatística esperada")
        r11_stats = ch_client.query('''
            SELECT round(avg(r11_poisson), 1) as media, round(min(r11_poisson), 1) as minimo, round(max(r11_poisson), 1) as maximo
            FROM loterias.v_score_individual
        ''')
        st.markdown(f"""
        <div style="display: flex; gap: 10px; margin: 5px 0;">
            <div style="background: #f8f9fa; padding: 8px 15px; border-radius: 6px; text-align: center; flex: 1;">
                <div style="font-size: 1.2rem; font-weight: bold; color: #4169E1;">{r11_stats.iloc[0]['media']}</div>
                <div style="font-size: 0.7rem; color: #666;">Média</div>
            </div>
            <div style="background: #f8f9fa; padding: 8px 15px; border-radius: 6px; text-align: center; flex: 1;">
                <div style="font-size: 1.2rem; font-weight: bold; color: #28a745;">{r11_stats.iloc[0]['minimo']}</div>
                <div style="font-size: 0.7rem; color: #666;">Mín</div>
            </div>
            <div style="background: #f8f9fa; padding: 8px 15px; border-radius: 6px; text-align: center; flex: 1;">
                <div style="font-size: 1.2rem; font-weight: bold; color: #dc3545;">{r11_stats.iloc[0]['maximo']}</div>
                <div style="font-size: 0.7rem; color: #666;">Máx</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # R2 - Atraso
        st.markdown("##### ⏰ R2 - Atraso (Regressão à Média)")
        st.caption("Há quantos concursos o número não sai")
        r2_stats = ch_client.query('''
            SELECT
                multiIf(r2_atraso >= 80, 'Alto (80+)', r2_atraso >= 50, 'Médio (50-79)',
                        r2_atraso >= 20, 'Baixo (20-49)', 'Recente (<20)') as faixa,
                count(*) as qtd
            FROM loterias.v_score_individual
            GROUP BY faixa ORDER BY faixa DESC
        ''')
        for _, r in r2_stats.iterrows():
            pct = float(r['qtd']) / 60 * 100
            cor = '#dc3545' if 'Alto' in r['faixa'] else '#ffc107' if 'Médio' in r['faixa'] else '#28a745'
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span>{r['faixa']}</span><span>{int(r['qtd'])} números</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: {cor}; width: {pct}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # R10 - Ciclo
        st.markdown("##### 🔄 R10 - Ciclo de Renovação (27 concursos)")
        st.caption("Números faltantes ganham score 100")
        r10_stats = ch_client.query('''
            SELECT if(r10_ciclo = 100, 'Faltante', 'Presente') as status, count(*) as qtd
            FROM loterias.v_score_individual GROUP BY status
        ''')
        faltantes = r10_stats[r10_stats['status'] == 'Faltante']['qtd'].values
        faltantes_qtd = int(faltantes[0]) if len(faltantes) > 0 else 0
        presentes_qtd = 60 - faltantes_qtd
        st.markdown(f"""
        <div style="display: flex; gap: 10px; margin: 5px 0;">
            <div style="background: #dc3545; color: white; padding: 10px 15px; border-radius: 8px; text-align: center; flex: 1;">
                <div style="font-size: 1.5rem; font-weight: bold;">{faltantes_qtd}</div>
                <div style="font-size: 0.8rem;">Faltantes (100)</div>
            </div>
            <div style="background: #28a745; color: white; padding: 10px 15px; border-radius: 8px; text-align: center; flex: 1;">
                <div style="font-size: 1.5rem; font-weight: bold;">{presentes_qtd}</div>
                <div style="font-size: 0.8rem;">Presentes (0)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # R15 - Pressão Ciclo
        st.markdown("##### 🎯 R15 - Pressão do Ciclo Completo")
        st.caption("Pressão dos números faltantes no ciclo de 60")
        r15_stats = ch_client.query('''
            SELECT round(max(r15_pressao), 1) as max_pressao,
                   count(if(r15_pressao > 0, 1, NULL)) as com_pressao
            FROM loterias.v_score_individual
        ''')
        max_pressao = r15_stats.iloc[0]['max_pressao']
        com_pressao = int(r15_stats.iloc[0]['com_pressao'])
        st.markdown(f"""
        <div style="display: flex; gap: 10px; margin: 5px 0;">
            <div style="background: #f8f9fa; padding: 8px 15px; border-radius: 6px; text-align: center; flex: 1; border-left: 3px solid #dc3545;">
                <div style="font-size: 1.2rem; font-weight: bold; color: #dc3545;">{max_pressao}%</div>
                <div style="font-size: 0.7rem; color: #666;">Pressão Máxima</div>
            </div>
            <div style="background: #f8f9fa; padding: 8px 15px; border-radius: 6px; text-align: center; flex: 1; border-left: 3px solid #ffc107;">
                <div style="font-size: 1.2rem; font-weight: bold; color: #ffc107;">{com_pressao}</div>
                <div style="font-size: 0.7rem; color: #666;">Com Pressão</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Tabela completa
    with st.expander("📋 Ver tabela completa dos 60 números", expanded=False):
        display_cols = ['numero', 'r1_freq', 'r2_atraso', 'r3_tend', 'r10_ciclo', 'r11_poisson', 'r15_pressao', 'score_individual']
        st.dataframe(score_ind[display_cols], use_container_width=True, hide_index=True)

    st.markdown("---")

    # =================================================================
    # SEÇÃO 2: REGRAS DE CONJUNTO (v_concurso_analise)
    # =================================================================
    st.markdown("#### 🎯 Regras de Conjunto (R4, R5, R6, R7, R8, R9, R12, R13, R14)")
    st.markdown("*Análise do jogo como um todo - padrões históricos*")

    # Linha 1: R4, R5
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🔲 R4 - Quadrantes (Q1-Q4)")
        st.caption("Q1: 1-15 | Q2: 16-30 | Q3: 31-45 | Q4: 46-60")
        quadrantes = ch_client.query('''
            SELECT concat(toString(q1_count), '-', toString(q2_count), '-', toString(q3_count), '-', toString(q4_count)) as padrao,
                   count(*) as qtd, round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY q1_count, q2_count, q3_count, q4_count ORDER BY qtd DESC LIMIT 6
        ''')
        for _, r in quadrantes.iterrows():
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{r['padrao']}</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: #667eea; width: {float(r['pct'])}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("##### ⚖️ R5 - Paridade (Pares/Ímpares)")
        st.caption("Equilíbrio entre números pares e ímpares")
        paridade = ch_client.query('''
            SELECT concat(toString(pares_count), 'P/', toString(impares_count), 'I') as padrao,
                   count(*) as qtd, round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY pares_count, impares_count ORDER BY qtd DESC
        ''')
        for _, r in paridade.iterrows():
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{r['padrao']}</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: #4169E1; width: {float(r['pct'])}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Linha 2: R6, R7
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("##### 📶 R6 - Faixas Baixo/Médio/Alto")
        st.caption("B: 1-20 | M: 21-40 | A: 41-60")
        bma = ch_client.query('''
            SELECT concat(toString(baixo_count), '-', toString(medio_count), '-', toString(alto_count)) as padrao,
                   count(*) as qtd, round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY baixo_count, medio_count, alto_count ORDER BY qtd DESC LIMIT 6
        ''')
        for _, r in bma.iterrows():
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{r['padrao']}</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: #FF8C00; width: {float(r['pct'])}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col4:
        st.markdown("##### ➡️ R7 - Linhas do Volante")
        st.caption("L1: 1-10 | L2: 11-20 | ... | L6: 51-60")
        linhas = ch_client.query('''
            SELECT (if(l1_count > 0, 1, 0) + if(l2_count > 0, 1, 0) + if(l3_count > 0, 1, 0) +
                    if(l4_count > 0, 1, 0) + if(l5_count > 0, 1, 0) + if(l6_count > 0, 1, 0)) as linhas_usadas,
                   count(*) as qtd, round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise GROUP BY linhas_usadas ORDER BY qtd DESC
        ''')
        for _, r in linhas.iterrows():
            cor = '#28a745' if r['linhas_usadas'] >= 5 else '#ffc107' if r['linhas_usadas'] == 4 else '#dc3545'
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{int(r['linhas_usadas'])} linhas</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: {cor}; width: {float(r['pct'])}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Linha 3: R8, R9
    col5, col6 = st.columns(2)

    with col5:
        st.markdown("##### ⬇️ R8 - Colunas/Terminações")
        st.caption("Terminações 0-9 (final do número)")
        colunas = ch_client.query('''
            SELECT (if(c0_count > 0, 1, 0) + if(c1_count > 0, 1, 0) + if(c2_count > 0, 1, 0) +
                    if(c3_count > 0, 1, 0) + if(c4_count > 0, 1, 0) + if(c5_count > 0, 1, 0) +
                    if(c6_count > 0, 1, 0) + if(c7_count > 0, 1, 0) + if(c8_count > 0, 1, 0) +
                    if(c9_count > 0, 1, 0)) as terminacoes,
                   count(*) as qtd, round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise GROUP BY terminacoes ORDER BY qtd DESC
        ''')
        for _, r in colunas.iterrows():
            cor = '#28a745' if r['terminacoes'] >= 5 else '#ffc107' if r['terminacoes'] == 4 else '#dc3545'
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{int(r['terminacoes'])} terminações</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: {cor}; width: {float(r['pct'])}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col6:
        st.markdown("##### ➕ R9 - Soma dos 6 Números")
        st.caption("Faixa ideal: 150-210")
        soma = ch_client.query('''
            SELECT multiIf(soma < 120, '< 120', soma < 150, '120-149', soma < 180, '150-179',
                          soma < 210, '180-209', soma < 240, '210-239', '>= 240') as faixa,
                   count(*) as qtd, round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise GROUP BY faixa ORDER BY qtd DESC
        ''')
        for _, r in soma.iterrows():
            cor = '#28a745' if '150' in str(r['faixa']) or '180' in str(r['faixa']) else '#ffc107'
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{r['faixa']}</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: {cor}; width: {float(r['pct'])}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Linha 4: R12, R13
    col7, col8 = st.columns(2)

    with col7:
        st.markdown("##### 🔥 R12 - H-N-F (Hot-Neutral-Frio)")
        st.caption("Classificacao por aparicoes nos ultimos 48 concursos: H>=6, N=4-5, F<=3")
        hnf = ch_client.query('''
            SELECT
                concat(toString(hot_count), 'H-', toString(neutral_count), 'N-', toString(cold_count), 'F') as pattern,
                count(*) as qtd,
                round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise
            GROUP BY hot_count, neutral_count, cold_count
            ORDER BY qtd DESC
            LIMIT 6
        ''')
        for _, r in hnf.iterrows():
            # Cor verde se tiver 2-3H, 2-3N, 0-2F (ideal)
            pattern = r['pattern']
            h = int(pattern.split('H')[0])
            n = int(pattern.split('H-')[1].split('N')[0])
            f = int(pattern.split('N-')[1].split('F')[0])
            ideal = (2 <= h <= 3) and (2 <= n <= 4) and (f <= 2)
            cor = '#28a745' if ideal else '#ffc107'
            st.markdown(f"""
            <div style="margin: 4px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span><strong>{r['pattern']}</strong></span><span>{r['pct']}% ({int(r['qtd'])}x)</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 4px; height: 6px;">
                    <div style="background: {cor}; width: {min(float(r['pct']) * 3, 100)}%; height: 6px; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col8:
        st.markdown("##### 🔢 R13 - Sequências Consecutivas")
        st.caption("Quantidade de números consecutivos no jogo (ex: 12-13, 25-26)")
        seq = ch_client.query('''
            SELECT sequencias_consecutivas as seq, count(*) as qtd,
                   round(count(*) * 100.0 / (SELECT count(*) FROM loterias.v_concurso_analise), 1) as pct
            FROM loterias.v_concurso_analise GROUP BY seq ORDER BY qtd DESC
        ''')
        cols_seq = st.columns(len(seq))
        for i, (_, r) in enumerate(seq.iterrows()):
            cor = '#28a745' if r['seq'] <= 1 else '#ffc107' if r['seq'] == 2 else '#dc3545'
            with cols_seq[i]:
                st.markdown(f"""
                <div style="background: {cor}; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.3rem; font-weight: bold;">{int(r['seq'])}</div>
                    <div style="font-size: 0.8rem;">{r['pct']}%</div>
                    <div style="font-size: 0.7rem; opacity: 0.8;">{int(r['qtd'])}x</div>
                </div>
                """, unsafe_allow_html=True)

    # Linha 5: R14 - Frequência por Quadrante
    st.markdown("##### 🗺️ R14 - Frequência por Quadrante")
    st.caption("Score médio de frequência histórica por quadrante (maior = mais sorteado)")
    freq_quad = ch_client.query('''
        SELECT quadrante, round(avg(score_freq_quadrante), 1) as score_medio
        FROM loterias.v_score_freq_quadrante
        GROUP BY quadrante
        ORDER BY quadrante
    ''')
    cols_r14 = st.columns(4)
    cores_quad = {'Q1': '#667eea', 'Q2': '#17a2b8', 'Q3': '#28a745', 'Q4': '#ffc107'}
    labels_quad = {'Q1': '1-15', 'Q2': '16-30', 'Q3': '31-45', 'Q4': '46-60'}
    for i, (_, r) in enumerate(freq_quad.iterrows()):
        quad = r['quadrante']
        score = float(r['score_medio'])
        cor = cores_quad.get(quad, '#666')
        label = labels_quad.get(quad, '')
        destaque = ' (Maior)' if score == 100 else ''
        with cols_r14[i]:
            st.markdown(f"""
            <div style="background: {cor}; color: white; padding: 12px; border-radius: 8px; text-align: center;">
                <div style="font-size: 1rem; font-weight: bold;">{quad}</div>
                <div style="font-size: 0.7rem; opacity: 0.8;">{label}</div>
                <div style="font-size: 1.4rem; font-weight: bold; margin-top: 5px;">{score}</div>
                <div style="font-size: 0.7rem;">{destaque}</div>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================================================
if __name__ == "__main__":
    main()
