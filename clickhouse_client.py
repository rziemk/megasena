"""
Cliente ClickHouse para o Projeto Mega-Sena
==========================================
Módulo para conexão e consultas ao banco de dados ClickHouse (local ou cloud).
"""

import subprocess
import pandas as pd
from io import StringIO
import os
from pathlib import Path


def load_dev_vars():
    """Carrega variáveis do arquivo dev.vars"""
    dev_vars_path = Path(__file__).parent / 'dev.vars'
    config = {}

    if dev_vars_path.exists():
        with open(dev_vars_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    return config


def load_clickhouse_config():
    """Carrega configuracao local e permite override por variaveis de ambiente."""
    config = load_dev_vars()
    env_keys = [
        'CLICKHOUSE_HOST',
        'CLICKHOUSE_PORT',
        'CLICKHOUSE_USER',
        'CLICKHOUSE_PASSWORD',
        'CLICKHOUSE_DATABASE',
        'CLICKHOUSE_SECURE',
    ]

    for key in env_keys:
        value = os.environ.get(key)
        if value is not None:
            config[key] = value

    return config


class ClickHouseClient:
    """Cliente para consultas ao ClickHouse (local ou cloud)."""

    def __init__(self, host=None, database='loterias'):
        # Carregar configurações do ambiente, com dev.vars como fallback local
        config = load_clickhouse_config()

        # Configurações cloud ou local
        self.host = host or config.get('CLICKHOUSE_HOST', 'localhost')
        self.port = config.get('CLICKHOUSE_PORT', '9000')
        self.user = config.get('CLICKHOUSE_USER', 'default')
        self.password = config.get('CLICKHOUSE_PASSWORD', '')
        self.database = config.get('CLICKHOUSE_DATABASE', database)
        self.secure = config.get('CLICKHOUSE_SECURE', 'false').lower() == 'true'

        # Determinar se é cloud ou local
        self.is_cloud = '.clickhouse.cloud' in self.host or self.secure

        if self.is_cloud:
            # Usar clickhouse-client via HTTPS para cloud
            self.client_path = 'clickhouse-client'
        else:
            # Usar path local
            self.client_path = '/opt/homebrew/bin/clickhouse'

    def query(self, sql: str, format: str = 'TabSeparatedWithNames') -> pd.DataFrame:
        """
        Executa uma query e retorna um DataFrame.

        Args:
            sql: Query SQL a executar
            format: Formato de saída (TabSeparatedWithNames para parsing fácil)

        Returns:
            DataFrame com os resultados
        """
        if self.is_cloud:
            # Conexão cloud via HTTPS usando curl
            # Remover https:// do host se existir
            host_clean = self.host.replace('https://', '').replace('http://', '')
            url = f"https://{host_clean}:{self.port}/"

            # Adicionar formato à query
            query_with_format = f"{sql.rstrip(';')} FORMAT {format}"

            cmd = [
                'curl',
                '-s',  # Silent mode
                '--fail-with-body',  # Return error on HTTP errors
                '--user', f"{self.user}:{self.password}",
                '--data-binary', query_with_format,
                url
            ]
        else:
            # Conexão local
            cmd = [
                self.client_path, 'client',
                '--host', self.host,
                '--database', self.database,
                '--query', sql,
                '--format', format
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"ClickHouse error: {result.stderr if result.stderr else result.stdout}")

        if not result.stdout.strip():
            return pd.DataFrame()

        return pd.read_csv(StringIO(result.stdout), sep='\t')

    def get_scores(self) -> pd.DataFrame:
        """Retorna os scores de todos os números."""
        df = self.query("SELECT * FROM loterias.v_scores ORDER BY score_final DESC")

        # Garantir conversão correta de tipos para todos os scores
        numeric_cols = [col for col in df.columns if 'score' in col or col == 'numero']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def get_top_numbers(self, n: int = 20) -> pd.DataFrame:
        """Retorna os top N números por score."""
        return self.query(f"""
            SELECT numero, round(score_final, 2) as score
            FROM loterias.v_scores
            ORDER BY score_final DESC
            LIMIT {n}
        """)

    def get_sorteios(self, limit: int = None) -> pd.DataFrame:
        """Retorna os sorteios históricos."""
        sql = "SELECT * FROM loterias.megasena ORDER BY concurso DESC"
        if limit:
            sql += f" LIMIT {limit}"
        return self.query(sql)

    def get_ultimo_concurso(self) -> int:
        """Retorna o número do último concurso."""
        df = self.query("SELECT max(concurso) as ultimo FROM loterias.megasena")
        return int(df['ultimo'].iloc[0])

    def get_total_concursos(self) -> int:
        """Retorna o total de concursos."""
        df = self.query("SELECT count() as total FROM loterias.megasena")
        return int(df['total'].iloc[0])

    def get_frequencia(self) -> pd.DataFrame:
        """Retorna frequência de cada número."""
        return self.query("SELECT * FROM loterias.v_frequencia ORDER BY numero")

    def get_atraso(self) -> pd.DataFrame:
        """Retorna atraso de cada número."""
        return self.query("SELECT * FROM loterias.v_atraso ORDER BY atraso DESC")

    def get_tendencia(self) -> pd.DataFrame:
        """Retorna tendência recente."""
        return self.query("SELECT * FROM loterias.v_tendencia ORDER BY aparicoes_ultimos_48 DESC")

    def get_ciclo(self) -> pd.DataFrame:
        """Retorna números faltantes no ciclo."""
        return self.query("SELECT * FROM loterias.v_ciclo ORDER BY faltante_no_ciclo DESC, concursos_sem_sair DESC")

    def get_detailed_scores(self) -> pd.DataFrame:
        """Retorna scores detalhados com todas as 15 regras."""
        df = self.query("""
            SELECT
                numero,
                round(coalesce(score_frequencia, 0), 1) as freq,
                round(coalesce(score_atraso, 0), 1) as atraso,
                round(coalesce(score_tendencia, 0), 1) as tend,
                round(coalesce(score_quadrante, 0), 1) as quad,
                round(coalesce(score_paridade, 0), 1) as parid,
                round(coalesce(score_bma, 0), 1) as bma,
                round(coalesce(score_linhas, 0), 1) as linhas,
                round(coalesce(score_colunas, 0), 1) as cols,
                round(coalesce(score_soma, 0), 1) as soma,
                round(coalesce(score_ciclo, 0), 1) as ciclo,
                round(coalesce(score_poisson, 0), 1) as poisson,
                round(coalesce(score_hnf, 0), 1) as hnf,
                round(coalesce(score_sequencia, 0), 1) as seq,
                round(coalesce(score_freq_quadrante, 0), 1) as freq_quad,
                round(coalesce(score_pressao_ciclo, 0), 1) as pressao,
                round(coalesce(score_final, 0), 2) as score_final
            FROM loterias.v_scores
            ORDER BY score_final DESC
        """)

        # Garantir conversão correta de tipos
        numeric_cols = ['numero', 'freq', 'atraso', 'tend', 'quad', 'parid', 'bma', 'linhas',
                       'cols', 'soma', 'ciclo', 'poisson', 'hnf', 'seq', 'freq_quad',
                       'pressao', 'score_final']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def get_numeros_faltantes_ciclo(self) -> list:
        """Retorna lista de números que não saíram nos últimos 27 concursos."""
        df = self.query("""
            SELECT numero FROM loterias.v_ciclo
            WHERE faltante_no_ciclo = 1
            ORDER BY concursos_sem_sair DESC
        """)
        return df['numero'].tolist() if not df.empty else []

    def get_sequencia_stats(self) -> dict:
        """Retorna estatísticas de sequências consecutivas nos sorteios."""
        df = self.query("SELECT * FROM loterias.v_sequencia_stats")
        if df.empty:
            return {}
        return df.iloc[0].to_dict()

    def get_stats_paridade(self) -> pd.DataFrame:
        """Retorna estatísticas de paridade por padrão."""
        return self.query("SELECT * FROM loterias.v_stats_paridade")

    def get_stats_quadrantes(self) -> pd.DataFrame:
        """Retorna estatísticas de quadrantes por padrão."""
        return self.query("SELECT * FROM loterias.v_stats_quadrantes")

    def get_stats_bma(self) -> pd.DataFrame:
        """Retorna estatísticas de B/M/A por padrão."""
        return self.query("SELECT * FROM loterias.v_stats_bma")

    def get_stats_soma(self) -> pd.DataFrame:
        """Retorna estatísticas de soma."""
        return self.query("SELECT * FROM loterias.v_stats_soma")

    def get_stats_linhas(self) -> pd.DataFrame:
        """Retorna estatísticas de linhas por padrão."""
        return self.query("SELECT * FROM loterias.v_stats_linhas")

    def get_stats_colunas(self) -> pd.DataFrame:
        """Retorna estatísticas de colunas (terminações) por padrão."""
        return self.query("SELECT * FROM loterias.v_stats_colunas")

    def get_stats_sequencias(self) -> pd.DataFrame:
        """Retorna estatísticas de sequências por padrão."""
        return self.query("SELECT * FROM loterias.v_stats_sequencias")

    def get_stats_terminacoes(self) -> pd.DataFrame:
        """Retorna estatísticas de cada terminação (0-9) nos sorteios."""
        return self.query("SELECT * FROM loterias.v_stats_terminacoes")

    def get_stats_freq_quadrante(self) -> pd.DataFrame:
        """Retorna estatísticas de frequência por quadrante."""
        return self.query("SELECT * FROM loterias.v_stats_freq_quadrante")

    def get_concurso_analise(self, limit: int = 10) -> pd.DataFrame:
        """Retorna análise detalhada dos últimos concursos."""
        return self.query(f"SELECT * FROM loterias.v_concurso_analise ORDER BY concurso DESC LIMIT {limit}")

    def get_ciclos_stats(self) -> pd.DataFrame:
        """Retorna estatísticas dos ciclos completos."""
        return self.query("SELECT * FROM loterias.v_ciclos_stats")

    def get_numeros_faltantes_ciclo_completo(self) -> list:
        """Retorna números faltantes para completar o ciclo atual (todos 60 números)."""
        df = self.query("SELECT numero FROM loterias.v_pressao_ciclo ORDER BY score_pressao_ciclo DESC")
        return df['numero'].tolist() if not df.empty else []

    def get_score_individual(self) -> pd.DataFrame:
        """Retorna scores baseados apenas nas regras individuais (número)."""
        df = self.query("""
            SELECT
                numero,
                r1_freq,
                r2_atraso,
                r3_tend,
                r10_ciclo,
                r11_poisson,
                r15_pressao,
                pct_r1,
                pct_r2,
                pct_r3,
                pct_r10,
                pct_r11,
                pct_r15,
                score_individual
            FROM loterias.v_score_individual
            ORDER BY score_individual DESC
        """)

        # Garantir conversão correta de tipos
        numeric_cols = ['numero', 'r1_freq', 'r2_atraso', 'r3_tend', 'r10_ciclo', 'r11_poisson',
                       'r15_pressao', 'pct_r1', 'pct_r2', 'pct_r3', 'pct_r10',
                       'pct_r11', 'pct_r15', 'score_individual']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def get_regras(self, tipo: str = None) -> pd.DataFrame:
        """Retorna as regras cadastradas."""
        sql = "SELECT * FROM loterias.regras WHERE ativo = 1"
        if tipo:
            sql += f" AND tipo = '{tipo}'"
        sql += " ORDER BY ordem"
        return self.query(sql)

    def get_regra_detalhada(self, codigo: str) -> dict:
        """Retorna uma regra com descrição detalhada formatada."""
        df = self.query(f"SELECT * FROM loterias.regras WHERE codigo = '{codigo}'")
        if df.empty:
            return None
        regra = df.iloc[0].to_dict()
        # Formatar quebras de linha
        regra['descricao_detalhada'] = regra['descricao_detalhada'].replace('\\n', '\n')
        return regra

    def insert_dataframe(self, table: str, df: pd.DataFrame) -> None:
        """
        Insere um DataFrame em uma tabela do ClickHouse.

        Args:
            table: Nome da tabela (ex: 'loterias.regras')
            df: DataFrame com os dados a inserir
        """
        import tempfile
        import csv

        # Criar arquivo CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False, quoting=csv.QUOTE_ALL)
            csv_path = f.name

        try:
            # Ler conteúdo do CSV
            with open(csv_path, 'r') as f:
                csv_content = f.read()

            # Query de inserção
            columns = ', '.join(df.columns)
            insert_sql = f"INSERT INTO {table} ({columns}) FORMAT CSVWithNames"

            if self.is_cloud:
                host_clean = self.host.replace('https://', '').replace('http://', '')
                url = f"https://{host_clean}:{self.port}/"

                cmd = [
                    'curl',
                    '-s',
                    '--fail-with-body',
                    '--user', f"{self.user}:{self.password}",
                    '-H', 'Content-Type: text/csv',
                    '--data-binary', f"{insert_sql}\n{csv_content}",
                    url
                ]
            else:
                cmd = [
                    self.client_path, 'client',
                    '--host', self.host,
                    '--database', self.database,
                    '--query', insert_sql,
                    '--format', 'CSVWithNames'
                ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"ClickHouse insert error: {result.stderr if result.stderr else result.stdout}")
        finally:
            # Limpar arquivo temporário
            import os
            os.unlink(csv_path)


# Instância global para uso no app
ch_client = ClickHouseClient()


def get_data_from_clickhouse():
    """
    Função de compatibilidade para carregar dados do ClickHouse.
    Retorna um DataFrame similar ao que era carregado do Excel.
    """
    client = ClickHouseClient()
    df = client.get_sorteios()

    # Renomear colunas para compatibilidade
    df.columns = ['Concurso', 'Data', 'bola 1', 'bola 2', 'bola 3', 'bola 4', 'bola 5', 'bola 6']

    return df
