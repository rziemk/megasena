# 🎰 Projeto Mega-Sena - Sistema de Análise Estatística

Sistema avançado de análise estatística para Mega-Sena com **15 regras inteligentes**, integração com ClickHouse Cloud e interface interativa Streamlit.

## ✨ Características Principais

### 📊 15 Regras de Análise Estatística

#### 🔢 Regras Individuais (por número)
1. **R1 - Frequência Histórica (9%)**: Quantas vezes cada número foi sorteado
2. **R2 - Atraso (9%)**: Há quantos concursos o número não sai (regressão à média)
3. **R3 - Tendência Recente (7%)**: Aparições nos últimos **48 concursos** (média de ciclos completos)
4. **R10 - Ciclo de Renovação (7%)**: Números faltantes nos últimos **27 concursos** (mínimo histórico)
5. **R11 - Distribuição de Poisson (6%)**: Probabilidade estatística esperada
6. **R15 - Pressão do Ciclo Completo (4%)**: Pressão quando todos 60 números já saíram

#### 🎯 Regras de Conjunto (análise do sorteio)
7. **R4 - Quadrantes (7%)**: Equilíbrio entre Q1(1-15), Q2(16-30), Q3(31-45), Q4(46-60)
8. **R5 - Paridade (6%)**: Equilíbrio entre pares e ímpares
9. **R6 - Faixas B/M/A (6%)**: Equilíbrio Baixo(1-20), Médio(21-40), Alto(41-60)
10. **R7 - Linhas (7%)**: Distribuição pelas 6 linhas do volante
11. **R8 - Colunas (7%)**: Distribuição pelas 10 colunas (terminações)
12. **R9 - Soma Ideal (7%)**: Contribuição para soma entre 150-200
13. **R12 - H-N-F (6%)**: Classificação Hot/Normal/Frio por frequência
14. **R13 - Sequências (6%)**: Análise de números consecutivos
15. **R14 - Freq. por Quadrante (6%)**: Frequência histórica por quadrante

### 🔄 Auto-Atualização de Dados
- ✅ Verifica automaticamente se há novos concursos
- ✅ Recalcula ciclos completos sem intervenção manual
- ✅ Mantém dados sempre sincronizados

### 💾 Tecnologias
- **ClickHouse Cloud**: Banco de dados analítico de alta performance
- **Streamlit**: Interface web interativa e responsiva
- **Python 3.9+**: Análises estatísticas com pandas e numpy
- **Plotly**: Visualizações interativas (radar charts, gráficos de barras, etc.)

## 📋 Janelas de Análise (v2.0.0)

| Regra | Janela | Justificativa |
|-------|--------|---------------|
| **R3 - Tendência** | 48 concursos | Média de duração dos ciclos completos |
| **R10 - Ciclo** | 27 concursos | Mínimo histórico dos ciclos completos |

> 💡 **Nota:** As janelas foram ajustadas com base em análise histórica real dos ciclos completos da Mega-Sena.

## 🚀 Instalação

### Pré-requisitos
- Python 3.9 ou superior
- Conta ClickHouse Cloud (ou instalação local)

### Passo a Passo

```bash
# 1. Clonar o repositório
cd megasena

# 2. Instalar dependências
pip3 install -r requirements.txt

# 3. Configurar ClickHouse
# Criar arquivo dev.vars com suas credenciais:
cat > dev.vars << EOF
CLICKHOUSE_HOST=seu-host.clickhouse.cloud
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=sua-senha
CLICKHOUSE_SECURE=true
EOF

# 4. Popular banco de dados
python3 data_loader.py

# 5. Criar tabela de ciclos completos
python3 create_ciclos_analysis.py

# 6. Criar views
python3 update_view_tendencia.py
python3 update_view_ciclo.py

# 7. Executar aplicação
streamlit run app.py
```

## 💻 Uso

### Interface Streamlit
```bash
streamlit run app.py --server.port 8501
```

Acesse: http://localhost:8501

### Scripts de Análise

```bash
# Atualizar dados automaticamente
python3 auto_update_data.py

# Análise de ciclos completos
python3 create_ciclos_analysis.py

# Atualizar view de tendência (R3)
python3 update_view_tendencia.py

# Atualizar view de ciclo (R10)
python3 update_view_ciclo.py

# Criar score individual (apenas regras de número)
python3 create_score_individual.py
```

## 📁 Estrutura do Projeto

```
megasena/
├── app.py                          # Interface Streamlit principal
├── config.py                       # Configurações e pesos das regras
├── data_loader.py                  # Carregamento de dados históricos
├── clickhouse_client.py            # Cliente ClickHouse
├── auto_update_data.py             # Auto-atualização de dados
├── create_ciclos_analysis.py       # Análise de ciclos completos
├── create_score_individual.py      # Score baseado apenas em regras individuais
├── update_view_tendencia.py        # Atualização da view R3
├── update_view_ciclo.py            # Atualização da view R10
├── setup_clickhouse_views.py       # Setup inicial das views
├── CHANGELOG.md                    # Histórico de mudanças
└── requirements.txt                # Dependências Python
```

## 🎯 Estratégias de Apostas

### Budget: R$ 180.000,00

**Estratégia A - "Sniper"**
- 1 jogo de 19 dezenas (R$ 162.792,00)
- Sobra: R$ 17.208,00 para jogos complementares
- Foco: Precisão máxima com os top números

**Estratégia B - "Bomber"**
- 1 jogo de 18 dezenas (R$ 111.384,00)
- Sobra: R$ 68.616,00 para fechamentos matemáticos
- Foco: Cobertura ampla com validações estatísticas

## 📊 Views ClickHouse

| View | Descrição |
|------|-----------|
| `v_frequencia` | Frequência histórica de cada número |
| `v_atraso` | Atraso (concursos sem aparecer) |
| `v_tendencia` | Tendência nos últimos 48 concursos |
| `v_ciclo` | Números faltantes nos últimos 27 concursos |
| `v_poisson` | Probabilidade de Poisson |
| `v_pressao_ciclo` | Pressão do ciclo completo (60 números) |
| `v_scores` | Score consolidado de todas as 15 regras |
| `v_score_individual` | Score apenas das 6 regras individuais |
| `ciclos_completos` | Tabela de ciclos históricos completos |

## 🔧 Configuração

As configurações principais estão em `config.py`:

```python
# Janelas de Análise
JANELA_HOT = 48           # R3: Tendência (média de ciclos completos)
CICLO_RENOVACAO = 27      # R10: Ciclo (mínimo de ciclos completos)

# Pesos das Regras (Total = 100%)
PESO_FREQUENCIA = 0.09        # R1
PESO_ATRASO = 0.09            # R2
PESO_TENDENCIA = 0.07         # R3
PESO_CICLO = 0.07             # R10
PESO_POISSON = 0.06           # R11
PESO_PRESSAO_CICLO = 0.04     # R15
# ... demais regras
```

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico completo de versões.

## ⚠️ Disclaimer

Este sistema é uma ferramenta de **análise estatística educacional** e **NÃO garante ganhos**. A Mega-Sena é um jogo de azar com esperança matemática negativa.

**Jogue com responsabilidade.**

## 📄 Licença

Projeto educacional - Uso pessoal apenas.

---

**Versão:** 2.0.0
**Última Atualização:** 29/12/2025
**Desenvolvido com:** Python 3.9 + ClickHouse Cloud + Streamlit
