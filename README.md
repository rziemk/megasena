# Projeto Mega-Sena - Algoritmo Preditivo

Algoritmo de análise estatística avançada para a Mega-Sena, desenvolvido em Python.

## Características

- **Análise de Frequências**: Identifica números mais e menos frequentes
- **Temperaturas Hot/Cold**: Números quentes (recentes) e frios (atrasados)
- **Análise de Quadrantes**: Mapeamento do volante 6x10
- **Padrões Par/Ímpar e Alto/Baixo**: Busca equilíbrio estatístico
- **Distribuição de Poisson**: Probabilidade de aparição
- **Sistema de Score (0-100)**: Pontuação ponderada para cada número
- **Duas Estratégias de Alocação**: Sniper (19 dezenas) e Bomber (18 dezenas + fechamentos)
- **Cálculo de Esperança Matemática**: E[X] para cada estratégia

## Budget

- **Orçamento Total**: R$ 180.000,00
- **Estratégia A (Sniper)**: 1 jogo de 19 dezenas (R$ 162.792,00) + jogos zebra
- **Estratégia B (Bomber)**: 1 jogo de 18 dezenas (R$ 111.384,00) + fechamentos matemáticos

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Análise completa com dados sintéticos
python main.py

# Usando arquivo CSV com histórico real
python main.py --csv dados.csv

# Apenas análise estatística
python main.py --analise

# Apenas comparação de estratégias
python main.py --estrategias

# Apenas sugestão de jogos
python main.py --sugestao
```

## Estrutura do Projeto

```
megasena/
├── config.py              # Configurações e parâmetros
├── data_loader.py         # Carregamento de dados históricos
├── statistical_analysis.py # Análises estatísticas e scoring
├── strategies.py          # Estratégias de apostas e E[X]
├── main.py               # Script principal
└── requirements.txt      # Dependências
```

## Disclaimer

Este algoritmo é uma ferramenta de **análise estatística** e **NÃO garante ganhos**. A Mega-Sena é um jogo de azar com esperança matemática negativa. Jogue com responsabilidade.
