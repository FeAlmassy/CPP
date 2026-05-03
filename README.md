# CPP — Curso de Programação em Python

Repositório dos cursos de programação do [Prandiano – Museu de Matemática](https://www.prandiano.com.br/).

## Estrutura

```
CPP/
├── python/          # Curso 1 — Python Puro
│   ├── documentos_conceituais/
│   ├── exercicios/
│   ├── html/
│   ├── notebooks/
│   └── videos/
│
└── mmap1/           # Curso 2 — MMAP: Modelagem Matemática Aplicada em Python
    ├── aula_1/
    ├── aula_2/
    └── aula_3/
```

## Cursos

### Python Puro
Fundamentos da linguagem Python: sintaxe, estruturas de dados, funções, orientação a objetos e aplicações gerais.

### MMAP — Modelagem Matemática Aplicada em Python
Modelagem matemática com Python, cobrindo ferramentas numéricas e computacionais para resolução de problemas aplicados.

## Setup

Cada curso tem seu próprio ambiente virtual. Para recriar:

```bash
# MMAP
cd mmap1
python -m venv venv_mmap1
venv_mmap1\Scripts\activate      # Windows
pip install -r requirements.txt

# Python Puro
cd python
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```
