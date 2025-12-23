#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     PROJETO MEGA-SENA - ALGORITMO PREDITIVO                  ║
║                        Análise Estatística Avançada                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Autor: Cientista de Dados Sênior                                            ║
║  Versão: 1.0                                                                 ║
║  Budget: R$ 180.000,00                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Este algoritmo implementa análises estatísticas rigorosas para seleção de
dezenas na Mega-Sena, incluindo:

- Análise de Quadrantes e Linhas (Volante 6x10)
- Temperaturas Hot/Cold
- Padrões Par/Ímpar e Alto/Baixo
- Lei dos Grandes Números e Ciclos
- Distribuição de Poisson
- Sistema de Scoring (0-100)
- Duas Estratégias de Alocação de Capital

IMPORTANTE: Este é um algoritmo de análise estatística. Cada sorteio é um
evento independente e o algoritmo NÃO garante ganhos.
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

from config import BUDGET_TOTAL, TABELA_CUSTOS_OFICIAL, PROBABILIDADES
from data_loader import MegaSenaDataLoader, load_data
from statistical_analysis import MegaSenaAnalyzer
from strategies import (
    EstrategiaA, EstrategiaB, ComparadorEstrategias,
    CalculadoraEsperanca
)


def print_header():
    """Imprime cabeçalho do programa."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     PROJETO MEGA-SENA - ALGORITMO PREDITIVO                  ║
║                        Análise Estatística Avançada                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                          Budget: R$ 180.000,00                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def print_section(titulo: str):
    """Imprime separador de seção."""
    print(f"\n{'='*80}")
    print(f" {titulo}")
    print('='*80)


def exibir_analise_completa(analyzer: MegaSenaAnalyzer, df: pd.DataFrame):
    """Exibe análise estatística completa dos dados."""

    print_section("1. SUMÁRIO DOS DADOS")
    loader = MegaSenaDataLoader()
    loader.df = df
    sumario = loader.get_summary()
    print(f"""
    Total de Concursos Analisados: {sumario['total_concursos']}
    Primeiro Concurso: #{sumario['primeiro_concurso']}
    Último Concurso: #{sumario['ultimo_concurso']}
    Número Mais Frequente: {sumario['numero_mais_frequente']}
    Número Menos Frequente: {sumario['numero_menos_frequente']}
    Soma Média das Dezenas: {sumario['media_soma_dezenas']:.2f}
    """)

    print_section("2. ANÁLISE DE FREQUÊNCIAS")
    freq = analyzer.calcular_frequencias()
    freq_sorted = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    print("\n    TOP 10 MAIS FREQUENTES:")
    for i, (num, count) in enumerate(freq_sorted[:10], 1):
        barra = '█' * int(count / max(freq.values()) * 30)
        print(f"    {i:2}. Número {num:02d}: {count:4d} vezes {barra}")

    print("\n    TOP 10 MENOS FREQUENTES:")
    for i, (num, count) in enumerate(freq_sorted[-10:], 1):
        barra = '█' * int(count / max(freq.values()) * 30)
        print(f"    {i:2}. Número {num:02d}: {count:4d} vezes {barra}")

    print_section("3. ANÁLISE HOT/COLD (TEMPERATURAS)")

    print("\n    NÚMEROS 'HOT' (Últimos 10 jogos):")
    hot = analyzer.calcular_hot_numbers()
    hot_sorted = sorted(hot.items(), key=lambda x: x[1], reverse=True)[:10]
    for num, count in hot_sorted:
        status = "🔥 MUITO QUENTE" if count >= 3 else "♨️  Quente" if count >= 2 else "Morno"
        print(f"    Número {num:02d}: {count} aparições - {status}")

    print("\n    NÚMEROS 'COLD' (Mais Atrasados):")
    cold = analyzer.calcular_cold_numbers()
    cold_sorted = sorted(cold.items(), key=lambda x: x[1], reverse=True)[:10]
    for num, atraso in cold_sorted:
        status = "❄️  MUITO FRIO" if atraso >= 20 else "🧊 Frio" if atraso >= 15 else "Fresco"
        print(f"    Número {num:02d}: {atraso} concursos sem sair - {status}")

    print_section("4. ANÁLISE DE PARIDADE (PAR/ÍMPAR)")
    paridade = analyzer.analisar_paridade()
    print("\n    Distribuição Histórica:")
    for padrao, perc in list(paridade.items())[:6]:
        barra = '█' * int(perc)
        print(f"    {padrao}: {perc:5.2f}% {barra}")
    print("\n    💡 Padrão ideal: 3P-3I (equilíbrio)")

    print_section("5. ANÁLISE ALTO/BAIXO")
    alto_baixo = analyzer.analisar_alto_baixo()
    print("\n    Distribuição Histórica (1-30 = Baixo, 31-60 = Alto):")
    for padrao, perc in list(alto_baixo.items())[:6]:
        barra = '█' * int(perc)
        print(f"    {padrao}: {perc:5.2f}% {barra}")
    print("\n    💡 Padrão ideal: 3B-3A (equilíbrio)")

    print_section("6. ANÁLISE DE QUADRANTES")
    quadrantes = analyzer.analisar_quadrantes()
    print("""
    Layout do Volante Mega-Sena (6x10):

    ┌─────────────────────┬─────────────────────┐
    │     QUADRANTE 1     │     QUADRANTE 2     │
    │   01-05, 11-15,     │   06-10, 16-20,     │
    │      21-25          │      26-30          │
    ├─────────────────────┼─────────────────────┤
    │     QUADRANTE 3     │     QUADRANTE 4     │
    │   31-35, 41-45,     │   36-40, 46-50,     │
    │      51-55          │      56-60          │
    └─────────────────────┴─────────────────────┘
    """)
    for q, data in quadrantes.items():
        print(f"    {q}: Média {data['media_aparicoes']:.2f} números por sorteio (ideal: 1.5)")

    print_section("7. CICLO DE RENOVAÇÃO (LEI DOS GRANDES NÚMEROS)")
    ciclo = analyzer.calcular_ciclo_renovacao()
    print(f"""
    Ciclo Médio Global: {ciclo['ciclo_medio_global']:.2f} concursos
    Ciclo Esperado Teórico: {ciclo['ciclo_esperado_teorico']:.2f} concursos (60/6)

    💡 Interpretação: Em média, cada número aparece a cada {ciclo['ciclo_medio_global']:.1f}
       concursos. A teoria prevê ~10 concursos entre aparições.
    """)


def exibir_scores(analyzer: MegaSenaAnalyzer):
    """Exibe ranking completo de scores."""

    print_section("8. RANKING DE SCORES (0-100)")
    print("""
    O Score é calculado combinando múltiplos fatores:
    - Frequência Histórica (25%)
    - Atraso/Regressão à Média (20%)
    - Tendência Recente (15%)
    - Equilíbrio de Quadrante (15%)
    - Contribuição para Paridade (10%)
    - Contribuição Alto/Baixo (10%)
    - Probabilidade Poisson (5%)
    """)

    scores_df = analyzer.calcular_todos_scores()

    print("\n    TOP 20 MELHORES SCORES:")
    print("    " + "-"*76)
    print(f"    {'Nº':>3} {'Score':>7} {'Freq':>6} {'Atraso':>7} {'Tend':>6} {'Quad':>6} {'Par':>5} {'A/B':>5}")
    print("    " + "-"*76)

    for _, row in scores_df.head(20).iterrows():
        print(f"    {int(row['numero']):3d} {row['score_final']:7.2f} "
              f"{row['score_frequencia']:6.1f} {row['score_atraso']:7.1f} "
              f"{row['score_tendencia']:6.1f} {row['score_quadrante']:6.1f} "
              f"{row['score_paridade']:5.1f} {row['score_alto_baixo']:5.1f}")

    print("\n    BOTTOM 10 (ZEBRAS):")
    print("    " + "-"*76)
    for _, row in scores_df.tail(10).iterrows():
        print(f"    {int(row['numero']):3d} {row['score_final']:7.2f} "
              f"{row['score_frequencia']:6.1f} {row['score_atraso']:7.1f} "
              f"{row['score_tendencia']:6.1f} {row['score_quadrante']:6.1f} "
              f"{row['score_paridade']:5.1f} {row['score_alto_baixo']:5.1f}")


def exibir_estrategias(analyzer: MegaSenaAnalyzer):
    """Exibe comparação detalhada das estratégias."""

    comparador = ComparadorEstrategias(analyzer)
    relatorio = comparador.gerar_relatorio()
    print(relatorio)


def exibir_sugestao_final(analyzer: MegaSenaAnalyzer):
    """Exibe sugestão final de jogos."""

    print_section("SUGESTÃO FINAL DE JOGOS")

    est_a = EstrategiaA(analyzer)
    est_b = EstrategiaB(analyzer)

    jogo_19 = est_a.gerar_jogo_principal()
    jogo_18 = est_b.gerar_jogo_principal()

    print(f"""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                    ESTRATÉGIA A - JOGO DE 19 DEZENAS                     ║
    ║                         (Custo: R$ 162.792,00)                           ║
    ╚══════════════════════════════════════════════════════════════════════════╝

    DEZENAS SELECIONADAS:
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  {' - '.join(f'{d:02d}' for d in jogo_19.dezenas[:10])}  │
    │  {' - '.join(f'{d:02d}' for d in jogo_19.dezenas[10:])}              │
    └──────────────────────────────────────────────────────────────────────────┘
    """)

    equilibrio_19 = analyzer.validar_equilibrio_jogo(jogo_19.dezenas)
    print(f"""    Validação de Equilíbrio:
    - Pares: {equilibrio_19['pares']} | Ímpares: {equilibrio_19['impares']}
    - Baixos (1-30): {equilibrio_19['baixos']} | Altos (31-60): {equilibrio_19['altos']}
    - Soma Total: {equilibrio_19['soma_total']}
    - Distribuição por Linhas: {equilibrio_19['distribuicao_linhas']}
    """)

    print(f"""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                    ESTRATÉGIA B - JOGO DE 18 DEZENAS                     ║
    ║                    (Números HOT - Custo: R$ 111.384,00)                  ║
    ╚══════════════════════════════════════════════════════════════════════════╝

    DEZENAS SELECIONADAS:
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  {' - '.join(f'{d:02d}' for d in jogo_18.dezenas[:9])}         │
    │  {' - '.join(f'{d:02d}' for d in jogo_18.dezenas[9:])}         │
    └──────────────────────────────────────────────────────────────────────────┘
    """)

    equilibrio_18 = analyzer.validar_equilibrio_jogo(jogo_18.dezenas)
    print(f"""    Validação de Equilíbrio:
    - Pares: {equilibrio_18['pares']} | Ímpares: {equilibrio_18['impares']}
    - Baixos (1-30): {equilibrio_18['baixos']} | Altos (31-60): {equilibrio_18['altos']}
    - Soma Total: {equilibrio_18['soma_total']}
    - Distribuição por Linhas: {equilibrio_18['distribuicao_linhas']}
    """)


def main():
    """Função principal do programa."""

    parser = argparse.ArgumentParser(
        description='Projeto Mega-Sena - Algoritmo Preditivo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                    # Executa análise completa com dados sintéticos
  python main.py --csv dados.csv    # Usa arquivo CSV com histórico real
  python main.py --analise          # Exibe apenas análise estatística
  python main.py --estrategias      # Exibe apenas comparação de estratégias
        """
    )

    parser.add_argument('--csv', type=str, help='Arquivo CSV com histórico de sorteios')
    parser.add_argument('--excel', type=str, help='Arquivo Excel com histórico de sorteios')
    parser.add_argument('--analise', action='store_true', help='Exibir apenas análise estatística')
    parser.add_argument('--estrategias', action='store_true', help='Exibir apenas estratégias')
    parser.add_argument('--scores', action='store_true', help='Exibir apenas ranking de scores')
    parser.add_argument('--sugestao', action='store_true', help='Exibir apenas sugestão final')

    args = parser.parse_args()

    # Cabeçalho
    print_header()
    print(f"    Execução iniciada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Carrega dados
    print_section("CARREGAMENTO DE DADOS")

    if args.csv:
        print(f"    Carregando dados de: {args.csv}")
        df = load_data('csv', args.csv)
    elif args.excel:
        print(f"    Carregando dados de: {args.excel}")
        df = load_data('excel', args.excel)
    else:
        print("    Gerando dados sintéticos para demonstração...")
        print("    (Use --csv ou --excel para carregar dados reais)")
        df = load_data('synthetic')

    print(f"    ✓ {len(df)} concursos carregados com sucesso!")

    # Inicializa analisador
    analyzer = MegaSenaAnalyzer(df)

    # Executa análises conforme argumentos
    if args.analise:
        exibir_analise_completa(analyzer, df)
    elif args.estrategias:
        exibir_estrategias(analyzer)
    elif args.scores:
        exibir_scores(analyzer)
    elif args.sugestao:
        exibir_sugestao_final(analyzer)
    else:
        # Execução completa
        exibir_analise_completa(analyzer, df)
        exibir_scores(analyzer)
        exibir_estrategias(analyzer)
        exibir_sugestao_final(analyzer)

    # Disclaimer final
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              ⚠️  DISCLAIMER ⚠️                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Este algoritmo é uma ferramenta de ANÁLISE ESTATÍSTICA e NÃO garante        ║
║  ganhos. A Mega-Sena é um jogo de azar onde cada sorteio é um evento         ║
║  INDEPENDENTE. A esperança matemática de qualquer loteria é NEGATIVA.        ║
║                                                                              ║
║  A análise de padrões históricos pode auxiliar na SELEÇÃO de números,        ║
║  mas NÃO aumenta a probabilidade matemática fundamental de acerto.           ║
║                                                                              ║
║                    JOGUE COM RESPONSABILIDADE.                               ║
║              NUNCA APOSTE MAIS DO QUE PODE PERDER.                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
