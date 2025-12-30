# Changelog - Sistema de Análise Mega-Sena

## [2.0.0] - 2025-12-29

### 🎯 Mudanças Importantes - Ajuste de Janelas de Análise

#### ⚠️ Correções Pós-Deploy (Críticas)
- ✅ **Corrigida view `v_scores`**: Calculando `score_tendencia` a partir de `aparicoes_ultimos_48`
- ✅ **Corrigida view `v_scores`**: Calculando `score_ciclo` a partir de `faltante_no_ciclo`
- ✅ **Corrigido `app.py`**: Referência de `aparicoes_ultimos_10` → `aparicoes_ultimos_48`
- ✅ **Criado `test_all_views.py`**: Script de validação completa (26 testes automatizados)
- ✅ **Criado `update_view_scores.py`**: Script de atualização da view principal

#### Atualização das Regras Individuais

**R3 - Tendência Recente**
- ❌ **Antes:** Analisava os últimos **10 concursos**
- ✅ **Agora:** Analisa os últimos **48 concursos** (média de duração dos ciclos completos)
- **Motivo:** Alinhamento com a média histórica dos ciclos completos (48 concursos)
- **Impacto:** Análise de tendência mais robusta e menos volátil
- **Fórmula:** `Score = (aparições / máx_aparições) × 100` (normalizado pelo máximo, igual à R2)

**R10 - Ciclo de Renovação**
- ❌ **Antes:** Analisava os últimos **15 concursos**
- ✅ **Agora:** Analisa os últimos **27 concursos** (mínimo histórico de ciclos completos)
- **Motivo:** Alinhamento com o mínimo histórico dos ciclos completos (27 concursos)
- **Impacto:** Identificação mais precisa de números com "pressão de aparição"
- **Fórmula:** `Score = 100 se faltante nos últimos 27, senão 0`

#### Sistema de Auto-Atualização

**Nova Funcionalidade: Atualização Automática de Dados**
- ✨ **Verificação automática** de novos concursos ao abrir o app
- ✨ **Recálculo automático** da tabela `ciclos_completos` quando houver novos sorteios
- ✨ **Comparação inteligente** entre `max(concurso)` das tabelas `megasena` e `ciclos_completos`
- ✨ **Processo transparente** executado antes de carregar qualquer página

**Como funciona:**
1. Usuário abre o Streamlit
2. Sistema verifica se há novos concursos
3. Se houver, recalcula automaticamente os ciclos completos
4. Views são atualizadas com os novos dados
5. App carrega com informações sempre atualizadas

#### Arquivos Modificados

**Configuração:**
- `config.py`:
  - `JANELA_HOT = 48` (era 10)
  - `CICLO_RENOVACAO = 27` (era 15)

**Views ClickHouse:**
- `v_tendencia`: Nova coluna `aparicoes_ultimos_48` (era `aparicoes_ultimos_10`)
- `v_ciclo`: Ajustada para janela de 27 concursos

**Scripts:**
- Novo: `auto_update_data.py` - Verifica e atualiza dados automaticamente
- Novo: `update_view_tendencia.py` - Script de atualização da view R3
- Novo: `update_view_ciclo.py` - Script de atualização da view R10

**Aplicação:**
- `app.py`: Todas as referências às janelas antigas atualizadas
- `clickhouse_client.py`: Método `get_tendencia()` atualizado
- `setup_clickhouse_views.py`: Definições das views atualizadas

#### Benefícios

1. **Maior Estabilidade:** Janelas maiores reduzem volatilidade nas análises
2. **Alinhamento Histórico:** Valores baseados em dados reais de ciclos completos
3. **Atualização Automática:** Zero intervenção manual para manter dados atualizados
4. **Consistência:** Todas as descrições e documentações sincronizadas

#### Compatibilidade

⚠️ **Breaking Changes:**
- Métodos que retornavam `aparicoes_ultimos_10` agora retornam `aparicoes_ultimos_48`
- Views antigas de ciclo (15 concursos) foram substituídas por novas (27 concursos)

#### Migração

Para atualizar um ambiente existente:
```bash
# 1. Atualizar views
python3 update_view_tendencia.py
python3 update_view_ciclo.py

# 2. Verificar dados
python3 auto_update_data.py

# 3. Reiniciar aplicação
streamlit run app.py
```

---

## [1.0.0] - 2025-12-28

### Versão Inicial
- Sistema completo com 15 regras de análise
- Integração com ClickHouse Cloud
- Dashboard Streamlit interativo
- Análise de padrões e estatísticas
