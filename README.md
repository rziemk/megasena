# Projeto Mega-Sena - Sistema de Analise Estatistica Avancada

Sistema completo de analise estatistica para Mega-Sena com **19 regras inteligentes**, processamento evolutivo concurso a concurso, rastreamento de 4 ciclos paralelos e interface interativa.

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE DADOS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Resultados     ──►  Analise Evolutiva  ──►  Tabela Historica  ──►  App     │
│  (megasena)          (19 regras)             (2913 registros)      Streamlit│
│                      (4 ciclos)                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Conceito Principal: Analise Evolutiva

O diferencial deste sistema e que **cada concurso e analisado olhando apenas o passado**. Isso significa que:

1. Para analisar o concurso 100, olhamos apenas concursos 1-99
2. Para analisar o concurso 2000, olhamos apenas concursos 1-1999
3. Isso permite entender como as probabilidades **evoluem ao longo do tempo**

A tabela `concurso_analise_evolutiva` armazena o resultado de todas as 19 regras para cada um dos 2913 concursos processados.

---

## As 19 Regras de Analise

### Regras Individuais (6 regras)

Sao regras que avaliam cada numero (1-60) individualmente. Para cada concurso, guardamos um resumo de como os 6 numeros sorteados se comportam nessas metricas.

---

#### R1 - Frequencia Historica

**O que mede:** Quantas vezes cada numero ja foi sorteado ate aquele momento.

**Como funciona:**
- A cada concurso, contamos quantas vezes cada numero (1-60) apareceu no historico
- Criamos um ranking dos 20 numeros mais frequentes (top 20)
- Verificamos quantos dos 6 numeros sorteados estao nesse top 20

**Campo na tabela:** `r1_freq_top20`

**Exemplo:**
```
Concurso 100:
- Historico: 99 concursos anteriores
- Top 20 mais frequentes: [10, 53, 5, 23, 33, ...]
- Sorteio: 05-12-23-34-45-56
- Resultado: 2 numeros estao no top 20 (05 e 23)
- r1_freq_top20 = 2
```

**Por que importa:** Numeros frequentes tendem a continuar frequentes (momentum estatistico).

---

#### R2 - Atraso

**O que mede:** Ha quantos concursos cada numero nao sai.

**Como funciona:**
- Para cada numero sorteado, contamos quantos concursos passaram desde sua ultima aparicao
- Calculamos a media e o maximo dos 6 atrasos

**Campos na tabela:** `r2_atraso_medio`, `r2_atraso_max`

**Exemplo:**
```
Concurso 100:
- Numero 05: ultimo sorteio foi no concurso 98 → atraso = 2
- Numero 45: ultimo sorteio foi no concurso 75 → atraso = 25
- Sorteio: 05-12-23-34-45-56
- Atrasos: [2, 10, 5, 15, 25, 8]
- r2_atraso_medio = 10.83
- r2_atraso_max = 25
```

**Por que importa:** Numeros com atraso alto tendem a "estar devendo" (regressao a media).

---

#### R3 - Tendencia Recente

**O que mede:** Quantas vezes cada numero apareceu nos ultimos 48 concursos (janela deslizante).

**Como funciona:**
- Olha apenas os ultimos 48 concursos (nao todo o historico)
- Conta aparicoes de cada numero nessa janela
- Numeros com 5+ aparicoes sao considerados "quentes recentes"
- Conta quantos dos 6 sorteados sao quentes recentes

**Campo na tabela:** `r3_tendencia_quentes`

**Exemplo:**
```
Concurso 100:
- Janela: concursos 52-99 (48 concursos)
- Numero 10 apareceu 8 vezes nesses 48 → quente
- Numero 55 apareceu 2 vezes nesses 48 → frio
- Sorteio: 05-10-23-34-45-55
- Quentes no sorteio: 3
- r3_tendencia_quentes = 3
```

**Por que importa:** Tendencias de curto prazo podem indicar padroes temporarios.

---

#### R4 - Poisson (Desvio Estatistico)

**O que mede:** O quanto a frequencia real de cada numero desvia da frequencia esperada.

**Como funciona:**
- Frequencia esperada = (total de concursos * 6) / 60
- Para cada numero sorteado, calcula o desvio percentual
- Retorna a media dos desvios absolutos

**Campo na tabela:** `r4_poisson_desvio`

**Exemplo:**
```
Concurso 1000:
- Frequencia esperada por numero: (1000 * 6) / 60 = 100
- Numero 33 apareceu 120 vezes → desvio = +20%
- Numero 07 apareceu 85 vezes → desvio = -15%
- r4_poisson_desvio = media dos desvios
```

