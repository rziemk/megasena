"""
Script para criar análise de ciclos completos no ClickHouse
Um ciclo completa quando todos os 60 números saíram pelo menos 1 vez
"""

from clickhouse_client import ClickHouseClient
import pandas as pd

client = ClickHouseClient()

print("🔄 CRIANDO ANÁLISE DE CICLOS COMPLETOS")
print("=" * 80)

# 1. Calcular os ciclos
print("\n1️⃣ Calculando ciclos...")
df = client.query("""
    SELECT concurso, numero
    FROM loterias.resultados
    ORDER BY concurso, numero
""")

ciclos = []
numeros_no_ciclo = set()
inicio_ciclo = 1

for idx, row in df.iterrows():
    concurso = row['concurso']
    numero = row['numero']

    numeros_no_ciclo.add(numero)

    if len(numeros_no_ciclo) == 60:
        ciclos.append({
            'ciclo': len(ciclos) + 1,
            'concurso_inicio': inicio_ciclo,
            'concurso_fim': concurso,
            'duracao_concursos': concurso - inicio_ciclo + 1,
            'ultimo_numero_completar': numero,
            'completo': 1
        })

        inicio_ciclo = concurso + 1
        numeros_no_ciclo = set()

# Ciclo incompleto atual
if len(numeros_no_ciclo) > 0:
    ciclos.append({
        'ciclo': len(ciclos) + 1,
        'concurso_inicio': inicio_ciclo,
        'concurso_fim': df['concurso'].max(),
        'duracao_concursos': df['concurso'].max() - inicio_ciclo + 1,
        'ultimo_numero_completar': 0,  # ainda não completou
        'completo': 0
    })

ciclos_df = pd.DataFrame(ciclos)
print(f"   ✅ {len(ciclos_df)} ciclos identificados ({len(ciclos_df[ciclos_df['completo']==1])} completos)")

# 2. Criar tabela no ClickHouse
print("\n2️⃣ Criando tabela...")
client.query("""
    CREATE TABLE IF NOT EXISTS loterias.ciclos_completos (
        ciclo UInt16,
        concurso_inicio UInt16,
        concurso_fim UInt16,
        duracao_concursos UInt16,
        ultimo_numero_completar UInt8,
        completo UInt8
    ) ENGINE = MergeTree()
    ORDER BY ciclo
""")
print("   ✅ Tabela criada")

# 3. Limpar dados antigos
print("\n3️⃣ Limpando dados antigos...")
client.query("TRUNCATE TABLE loterias.ciclos_completos")
print("   ✅ Tabela limpa")

# 4. Inserir dados via CSV
print("\n4️⃣ Inserindo dados...")
import subprocess
from io import StringIO

# Converter para CSV
csv_data = ciclos_df.to_csv(index=False, header=False)

# Inserir usando curl
host_clean = client.host.replace('https://', '').replace('http://', '')
url = f"https://{host_clean}:{client.port}/"

insert_query = "INSERT INTO loterias.ciclos_completos FORMAT CSV"

cmd = [
    'curl',
    '-s',
    '--fail-with-body',
    '--user', f"{client.user}:{client.password}",
    '--data-binary', f"{insert_query}\n{csv_data}",
    url
]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"   ❌ Erro: {result.stderr if result.stderr else result.stdout}")
else:
    print(f"   ✅ {len(ciclos_df)} registros inseridos")

# 5. Criar view de estatísticas
print("\n5️⃣ Criando view de estatísticas...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_ciclos_stats AS
    SELECT
        count() as total_ciclos,
        countIf(completo = 1) as ciclos_completos,
        countIf(completo = 0) as ciclos_em_andamento,
        round(avgIf(duracao_concursos, completo = 1), 1) as duracao_media,
        minIf(duracao_concursos, completo = 1) as duracao_minima,
        maxIf(duracao_concursos, completo = 1) as duracao_maxima
    FROM loterias.ciclos_completos
""")
print("   ✅ View v_ciclos_stats criada")

# 6. Criar view para identificar o ciclo de cada concurso
print("\n6️⃣ Criando view de mapeamento concurso -> ciclo...")
client.query("""
    CREATE OR REPLACE VIEW loterias.v_concurso_ciclo AS
    SELECT
        m.concurso,
        c.ciclo,
        c.concurso_inicio,
        c.concurso_fim,
        m.concurso - c.concurso_inicio + 1 as posicao_no_ciclo,
        c.duracao_concursos,
        c.completo
    FROM loterias.megasena m
    LEFT JOIN loterias.ciclos_completos c
        ON m.concurso >= c.concurso_inicio
        AND m.concurso <= c.concurso_fim
    ORDER BY m.concurso
""")
print("   ✅ View v_concurso_ciclo criada")

# 7. Verificar
print("\n7️⃣ Verificando...")
stats = client.query("SELECT * FROM loterias.v_ciclos_stats")
print("\n📊 ESTATÍSTICAS:")
print(stats.to_string(index=False))

print("\n📋 PRIMEIROS 5 CICLOS:")
primeiros = client.query("SELECT * FROM loterias.ciclos_completos ORDER BY ciclo LIMIT 5")
print(primeiros.to_string(index=False))

print("\n📋 ÚLTIMOS 3 CICLOS:")
ultimos = client.query("SELECT * FROM loterias.ciclos_completos ORDER BY ciclo DESC LIMIT 3")
print(ultimos.to_string(index=False))

print("\n✅ ANÁLISE DE CICLOS CRIADA COM SUCESSO!")
