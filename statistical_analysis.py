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
    VOLANTE_LINHAS, VOLANTE_COLUNAS,
    JANELA_HOT, JANELA_COLD, CICLO_RENOVACAO,
    PESO_FREQUENCIA, PESO_ATRASO, PESO_TENDENCIA,
    PESO_QUADRANTE, PESO_PARIDADE, PESO_ALTO_BAIXO, PESO_POISSON
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
    # CÁLCULO DO SCORE FINAL (0-100)
    # =========================================================================

    def calcular_score_numero(self, num: int) -> Dict[str, float]:
        """
        Calcula score composto (0-100) para um número específico.

        Combina múltiplos fatores com pesos configuráveis.
        """
        # 1. Score de Frequência (normalizado)
        freq = self.calcular_frequencias()
        freq_min = min(freq.values())
        freq_max = max(freq.values())
        score_freq = ((freq[num] - freq_min) / (freq_max - freq_min)) * 100 if freq_max > freq_min else 50

        # 2. Score de Atraso (números atrasados ganham pontos)
        atrasos = self.calcular_cold_numbers()
        atraso_max = max(atrasos.values())
        atraso_min = min(atrasos.values())
        score_atraso = ((atrasos[num] - atraso_min) / (atraso_max - atraso_min)) * 100 if atraso_max > atraso_min else 50

        # 3. Score de Tendência
        tendencia = self.calcular_tendencia(num)
        # Normaliza tendência para 0-100
        score_tendencia = 50 + (tendencia * 500)  # Ajuste empírico
        score_tendencia = max(0, min(100, score_tendencia))

        # 4. Score de Quadrante (baseado em equilíbrio)
        quadrantes = self.analisar_quadrantes()
        for q, data in quadrantes.items():
            if num in data['numeros']:
                desvio = abs(data['media_aparicoes'] - data['distribuicao_ideal'])
                score_quadrante = 100 - (desvio * 30)  # Penaliza desvios
                break
        score_quadrante = max(0, min(100, score_quadrante))

        # 5. Score de Paridade (números que contribuem para equilíbrio)
        paridade = self.analisar_paridade()
        # 3P-3I é o mais comum/equilibrado
        if num % 2 == 0:
            score_paridade = 50 + (paridade.get('3P-3I', 0) - 30)
        else:
            score_paridade = 50 + (paridade.get('3P-3I', 0) - 30)
        score_paridade = max(0, min(100, score_paridade))

        # 6. Score Alto/Baixo
        alto_baixo = self.analisar_alto_baixo()
        if num <= LIMITE_ALTO_BAIXO:
            score_alto_baixo = 50 + (alto_baixo.get('3B-3A', 0) - 30)
        else:
            score_alto_baixo = 50 + (alto_baixo.get('3B-3A', 0) - 30)
        score_alto_baixo = max(0, min(100, score_alto_baixo))

        # 7. Score Poisson
        prob_poisson = self.calcular_probabilidade_poisson(num)
        score_poisson = prob_poisson * 100

        # Score Final Ponderado
        score_final = (
            PESO_FREQUENCIA * score_freq +
            PESO_ATRASO * score_atraso +
            PESO_TENDENCIA * score_tendencia +
            PESO_QUADRANTE * score_quadrante +
            PESO_PARIDADE * score_paridade +
            PESO_ALTO_BAIXO * score_alto_baixo +
            PESO_POISSON * score_poisson
        )

        return {
            'numero': num,
            'score_final': round(score_final, 2),
            'score_frequencia': round(score_freq, 2),
            'score_atraso': round(score_atraso, 2),
            'score_tendencia': round(score_tendencia, 2),
            'score_quadrante': round(score_quadrante, 2),
            'score_paridade': round(score_paridade, 2),
            'score_alto_baixo': round(score_alto_baixo, 2),
            'score_poisson': round(score_poisson, 2),
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
        todos_concursos = []
        numeros_vistos = set()
        inicio_ciclo = 0
        ciclos = []
        aparicoes_por_ciclo = []

        for idx, row in self.df.iterrows():
            dezenas = row[self.colunas_dezenas].values
            numeros_vistos.update(dezenas)

            # Se viu todos os 60 números
            if len(numeros_vistos) == 60:
                tamanho_ciclo = idx - inicio_ciclo + 1
                ciclos.append(tamanho_ciclo)

                # Conta aparições de cada número neste ciclo
                ciclo_df = self.df.iloc[inicio_ciclo:idx+1]
                freq_ciclo = Counter()
                for _, r in ciclo_df.iterrows():
                    freq_ciclo.update(r[self.colunas_dezenas].values)

                aparicoes_por_ciclo.append(dict(freq_ciclo))

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
            'media_aparicoes_por_numero_no_ciclo': media_aparicoes,
            'numeros_mais_frequentes_no_ciclo': sorted(
                media_aparicoes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
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