**Por que importa:** Numeros muito acima ou abaixo do esperado tendem a se normalizar.

---

#### R5 - Pressao do Ciclo 60

**O que mede:** Quantos dos 6 numeros sorteados eram "faltantes" no ciclo atual.

**Como funciona:**
- Um ciclo se completa quando todos os 60 numeros ja sairam pelo menos uma vez
- Antes de cada sorteio, sabemos quais numeros ainda faltam sair no ciclo
- Contamos quantos dos 6 sorteados estavam nessa lista de faltantes

**Campo na tabela:** `r5_pressao_faltantes`

**Exemplo:**
```
Concurso 2900:
- Ciclo atual: 61
- Numeros que ainda nao sairam neste ciclo: [7, 19, 33, 41, 52]
- Sorteio: 07-12-23-33-45-56
- Faltantes sorteados: 2 (07 e 33)
- r5_pressao_faltantes = 2
```

**Por que importa:** Numeros faltantes tem "pressao" para sair e completar o ciclo.

---

#### R6 - Classificacao Hot/Neutral/Frio (HNF)

**O que mede:** Distribui os 60 numeros em 3 categorias baseado na frequencia acumulada.

**Como funciona:**
- Ordena os 60 numeros por frequencia
- Top 20 = Hot (H)
- Meio 20 = Neutral (N)
- Bottom 20 = Frio (F)
- Conta quantos dos 6 sorteados sao H, N e F

**Campos na tabela:** `r6_hot`, `r6_neutral`, `r6_frio`

**Exemplo:**
```
Concurso 500:
- Hot (mais frequentes): [10, 53, 5, 23, 33, ...]
- Neutral (frequencia media): [15, 28, 42, ...]
- Frio (menos frequentes): [1, 60, 49, ...]
- Sorteio: 05-10-28-42-49-60
- r6_hot = 2 (05, 10)
- r6_neutral = 2 (28, 42)
- r6_frio = 2 (49, 60)
```

**Por que importa:** Sorteios tendem a ter um mix equilibrado de H-N-F.

---

### Regras de Conjunto (13 regras)

Sao regras que analisam o padrao do sorteio como um todo (os 6 numeros juntos).

---

#### R7 - Soma das Dezenas

**O que mede:** A soma dos 6 numeros sorteados.

**Como funciona:**
- Soma simples dos 6 numeros
- Classifica em: baixa (<140), ideal (140-200), alta (>200)

**Campos na tabela:** `r7_soma`, `r7_soma_classe`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
Soma: 5 + 12 + 23 + 34 + 45 + 56 = 175
r7_soma = 175
r7_soma_classe = 'ideal'
```

**Estatistica historica:**
- Soma media: ~170
- 80% dos sorteios tem soma entre 120 e 220
- Faixa ideal: 140-200

---

#### R8 - Paridade (Pares e Impares)

**O que mede:** Quantos numeros pares e impares no sorteio.

**Como funciona:**
- Pares: 2, 4, 6, 8, ..., 60 (30 numeros)
- Impares: 1, 3, 5, 7, ..., 59 (30 numeros)
- Conta a distribuicao no sorteio

**Campos na tabela:** `r8_pares`, `r8_impares`, `r8_padrao`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
Pares: 12, 34, 56 = 3
Impares: 05, 23, 45 = 3
r8_pares = 3
r8_impares = 3
r8_padrao = '3P-3I'
```

**Estatistica historica:**
| Padrao | Frequencia |
|--------|------------|
| 3P-3I  | 30.66%     |
| 4P-2I  | 24.30%     |
| 2P-4I  | 24.17%     |
| 5P-1I  | 9.47%      |
| 1P-5I  | 8.82%      |

---

#### R9 - Numeros Primos

**O que mede:** Quantos numeros primos no sorteio.

**Numeros primos de 1-60:**
```
2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59
Total: 17 numeros primos
```

