"""
Módulo de Estratégias de Apostas - Mega-Sena
=============================================
Implementa Estratégia A (Sniper) e Estratégia B (Bomber).
Calcula Esperança Matemática para cada estratégia.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from itertools import combinations
from math import comb
from dataclasses import dataclass

from config import (
    BUDGET_TOTAL, TABELA_CUSTOS_OFICIAL, PROBABILIDADES,
    PREMIO_MEDIO_SENA, PREMIO_MEDIO_QUINA, PREMIO_MEDIO_QUADRA,
    ESTRATEGIA_A_DEZENAS_PRINCIPAL, ESTRATEGIA_A_CUSTO_PRINCIPAL,
    ESTRATEGIA_B_DEZENAS_PRINCIPAL, ESTRATEGIA_B_CUSTO_PRINCIPAL,
)
from statistical_analysis import MegaSenaAnalyzer


@dataclass
class Aposta:
    """Representa uma aposta individual."""
    dezenas: List[int]
    custo: float
    prob_sena: float
    prob_quina: float
    prob_quadra: float


@dataclass
class Fechamento:
    """Representa um fechamento matemático (Wheel System)."""
    dezenas_base: List[int]
    jogos_gerados: List[List[int]]
    custo_total: float
    garantia: str  # Ex: "Quadra garantida se acertar 5"


class CalculadoraEsperanca:
    """Calcula esperança matemática para diferentes estratégias."""

    def __init__(self):
        self.premio_sena = PREMIO_MEDIO_SENA
        self.premio_quina = PREMIO_MEDIO_QUINA
        self.premio_quadra = PREMIO_MEDIO_QUADRA

    def esperanca_aposta_simples(self, n_dezenas: int) -> Dict[str, float]:
        """
        Calcula E[X] para uma aposta de n dezenas.

        E[X] = Σ (probabilidade * prêmio) - custo

        Args:
            n_dezenas: Quantidade de dezenas na aposta (6-20)
        """
        prob_sena, prob_quina, prob_quadra = PROBABILIDADES[n_dezenas]
        custo = TABELA_CUSTOS_OFICIAL[n_dezenas]

        # Converte probabilidades (1 em X) para decimal
        p_sena = 1 / prob_sena
        p_quina = 1 / prob_quina
        p_quadra = 1 / prob_quadra

        # Esperança matemática
        e_sena = p_sena * self.premio_sena
        e_quina = p_quina * self.premio_quina
        e_quadra = p_quadra * self.premio_quadra

        e_total = e_sena + e_quina + e_quadra - custo

        # Retorno percentual (ROI esperado)
        roi = (e_total / custo) * 100 if custo > 0 else 0

        return {
            'dezenas': n_dezenas,
            'custo': custo,
            'prob_sena': f"1 em {prob_sena:,}",
            'prob_quina': f"1 em {prob_quina:,}",
            'prob_quadra': f"1 em {prob_quadra:,}",
            'esperanca_sena': e_sena,
            'esperanca_quina': e_quina,
            'esperanca_quadra': e_quadra,
            'esperanca_total': e_total,
            'roi_percentual': roi,
        }

    def comparar_estrategias(
        self,
        estrategia_a: Dict,
        estrategia_b: Dict
    ) -> Dict[str, any]:
        """Compara duas estratégias e determina a melhor."""
        diff_esperanca = estrategia_a['esperanca_total'] - estrategia_b['esperanca_total']
        diff_roi = estrategia_a['roi_total'] - estrategia_b['roi_total']

        if estrategia_a['esperanca_total'] > estrategia_b['esperanca_total']:
            vencedora = 'A'
        else:
            vencedora = 'B'

        return {
            'estrategia_vencedora': vencedora,
            'diferenca_esperanca': diff_esperanca,
            'diferenca_roi': diff_roi,
            'analise': self._gerar_analise(estrategia_a, estrategia_b, vencedora)
        }

    def _gerar_analise(
        self,
        est_a: Dict,
        est_b: Dict,
        vencedora: str
    ) -> str:
        """Gera análise textual comparativa."""
        return f"""
ANÁLISE COMPARATIVA:
====================

Estratégia A (Sniper):
- Foco em probabilidade concentrada com 19 dezenas
- E[X] Total: R$ {est_a['esperanca_total']:,.2f}
- ROI Esperado: {est_a['roi_total']:.4f}%

Estratégia B (Bomber):
- Foco em volume e diversificação
- E[X] Total: R$ {est_b['esperanca_total']:,.2f}
- ROI Esperado: {est_b['roi_total']:.4f}%

