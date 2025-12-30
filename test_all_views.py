"""
Script de Teste Completo - Todas as Views
==========================================
Testa todas as views e funções críticas do sistema
"""

from clickhouse_client import ClickHouseClient
import sys

client = ClickHouseClient()

print("🧪 TESTE COMPLETO DO SISTEMA")
print("=" * 80)

testes_ok = 0
testes_total = 0

def testar(nome, funcao):
    global testes_ok, testes_total
    testes_total += 1
    try:
        resultado = funcao()
        if resultado is not None and (hasattr(resultado, '__len__') and len(resultado) > 0 or isinstance(resultado, (int, float))):
            print(f"✅ {nome}")
            testes_ok += 1
            return True
        else:
            print(f"⚠️  {nome} - Vazio ou None")
            return False
    except Exception as e:
        print(f"❌ {nome} - ERRO: {str(e)[:100]}")
        return False

print("\n📊 VIEWS PRINCIPAIS:")
print("-" * 80)

# Views de regras individuais
testar("v_frequencia", lambda: client.get_frequencia())
testar("v_atraso", lambda: client.get_atraso())
testar("v_tendencia (48 concursos)", lambda: client.get_tendencia())
testar("v_ciclo (27 concursos)", lambda: client.get_ciclo())

# View consolidada
testar("v_scores (todas 15 regras)", lambda: client.get_scores())
testar("v_score_individual (6 regras)", lambda: client.get_score_individual())

# Views de estatísticas
print("\n📈 VIEWS DE ESTATÍSTICAS:")
print("-" * 80)
testar("v_stats_paridade", lambda: client.get_stats_paridade())
testar("v_stats_quadrantes", lambda: client.get_stats_quadrantes())
testar("v_stats_bma", lambda: client.get_stats_bma())
testar("v_stats_soma", lambda: client.get_stats_soma())
testar("v_stats_linhas", lambda: client.get_stats_linhas())
testar("v_stats_colunas", lambda: client.get_stats_colunas())
testar("v_stats_sequencias", lambda: client.get_stats_sequencias())
testar("v_stats_terminacoes", lambda: client.get_stats_terminacoes())
testar("v_stats_freq_quadrante", lambda: client.get_stats_freq_quadrante())

# Views de ciclos
print("\n🔄 VIEWS DE CICLOS:")
print("-" * 80)
testar("v_ciclos_stats", lambda: client.get_ciclos_stats())
testar("ciclos_completos (tabela)", lambda: client.query("SELECT * FROM loterias.ciclos_completos LIMIT 1"))

# Métodos do client
print("\n🔧 MÉTODOS DO CLIENT:")
print("-" * 80)
testar("get_detailed_scores()", lambda: client.get_detailed_scores())
testar("get_top_numbers(20)", lambda: client.get_top_numbers(20))
testar("get_sorteios(10)", lambda: client.get_sorteios(10))
testar("get_ultimo_concurso()", lambda: client.get_ultimo_concurso())
testar("get_total_concursos()", lambda: client.get_total_concursos())
testar("get_numeros_faltantes_ciclo()", lambda: client.get_numeros_faltantes_ciclo())

# Teste específico das colunas corretas
print("\n🎯 VALIDAÇÃO DE COLUNAS:")
print("-" * 80)

# Verificar v_tendencia tem aparicoes_ultimos_48
try:
    tend = client.query("SELECT * FROM loterias.v_tendencia LIMIT 1")
    if 'aparicoes_ultimos_48' in tend.columns:
        print("✅ v_tendencia tem coluna 'aparicoes_ultimos_48'")
        testes_ok += 1
    else:
        print(f"❌ v_tendencia não tem coluna 'aparicoes_ultimos_48'. Colunas: {tend.columns.tolist()}")
    testes_total += 1
except Exception as e:
    print(f"❌ Erro ao verificar v_tendencia: {e}")
    testes_total += 1

# Verificar v_ciclo tem faltante_no_ciclo
try:
    ciclo = client.query("SELECT * FROM loterias.v_ciclo LIMIT 1")
    if 'faltante_no_ciclo' in ciclo.columns:
        print("✅ v_ciclo tem coluna 'faltante_no_ciclo'")
        testes_ok += 1
    else:
        print(f"❌ v_ciclo não tem coluna 'faltante_no_ciclo'. Colunas: {ciclo.columns.tolist()}")
    testes_total += 1
except Exception as e:
    print(f"❌ Erro ao verificar v_ciclo: {e}")
    testes_total += 1

# Verificar v_scores tem score_tendencia e score_ciclo calculados
try:
    scores = client.query("SELECT score_tendencia, score_ciclo FROM loterias.v_scores LIMIT 1")
    if 'score_tendencia' in scores.columns and 'score_ciclo' in scores.columns:
        print("✅ v_scores tem colunas 'score_tendencia' e 'score_ciclo' calculadas")
        testes_ok += 1
    else:
        print(f"❌ v_scores faltando colunas. Colunas: {scores.columns.tolist()}")
    testes_total += 1
except Exception as e:
    print(f"❌ Erro ao verificar v_scores: {e}")
    testes_total += 1

# Resultado final
print("\n" + "=" * 80)
print(f"📊 RESULTADO FINAL: {testes_ok}/{testes_total} testes passaram")
print("=" * 80)

if testes_ok == testes_total:
    print("\n🎉 TODOS OS TESTES PASSARAM! Sistema 100% funcional!")
    sys.exit(0)
else:
    print(f"\n⚠️  {testes_total - testes_ok} teste(s) falharam!")
    sys.exit(1)