**Campos na tabela:** `r9_primos`, `r9_nao_primos`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
Primos: 05, 23 = 2
Nao primos: 12, 34, 45, 56 = 4
r9_primos = 2
r9_nao_primos = 4
```

**Estatistica historica:**
| Qtd Primos | Frequencia |
|------------|------------|
| 2 primos   | 33.44%     |
| 1 primo    | 32.68%     |
| 3 primos   | 16.89%     |
| 0 primos   | 11.67%     |
| 4+ primos  | 5.32%      |

---

#### R10 - Quadrantes

**O que mede:** Distribuicao dos numeros pelos 4 quadrantes do volante.

**Divisao do volante:**
```
Q1: 01-15 (canto superior esquerdo)
Q2: 16-30 (canto superior direito)
Q3: 31-45 (canto inferior esquerdo)
Q4: 46-60 (canto inferior direito)
```

**Campos na tabela:** `r10_q1`, `r10_q2`, `r10_q3`, `r10_q4`, `r10_padrao`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
Q1: 05, 12 = 2
Q2: 23 = 1
Q3: 34, 45 = 2
Q4: 56 = 1
r10_padrao = '2-1-2-1'
```

---

#### R11 - Faixas BMA (Baixo/Medio/Alto)

**O que mede:** Distribuicao dos numeros pelas 3 faixas.

**Divisao:**
```
Baixo (B): 01-20
Medio (M): 21-40
Alto (A):  41-60
```

**Campos na tabela:** `r11_baixo`, `r11_medio`, `r11_alto`, `r11_padrao`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
Baixo: 05, 12 = 2
Medio: 23, 34 = 2
Alto: 45, 56 = 2
r11_padrao = '2-2-2'
```

---

#### R12 - Linhas do Volante

**O que mede:** Distribuicao dos numeros pelas 6 linhas do volante.

**Divisao:**
```
L1: 01-10
L2: 11-20
L3: 21-30
L4: 31-40
L5: 41-50
L6: 51-60
```

**Campos na tabela:** `r12_l1` a `r12_l6`, `r12_padrao`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
L1: 05 = 1
L2: 12 = 1
L3: 23 = 1
L4: 34 = 1
L5: 45 = 1
L6: 56 = 1
r12_padrao = '1-1-1-1-1-1'
```

---

#### R13 - Colunas/Terminacoes

**O que mede:** Distribuicao dos numeros pela terminacao (ultimo digito).

**Divisao:**
```
T0: 10, 20, 30, 40, 50, 60
T1: 01, 11, 21, 31, 41, 51
T2: 02, 12, 22, 32, 42, 52
...
T9: 09, 19, 29, 39, 49, 59
```

**Campos na tabela:** `r13_t0` a `r13_t9`, `r13_padrao`

**Exemplo:**
```
Sorteio: 05-12-23-34-45-56
T2: 12 = 1
T3: 23 = 1
T4: 34 = 1
T5: 05, 45 = 2
T6: 56 = 1
r13_padrao = '0-0-1-1-1-2-1-0-0-0'
```

---

#### R14 - Sequencias Consecutivas

**O que mede:** Se existem numeros consecutivos no sorteio.

**Campos na tabela:** `r14_tem_sequencia`, `r14_maior_sequencia`, `r14_total_sequencias`

**Exemplo:**
```
Sorteio: 05-06-23-24-25-56
Sequencias: [05-06] e [23-24-25]
r14_tem_sequencia = 1 (sim)
r14_maior_sequencia = 3 (23-24-25)
r14_total_sequencias = 2
```

---

#### R15 - Ciclo 60 (Cobertura Completa)

**O que mede:** Estado do ciclo onde todos os 60 numeros devem sair.

**Como funciona:**
- Um ciclo se completa quando todos os 60 numeros ja sairam pelo menos 1 vez
- Para cada sorteio, rastreamos:
  - Em qual ciclo estamos
  - Quantos faltavam ANTES do sorteio
  - Quantos eram "novos" (primeira vez no ciclo)
  - Quantos eram "repetidos" (ja tinham saido no ciclo)
  - Quantos faltam DEPOIS do sorteio

**Campos na tabela:** `r15_ciclo_numero`, `r15_faltam_antes`, `r15_novos`, `r15_repetidos`, `r15_faltam_depois`

**Exemplo:**
```
Concurso 2900:
- Estamos no ciclo 61
- Antes do sorteio: faltavam 5 numeros [7, 19, 33, 41, 52]
- Sorteio: 07-12-23-33-45-56
- Novos: 2 (07 e 33 eram faltantes)
- Repetidos: 4 (12, 23, 45, 56 ja tinham saido)
- Depois: faltam 3 numeros [19, 41, 52]

r15_ciclo_numero = 61
r15_faltam_antes = 5
r15_novos = 2
r15_repetidos = 4
r15_faltam_depois = 3
```

