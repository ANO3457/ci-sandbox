# CI Sandbox

![ci](https://github.com/yunaremaia/ci-sandbox/actions/workflows/ci.yml/badge.svg) ![py](https://img.shields.io/badge/python-3.11-blue.svg) ![license](https://img.shields.io/github/license/yunaremaia/ci-sandbox) ![stars](https://img.shields.io/github/stars/yunaremaia/ci-sandbox) [![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

Simulador local de pipelines CI. Veja quais jobs rodam e quais são skipados — sem executar nada.

## O que faz

- Faz parse de workflows do GitHub Actions (`.github/workflows/*.yml`)
- Resolve o DAG de jobs (dependências `needs`)
- Avalia condições `if` para determinar skip/run
- Mostra resultado colorido no terminal

## Instalação

```bash
pip install git+https://github.com/yunaremaia/ci-sandbox.git
```

## Uso

```bash
# Simular um workflow
ci-sandbox simulate .github/workflows/ci.yml

# Simular evento específico
ci-sandbox simulate .github/workflows/ci.yml --event pull_request --branch feature-x

# Com secrets
ci-sandbox simulate .github/workflows/ci.yml -s DATABASE_URL=postgres://localhost

# Mostrar steps
ci-sandbox simulate .github/workflows/ci.yml --steps

# Listar workflows do repo
ci-sandbox list-workflows
```

## Exemplo

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .

  test:
    needs: lint
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - run: pytest

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

```bash
$ ci-sandbox simulate .github/workflows/ci.yml --event push --branch main
🔧 CI
   Event: push | Branch: main | Ref: refs/heads/main

  ✓ lint [ubuntu-latest]
  ↓
  ✓ test [ubuntu-latest]
  ↓
  ✓ deploy [ubuntu-latest]

  ══ 3 success · 0 skipped (3 jobs) ══
```

```bash
$ ci-sandbox simulate .github/workflows/ci.yml --event pull_request --branch feature-x
🔧 CI
   Event: pull_request | Branch: feature-x | Ref: refs/heads/feature-x

  ✓ lint [ubuntu-latest]
  ↓
  ○ test (condition: github.event_name == 'push')
  ↓
  ○ deploy (dependency 'test' did not succeed)

  ══ 1 success · 2 skipped (3 jobs) ══
```

## Visualização de matrizes

Cada combinação de uma matriz literal aparece em sua própria linha, com as variáveis:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [18, 20]
        os: [ubuntu, windows]
```

```text
  ✓ test (node=18, os=ubuntu) [ubuntu-latest]
  ✓ test (node=18, os=windows) [ubuntu-latest]
  ✓ test (node=20, os=ubuntu) [ubuntu-latest]
  ✓ test (node=20, os=windows) [ubuntu-latest]
```

O resumo conta as combinações exibidas. `exclude` remove combinações correspondentes;
`include` acrescenta variáveis sem sobrescrever os eixos originais ou adiciona uma nova
combinação. Matrizes somente com `include` também são aceitas. O status e o motivo de
skip do job são repetidos em cada combinação, inclusive quando o evento não dispara
o workflow. As dependências continuam usando o identificador original (`needs: test`).

Esta é uma visualização da simulação, não uma execução dos runners: não avalia steps
ou expressões `matrix.*` por combinação, nem simula `fail-fast`/`max-parallel`.
Matrizes dinâmicas (por exemplo, `fromJSON`) não são resolvidas; em vez de apresentar
uma contagem fictícia, o comando termina com uma mensagem clara. A expansão está
limitada a 256 combinações.

## Limitações

- Não executa steps (só simula a lógica de skip/run)
- Não suporta todos os functions do GitHub Actions (implementação parcial)
- Matrizes dinâmicas e expressões por combinação não são avaliadas (veja acima)

If this tool is useful to you, a star helps other people find it.

## Related tools

- **[ci-test-gate](https://github.com/yunaremaia/ci-test-gate)** — block PRs until the required tests actually run
- **[sandbox-ffi-layers](https://github.com/yunaremaia/sandbox-ffi-layers)** — layer FFI calls behind a sandbox boundary
- **[agent-workspace](https://github.com/yunaremaia/agent-workspace)** — isolated workspaces per AI agent session
- **[vibeguard](https://github.com/yunaremaia/vibeguard)** — scan AI-generated code for hardcoded secrets, SQL injection and dangerous eval/exec

Part of a family of focused, single-purpose developer tools — each one does one thing
and does it well.

## Licença

MIT

## Local dry-run

Run the project's test or dry-run command before opening a PR to catch workflow YAML issues early.
