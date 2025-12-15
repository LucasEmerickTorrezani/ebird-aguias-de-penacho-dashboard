# eBird Águias de Penacho Dashboard

Dashboard web para visualização e análise de observações de grandes águias neotropicais no Brasil, utilizando dados do **eBird** com uma arquitetura **CSV-first**, automatizada e segura.

Este projeto foi desenvolvido com foco em **pesquisa**, **reprodutibilidade** e **boas práticas de engenharia de dados**, evitando dependência direta de APIs em tempo real.

---

O objetivo do projeto é:

* Monitorar ocorrências recentes de águias raras no Brasil
* Visualizar dados em mapas e tabelas interativos
* Manter um **histórico completo** de observações
* Evitar limites e bloqueios da API do eBird
* Garantir desempenho rápido no dashboard

Espécies monitoradas:

* Harpia (*Harpia harpyja*)
* Uiraçu (*Morphnus guianensis*)
* Gavião-de-penacho (*Spizaetus ornatus*)
* Gavião-pega-macaco (*Spizaetus tyrannus*)
* Gavião-pato (*Spizaetus melanoleucus*)


##  Arquitetura (Visão Geral)

O projeto segue uma arquitetura desacoplada em duas camadas:

### 1️Ingestão de dados (background)

```
eBird API → update_data.py → observations.csv
```

* Executada automaticamente via **GitHub Actions**
* Atualização diária
* Dados **apenas adicionados** (append-only)
* Proteção contra duplicatas

###  Visualização (dashboard)

```
observations.csv → Flask → Dashboard Web
```

* Nenhuma chamada à API em tempo real
* Carregamento instantâneo
* Estável e reprodutível

---

## Estrutura do Projeto

```
.
├─ app.py                     # Dashboard Flask (CSV-only)
├─ update_data.py             # Script de ingestão (eBird → CSV)
├─ data/
│  └─ observations.csv        # Dataset histórico
├─ services/
│  └─ ebird_service.py        # Cliente eBird
├─ static/
│  ├─ css/
│  └─ images/
├─ templates/
│  └─ index.html
├─ .github/
│  └─ workflows/
│     └─ update-data.yml      # Automação GitHub Actions
├─ .gitignore
└─ README.md
```

---

## Dados

O dataset principal está em:

```
data/observations.csv
```

### Características

* Formato CSV (simples, portátil e versionado)
* Append-only (histórico preservado)
* Sem sobrescrita de dados
* Deduplicação por chave composta:

```
species + lat + lng + obsDt + locName
```

### Campos

* `species`
* `comName`
* `locName`
* `lat`
* `lng`
* `obsDt`

---

## Atualização Automática

A atualização do CSV é feita via **GitHub Actions**:

* Executa diariamente (06:00 UTC)
* Pode ser disparada manualmente
* Usa variável secreta para a API key

### Segurança

* A chave do eBird é armazenada em:

```
Settings → Secrets → Actions → EBIRD_API_KEY
```

* Nunca aparece em commits ou logs

---

##  Executando Localmente

