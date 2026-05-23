"""
Importador de Concursos da Mega-Sena
====================================
Busca concursos faltantes na API da Caixa e insere em loterias.megasena.
Idempotente: detecta o último concurso no DB e baixa só o que falta.
"""

import subprocess
import time
import requests
from datetime import datetime
from clickhouse_client import ClickHouseClient


API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
HEADERS = {"User-Agent": "Mozilla/5.0"}
REQUEST_SLEEP = 0.35  # segundos entre requests pra não estressar a Caixa


def fetch_concurso(numero=None, retries=3):
    """Busca um concurso (ou o último, se numero=None). Retorna dict ou None."""
    url = f"{API_URL}/{numero}" if numero else API_URL
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries - 1:
                print(f"   ❌ Falha definitiva no concurso {numero}: {e}")
                return None
            time.sleep(1.5 * (attempt + 1))


def parse_concurso(data):
    """Converte payload da API → tupla (concurso, data_iso, b1..b6) ou None."""
    if not data or not data.get("listaDezenas"):
        return None
    numero = int(data["numero"])
    dezenas = sorted(int(d) for d in data["listaDezenas"])
    if len(dezenas) != 6:
        return None
    # dataApuracao vem "DD/MM/YYYY"
    data_iso = datetime.strptime(data["dataApuracao"], "%d/%m/%Y").strftime("%Y-%m-%d")
    return (numero, data_iso, *dezenas)


def bulk_insert(client, rows):
    """INSERT em batch via curl + CSV (mesmo padrão do auto_update_data.py)."""
    if not rows:
        return
    csv_data = "\n".join(",".join(str(v) for v in r) for r in rows) + "\n"
    host_clean = client.host.replace("https://", "").replace("http://", "")
    url = f"https://{host_clean}:{client.port}/"
    insert_query = "INSERT INTO loterias.megasena FORMAT CSV"
    cmd = [
        "curl", "-s", "--fail-with-body",
        "--user", f"{client.user}:{client.password}",
        "--data-binary", f"{insert_query}\n{csv_data}",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"INSERT falhou: {result.stderr or result.stdout}")


def importar_faltantes(atualizar_ciclos=True):
    """
    Retorna dict com resumo:
      {
        "importados": int,
        "ultimo_db_antes": int,
        "ultimo_concurso": int | None,
        "ultima_data": str | None,  # ISO yyyy-mm-dd
        "falhas": list[int],
        "erro": str | None,
      }
    """
    resumo = {
        "importados": 0,
        "ultimo_db_antes": 0,
        "ultimo_concurso": None,
        "ultima_data": None,
        "falhas": [],
        "erro": None,
    }
    client = ClickHouseClient()

    df = client.query("SELECT max(concurso) AS ultimo FROM loterias.megasena")
    ultimo_db = int(df["ultimo"].iloc[0]) if not df.empty and df["ultimo"].iloc[0] is not None else 0
    resumo["ultimo_db_antes"] = ultimo_db

    print(f"📦 Último concurso no DB: {ultimo_db}")
    print("🌐 Consultando Caixa pelo último concurso disponível...")

    latest = fetch_concurso()
    if not latest:
        msg = "Não consegui falar com a API da Caixa."
        print(f"❌ {msg}")
        resumo["erro"] = msg
        return resumo
    ultimo_api = int(latest["numero"])
    print(f"   Último na Caixa: {ultimo_api} ({latest.get('dataApuracao')})")

    if ultimo_api <= ultimo_db:
        print("✓ Já está atualizado, nada a fazer.")
        resumo["ultimo_concurso"] = ultimo_db
        return resumo

    faltantes = list(range(ultimo_db + 1, ultimo_api + 1))
    print(f"⬇️  Baixando {len(faltantes)} concursos ({faltantes[0]} → {faltantes[-1]})...")

    rows = []
    falhas = []
    for i, n in enumerate(faltantes, 1):
        # Reusa o payload já baixado pro último, evita uma chamada redundante
        data = latest if n == ultimo_api else fetch_concurso(n)
        parsed = parse_concurso(data)
        if parsed is None:
            falhas.append(n)
            print(f"   ⚠️  Concurso {n}: payload inválido ou ausente, pulando")
            continue
        rows.append(parsed)
        if i % 10 == 0 or i == len(faltantes):
            print(f"   ... {i}/{len(faltantes)}")
        if n != ultimo_api:
            time.sleep(REQUEST_SLEEP)

    resumo["falhas"] = falhas

    if not rows:
        print("❌ Nenhum concurso válido baixado.")
        resumo["erro"] = "Nenhum concurso válido baixado."
        return resumo

    print(f"💾 Inserindo {len(rows)} concursos em loterias.megasena...")
    bulk_insert(client, rows)
    print("   ✅ Insert concluído")

    if falhas:
        print(f"⚠️  {len(falhas)} concursos falharam: {falhas}")

    # rows é uma lista de tuplas (concurso, data_iso, b1..b6) já em ordem crescente
    ultimo = rows[-1]
    resumo["importados"] = len(rows)
    resumo["ultimo_concurso"] = ultimo[0]
    resumo["ultima_data"] = ultimo[1]

    if atualizar_ciclos:
        print("\n🔄 Atualizando ciclos_completos...")
        from auto_update_data import verificar_e_atualizar
        verificar_e_atualizar()

    return resumo


if __name__ == "__main__":
    r = importar_faltantes()
    print(f"\n✅ Concluído. {r['importados']} concursos importados.")