**Estatistica historica:**
| Novos no sorteio | Frequencia |
|------------------|------------|
| 0 novos          | 49.85%     |
| 1 novo           | 20.32%     |
| 2 novos          | 9.75%      |
| 3+ novos         | 20.08%     |

---

#### R16 - Ciclo de Pares

**O que mede:** Estado do ciclo onde todos os 30 numeros pares devem sair.

**Mesma logica do R15, mas apenas para os pares (2, 4, 6, ..., 60).**

**Campos na tabela:** `r16_ciclo_numero`, `r16_faltam_antes`, `r16_novos`, `r16_repetidos`, `r16_faltam_depois`

---

#### R17 - Ciclo de Impares

**O que mede:** Estado do ciclo onde todos os 30 numeros impares devem sair.

**Mesma logica do R15, mas apenas para os impares (1, 3, 5, ..., 59).**

**Campos na tabela:** `r17_ciclo_numero`, `r17_faltam_antes`, `r17_novos`, `r17_repetidos`, `r17_faltam_depois`

---

#### R18 - Ciclo de Primos

**O que mede:** Estado do ciclo onde todos os 17 numeros primos devem sair.

**Numeros primos:** 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59

**Mesma logica do R15, mas apenas para os primos.**

**Campos na tabela:** `r18_ciclo_numero`, `r18_faltam_antes`, `r18_novos`, `r18_repetidos`, `r18_faltam_depois`

---

#### R19 - Mix HNF do Concurso

**O que mede:** Padrao Hot/Neutral/Frio do sorteio (resumo visual do R6).

**Campo na tabela:** `r19_padrao`

**Exemplo:**
```
r6_hot = 3, r6_neutral = 2, r6_frio = 1
r19_padrao = '3H-2N-1F'
```

**Estatistica historica:**
| Padrao   | Frequencia |
|----------|------------|
| 2H-2N-2F | 13.53%     |
| 3H-2N-1F | 9.51%      |
| 3H-1N-2F | 8.86%      |
| 1H-3N-2F | 8.82%      |
| 1H-2N-3F | 8.75%      |

---

## Metadados de Ciclos

Alem das 19 regras, a tabela armazena 4 campos com os numeros que ainda faltam em cada ciclo apos cada sorteio:

| Campo | Descricao |
|-------|-----------|
| `meta_faltam_ciclo60` | Lista dos numeros (1-60) que ainda faltam no ciclo atual |
| `meta_faltam_pares` | Lista dos pares que ainda faltam |
| `meta_faltam_impares` | Lista dos impares que ainda faltam |
| `meta_faltam_primos` | Lista dos primos que ainda faltam |

**Exemplo (ultimo concurso 2954):**
```
meta_faltam_ciclo60 = [43]           # So falta o 43
meta_faltam_pares = [2, 4, 6, ...]   # 25 pares faltando
meta_faltam_impares = [1, 3]         # 2 impares faltando
meta_faltam_primos = [41, 43]        # 2 primos faltando
```

---

## Resumo dos 4 Ciclos

| Ciclo | Numeros | Total | Ciclo Atual (2954) | Faltam |
|-------|---------|-------|-------------------|--------|
| Ciclo 60 | Todos (01-60) | 60 | #62 | 1 |
| Ciclo Pares | 02,04,...,60 | 30 | #74 | 25 |
| Ciclo Impares | 01,03,...,59 | 30 | #77 | 2 |
| Ciclo Primos | 17 primos | 17 | #87 | 2 |

---

## Estrutura da Tabela ClickHouse

