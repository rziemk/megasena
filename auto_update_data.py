"""
Script de Auto-Atualização de Dados
====================================
Verifica se há novos concursos e recalcula a tabela ciclos_completos
"""

from clickhouse_client import ClickHouseClient
import pandas as pd
import subprocess


def verificar_e_atualizar():
    """
    Verifica se há novos concursos e atualiza a tabela ciclos_completos se necessário.

    Returns:
        bool: True se houve atualização, False caso contrário
    """
    client = ClickHouseClient()

    # 1. Pegar último concurso da tabela megasena
    ultimo_megasena = client.query("SELECT max(concurso) as ultimo FROM loterias.megasena")
    if ultimo_megasena.empty:
        return False
    ultimo_concurso_megasena = int(ultimo_megasena['ultimo'].iloc[0])

    # 2. Pegar último concurso da tabela ciclos_completos (pode não existir ainda)
    try:
        ultimo_ciclos = client.query("SELECT max(concurso_fim) as ultimo FROM loterias.ciclos_completos")
        ultimo_concurso_ciclos = int(ultimo_ciclos['ultimo'].iloc[0]) if not ultimo_ciclos.empty and ultimo_ciclos['ultimo'].iloc[0] is not None else 0
    except:
        ultimo_concurso_ciclos = 0

    # 3. Se não há novos concursos, retornar False
    if ultimo_concurso_megasena <= ultimo_concurso_ciclos:
        return False

    # 4. Há novos concursos! Recalcular toda a tabela ciclos_completos
    print(f"🔄 Novos concursos detectados! Megasena: {ultimo_concurso_megasena}, Ciclos: {ultimo_concurso_ciclos}")
    print("📊 Recalculando tabela ciclos_completos...")

    # Buscar todos os sorteios
    sorteios = client.query("""
        SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6
        FROM loterias.megasena
        ORDER BY concurso
    """)

    # Calcular ciclos completos
    ciclos = []
    numeros_no_ciclo = set()
    inicio_ciclo = sorteios['concurso'].iloc[0]

    for _, row in sorteios.iterrows():
        concurso = int(row['concurso'])
        bolas = [int(row[f'bola{i}']) for i in range(1, 7)]

        for bola in bolas:
            numeros_no_ciclo.add(bola)

        # Se completou o ciclo (60 números)
        if len(numeros_no_ciclo) == 60:
            ciclos.append({
                'concurso_inicio': inicio_ciclo,
                'concurso_fim': concurso,
                'duracao': concurso - inicio_ciclo + 1,
                'completo': 1
            })

            # Resetar para próximo ciclo
            numeros_no_ciclo = set()
            inicio_ciclo = concurso + 1

    # Adicionar ciclo em andamento (se houver)
    if len(numeros_no_ciclo) > 0:
        ciclos.append({
            'concurso_inicio': inicio_ciclo,
            'concurso_fim': sorteios['concurso'].iloc[-1],
            'duracao': sorteios['concurso'].iloc[-1] - inicio_ciclo + 1,
            'completo': 0
        })

    ciclos_df = pd.DataFrame(ciclos)

    # TRUNCAR e inserir novos dados
    client.query("TRUNCATE TABLE loterias.ciclos_completos")

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
        print(f"❌ Erro ao atualizar ciclos: {result.stderr if result.stderr else result.stdout}")
        return False

    print(f"✅ Tabela ciclos_completos atualizada com {len(ciclos_df)} registros!")
    return True


if __name__ == "__main__":
    atualizado = verificar_e_atualizar()
    if atualizado:
        print("\n✅ Dados atualizados com sucesso!")
    else:
        print("\n✓ Dados já estão atualizados!")