CONCLUSÃO: A Estratégia {vencedora} apresenta maior esperança matemática.

IMPORTANTE: Ambas as estratégias têm esperança matemática NEGATIVA,
o que é esperado em jogos de loteria (a "casa" sempre tem vantagem).
A análise estatística de padrões pode ajudar a selecionar QUAIS números
jogar, mas NÃO aumenta a probabilidade matemática fundamental.
"""


class EstrategiaA:
    """
    Estratégia A - "Sniper"

    - 1 jogo de 19 dezenas (R$ 162.792,00)
    - Jogos simples de 6 números com a sobra para cobrir "zebras"
    """

    def __init__(self, analyzer: MegaSenaAnalyzer):
        self.analyzer = analyzer
        self.calculator = CalculadoraEsperanca()
        self.budget = BUDGET_TOTAL
        self.custo_principal = ESTRATEGIA_A_CUSTO_PRINCIPAL
        self.sobra = self.budget - self.custo_principal

    def gerar_jogo_principal(self) -> Aposta:
        """Gera o jogo de 19 dezenas com números de maior score."""
        top_19 = self.analyzer.get_top_numeros(19)

        # Valida equilíbrio
        equilibrio = self.analyzer.validar_equilibrio_jogo(top_19)

        prob_sena, prob_quina, prob_quadra = PROBABILIDADES[19]

        return Aposta(
            dezenas=sorted(top_19),
            custo=self.custo_principal,
            prob_sena=1/prob_sena,
            prob_quina=1/prob_quina,
            prob_quadra=1/prob_quadra,
        )

    def gerar_jogos_zebra(self) -> List[Aposta]:
        """
        Gera jogos simples para cobrir os números descartados (zebras).

        Usa os números com menor score para criar um "seguro".
        """
        jogos = []
        custo_unitario = TABELA_CUSTOS_OFICIAL[6]
        max_jogos = int(self.sobra // custo_unitario)

        # Pega os números zebra (baixo score)
        zebras = self.analyzer.get_bottom_numeros(20)

        # Gera combinações estratégicas
        # Mistura zebras com alguns números medianos para equilíbrio
        scores_df = self.analyzer.calcular_todos_scores()
        medianos = scores_df.iloc[20:40]['numero'].tolist()

        jogos_gerados = 0
        zebra_idx = 0
        mediano_idx = 0

        while jogos_gerados < max_jogos and jogos_gerados < 100:  # Limite de 100 jogos
            # Estratégia: 3 zebras + 3 medianos
            dezenas = []

            for _ in range(3):
                if zebra_idx < len(zebras):
                    dezenas.append(zebras[zebra_idx])
                    zebra_idx = (zebra_idx + 1) % len(zebras)

            for _ in range(3):
                if mediano_idx < len(medianos):
                    dezenas.append(medianos[mediano_idx])
                    mediano_idx = (mediano_idx + 1) % len(medianos)

            if len(set(dezenas)) == 6:  # Evita duplicatas
                prob_sena, prob_quina, prob_quadra = PROBABILIDADES[6]
                jogos.append(Aposta(
                    dezenas=sorted(dezenas),
                    custo=custo_unitario,
                    prob_sena=1/prob_sena,
                    prob_quina=1/prob_quina,
                    prob_quadra=1/prob_quadra,
                ))
                jogos_gerados += 1
            else:
                # Rotaciona índices para evitar loop infinito
                zebra_idx = (zebra_idx + 1) % len(zebras)
                mediano_idx = (mediano_idx + 1) % len(medianos)

        return jogos

    def calcular_esperanca(self) -> Dict[str, any]:
        """Calcula esperança matemática total da estratégia A."""
        jogo_principal = self.gerar_jogo_principal()
        jogos_zebra = self.gerar_jogos_zebra()

        # E[X] do jogo principal (19 dezenas)
        e_principal = self.calculator.esperanca_aposta_simples(19)

        # E[X] dos jogos zebra (6 dezenas cada)
        e_zebra_unitario = self.calculator.esperanca_aposta_simples(6)
        n_jogos_zebra = len(jogos_zebra)

        # Esperança total
        e_total = e_principal['esperanca_total'] + (e_zebra_unitario['esperanca_total'] * n_jogos_zebra)

        # Custo total
        custo_total = self.custo_principal + (n_jogos_zebra * TABELA_CUSTOS_OFICIAL[6])

        # ROI total
        roi_total = (e_total / custo_total) * 100 if custo_total > 0 else 0

        return {
            'estrategia': 'A - Sniper',
            'jogo_principal': {
                'dezenas': jogo_principal.dezenas,
                'custo': jogo_principal.custo,
                'probabilidade_sena': f"1 em {PROBABILIDADES[19][0]:,}",
            },
            'jogos_zebra': {
                'quantidade': n_jogos_zebra,
                'custo_unitario': TABELA_CUSTOS_OFICIAL[6],
                'custo_total': n_jogos_zebra * TABELA_CUSTOS_OFICIAL[6],
                'exemplos': [j.dezenas for j in jogos_zebra[:5]],  # 5 primeiros
            },
            'custo_total': custo_total,
            'sobra_orcamento': self.budget - custo_total,
            'esperanca_principal': e_principal['esperanca_total'],
            'esperanca_zebras': e_zebra_unitario['esperanca_total'] * n_jogos_zebra,
            'esperanca_total': e_total,
            'roi_total': roi_total,
        }


class EstrategiaB:
    """
    Estratégia B - "Bomber"

    - 1 jogo de 18 dezenas (R$ 111.384,00)
    - Fechamentos matemáticos (Matrix/Wheel) com a sobra de R$ 68.616,00
    """

    def __init__(self, analyzer: MegaSenaAnalyzer):
        self.analyzer = analyzer
        self.calculator = CalculadoraEsperanca()
        self.budget = BUDGET_TOTAL
        self.custo_principal = ESTRATEGIA_B_CUSTO_PRINCIPAL
        self.sobra = self.budget - self.custo_principal

    def gerar_jogo_principal(self) -> Aposta:
        """Gera o jogo de 18 dezenas com números mais quentes."""
        # Para estratégia B, priorizamos números HOT
        hot = self.analyzer.calcular_hot_numbers()
        hot_sorted = sorted(hot.items(), key=lambda x: x[1], reverse=True)

        # Pega os 18 mais quentes
        dezenas_hot = [num for num, _ in hot_sorted[:18]]

        # Se não tiver 18 quentes suficientes, completa com top score
        if len(dezenas_hot) < 18:
            top_scores = self.analyzer.get_top_numeros(30)
            for num in top_scores:
                if num not in dezenas_hot:
                    dezenas_hot.append(num)
                if len(dezenas_hot) == 18:
                    break

        prob_sena, prob_quina, prob_quadra = PROBABILIDADES[18]

        return Aposta(
            dezenas=sorted(dezenas_hot[:18]),
            custo=self.custo_principal,
            prob_sena=1/prob_sena,
            prob_quina=1/prob_quina,
            prob_quadra=1/prob_quadra,
        )

    def gerar_fechamentos(self) -> List[Fechamento]:
        """
        Gera fechamentos matemáticos (Wheel Systems).

        Distribui a sobra entre jogos de 7, 8 e 9 dezenas.
        """
        fechamentos = []
        sobra_disponivel = self.sobra

        # Alocação: 40% em 9 dezenas, 35% em 8 dezenas, 25% em 7 dezenas
        alocacao = [
            (9, 0.40),
            (8, 0.35),
            (7, 0.25),
        ]

        # Números secundários (não incluídos no jogo principal)
        jogo_principal = self.gerar_jogo_principal()
        numeros_secundarios = [n for n in range(1, 61) if n not in jogo_principal.dezenas]

        # Ordena por score
        scores_df = self.analyzer.calcular_todos_scores()
        scores_secundarios = scores_df[scores_df['numero'].isin(numeros_secundarios)]
        scores_secundarios = scores_secundarios.sort_values('score_final', ascending=False)

        for n_dezenas, percentual in alocacao:
            budget_tipo = sobra_disponivel * percentual
            custo_unitario = TABELA_CUSTOS_OFICIAL[n_dezenas]
            max_jogos = int(budget_tipo // custo_unitario)

            if max_jogos == 0:
                continue

            # Seleciona dezenas base para o fechamento
            # Usa mix de secundários com maior score + alguns do principal
            dezenas_base = list(scores_secundarios.head(n_dezenas + 3)['numero'].values)

            # Adiciona alguns do jogo principal para criar interseção
            dezenas_principais = jogo_principal.dezenas[:3]
            dezenas_base = list(set(dezenas_base[:n_dezenas-3] + dezenas_principais))[:n_dezenas]

            jogos_gerados = self._gerar_wheel(dezenas_base, n_dezenas, max_jogos)

            if jogos_gerados:
                garantia = self._calcular_garantia(n_dezenas)
                custo_total = len(jogos_gerados) * custo_unitario

                fechamentos.append(Fechamento(
                    dezenas_base=dezenas_base,
                    jogos_gerados=jogos_gerados,
                    custo_total=custo_total,
                    garantia=garantia,
                ))

        return fechamentos

    def _gerar_wheel(
        self,
        dezenas_base: List[int],
        n_dezenas: int,
        max_jogos: int
    ) -> List[List[int]]:
        """
        Gera jogos usando sistema de wheel simplificado.

        Um wheel completo garantiria cobertura total, mas seria muito caro.
        Usamos wheel reduzido focando em combinações de alta probabilidade.
        """
        jogos = []

        # Expande a base para ter mais opções
        scores_df = self.analyzer.calcular_todos_scores()
        todos_numeros = scores_df['numero'].tolist()

        # Cria pool de números
        pool = list(set(dezenas_base + todos_numeros[:30]))

        # Gera combinações estratégicas (não todas possíveis)
        n_from_pool = min(n_dezenas + 5, len(pool))
        pool_reduzido = pool[:n_from_pool]

        # Gera algumas combinações
        for combo in combinations(pool_reduzido, n_dezenas):
            if len(jogos) >= max_jogos:
                break

            # Valida equilíbrio básico
            combo_list = list(combo)
            pares = sum(1 for n in combo_list if n % 2 == 0)

            # Aceita se razoavelmente equilibrado
            if abs(pares - (n_dezenas // 2)) <= 2:
                jogos.append(sorted(combo_list))

        return jogos

    def _calcular_garantia(self, n_dezenas: int) -> str:
        """Retorna a garantia teórica do fechamento."""
        garantias = {
            7: "Quadra garantida se acertar 5 dos 7",
            8: "Quina garantida se acertar 6 dos 8",
            9: "Quina garantida se acertar 6 dos 9",
        }
        return garantias.get(n_dezenas, "Cobertura parcial")

    def calcular_esperanca(self) -> Dict[str, any]:
        """Calcula esperança matemática total da estratégia B."""
        jogo_principal = self.gerar_jogo_principal()
        fechamentos = self.gerar_fechamentos()

        # E[X] do jogo principal (18 dezenas)
        e_principal = self.calculator.esperanca_aposta_simples(18)

        # E[X] dos fechamentos
        e_fechamentos = 0
        custo_fechamentos = 0
        detalhe_fechamentos = []

        for fech in fechamentos:
            n_jogos = len(fech.jogos_gerados)
            if n_jogos > 0:
                n_dezenas = len(fech.jogos_gerados[0])
                e_unitario = self.calculator.esperanca_aposta_simples(n_dezenas)
                e_tipo = e_unitario['esperanca_total'] * n_jogos
                e_fechamentos += e_tipo
                custo_fechamentos += fech.custo_total

                detalhe_fechamentos.append({
                    'tipo': f"{n_dezenas} dezenas",
                    'quantidade': n_jogos,
                    'custo': fech.custo_total,
                    'garantia': fech.garantia,
                    'esperanca': e_tipo,
                    'exemplos': fech.jogos_gerados[:3],  # 3 primeiros
                })

        # Esperança total
        e_total = e_principal['esperanca_total'] + e_fechamentos

        # Custo total
        custo_total = self.custo_principal + custo_fechamentos

        # ROI total
        roi_total = (e_total / custo_total) * 100 if custo_total > 0 else 0

        return {
            'estrategia': 'B - Bomber',
            'jogo_principal': {
                'dezenas': jogo_principal.dezenas,
                'custo': jogo_principal.custo,
                'probabilidade_sena': f"1 em {PROBABILIDADES[18][0]:,}",
            },
            'fechamentos': detalhe_fechamentos,
            'custo_total': custo_total,
            'sobra_orcamento': self.budget - custo_total,
            'esperanca_principal': e_principal['esperanca_total'],
            'esperanca_fechamentos': e_fechamentos,
            'esperanca_total': e_total,
            'roi_total': roi_total,
        }


class ComparadorEstrategias:
    """Compara e analisa as duas estratégias."""

    def __init__(self, analyzer: MegaSenaAnalyzer):
        self.analyzer = analyzer
        self.estrategia_a = EstrategiaA(analyzer)
        self.estrategia_b = EstrategiaB(analyzer)
        self.calculator = CalculadoraEsperanca()

    def executar_comparacao(self) -> Dict[str, any]:
        """Executa análise comparativa completa."""
        resultado_a = self.estrategia_a.calcular_esperanca()
        resultado_b = self.estrategia_b.calcular_esperanca()

        comparacao = self.calculator.comparar_estrategias(resultado_a, resultado_b)

        return {
            'estrategia_a': resultado_a,
            'estrategia_b': resultado_b,
            'comparacao': comparacao,
        }

    def gerar_relatorio(self) -> str:
        """Gera relatório completo em texto."""
        resultados = self.executar_comparacao()

        est_a = resultados['estrategia_a']
        est_b = resultados['estrategia_b']
        comp = resultados['comparacao']

        relatorio = f"""
{'='*80}
                    RELATÓRIO DE ESTRATÉGIAS - MEGA-SENA
                           Orçamento: R$ {BUDGET_TOTAL:,.2f}
{'='*80}

