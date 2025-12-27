"""
Módulo de Análise Estatística - Mega-Sena
=========================================
Implementa todas as análises estatísticas e cálculo de scores.
"""

import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
from scipy import stats
from scipy.stats import poisson
import warnings

warnings.filterwarnings('ignore')

from config import (
    TOTAL_NUMEROS, NUMEROS_SORTEADOS, LIMITE_ALTO_BAIXO,
    LIMITE_BAIXO, LIMITE_MEDIO,
    VOLANTE_LINHAS, VOLANTE_COLUNAS,
    JANELA_HOT, JANELA_COLD, CICLO_RENOVACAO,
    PESO_FREQUENCIA, PESO_ATRASO, PESO_TENDENCIA,
    PESO_QUADRANTE, PESO_PARIDADE, PESO_BAIXO_MEDIO_ALTO,
    PESO_LINHAS, PESO_COLUNAS, PESO_SOMA, PESO_CICLO, PESO_POISSON,
    PESO_FREQUENCIA_HNF, PESO_SEQUENCIA,
    SOMA_IDEAL_MIN, SOMA_IDEAL_MAX, SOMA_IDEAL_MEDIA
)


class MegaSenaAnalyzer:
    """
    Analisador estatístico completo para Mega-Sena.
    Implementa múltiplas técnicas de análise de padrões.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa o analisador.

        Args:
            df: DataFrame com histórico de sorteios
        """
        self.df = df.copy()
        self.colunas_dezenas = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
        self.numeros = list(range(1, TOTAL_NUMEROS + 1))

        # Cache de análises
        self._frequencias = None
        self._atrasos = None
        self._scores = None

        # Mapeamento do volante 6x10
        self.volante = self._criar_volante()

    def _criar_volante(self) -> Dict[int, Tuple[int, int]]:
        """
        Cria mapeamento do volante da Mega-Sena (6 linhas x 10 colunas).

        Returns:
            Dict mapeando número para (linha, coluna)
        """
        volante = {}
        for num in range(1, 61):
            linha = (num - 1) // 10 + 1  # 1-6
            coluna = (num - 1) % 10 + 1   # 1-10
            volante[num] = (linha, coluna)
        return volante

    # =========================================================================
    # ANÁLISE DE FREQUÊNCIA
    # =========================================================================

    def calcular_frequencias(self) -> Dict[int, int]:
        """Calcula frequência absoluta de cada número no histórico completo."""
        if self._frequencias is not None:
            return self._frequencias

        todas_dezenas = []
        for col in self.colunas_dezenas:
            todas_dezenas.extend(self.df[col].tolist())

        self._frequencias = Counter(todas_dezenas)

        # Garante que todos os números de 1-60 estão presentes
        for num in self.numeros:
            if num not in self._frequencias:
                self._frequencias[num] = 0

        return self._frequencias

    def calcular_frequencias_relativas(self) -> Dict[int, float]:
        """Calcula frequência relativa (percentual) de cada número."""
        freq = self.calcular_frequencias()
        total = sum(freq.values())
        return {num: count / total * 100 for num, count in freq.items()}

    # =========================================================================
    # ANÁLISE DE TEMPERATURAS (HOT/COLD)
    # =========================================================================

    def calcular_hot_numbers(self, janela: int = JANELA_HOT) -> Dict[int, int]:
        """
        Identifica números "quentes" (alta frequência recente).

        Args:
            janela: Últimos N concursos para análise
        """
        ultimos = self.df.tail(janela)
        dezenas_recentes = []
        for col in self.colunas_dezenas:
            dezenas_recentes.extend(ultimos[col].tolist())

        return Counter(dezenas_recentes)

    def calcular_cold_numbers(self) -> Dict[int, int]:
        """
        Calcula o atraso de cada número (concursos desde última aparição).

        Returns:
            Dict com número -> atraso em concursos
        """
        if self._atrasos is not None:
            return self._atrasos

        atrasos = {}
        ultimo_concurso = len(self.df)

        for num in self.numeros:
            ultima_aparicao = 0
            for idx, row in self.df.iterrows():
                dezenas = [row[col] for col in self.colunas_dezenas]
                if num in dezenas:
                    ultima_aparicao = row['Concurso']

            atrasos[num] = ultimo_concurso - ultima_aparicao

        self._atrasos = atrasos
        return atrasos

    def get_numeros_atrasados(self, limite_atraso: int = 15) -> List[int]:
        """
        Retorna números com atraso maior que o limite.
        Estes são candidatos à "regressão à média".
        """
        atrasos = self.calcular_cold_numbers()
        return [num for num, atraso in atrasos.items() if atraso >= limite_atraso]

    # =========================================================================
    # ANÁLISE DE QUADRANTES E LINHAS
    # =========================================================================

    def analisar_quadrantes(self) -> Dict[str, Dict]:
        """
        Analisa distribuição por quadrantes do volante.

        Quadrantes:
        - Q1: Linhas 1-3, Colunas 1-5 (Superior Esquerdo)
        - Q2: Linhas 1-3, Colunas 6-10 (Superior Direito)
        - Q3: Linhas 4-6, Colunas 1-5 (Inferior Esquerdo)
        - Q4: Linhas 4-6, Colunas 6-10 (Inferior Direito)
        """
        quadrantes = {
            'Q1': [],  # 1-5, 11-15, 21-25
            'Q2': [],  # 6-10, 16-20, 26-30
            'Q3': [],  # 31-35, 41-45, 51-55
            'Q4': [],  # 36-40, 46-50, 56-60
        }

        for num in self.numeros:
            linha, coluna = self.volante[num]
            if linha <= 3 and coluna <= 5:
                quadrantes['Q1'].append(num)
            elif linha <= 3 and coluna > 5:
                quadrantes['Q2'].append(num)
            elif linha > 3 and coluna <= 5:
                quadrantes['Q3'].append(num)
            else:
                quadrantes['Q4'].append(num)

        # Analisa distribuição histórica por quadrante
        distribuicao_historica = defaultdict(list)

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            contagem = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}

            for dez in dezenas:
                for q, nums in quadrantes.items():
                    if dez in nums:
                        contagem[q] += 1
                        break

            for q, count in contagem.items():
                distribuicao_historica[q].append(count)

        # Calcula estatísticas
        resultado = {}
        for q, nums in quadrantes.items():
            resultado[q] = {
                'numeros': nums,
                'media_aparicoes': np.mean(distribuicao_historica[q]),
                'desvio_padrao': np.std(distribuicao_historica[q]),
                'distribuicao_ideal': 1.5,  # 6 números / 4 quadrantes
            }

        return resultado

    def analisar_linhas(self) -> Dict[int, Dict]:
        """Analisa distribuição por linhas do volante."""
        linhas = {i: list(range((i-1)*10 + 1, i*10 + 1)) for i in range(1, 7)}

        distribuicao_historica = defaultdict(list)

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            contagem = {i: 0 for i in range(1, 7)}

            for dez in dezenas:
                for linha, nums in linhas.items():
                    if dez in nums:
                        contagem[linha] += 1
                        break

            for linha, count in contagem.items():
                distribuicao_historica[linha].append(count)

        resultado = {}
        for linha, nums in linhas.items():
            resultado[linha] = {
                'numeros': nums,
                'media_aparicoes': np.mean(distribuicao_historica[linha]),
                'desvio_padrao': np.std(distribuicao_historica[linha]),
                'distribuicao_ideal': 1.0,  # 6 números / 6 linhas
            }

        return resultado

    # =========================================================================
    # ANÁLISE PAR/ÍMPAR E ALTO/BAIXO
    # =========================================================================

    def analisar_paridade(self) -> Dict[str, float]:
        """
        Analisa distribuição par/ímpar nos sorteios.

        Retorna padrões mais frequentes (ex: 3P-3I, 4P-2I, etc.)
        """
        padroes = []

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            pares = sum(1 for d in dezenas if d % 2 == 0)
            impares = 6 - pares
            padroes.append(f"{pares}P-{impares}I")

        contagem = Counter(padroes)
        total = len(padroes)

        return {padrao: count / total * 100 for padrao, count in contagem.most_common()}

    def analisar_alto_baixo(self) -> Dict[str, float]:
        """
        Analisa distribuição alto/baixo nos sorteios.

        Baixo: 1-30, Alto: 31-60
        """
        padroes = []

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            baixos = sum(1 for d in dezenas if d <= LIMITE_ALTO_BAIXO)
            altos = 6 - baixos
            padroes.append(f"{baixos}B-{altos}A")

        contagem = Counter(padroes)
        total = len(padroes)

        return {padrao: count / total * 100 for padrao, count in contagem.most_common()}

    def analisar_padrao_linhas_jogo(self) -> Dict[str, any]:
        """
        Analisa quantos números por linha aparecem nos jogos históricos.
        Ex: '2-1-1-1-1-0' = 2 números na L1, 1 na L2, 1 na L3, 1 na L4, 1 na L5, 0 na L6

        Identifica padrões raros (ex: 4+ números na mesma linha) que devem ser evitados.
        """
        padroes = []
        max_por_linha_historico = []

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            contagem_linhas = [0] * 6  # 6 linhas

            for d in dezenas:
                linha = (d - 1) // 10  # 0-5
                contagem_linhas[linha] += 1

            # Ordenar para criar padrão normalizado
            padrao = '-'.join(map(str, sorted(contagem_linhas, reverse=True)))
            padroes.append(padrao)
            max_por_linha_historico.append(max(contagem_linhas))

        contagem = Counter(padroes)
        total = len(padroes)

        # Estatísticas sobre máximo por linha
        max_counts = Counter(max_por_linha_historico)

        return {
            'padroes_frequentes': {p: c/total*100 for p, c in contagem.most_common(10)},
            'max_numeros_mesma_linha': {
                f'{k}_numeros': v/total*100 for k, v in sorted(max_counts.items())
            },
            'media_max_por_linha': np.mean(max_por_linha_historico),
            'evitar_4_ou_mais_mesma_linha': max_counts.get(4, 0)/total*100 + max_counts.get(5, 0)/total*100 + max_counts.get(6, 0)/total*100
        }

    def analisar_padrao_colunas_jogo(self) -> Dict[str, any]:
        """
        Analisa quantos números por coluna aparecem nos jogos históricos.
        Identifica padrões raros (ex: 3+ números na mesma coluna) que devem ser evitados.
        """
        padroes = []
        max_por_coluna_historico = []

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            contagem_colunas = [0] * 10  # 10 colunas

            for d in dezenas:
                coluna = (d - 1) % 10  # 0-9
                contagem_colunas[coluna] += 1

            # Ordenar para criar padrão normalizado
            padrao = '-'.join(map(str, sorted(contagem_colunas, reverse=True)))
            padroes.append(padrao)
            max_por_coluna_historico.append(max(contagem_colunas))

        contagem = Counter(padroes)
        total = len(padroes)

        # Estatísticas sobre máximo por coluna
        max_counts = Counter(max_por_coluna_historico)

        return {
            'padroes_frequentes': {p: c/total*100 for p, c in contagem.most_common(10)},
            'max_numeros_mesma_coluna': {
                f'{k}_numeros': v/total*100 for k, v in sorted(max_counts.items())
            },
            'media_max_por_coluna': np.mean(max_por_coluna_historico),
            'evitar_3_ou_mais_mesma_coluna': max_counts.get(3, 0)/total*100 + max_counts.get(4, 0)/total*100 + max_counts.get(5, 0)/total*100 + max_counts.get(6, 0)/total*100
        }

    def validar_distribuicao_jogo(self, dezenas: List[int]) -> Dict[str, any]:
        """
        Valida se um jogo proposto tem distribuição aceitável de linhas/colunas.

        Returns:
            Dict com validações e alertas
        """
        # Contagem por linha
        contagem_linhas = [0] * 6
        for d in dezenas:
            linha = (d - 1) // 10
            contagem_linhas[linha] += 1

        # Contagem por coluna
        contagem_colunas = [0] * 10
        for d in dezenas:
            coluna = (d - 1) % 10
            contagem_colunas[coluna] += 1

        max_linha = max(contagem_linhas)
        max_coluna = max(contagem_colunas)

        # Análise histórica para comparação
        padrao_linhas = self.analisar_padrao_linhas_jogo()
        padrao_colunas = self.analisar_padrao_colunas_jogo()

        alertas = []
        score_distribuicao = 100

        # Verificar concentração em linhas
        if max_linha >= 4:
            alertas.append(f"⚠️ {max_linha} números na mesma linha (raro: {padrao_linhas['evitar_4_ou_mais_mesma_linha']:.1f}% histórico)")
            score_distribuicao -= 30
        elif max_linha == 3:
            alertas.append(f"⚡ 3 números em uma linha (comum mas não ideal)")
            score_distribuicao -= 10

        # Verificar concentração em colunas
        if max_coluna >= 3:
            alertas.append(f"⚠️ {max_coluna} números na mesma coluna (raro: {padrao_colunas['evitar_3_ou_mais_mesma_coluna']:.1f}% histórico)")
            score_distribuicao -= 25
        elif max_coluna == 2:
            # 2 na mesma coluna é comum, ok
            pass

        # Verificar linhas vazias demais
        linhas_vazias = contagem_linhas.count(0)
        if linhas_vazias >= 3:
            alertas.append(f"⚡ {linhas_vazias} linhas vazias (pouca dispersão)")
            score_distribuicao -= 15

        return {
            'contagem_linhas': contagem_linhas,
            'contagem_colunas': contagem_colunas,
            'max_linha': max_linha,
            'max_coluna': max_coluna,
            'linhas_usadas': 6 - linhas_vazias,
            'colunas_usadas': 10 - contagem_colunas.count(0),
            'alertas': alertas,
            'score_distribuicao': max(0, score_distribuicao),
            'distribuicao_ok': len(alertas) == 0
        }

    # =========================================================================
    # LEI DOS GRANDES NÚMEROS E CICLOS
    # =========================================================================

    def calcular_ciclo_renovacao(self) -> Dict[str, float]:
        """
        Calcula a cada quantos concursos ocorre renovação total das dezenas.
        Analisa o ciclo médio de aparecimento de cada número.
        """
        ciclos = defaultdict(list)

        for num in self.numeros:
            aparicoes = []
            for idx, row in self.df.iterrows():
                dezenas = [row[col] for col in self.colunas_dezenas]
                if num in dezenas:
                    aparicoes.append(row['Concurso'])

            # Calcula intervalos entre aparições
            if len(aparicoes) > 1:
                intervalos = np.diff(aparicoes)
                ciclos[num] = {
                    'media_intervalo': np.mean(intervalos),
                    'max_intervalo': np.max(intervalos),
                    'min_intervalo': np.min(intervalos),
                    'total_aparicoes': len(aparicoes)
                }

        # Média geral
        medias = [v['media_intervalo'] for v in ciclos.values()]

        return {
            'ciclo_medio_global': np.mean(medias),
            'ciclo_esperado_teorico': TOTAL_NUMEROS / NUMEROS_SORTEADOS,  # 10
            'ciclos_por_numero': ciclos
        }

    # =========================================================================
    # ANÁLISE DE POISSON
    # =========================================================================

    def calcular_probabilidade_poisson(self, num: int, janela: int = 50) -> float:
        """
        Calcula probabilidade de um número sair usando Distribuição de Poisson.

        Lambda = taxa média de ocorrência do número por concurso
        """
        # Taxa média de aparição (lambda)
        freq = self.calcular_frequencias()
        total_concursos = len(self.df)

        # Lambda: média de aparições por concurso
        lambda_param = freq[num] / total_concursos

        # Analisando os últimos N concursos
        ultimos = self.df.tail(janela)
        aparicoes_recentes = 0
        for _, row in ultimos.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]
            if num in dezenas:
                aparicoes_recentes += 1

        # Probabilidade de aparecer pelo menos 1 vez nos próximos concursos
        # P(X >= 1) = 1 - P(X = 0)
        prob_nao_aparecer = poisson.pmf(0, lambda_param * 10)  # próximos 10 concursos
        prob_aparecer = 1 - prob_nao_aparecer

        return prob_aparecer

    # =========================================================================
    # ANÁLISE DE TENDÊNCIA
    # =========================================================================

    def calcular_tendencia(self, num: int, janelas: List[int] = [10, 20, 50]) -> float:
        """
        Calcula tendência de um número comparando frequências em diferentes janelas.

        Tendência positiva: número está aparecendo mais recentemente
        Tendência negativa: número está esfriando
        """
        tendencias = []

        for janela in janelas:
            ultimos = self.df.tail(janela)
            aparicoes = 0
            for _, row in ultimos.iterrows():
                dezenas = [row[col] for col in self.colunas_dezenas]
                if num in dezenas:
                    aparicoes += 1

            taxa_janela = aparicoes / janela
            tendencias.append(taxa_janela)

        # Tendência: diferença entre taxa recente e taxa antiga
        if len(tendencias) >= 2:
            tendencia = tendencias[0] - tendencias[-1]
        else:
            tendencia = 0

        return tendencia

    # =========================================================================
    # ANÁLISE DE FAIXAS DE FREQUÊNCIA (QUENTE/NEUTRO/FRIO) - 12ª REGRA
    # =========================================================================

    def classificar_numeros_por_frequencia(self) -> Dict[str, List[int]]:
        """
        Classifica os 60 números em 3 faixas baseado na frequência histórica:
        - Quente (Hot): Top 20 números mais frequentes
        - Neutro: 20 números do meio
        - Frio (Cold): 20 números menos frequentes

        Returns:
            Dict com listas de números em cada faixa
        """
        freq = self.calcular_frequencias()

        # Ordena por frequência (maior para menor)
        numeros_ordenados = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        # Divide em 3 faixas de 20 números cada
        quentes = [num for num, _ in numeros_ordenados[:20]]
        neutros = [num for num, _ in numeros_ordenados[20:40]]
        frios = [num for num, _ in numeros_ordenados[40:]]

        return {
            'quente': sorted(quentes),
            'neutro': sorted(neutros),
            'frio': sorted(frios),
            'ranking': {num: idx + 1 for idx, (num, _) in enumerate(numeros_ordenados)}
        }

    def get_faixa_frequencia(self, num: int) -> str:
        """
        Retorna a faixa de frequência de um número específico.

        Args:
            num: Número de 1 a 60

        Returns:
            'H' (Hot/Quente), 'N' (Neutro), ou 'F' (Frio/Cold)
        """
        classificacao = self.classificar_numeros_por_frequencia()

        if num in classificacao['quente']:
            return 'H'
        elif num in classificacao['neutro']:
            return 'N'
        else:
            return 'F'

    def analisar_padroes_hnf(self) -> Dict[str, any]:
        """
        Analisa padrões de combinação Hot-Neutro-Frio nos sorteios históricos.

        Padrões como:
        - 2H-2N-2F: 2 quentes, 2 neutros, 2 frios (equilibrado)
        - 3H-2N-1F: 3 quentes, 2 neutros, 1 frio
        - etc.

        Returns:
            Dict com estatísticas dos padrões mais comuns
        """
        classificacao = self.classificar_numeros_por_frequencia()
        quentes_set = set(classificacao['quente'])
        neutros_set = set(classificacao['neutro'])
        frios_set = set(classificacao['frio'])

        padroes = Counter()
        distribuicoes = []

        for _, row in self.df.iterrows():
            dezenas = [row[col] for col in self.colunas_dezenas]

            h = sum(1 for d in dezenas if d in quentes_set)
            n = sum(1 for d in dezenas if d in neutros_set)
            f = sum(1 for d in dezenas if d in frios_set)

            padrao = f"{h}H-{n}N-{f}F"
            padroes[padrao] += 1
            distribuicoes.append({'H': h, 'N': n, 'F': f})

        total = len(self.df)

        # Estatísticas detalhadas
        resultado = {
            'padroes_frequentes': {
                padrao: {
                    'contagem': count,
                    'percentual': round(count / total * 100, 2)
                }
                for padrao, count in padroes.most_common()
            },
            'top_5_padroes': [
                (padrao, round(count / total * 100, 2))
                for padrao, count in padroes.most_common(5)
            ],
            'media_quentes': np.mean([d['H'] for d in distribuicoes]),
            'media_neutros': np.mean([d['N'] for d in distribuicoes]),
            'media_frios': np.mean([d['F'] for d in distribuicoes]),
            'padrao_ideal': '2H-2N-2F',  # Padrão mais equilibrado
            'total_sorteios': total,
        }

        # Identifica os padrões mais comuns (que somam ~70% dos sorteios)
        acumulado = 0
        padroes_comuns = []
        for padrao, count in padroes.most_common():
            pct = count / total * 100
            acumulado += pct
            padroes_comuns.append(padrao)
            if acumulado >= 70:
                break

        resultado['padroes_recomendados'] = padroes_comuns
        resultado['cobertura_recomendados'] = round(acumulado, 2)

        return resultado

    def calcular_score_hnf(self, num: int) -> float:
        """
        Calcula o score de um número baseado nos padrões H-N-F mais comuns.

        Números que contribuem para padrões mais frequentes ganham mais pontos.

        Args:
            num: Número de 1 a 60

        Returns:
            Score de 0 a 100
        """
        faixa = self.get_faixa_frequencia(num)
        padroes = self.analisar_padroes_hnf()

        # Baseado na média histórica de cada faixa
        # Se a média de quentes é 2.0, números quentes são importantes
        # para atingir esse equilíbrio

        media_h = padroes['media_quentes']
        media_n = padroes['media_neutros']
        media_f = padroes['media_frios']

        # Score baseado em quanto cada faixa contribui para o equilíbrio
        # Padrão ideal seria 2-2-2, então avaliamos o quão próximo estamos

        if faixa == 'H':
            # Quentes: se média histórica é ~2, então são importantes
            # Score proporcional à presença histórica
            score = min(100, (media_h / 2) * 50 + 50)
        elif faixa == 'N':
            # Neutros: geralmente ~2 também
            score = min(100, (media_n / 2) * 50 + 50)
        else:  # 'F'
            # Frios: também ~2
            score = min(100, (media_f / 2) * 50 + 50)

        # Bônus para números em faixas que aparecem nos padrões mais comuns
        # Os padrões mais comuns geralmente têm distribuição próxima de 2-2-2
        top_padrao = padroes['top_5_padroes'][0] if padroes['top_5_padroes'] else ('2H-2N-2F', 20)
        padrao_str, percentual = top_padrao

        # Extrai quantos de cada faixa no padrão mais comum
        import re
        match = re.match(r'(\d+)H-(\d+)N-(\d+)F', padrao_str)
        if match:
            h_ideal = int(match.group(1))
            n_ideal = int(match.group(2))
            f_ideal = int(match.group(3))

            # Ajusta score baseado no padrão mais comum
            if faixa == 'H' and h_ideal >= 2:
                score += 10
            elif faixa == 'N' and n_ideal >= 2:
                score += 10
            elif faixa == 'F' and f_ideal >= 2:
                score += 10

        return min(100, max(0, score))

    def validar_equilibrio_hnf(self, dezenas: List[int]) -> Dict[str, any]:
        """
        Valida se um jogo tem bom equilíbrio de números Quentes/Neutros/Frios.

        Args:
            dezenas: Lista de números do jogo

        Returns:
            Dict com análise do equilíbrio H-N-F
        """
        classificacao = self.classificar_numeros_por_frequencia()
        quentes_set = set(classificacao['quente'])
        neutros_set = set(classificacao['neutro'])
        frios_set = set(classificacao['frio'])

        h = sum(1 for d in dezenas if d in quentes_set)
        n = sum(1 for d in dezenas if d in neutros_set)
        f = sum(1 for d in dezenas if d in frios_set)

        padrao = f"{h}H-{n}N-{f}F"
        padroes = self.analisar_padroes_hnf()

        # Verifica se o padrão está entre os recomendados
        recomendado = padrao in padroes['padroes_recomendados']
        percentual_historico = padroes['padroes_frequentes'].get(padrao, {}).get('percentual', 0)

        return {
            'padrao': padrao,
            'quentes': h,
            'neutros': n,
            'frios': f,
            'numeros_quentes': [d for d in dezenas if d in quentes_set],
            'numeros_neutros': [d for d in dezenas if d in neutros_set],
            'numeros_frios': [d for d in dezenas if d in frios_set],
            'padrao_recomendado': recomendado,
            'percentual_historico': percentual_historico,
            'score_equilibrio': 100 if recomendado else max(0, 50 - abs(h-2)*15 - abs(n-2)*15 - abs(f-2)*15)
        }

    # =========================================================================
    # ANÁLISE 13: SEQUÊNCIAS CONSECUTIVAS
    # =========================================================================

    def analisar_sequencias_historico(self) -> Dict[str, any]:
        """
        Analisa padrões de sequências (números consecutivos) no histórico.

        Returns:
            Dict com estatísticas de sequências
        """
        padroes_sequencia = Counter()
        total_jogos = len(self.df)

        for _, row in self.df.iterrows():
            dezenas = sorted([row['D1'], row['D2'], row['D3'], row['D4'], row['D5'], row['D6']])

            # Contar sequências no jogo
            sequencias = []
            seq_atual = [dezenas[0]]

            for i in range(1, len(dezenas)):
                if dezenas[i] == dezenas[i-1] + 1:
                    seq_atual.append(dezenas[i])
                else:
                    if len(seq_atual) >= 2:
                        sequencias.append(seq_atual)
                    seq_atual = [dezenas[i]]

            if len(seq_atual) >= 2:
                sequencias.append(seq_atual)

            # Classificar padrão
            qtd_seq = len(sequencias)
            tamanhos = [len(s) for s in sequencias]

            if qtd_seq == 0:
                padrao = "0 seq"
            elif qtd_seq == 1:
                padrao = f"1 seq ({tamanhos[0]} nums)"
            else:
                padrao = f"{qtd_seq} seqs"

            padroes_sequencia[padrao] += 1

        # Calcular percentuais
        resultado = {
            'padroes': {},
            'total_jogos': total_jogos,
            'media_sequencias': 0,
            'jogos_sem_sequencia': 0,
            'jogos_com_sequencia': 0
        }

        for padrao, count in padroes_sequencia.most_common():
            resultado['padroes'][padrao] = {
                'count': count,
                'percentual': round((count / total_jogos) * 100, 2)
            }
            if padrao == "0 seq":
                resultado['jogos_sem_sequencia'] = count
            else:
                resultado['jogos_com_sequencia'] += count

        return resultado

    def validar_sequencias_jogo(self, dezenas: List[int]) -> Dict[str, any]:
        """
        Valida as sequências em um jogo específico.

        Args:
            dezenas: Lista de números do jogo

        Returns:
            Dict com análise das sequências
        """
        dezenas_sorted = sorted(dezenas)
        sequencias = []
        seq_atual = [dezenas_sorted[0]]

        for i in range(1, len(dezenas_sorted)):
            if dezenas_sorted[i] == dezenas_sorted[i-1] + 1:
                seq_atual.append(dezenas_sorted[i])
            else:
                if len(seq_atual) >= 2:
                    sequencias.append(seq_atual)
                seq_atual = [dezenas_sorted[i]]

        if len(seq_atual) >= 2:
            sequencias.append(seq_atual)

        qtd_seq = len(sequencias)
        tamanhos = [len(s) for s in sequencias]

        if qtd_seq == 0:
            padrao = "0 seq"
        elif qtd_seq == 1:
            padrao = f"1 seq ({tamanhos[0]} nums)"
        else:
            padrao = f"{qtd_seq} seqs"

        return {
            'qtd_sequencias': qtd_seq,
            'sequencias': sequencias,
            'tamanhos': tamanhos,
            'padrao': padrao,
            'numeros_em_sequencia': [n for seq in sequencias for n in seq]
        }

    def calcular_score_sequencia(self, num: int) -> float:
        """
        Calcula score baseado em padrões de sequência.

        Números que formam sequências com vizinhos frequentes ganham pontos.
        Mas sequências muito longas são raras, então há um equilíbrio.

        Args:
            num: Número de 1 a 60

        Returns:
            Score de 0 a 100
        """
        # Analisar frequência de sequências com vizinhos
        vizinho_anterior = num - 1 if num > 1 else None
        vizinho_posterior = num + 1 if num < 60 else None

        freq = self.calcular_frequencias()

        score = 50  # Base

        # Se os vizinhos têm boa frequência, há chance de formar sequência
        if vizinho_anterior and vizinho_anterior in freq:
            freq_viz_ant = freq[vizinho_anterior]
            media_freq = sum(freq.values()) / len(freq)
            if freq_viz_ant > media_freq:
                score += 15  # Vizinho anterior é frequente

        if vizinho_posterior and vizinho_posterior in freq:
            freq_viz_pos = freq[vizinho_posterior]
            media_freq = sum(freq.values()) / len(freq)
            if freq_viz_pos > media_freq:
                score += 15  # Vizinho posterior é frequente

        # Bônus para números no "meio" do volante (mais combinações possíveis)
        if 10 <= num <= 50:
            score += 10

        # Penalizar extremos (1-5 e 56-60) que têm menos opções de sequência
        if num <= 5 or num >= 56:
            score -= 10

        return max(0, min(100, score))

    # =========================================================================
    # CÁLCULO DO SCORE FINAL (0-100)
    # =========================================================================

    def calcular_score_numero(self, num: int) -> Dict[str, float]:
        """
        Calcula score composto (0-100) para um número específico.

        Combina múltiplos fatores com pesos configuráveis (Total = 100%):
        - Frequência histórica (14%)
        - Atraso/Regressão à média (14%)
        - Tendência recente (9%)
        - Equilíbrio por quadrante (9%)
        - Paridade par/ímpar (7%)
        - Baixo/Médio/Alto - 3 faixas (7%)
        - Distribuição por linhas (7%)
        - Distribuição por colunas (7%)
        - Contribuição para Soma ideal (7%)
        - Ciclo atual - números faltantes (5%)
        - Probabilidade Poisson (5%)
        - Faixas H-N-F (Quente/Neutro/Frio) (9%) - NOVA REGRA
        """
        # 1. Score de Frequência (normalizado) - 15%
        freq = self.calcular_frequencias()
        freq_min = min(freq.values())
        freq_max = max(freq.values())
        score_freq = ((freq[num] - freq_min) / (freq_max - freq_min)) * 100 if freq_max > freq_min else 50

        # 2. Score de Atraso (números atrasados ganham pontos) - 15%
        atrasos = self.calcular_cold_numbers()
        atraso_max = max(atrasos.values())
        atraso_min = min(atrasos.values())
        score_atraso = ((atrasos[num] - atraso_min) / (atraso_max - atraso_min)) * 100 if atraso_max > atraso_min else 50

        # 3. Score de Tendência - 10%
        tendencia = self.calcular_tendencia(num)
        score_tendencia = 50 + (tendencia * 500)  # Ajuste empírico
        score_tendencia = max(0, min(100, score_tendencia))

        # 4. Score de Quadrante (baseado em equilíbrio) - 10%
        quadrantes = self.analisar_quadrantes()
        score_quadrante = 50  # Default
        for q, data in quadrantes.items():
            if num in data['numeros']:
                desvio = abs(data['media_aparicoes'] - data['distribuicao_ideal'])
                score_quadrante = 100 - (desvio * 30)
                break
        score_quadrante = max(0, min(100, score_quadrante))

        # 5. Score de Paridade (números que contribuem para equilíbrio) - 8%
        paridade = self.analisar_paridade()
        score_paridade = 50 + (paridade.get('3P-3I', 0) - 30)
        score_paridade = max(0, min(100, score_paridade))

        # 6. Score Baixo/Médio/Alto (3 faixas) - 8%
        bma = self.analisar_baixo_medio_alto()
        # Padrão mais equilibrado é 2B-2M-2A
        if 1 <= num <= LIMITE_BAIXO:
            faixa = 'baixo'
        elif LIMITE_BAIXO < num <= LIMITE_MEDIO:
            faixa = 'medio'
        else:
            faixa = 'alto'
        # Score baseado no quanto o padrão 2-2-2 é comum
        score_bma = 50 + (bma.get('2B-2M-2A', 0) - 15)
        score_bma = max(0, min(100, score_bma))

        # 7. Score de Linhas do Volante - 8%
        analise_linhas = self.analisar_linhas_volante()
        linha_num = (num - 1) // 10  # 0-5
        linha_key = f'L{linha_num + 1}'
        media_linha = analise_linhas['medias_por_linha'].get(linha_key, 1.0)
        # Linhas próximas da média ideal (1.0) ganham mais pontos
        desvio_linha = abs(media_linha - 1.0)
        score_linhas = 100 - (desvio_linha * 50)
        score_linhas = max(0, min(100, score_linhas))

        # 8. Score de Colunas do Volante - 8%
        analise_colunas = self.analisar_colunas_volante()
        coluna_num = (num - 1) % 10  # 0-9
        coluna_key = f'C{coluna_num + 1}'
        media_coluna = analise_colunas['medias_por_coluna'].get(coluna_key, 0.6)
        # Colunas próximas da média ideal (0.6) ganham mais pontos
        desvio_coluna = abs(media_coluna - 0.6)
        score_colunas = 100 - (desvio_coluna * 80)
        score_colunas = max(0, min(100, score_colunas))

        # 9. Score de Soma (contribuição para soma ideal 150-200) - 8%
        # Números que contribuem para uma soma na faixa ideal ganham mais pontos
        # Soma ideal média para 6 números = 175, cada número deveria contribuir ~29
        contribuicao_ideal = SOMA_IDEAL_MEDIA / 6  # ~29.17
        desvio_soma = abs(num - contribuicao_ideal)
        # Números próximos de 29 (contribuição ideal) ganham mais pontos
        # Números muito baixos (1-10) ou muito altos (50-60) ganham menos
        if SOMA_IDEAL_MIN / 6 <= num <= SOMA_IDEAL_MAX / 6:
            # Número está na faixa ideal de contribuição
            score_soma = 100
        else:
            # Penaliza proporcionalmente ao desvio da faixa ideal
            score_soma = max(0, 100 - (desvio_soma * 3))
        score_soma = max(0, min(100, score_soma))

        # 10. Score de Ciclo (números faltantes no ciclo atual ganham pontos) - 5%
        ciclo_atual = self.obter_ciclo_atual()
        if num in ciclo_atual['numeros_faltantes']:
            # Número está faltando no ciclo - bônus!
            # Quanto menos números faltam, maior o bônus
            qtd_faltantes = ciclo_atual['qtd_faltantes']
            if qtd_faltantes <= 10:
                score_ciclo = 100  # Muito poucos faltando, urgente!
            elif qtd_faltantes <= 20:
                score_ciclo = 80
            elif qtd_faltantes <= 30:
                score_ciclo = 60
            else:
                score_ciclo = 40
        else:
            # Número já apareceu no ciclo atual
            score_ciclo = 20
        score_ciclo = max(0, min(100, score_ciclo))

        # 11. Score Poisson - 5%
        prob_poisson = self.calcular_probabilidade_poisson(num)
        score_poisson = prob_poisson * 100

        # 12. Score H-N-F (Quente/Neutro/Frio) - 7%
        score_hnf = self.calcular_score_hnf(num)

        # 13. Score de Sequências - 6% - NOVA REGRA
        score_sequencia = self.calcular_score_sequencia(num)

        # Score Final Ponderado (13 regras)
        score_final = (
            PESO_FREQUENCIA * score_freq +
            PESO_ATRASO * score_atraso +
            PESO_TENDENCIA * score_tendencia +
            PESO_QUADRANTE * score_quadrante +
            PESO_PARIDADE * score_paridade +
            PESO_BAIXO_MEDIO_ALTO * score_bma +
            PESO_LINHAS * score_linhas +
            PESO_COLUNAS * score_colunas +
            PESO_SOMA * score_soma +
            PESO_CICLO * score_ciclo +
            PESO_POISSON * score_poisson +
            PESO_FREQUENCIA_HNF * score_hnf +
            PESO_SEQUENCIA * score_sequencia
        )

        return {
            'numero': num,
            'score_final': round(score_final, 2),
            'score_frequencia': round(score_freq, 2),
            'score_atraso': round(score_atraso, 2),
            'score_tendencia': round(score_tendencia, 2),
            'score_quadrante': round(score_quadrante, 2),
            'score_paridade': round(score_paridade, 2),
            'score_bma': round(score_bma, 2),
            'score_linhas': round(score_linhas, 2),
            'score_colunas': round(score_colunas, 2),
            'score_soma': round(score_soma, 2),
            'score_ciclo': round(score_ciclo, 2),
            'score_poisson': round(score_poisson, 2),
            'score_hnf': round(score_hnf, 2),
            'score_sequencia': round(score_sequencia, 2),
            'faixa_hnf': self.get_faixa_frequencia(num),
        }

    def calcular_todos_scores(self) -> pd.DataFrame:
        """Calcula scores para todos os 60 números."""
        if self._scores is not None:
            return self._scores

        scores = []
        for num in self.numeros:
            scores.append(self.calcular_score_numero(num))

        self._scores = pd.DataFrame(scores)
        self._scores = self._scores.sort_values('score_final', ascending=False)
        return self._scores

    def get_top_numeros(self, n: int) -> List[int]:
        """Retorna os N números com maior score."""
        scores_df = self.calcular_todos_scores()
        return scores_df.head(n)['numero'].tolist()

    def get_bottom_numeros(self, n: int) -> List[int]:
        """Retorna os N números com menor score (zebras)."""
        scores_df = self.calcular_todos_scores()
        return scores_df.tail(n)['numero'].tolist()

    # =========================================================================
    # NOVAS ANÁLISES PROFUNDAS
    # =========================================================================

    def analisar_baixo_medio_alto(self) -> Dict[str, float]:
        """
        Analisa distribuição em 3 faixas: Baixo (1-20), Médio (21-40), Alto (41-60).

        Returns:
            Dicionário com percentual de cada padrão (ex: '2B-2M-2A')
        """
        padroes = Counter()

        for _, row in self.df.iterrows():
            dezenas = row[self.colunas_dezenas].values

            baixos = sum(1 for d in dezenas if 1 <= d <= 20)
            medios = sum(1 for d in dezenas if 21 <= d <= 40)
            altos = sum(1 for d in dezenas if 41 <= d <= 60)

            padrao = f"{baixos}B-{medios}M-{altos}A"
            padroes[padrao] += 1

        total = sum(padroes.values())
        return {p: (count / total) * 100 for p, count in padroes.most_common()}

    def analisar_linhas_volante(self) -> Dict[str, any]:
        """
        Analisa distribuição por linhas do volante (6 linhas de 10 números).

        Linhas:
        - L1: 01-10
        - L2: 11-20
        - L3: 21-30
        - L4: 31-40
        - L5: 41-50
        - L6: 51-60

        Returns:
            Estatísticas detalhadas por linha
        """
        linhas = {
            'L1': (1, 10),
            'L2': (11, 20),
            'L3': (21, 30),
            'L4': (31, 40),
            'L5': (41, 50),
            'L6': (51, 60),
        }

        # Contadores por linha
        aparicoes_por_linha = {l: [] for l in linhas.keys()}
        padroes_distribuicao = Counter()

        for _, row in self.df.iterrows():
            dezenas = row[self.colunas_dezenas].values
            distribuicao = {}

            for linha, (inicio, fim) in linhas.items():
                count = sum(1 for d in dezenas if inicio <= d <= fim)
                aparicoes_por_linha[linha].append(count)
                distribuicao[linha] = count

            # Cria padrão de distribuição (ex: "L1:1-L2:2-L3:1-L4:1-L5:1-L6:0")
            padrao = "-".join([f"{l}:{distribuicao[l]}" for l in sorted(linhas.keys())])
            padroes_distribuicao[padrao] += 1

        # Estatísticas
        resultado = {
            'medias_por_linha': {
                linha: np.mean(vals) for linha, vals in aparicoes_por_linha.items()
            },
            'desvio_por_linha': {
                linha: np.std(vals) for linha, vals in aparicoes_por_linha.items()
            },
            'max_por_linha': {
                linha: max(vals) for linha, vals in aparicoes_por_linha.items()
            },
            'top_padroes': padroes_distribuicao.most_common(10),
            'total_padroes': len(padroes_distribuicao),
        }

        return resultado

    def analisar_colunas_volante(self) -> Dict[str, any]:
        """
        Analisa distribuição por colunas do volante (10 colunas de 6 números).

        Colunas:
        - C1: 01,11,21,31,41,51
        - C2: 02,12,22,32,42,52
        - ...
        - C10: 10,20,30,40,50,60

        Returns:
            Estatísticas detalhadas por coluna
        """
        # Monta as colunas
        colunas = {}
        for c in range(1, 11):
            colunas[f'C{c}'] = [c, c+10, c+20, c+30, c+40, c+50]

        # Contadores por coluna
        aparicoes_por_coluna = {c: [] for c in colunas.keys()}
        padroes_distribuicao = Counter()

        for _, row in self.df.iterrows():
            dezenas = set(row[self.colunas_dezenas].values)
            distribuicao = {}

            for coluna, nums in colunas.items():
                count = sum(1 for n in nums if n in dezenas)
                aparicoes_por_coluna[coluna].append(count)
                distribuicao[coluna] = count

            # Padrão de distribuição
            # Simplificado: quantas colunas com 0, 1, 2+ números
            zeros = sum(1 for c in distribuicao.values() if c == 0)
            uns = sum(1 for c in distribuicao.values() if c == 1)
            dois_ou_mais = sum(1 for c in distribuicao.values() if c >= 2)

            padrao = f"{zeros}C0-{uns}C1-{dois_ou_mais}C2+"
            padroes_distribuicao[padrao] += 1

        resultado = {
            'medias_por_coluna': {
                col: np.mean(vals) for col, vals in aparicoes_por_coluna.items()
            },
            'desvio_por_coluna': {
                col: np.std(vals) for col, vals in aparicoes_por_coluna.items()
            },
            'max_por_coluna': {
                col: max(vals) for col, vals in aparicoes_por_coluna.items()
            },
            'top_padroes': padroes_distribuicao.most_common(10),
            'total_padroes': len(padroes_distribuicao),
        }

        return resultado

    def analisar_ciclos_renovacao_completa(self) -> Dict[str, any]:
        """
        Analisa a cada quantos concursos TODOS os 60 números aparecem pelo menos 1 vez.
        Também analisa quantas vezes cada número aparece dentro desses ciclos.

        Returns:
            Estatísticas de ciclos de renovação completa
        """
        # IMPORTANTE: Ordenar por Concurso para garantir ordem cronológica
        df_ordenado = self.df.sort_values('Concurso').reset_index(drop=True)

        numeros_vistos = set()
        inicio_ciclo = 0
        ciclos = []
        aparicoes_por_ciclo = []
        ciclos_info = []  # Guarda info detalhada de cada ciclo

        for idx, row in df_ordenado.iterrows():
            dezenas = row[self.colunas_dezenas].values
            numeros_vistos.update(dezenas)

            # Se viu todos os 60 números
            if len(numeros_vistos) == 60:
                tamanho_ciclo = idx - inicio_ciclo + 1
                ciclos.append(tamanho_ciclo)

                # Conta aparições de cada número neste ciclo
                ciclo_df = df_ordenado.iloc[inicio_ciclo:idx+1]
                freq_ciclo = Counter()
                for _, r in ciclo_df.iterrows():
                    freq_ciclo.update(r[self.colunas_dezenas].values)

                aparicoes_por_ciclo.append(dict(freq_ciclo))

                # Info detalhada do ciclo
                concurso_inicio = df_ordenado.iloc[inicio_ciclo]['Concurso']
                concurso_fim = row['Concurso']
                ciclos_info.append({
                    'concurso_inicio': concurso_inicio,
                    'concurso_fim': concurso_fim,
                    'tamanho': tamanho_ciclo
                })

                # Reinicia
                numeros_vistos = set()
                inicio_ciclo = idx + 1

        if not ciclos:
            return {
                'ciclo_medio': 0,
                'ciclo_minimo': 0,
                'ciclo_maximo': 0,
                'total_ciclos_completos': 0,
                'media_aparicoes_por_numero_no_ciclo': {},
                'ciclos_info': [],
            }

        # Calcula médias de aparições por número
        media_aparicoes = {}
        for num in range(1, 61):
            aparicoes = [ciclo.get(num, 0) for ciclo in aparicoes_por_ciclo]
            media_aparicoes[num] = np.mean(aparicoes) if aparicoes else 0

        return {
            'ciclo_medio': np.mean(ciclos),
            'ciclo_minimo': min(ciclos),
            'ciclo_maximo': max(ciclos),
            'ciclo_desvio': np.std(ciclos),
            'total_ciclos_completos': len(ciclos),
            'ultimos_5_ciclos': ciclos[-5:] if len(ciclos) >= 5 else ciclos,
            'ciclos_info': ciclos_info[-5:] if len(ciclos_info) >= 5 else ciclos_info,
            'media_aparicoes_por_numero_no_ciclo': media_aparicoes,
            'numeros_mais_frequentes_no_ciclo': sorted(
                media_aparicoes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }

    def obter_ciclo_atual(self) -> Dict[str, any]:
        """
        Obtém informações sobre o ciclo atual em andamento.

        Percorre do PRIMEIRO concurso em diante, mapeando todos os ciclos:
        - Ciclo 1: concurso X até concurso Y (quando todos 60 números apareceram)
        - Ciclo 2: concurso Y+1 até concurso Z
        - ...
        - Ciclo Atual: concurso W até agora (em andamento, ainda não completou)

        Returns:
            Dict com info do ciclo atual em andamento
        """
        # IMPORTANTE: Ordenar por Concurso para garantir ordem cronológica
        df_ordenado = self.df.sort_values('Concurso').reset_index(drop=True)

        todos_numeros = set(range(1, 61))
        numeros_vistos = set()
        inicio_ciclo_idx = 0
        numero_ciclo = 1
        ciclos_completos = []

        # Percorre do primeiro ao último concurso mapeando os ciclos
        for idx, row in df_ordenado.iterrows():
            dezenas = row[self.colunas_dezenas].values
            numeros_vistos.update(dezenas)

            # Se completou um ciclo (viu todos os 60 números)
            if len(numeros_vistos) == 60:
                concurso_inicio = df_ordenado.iloc[inicio_ciclo_idx]['Concurso']
                concurso_fim = row['Concurso']
                tamanho = idx - inicio_ciclo_idx + 1

                ciclos_completos.append({
                    'numero_ciclo': numero_ciclo,
                    'concurso_inicio': concurso_inicio,
                    'concurso_fim': concurso_fim,
                    'tamanho': tamanho
                })

                # Reinicia para próximo ciclo
                numeros_vistos = set()
                inicio_ciclo_idx = idx + 1
                numero_ciclo += 1

        # O ciclo atual é o que está em andamento (após o último ciclo completo)
        ciclo_atual_numero = numero_ciclo
        numeros_aparecidos_ciclo_atual = set()
        concurso_inicio_ciclo_atual = None
        concursos_no_ciclo_atual = 0

        if inicio_ciclo_idx < len(df_ordenado):
            # Há um ciclo em andamento
            ciclo_atual_df = df_ordenado.iloc[inicio_ciclo_idx:]
            concurso_inicio_ciclo_atual = ciclo_atual_df.iloc[0]['Concurso']
            concursos_no_ciclo_atual = len(ciclo_atual_df)

            for _, row in ciclo_atual_df.iterrows():
                dezenas = row[self.colunas_dezenas].values
                numeros_aparecidos_ciclo_atual.update(dezenas)

        numeros_faltantes = sorted(todos_numeros - numeros_aparecidos_ciclo_atual)
        ultimo_concurso = df_ordenado.iloc[-1]['Concurso'] if len(df_ordenado) > 0 else None

        # Calcular média de concursos por ciclo para estimativa
        if ciclos_completos:
            media_concursos_por_ciclo = np.mean([c['tamanho'] for c in ciclos_completos])
        else:
            media_concursos_por_ciclo = 15  # Valor teórico aproximado

        # Estimativa de concursos restantes
        qtd_faltantes = len(numeros_faltantes)
        if qtd_faltantes > 0:
            # Proporção: se faltam X números de 60, faltam aproximadamente X/60 do ciclo
            estimativa_restante = int(media_concursos_por_ciclo * (qtd_faltantes / 60))
        else:
            estimativa_restante = 0

        return {
            'numero_ciclo': ciclo_atual_numero,
            'total_ciclos_completos': len(ciclos_completos),
            'concurso_inicio': concurso_inicio_ciclo_atual,
            'concurso_atual': ultimo_concurso,
            'concursos_no_ciclo': concursos_no_ciclo_atual,
            'numeros_aparecidos': sorted(numeros_aparecidos_ciclo_atual),
            'numeros_faltantes': numeros_faltantes,
            'qtd_aparecidos': len(numeros_aparecidos_ciclo_atual),
            'qtd_faltantes': qtd_faltantes,
            'progresso_pct': (len(numeros_aparecidos_ciclo_atual) / 60) * 100,
            'ciclo_completo': qtd_faltantes == 0,
            'media_concursos_por_ciclo': media_concursos_por_ciclo,
            'estimativa_concursos_restantes': estimativa_restante,
            'ultimos_ciclos': ciclos_completos[-5:] if ciclos_completos else [],
            'todos_ciclos': ciclos_completos,  # Lista completa de todos os ciclos
        }

    def criar_perfis_de_jogos(self) -> pd.DataFrame:
        """
        Cria perfis completos de cada jogo com todos os padrões combinados.

        Returns:
            DataFrame com perfil completo de cada concurso
        """
        perfis = []

        for idx, row in self.df.iterrows():
            dezenas = sorted(row[self.colunas_dezenas].values)

            # Padrões básicos
            pares = sum(1 for d in dezenas if d % 2 == 0)
            impares = 6 - pares

            baixos_1_20 = sum(1 for d in dezenas if 1 <= d <= 20)
            medios_21_40 = sum(1 for d in dezenas if 21 <= d <= 40)
            altos_41_60 = sum(1 for d in dezenas if 41 <= d <= 60)

            baixos_1_30 = sum(1 for d in dezenas if 1 <= d <= 30)
            altos_31_60 = 6 - baixos_1_30

            # Distribuição por linha
            linhas = [
                sum(1 for d in dezenas if 1 <= d <= 10),
                sum(1 for d in dezenas if 11 <= d <= 20),
                sum(1 for d in dezenas if 21 <= d <= 30),
                sum(1 for d in dezenas if 31 <= d <= 40),
                sum(1 for d in dezenas if 41 <= d <= 50),
                sum(1 for d in dezenas if 51 <= d <= 60),
            ]

            # Distribuição por coluna
            colunas_map = {}
            for c in range(1, 11):
                nums_coluna = [c, c+10, c+20, c+30, c+40, c+50]
                colunas_map[c] = sum(1 for n in nums_coluna if n in dezenas)

            # Sequências e gaps
            gaps = [dezenas[i+1] - dezenas[i] for i in range(5)]
            gap_medio = np.mean(gaps)
            gap_max = max(gaps)
            gap_min = min(gaps)

            sequencias = sum(1 for g in gaps if g == 1)

            # Quadrantes
            q1 = sum(1 for d in dezenas if d in [*range(1,6), *range(11,16), *range(21,26)])
            q2 = sum(1 for d in dezenas if d in [*range(6,11), *range(16,21), *range(26,31)])
            q3 = sum(1 for d in dezenas if d in [*range(31,36), *range(41,46), *range(51,56)])
            q4 = sum(1 for d in dezenas if d in [*range(36,41), *range(46,51), *range(56,61)])

            perfis.append({
                'Concurso': row.get('Concurso', idx),
                'Dezenas': ','.join(map(str, dezenas)),
                'Soma': sum(dezenas),
                'Pares': pares,
                'Impares': impares,
                'Baixos_1_20': baixos_1_20,
                'Medios_21_40': medios_21_40,
                'Altos_41_60': altos_41_60,
                'Baixos_1_30': baixos_1_30,
                'Altos_31_60': altos_31_60,
                'L1': linhas[0],
                'L2': linhas[1],
                'L3': linhas[2],
                'L4': linhas[3],
                'L5': linhas[4],
                'L6': linhas[5],
                'Linhas_Com_Numeros': sum(1 for l in linhas if l > 0),
                'Colunas_Com_2+': sum(1 for c in colunas_map.values() if c >= 2),
                'Gap_Medio': round(gap_medio, 2),
                'Gap_Maximo': gap_max,
                'Gap_Minimo': gap_min,
                'Sequencias': sequencias,
                'Q1': q1,
                'Q2': q2,
                'Q3': q3,
                'Q4': q4,
            })

        return pd.DataFrame(perfis)

    # =========================================================================
    # VALIDAÇÃO DE EQUILÍBRIO DO JOGO
    # =========================================================================

    def validar_equilibrio_jogo(self, dezenas: List[int]) -> Dict[str, any]:
        """
        Valida se um conjunto de dezenas está equilibrado.

        Args:
            dezenas: Lista de números selecionados

        Returns:
            Dict com análise de equilíbrio
        """
        n = len(dezenas)

        # Par/Ímpar
        pares = sum(1 for d in dezenas if d % 2 == 0)
        impares = n - pares

        # Alto/Baixo
        baixos = sum(1 for d in dezenas if d <= LIMITE_ALTO_BAIXO)
        altos = n - baixos

        # Linhas
        linhas_count = Counter((d - 1) // 10 + 1 for d in dezenas)

        # Quadrantes
        quadrantes_count = Counter()
        for d in dezenas:
            linha, col = self.volante[d]
            if linha <= 3 and col <= 5:
                quadrantes_count['Q1'] += 1
            elif linha <= 3:
                quadrantes_count['Q2'] += 1
            elif col <= 5:
                quadrantes_count['Q3'] += 1
            else:
                quadrantes_count['Q4'] += 1

        # Soma total
        soma = sum(dezenas)

        return {
            'dezenas': sorted(dezenas),
            'total': n,
            'pares': pares,
            'impares': impares,
            'equilibrio_paridade': abs(pares - impares) <= 2,
            'baixos': baixos,
            'altos': altos,
            'equilibrio_alto_baixo': abs(baixos - altos) <= 2,
            'distribuicao_linhas': dict(linhas_count),
            'distribuicao_quadrantes': dict(quadrantes_count),
            'soma_total': soma,
            'media': soma / n,
        }


if __name__ == "__main__":
    from data_loader import load_data

    # Carrega dados
    df = load_data('synthetic')
    print(f"Dados carregados: {len(df)} concursos\n")

    # Inicializa analisador
    analyzer = MegaSenaAnalyzer(df)

    # Exibe análises
    print("=" * 60)
    print("ANÁLISE DE FREQUÊNCIAS")
    print("=" * 60)
    freq = analyzer.calcular_frequencias()
    top_5 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"Top 5 mais frequentes: {top_5}")

    print("\n" + "=" * 60)
    print("ANÁLISE HOT/COLD")
    print("=" * 60)
    hot = analyzer.calcular_hot_numbers()
    print(f"Hot (últimos 10 jogos): {hot.most_common(10)}")

    cold = analyzer.calcular_cold_numbers()
    cold_sorted = sorted(cold.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"Cold (mais atrasados): {cold_sorted}")

    print("\n" + "=" * 60)
    print("ANÁLISE PAR/ÍMPAR")
    print("=" * 60)
    paridade = analyzer.analisar_paridade()
    for padrao, perc in list(paridade.items())[:5]:
        print(f"  {padrao}: {perc:.2f}%")

    print("\n" + "=" * 60)
    print("ANÁLISE ALTO/BAIXO")
    print("=" * 60)
    alto_baixo = analyzer.analisar_alto_baixo()
    for padrao, perc in list(alto_baixo.items())[:5]:
        print(f"  {padrao}: {perc:.2f}%")

    print("\n" + "=" * 60)
    print("SCORES DOS NÚMEROS (Top 20)")
    print("=" * 60)
    scores = analyzer.calcular_todos_scores()
    print(scores.head(20).to_string(index=False))


