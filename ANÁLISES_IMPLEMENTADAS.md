# 📊 ANÁLISES PROFUNDAS IMPLEMENTADAS - MEGA-SENA

## ✅ **Sistema Completo de Análise Estatística**

### 🎯 **1. Análises Básicas**
- ✅ Frequência de aparição (todos os 60 números)
- ✅ Números HOT (últimos 10 concursos)
- ✅ Números COLD (atraso máximo)
- ✅ Ciclo médio de renovação individual

### 📐 **2. Análise de Paridade e Distribuição**
- ✅ Par/Ímpar (distribuições: 0P-6I até 6P-0I)
- ✅ Alto/Baixo 1-30 vs 31-60 (distribuições: 0B-6A até 6B-0A)
- ✅ **NOVO:** Baixo/Médio/Alto (1-20, 21-40, 41-60)

### 🎲 **3. Análise do Volante (6x10)**

#### **Quadrantes (4 áreas)**
- Q1: 01-05, 11-15, 21-25
- Q2: 06-10, 16-20, 26-30
- Q3: 31-35, 41-45, 51-55
- Q4: 36-40, 46-50, 56-60

#### **NOVO: Linhas do Volante (6 linhas)**
- L1: 01-10
- L2: 11-20
- L3: 21-30
- L4: 31-40
- L5: 41-50
- L6: 51-60

**Métricas:**
- Média de aparições por linha
- Desvio padrão por linha
- Máximo de números por linha
- Padrões de distribuição mais comuns
- Total de padrões únicos encontrados

#### **NOVO: Colunas do Volante (10 colunas)**
- C1: 01, 11, 21, 31, 41, 51
- C2: 02, 12, 22, 32, 42, 52
- ...
- C10: 10, 20, 30, 40, 50, 60

**Métricas:**
- Média de aparições por coluna
- Desvio padrão por coluna  
- Máximo de números por coluna
- Padrões de distribuição (quantas colunas com 0, 1, 2+ números)
- Total de padrões únicos

### 🔄 **4. NOVO: Ciclos de Renovação Completa**

**Análise detalhada:**
- A cada quantos concursos TODOS os 60 números aparecem pelo menos 1 vez
- Ciclo médio, mínimo, máximo e desvio padrão
- Média de aparições de cada número dentro de um ciclo
- Números mais frequentes em ciclos completos
- Últimos 5 ciclos registrados

**Exemplo de uso:**
Se o ciclo médio é 47 concursos, significa que a cada ~47 sorteios todos os 60 números apareceram pelo menos uma vez.

### 📋 **5. NOVO: Perfis Completos de Jogos**

**Cada concurso é analisado em 25+ dimensões:**

**Básicas:**
- Soma total das dezenas
- Quantidade de pares/ímpares
- Distribuição Baixo(1-20), Médio(21-40), Alto(41-60)
- Distribuição Baixo(1-30) vs Alto(31-60)

**Distribuição Espacial:**
- Números em cada linha (L1 até L6)
- Quantidade de linhas com números
- Quantidade de colunas com 2+ números
- Números em cada quadrante (Q1 até Q4)

**Padrões de Sequência:**
- Gap médio entre números consecutivos
- Gap máximo e mínimo
- Quantidade de sequências (números consecutivos)

**Uso:** Permite identificar perfis vencedores e replicar padrões!

### 🎯 **6. Sistema de Scoring (0-100)**

**Pesos dos fatores:**
- 25% - Frequência Histórica
- 20% - Atraso/Regressão à Média
- 15% - Tendência Recente (últimos jogos)
- 15% - Equilíbrio de Quadrante
- 10% - Contribuição para Paridade
- 10% - Contribuição Alto/Baixo
- 5% - Probabilidade de Poisson

### 💰 **7. Estratégias de Alocação**

**Estratégia A - SNIPER:**
- 1 jogo de 19 dezenas (R$ 162.792)
- Probabilidade: 1 em 1.845
- + Jogos zebra de seguro

**Estratégia B - BOMBER:**
- 1 jogo de 18 dezenas (R$ 111.384)
- Probabilidade: 1 em 2.697
- + Fechamentos matemáticos

**Métricas calculadas:**
- Esperança matemática E[X]
- ROI esperado
- Custo total vs sobra de orçamento

### 🔬 **8. Análises Cruzadas Disponíveis**

Todos os perfis podem ser cruzados para encontrar padrões como:
- Jogos com 3P-3I + 2B-2M-2A + L1:1-L2:1-L3:1-L4:1-L5:1-L6:1
- Correlação entre gap médio e soma total
- Padrões de quadrantes vs linhas
- Etc.

---

## 📊 **Interface Web (Streamlit)**

**5 Abas Completas:**
1. 📊 Análises Estatísticas - Gráficos interativos de todas as análises
2. 🏆 Ranking de Scores - Top 20 e Bottom 20 com gradientes
3. 🎯 Estratégias - Comparação lado a lado com métricas
4. 🎲 Sugestão de Jogos - Volante visual + validação de equilíbrio
5. 📋 Dados Brutos - Tabela completa + download CSV

---

## 🚀 **Como Usar**

```bash
# Terminal (análise completa)
python3 main.py

# Terminal (apenas análises específicas)
python3 main.py --analise
python3 main.py --scores
python3 main.py --estrategias

# Interface Web
streamlit run app.py
```

---

## ⚠️ **Disclaimer**

Este é um sistema de **ANÁLISE ESTATÍSTICA** e **NÃO garante ganhos**.
A Mega-Sena é um jogo de azar com esperança matemática **NEGATIVA**.

**JOGUE COM RESPONSABILIDADE!**