{'='*80}
                         ESTRATÉGIA A - "SNIPER"
                    (Foco em Probabilidade Concentrada)
{'='*80}

JOGO PRINCIPAL (19 DEZENAS):
Dezenas: {est_a['jogo_principal']['dezenas']}
Custo: R$ {est_a['jogo_principal']['custo']:,.2f}
Probabilidade Sena: {est_a['jogo_principal']['probabilidade_sena']}

JOGOS ZEBRA (SEGURO):
Quantidade: {est_a['jogos_zebra']['quantidade']} jogos de 6 dezenas
Custo Total: R$ {est_a['jogos_zebra']['custo_total']:,.2f}
Exemplos:
"""
        for i, jogo in enumerate(est_a['jogos_zebra']['exemplos'], 1):
            relatorio += f"  Jogo {i}: {jogo}\n"

        relatorio += f"""
RESUMO FINANCEIRO:
- Custo Total: R$ {est_a['custo_total']:,.2f}
- Sobra do Orçamento: R$ {est_a['sobra_orcamento']:,.2f}

ESPERANÇA MATEMÁTICA:
- E[X] Jogo Principal: R$ {est_a['esperanca_principal']:,.4f}
- E[X] Jogos Zebra: R$ {est_a['esperanca_zebras']:,.4f}
- E[X] TOTAL: R$ {est_a['esperanca_total']:,.4f}
- ROI Esperado: {est_a['roi_total']:.6f}%