```sql
CREATE TABLE loterias.concurso_analise_evolutiva (
    -- Identificacao
    concurso UInt32,
    data Date,
    numeros Array(UInt8),

    -- R1-R6: Regras Individuais
    r1_freq_top20 UInt8,
    r2_atraso_medio Float32,
    r2_atraso_max UInt16,
    r3_tendencia_quentes UInt8,
    r4_poisson_desvio Float32,
    r5_pressao_faltantes UInt8,
    r6_hot UInt8,
    r6_neutral UInt8,
    r6_frio UInt8,

    -- R7-R19: Regras de Conjunto
    r7_soma UInt16,
    r7_soma_classe String,
    r8_pares UInt8,
    r8_impares UInt8,
    r8_padrao String,
    r9_primos UInt8,
    r9_nao_primos UInt8,
    r10_q1 UInt8, r10_q2 UInt8, r10_q3 UInt8, r10_q4 UInt8,
    r10_padrao String,
    r11_baixo UInt8, r11_medio UInt8, r11_alto UInt8,
    r11_padrao String,
    r12_l1 UInt8, r12_l2 UInt8, r12_l3 UInt8, r12_l4 UInt8, r12_l5 UInt8, r12_l6 UInt8,
    r12_padrao String,
    r13_t0 UInt8, r13_t1 UInt8, ... r13_t9 UInt8,
    r13_padrao String,
    r14_tem_sequencia UInt8,
    r14_maior_sequencia UInt8,
    r14_total_sequencias UInt8,
    r15_ciclo_numero UInt16, r15_faltam_antes UInt8, r15_novos UInt8, r15_repetidos UInt8, r15_faltam_depois UInt8,
    r16_ciclo_numero UInt16, r16_faltam_antes UInt8, r16_novos UInt8, r16_repetidos UInt8, r16_faltam_depois UInt8,
    r17_ciclo_numero UInt16, r17_faltam_antes UInt8, r17_novos UInt8, r17_repetidos UInt8, r17_faltam_depois UInt8,
    r18_ciclo_numero UInt16, r18_faltam_antes UInt8, r18_novos UInt8, r18_repetidos UInt8, r18_faltam_depois UInt8,
    r19_padrao String,

    -- Metadados
    meta_faltam_ciclo60 Array(UInt8),
    meta_faltam_pares Array(UInt8),
    meta_faltam_impares Array(UInt8),
    meta_faltam_primos Array(UInt8)

) ENGINE = MergeTree()
ORDER BY concurso
```

---

## Como Usar

### Instalacao

```bash
# 1. Clonar repositorio
git clone https://github.com/seu-usuario/megasena.git
cd megasena

# 2. Instalar dependencias
pip3 install -r requirements.txt

# 3. Configurar ClickHouse Cloud
cat > dev.vars << EOF
CLICKHOUSE_HOST=seu-host.clickhouse.cloud
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=sua-senha
CLICKHOUSE_SECURE=true
EOF

# 4. Carregar dados historicos
python3 data_loader.py

# 5. Processar analise evolutiva (19 regras + 4 ciclos)
python3 create_analise_evolutiva.py

# 6. Executar aplicacao
streamlit run app.py
```

### Scripts Principais

| Script | Funcao |
|--------|--------|
| `create_analise_evolutiva.py` | Processa todos os concursos com as 19 regras |
| `app.py` | Interface Streamlit principal |
| `gerador_jogos.py` | Gerador de jogos otimizados |
| `clickhouse_client.py` | Cliente para ClickHouse Cloud |
| `auto_update_data.py` | Atualizacao automatica de dados |

---

## Consultas Uteis

### Ver ultimo concurso analisado
```sql
SELECT * FROM loterias.concurso_analise_evolutiva
ORDER BY concurso DESC LIMIT 1
```

### Ver padroes mais frequentes de paridade
```sql
SELECT r8_padrao, count() as qtd,
       round(count() * 100.0 / (SELECT count() FROM loterias.concurso_analise_evolutiva), 2) as pct
FROM loterias.concurso_analise_evolutiva
GROUP BY r8_padrao
ORDER BY qtd DESC
```

### Ver numeros faltantes no ciclo atual
```sql
SELECT meta_faltam_ciclo60, meta_faltam_primos
FROM loterias.concurso_analise_evolutiva
ORDER BY concurso DESC LIMIT 1
```

### Ver evolucao dos ciclos
```sql
SELECT
    r15_ciclo_numero as ciclo_60,
    r16_ciclo_numero as ciclo_pares,
    r17_ciclo_numero as ciclo_impares,
    r18_ciclo_numero as ciclo_primos,
    count() as concursos
FROM loterias.concurso_analise_evolutiva
GROUP BY ciclo_60, ciclo_pares, ciclo_impares, ciclo_primos
ORDER BY ciclo_60 DESC
LIMIT 10
```

---

## Tecnologias

- **Python 3.9+**: Processamento e analise
- **ClickHouse Cloud**: Banco de dados analitico
- **Streamlit**: Interface web interativa
- **Pandas/NumPy**: Manipulacao de dados
- **Plotly**: Visualizacoes interativas

---

## Disclaimer

Este sistema e uma ferramenta de **analise estatistica educacional** e **NAO garante ganhos**. A Mega-Sena e um jogo de azar com esperanca matematica negativa.

**Jogue com responsabilidade.**

---

**Versao:** 3.0.0
**Ultima Atualizacao:** 01/01/2026
**Total de Regras:** 19
**Concursos Processados:** 2913 (do 42 ao 2954)
