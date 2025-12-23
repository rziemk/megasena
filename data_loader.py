"""
Módulo de Carregamento de Dados - Mega-Sena
===========================================
Funções para download e processamento do histórico de sorteios.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import requests
from typing import Optional, List, Tuple
import warnings

warnings.filterwarnings('ignore')


class MegaSenaDataLoader:
    """
    Carregador de dados históricos da Mega-Sena.
    Suporta múltiplas fontes: CSV, Excel, API.
    """

    # URL da API da Caixa (endpoint não oficial, mas funcional)
    API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

    def __init__(self, data_path: Optional[str] = None):
        """
        Inicializa o carregador.

        Args:
            data_path: Caminho para arquivo local (CSV ou Excel)
        """
        self.data_path = data_path
        self.df = None
        self.colunas_dezenas = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Carrega dados de um arquivo CSV."""
        # Tenta detectar o separador automaticamente
        try:
            # Tenta com ponto-e-vírgula primeiro
            df = pd.read_csv(filepath, sep=';', encoding='utf-8', on_bad_lines='skip')
        except Exception:
            try:
                # Tenta com vírgula
                df = pd.read_csv(filepath, sep=',', encoding='utf-8', on_bad_lines='skip')
            except Exception:
                try:
                    # Tenta com tabulação
                    df = pd.read_csv(filepath, sep='\t', encoding='utf-8', on_bad_lines='skip')
                except Exception:
                    # Última tentativa: deixa o pandas detectar automaticamente
                    df = pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')

        return self._normalize_dataframe(df)

    def load_from_excel(self, filepath: str) -> pd.DataFrame:
        """Carrega dados de um arquivo Excel."""
        df = pd.read_excel(filepath)
        return self._normalize_dataframe(df)

    def load_from_api(self, concurso: Optional[int] = None) -> pd.DataFrame:
        """
        Carrega dados da API da Caixa.

        Args:
            concurso: Número do concurso específico. Se None, busca o último.
        """
        try:
            url = f"{self.API_URL}/{concurso}" if concurso else self.API_URL
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if concurso:
                return self._parse_api_single(data)
            return self._parse_api_response(data)

        except Exception as e:
            print(f"Erro ao acessar API: {e}")
            return None

    def generate_synthetic_data(self, n_concursos: int = 2800) -> pd.DataFrame:
        """
        Gera dados sintéticos realistas para demonstração.
        Baseado em distribuições estatísticas reais da Mega-Sena.

        Args:
            n_concursos: Número de concursos a gerar
        """
        np.random.seed(42)  # Reprodutibilidade

        # Histórico real de frequências aproximadas (baseado em dados reais)
        # Alguns números historicamente saem mais que outros
        frequencias_base = self._get_frequencias_historicas()

        dados = []
        data_inicio = datetime(1996, 3, 11)  # Data do primeiro concurso

        for i in range(1, n_concursos + 1):
            # Gera 6 números usando probabilidades ponderadas
            probs = frequencias_base / frequencias_base.sum()
            dezenas = np.random.choice(
                range(1, 61),
                size=6,
                replace=False,
                p=probs
            )
            dezenas = sorted(dezenas)

            # Calcula data aproximada (2-3 sorteios por semana)
            dias_passados = int(i * 2.5)
            data_sorteio = data_inicio + pd.Timedelta(days=dias_passados)

            dados.append({
                'Concurso': i,
                'Data': data_sorteio.strftime('%d/%m/%Y'),
                'D1': dezenas[0],
                'D2': dezenas[1],
                'D3': dezenas[2],
                'D4': dezenas[3],
                'D5': dezenas[4],
                'D6': dezenas[5],
            })

        self.df = pd.DataFrame(dados)
        return self.df

    def _get_frequencias_historicas(self) -> np.ndarray:
        """
        Retorna frequências históricas aproximadas de cada número.
        Baseado em dados reais da Mega-Sena até 2024.
        """
        # Frequências aproximadas reais (alguns números são "mais frequentes")
        frequencias = np.array([
            # 01-10
            285, 295, 280, 310, 330, 290, 275, 285, 270, 340,
            # 11-20
            300, 295, 315, 280, 270, 305, 325, 290, 275, 285,
            # 21-30
            280, 270, 335, 320, 285, 275, 295, 310, 305, 290,
            # 31-40
            295, 285, 340, 300, 315, 295, 325, 280, 275, 290,
            # 41-50
            330, 285, 305, 295, 280, 300, 275, 270, 290, 310,
            # 51-60
            340, 295, 320, 330, 285, 290, 305, 295, 310, 280
        ])
        return frequencias.astype(float)

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza o DataFrame para formato padrão."""
        # Mapeamento de possíveis nomes de colunas
        col_mapping = {
            'concurso': 'Concurso',
            'numero_concurso': 'Concurso',
            'numero': 'Concurso',
            'nº': 'Concurso',
            'num': 'Concurso',
            'data': 'Data',
            'data_sorteio': 'Data',
            'data do sorteio': 'Data',
            'bola1': 'D1', 'bola2': 'D2', 'bola3': 'D3',
            'bola4': 'D4', 'bola5': 'D5', 'bola6': 'D6',
            'bola 1': 'D1', 'bola 2': 'D2', 'bola 3': 'D3',
            'bola 4': 'D4', 'bola 5': 'D5', 'bola 6': 'D6',
            'dezena1': 'D1', 'dezena2': 'D2', 'dezena3': 'D3',
            'dezena4': 'D4', 'dezena5': 'D5', 'dezena6': 'D6',
            'dezena 1': 'D1', 'dezena 2': 'D2', 'dezena 3': 'D3',
            'dezena 4': 'D4', 'dezena 5': 'D5', 'dezena 6': 'D6',
            '1ª dezena': 'D1', '2ª dezena': 'D2', '3ª dezena': 'D3',
            '4ª dezena': 'D4', '5ª dezena': 'D5', '6ª dezena': 'D6',
        }

        # Renomeia colunas
        df.columns = [col_mapping.get(c.lower().strip(), c) for c in df.columns]

        # Se não encontrou as colunas padrão, tenta detectar automaticamente
        if 'Concurso' not in df.columns:
            # Primeira coluna numérica vira Concurso
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    df.rename(columns={col: 'Concurso'}, inplace=True)
                    break

        # Procura colunas de dezenas (colunas com números de 1-60)
        dezena_cols = []
        for col in df.columns:
            if col not in ['Concurso', 'Data']:
                try:
                    # Verifica se a coluna tem números na faixa 1-60
                    valores = pd.to_numeric(df[col], errors='coerce')
                    if valores.min() >= 1 and valores.max() <= 60:
                        dezena_cols.append(col)
                except:
                    continue

        # Renomeia as primeiras 6 colunas de dezenas
        for i, col in enumerate(dezena_cols[:6]):
            df.rename(columns={col: f'D{i+1}'}, inplace=True)

        # Garante que dezenas são inteiros
        for col in self.colunas_dezenas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Remove linhas com valores inválidos
        df = df[df['D1'] > 0].copy()

        self.df = df
        return df

    def _parse_api_single(self, data: dict) -> pd.DataFrame:
        """Parseia resposta de concurso único da API."""
        dezenas = sorted([int(d) for d in data.get('listaDezenas', [])])

        return pd.DataFrame([{
            'Concurso': data.get('numero'),
            'Data': data.get('dataApuracao'),
            'D1': dezenas[0] if len(dezenas) > 0 else None,
            'D2': dezenas[1] if len(dezenas) > 1 else None,
            'D3': dezenas[2] if len(dezenas) > 2 else None,
            'D4': dezenas[3] if len(dezenas) > 3 else None,
            'D5': dezenas[4] if len(dezenas) > 4 else None,
            'D6': dezenas[5] if len(dezenas) > 5 else None,
        }])

    def _parse_api_response(self, data: dict) -> pd.DataFrame:
        """Parseia resposta completa da API."""
        # A API retorna apenas o último concurso por padrão
        return self._parse_api_single(data)

    def get_all_dezenas(self) -> List[Tuple[int, ...]]:
        """Retorna lista de tuplas com todas as dezenas sorteadas."""
        if self.df is None:
            raise ValueError("Dados não carregados. Execute load_* primeiro.")

        return [
            tuple(row[self.colunas_dezenas].values)
            for _, row in self.df.iterrows()
        ]

    def get_ultimo_n_sorteios(self, n: int) -> pd.DataFrame:
        """Retorna os últimos N sorteios."""
        if self.df is None:
            raise ValueError("Dados não carregados.")
        return self.df.tail(n).copy()

    def save_to_csv(self, filepath: str):
        """Salva dados em CSV."""
        if self.df is not None:
            self.df.to_csv(filepath, index=False, sep=';')
            print(f"Dados salvos em: {filepath}")

    def get_summary(self) -> dict:
        """Retorna sumário estatístico dos dados."""
        if self.df is None:
            return {}

        todas_dezenas = []
        for col in self.colunas_dezenas:
            todas_dezenas.extend(self.df[col].tolist())

        from collections import Counter
        freq = Counter(todas_dezenas)

        return {
            'total_concursos': len(self.df),
            'primeiro_concurso': self.df['Concurso'].min(),
            'ultimo_concurso': self.df['Concurso'].max(),
            'numero_mais_frequente': freq.most_common(1)[0],
            'numero_menos_frequente': freq.most_common()[-1],
            'media_soma_dezenas': self.df[self.colunas_dezenas].sum(axis=1).mean(),
        }


def load_data(source: str = 'synthetic', filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Função de conveniência para carregar dados.

    Args:
        source: 'synthetic', 'csv', 'excel', ou 'api'
        filepath: Caminho do arquivo (para csv/excel)

    Returns:
        DataFrame com histórico de sorteios
    """
    loader = MegaSenaDataLoader()

    if source == 'synthetic':
        return loader.generate_synthetic_data()
    elif source == 'csv' and filepath:
        return loader.load_from_csv(filepath)
    elif source == 'excel' and filepath:
        return loader.load_from_excel(filepath)
    elif source == 'api':
        return loader.load_from_api()
    else:
        print("Gerando dados sintéticos por padrão...")
        return loader.generate_synthetic_data()


if __name__ == "__main__":
    # Teste do módulo
    loader = MegaSenaDataLoader()
    df = loader.generate_synthetic_data(2800)
    print(f"\nDados gerados: {len(df)} concursos")
    print(f"\nPrimeiros 5 sorteios:\n{df.head()}")
    print(f"\nÚltimos 5 sorteios:\n{df.tail()}")
    print(f"\nSumário: {loader.get_summary()}")