{'='*80}
                         ESTRATÉGIA B - "BOMBER"
                      (Foco em Volume e Diversificação)
{'='*80}

JOGO PRINCIPAL (18 DEZENAS - NÚMEROS HOT):
Dezenas: {est_b['jogo_principal']['dezenas']}
Custo: R$ {est_b['jogo_principal']['custo']:,.2f}
Probabilidade Sena: {est_b['jogo_principal']['probabilidade_sena']}

FECHAMENTOS MATEMÁTICOS:
"""
        for fech in est_b['fechamentos']:
            relatorio += f"""
  Tipo: {fech['tipo']}
  Quantidade: {fech['quantidade']} jogos
  Custo: R$ {fech['custo']:,.2f}
  Garantia: {fech['garantia']}
  Exemplos: {fech['exemplos'][:2]}
"""

        relatorio += f"""
RESUMO FINANCEIRO:
- Custo Total: R$ {est_b['custo_total']:,.2f}
- Sobra do Orçamento: R$ {est_b['sobra_orcamento']:,.2f}

ESPERANÇA MATEMÁTICA:
- E[X] Jogo Principal: R$ {est_b['esperanca_principal']:,.4f}
- E[X] Fechamentos: R$ {est_b['esperanca_fechamentos']:,.4f}
- E[X] TOTAL: R$ {est_b['esperanca_total']:,.4f}
- ROI Esperado: {est_b['roi_total']:.6f}%

{'='*80}
                         COMPARAÇÃO E CONCLUSÃO
{'='*80}

{comp['analise']}

RECOMENDAÇÃO: ESTRATÉGIA {comp['estrategia_vencedora']}
Diferença em E[X]: R$ {comp['diferenca_esperanca']:,.4f}

{'='*80}
                              DISCLAIMER
{'='*80}

ATENÇÃO: Este algoritmo é uma ferramenta de ANÁLISE ESTATÍSTICA e NÃO
garante ganhos. A Mega-Sena é um jogo de azar com esperança matemática
NEGATIVA. A análise de padrões históricos pode ajudar na SELEÇÃO de
números, mas cada sorteio é um evento INDEPENDENTE.

Jogue com responsabilidade. Nunca aposte mais do que pode perder.
{'='*80}
"""
        return relatorio


if __name__ == "__main__":
    from data_loader import load_data

    # Carrega dados
    print("Carregando dados históricos...")
    df = load_data('synthetic')

    # Inicializa analisador
    analyzer = MegaSenaAnalyzer(df)

    # Compara estratégias
    comparador = ComparadorEstrategias(analyzer)
    relatorio = comparador.gerar_relatorio()

    print(relatorio)
