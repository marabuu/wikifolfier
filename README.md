# D&D 2024 — Compêndio Pessoal da Campanha

Um compêndio pessoal de D&D para uma campanha específica, com a experiência de
navegação do [dnd5e.wikidot.com](https://dnd5e.wikidot.com/).

Conteúdo importado (D&D 2024) e conteúdo homebrew vivem **na mesma estrutura**:
não existe seção "My Campaign" nem "Homebrew" — a origem da página é apenas
metadado.

---

## Conceito

```
D&D 2024
├── Classes
│   ├── Wizard        (Source: Wikidot)
│   └── Rune Mage     (Source: Homebrew)
├── Subclasses
├── Species
├── Backgrounds
├── Feats
├── Spells
│   ├── Fireball      (Source: Wikidot)
│   └── Rune Blast    (Source: Homebrew)
├── Equipment
│   ├── Weapons
│   ├── Armor
│   └── Adventuring Gear
├── Magic Items
└── Rules

Conteúdo da Campanha
├── Locations
├── NPCs
├── Factions
├── Lore
├── Events
├── Sessions
└── House Rules
```

Monstros, criaturas e stat blocks estão **fora do escopo** e nunca são importados.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, Django 5, Django REST Framework |
| Banco | PostgreSQL 16 (volume persistente, full text search) |
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| Conteúdo | Markdown editável + HTML renderizado no servidor |
| Importer | Parser modular do Wikidot (Python) |
| Infra | Docker, Docker Compose, Nginx, Certbot |

---

## Execução local

Requisitos: apenas **Docker** e **Docker Compose**.

```bash
cp .env.example .env
# edite .env: troque POSTGRES_PASSWORD e gere um DJANGO_SECRET_KEY
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api |
| Django Admin | http://localhost:8000/admin |
| Healthcheck | http://localhost:8000/api/health |

Primeiros passos dentro do container:

```bash
docker compose exec backend python manage.py seed_categories
docker compose exec backend python manage.py seed_demo   # conteúdo de exemplo
docker compose exec backend python manage.py createsuperuser
```

---

## Estrutura do projeto

```
.
├── backend/            Django + DRF (models, API, admin, rendering)
├── frontend/           Next.js + TypeScript (layout Wikidot, páginas, editor)
├── importer/           Parser e importer do Wikidot
├── nginx/              Reverse proxy (HTTP/HTTPS)
├── scripts/            backup, restore, deploy, update
├── docs/               Análise da Fase 0
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── .env.example
```

---

## Princípios de organização

1. **Source é metadado.** `official`, `wikidot`, `homebrew`, `campaign`, `custom`.
   Homebrew aparece na mesma lista e usa o mesmo template.
2. **Visibilidade é propriedade.** `public` / `gm_only` — sem seção "GM Only".
3. **Markdown é a fonte.** Nunca se armazena apenas HTML.
4. **Uma única página (`Page`).** Locations, NPCs, Lore e Sessions usam o
   mesmo modelo. Não existe CMS separado.
5. **Fidelidade visual ao Wikidot.** Tabelas, info blocks, breadcrumbs, serifas.
   Sem cards, gradientes, glassmorphism ou CTAs.

Detalhes em [ARCHITECTURE.md](ARCHITECTURE.md) · [DEVELOPMENT.md](DEVELOPMENT.md) ·
[DEPLOY.md](DEPLOY.md) · [IMPORTER.md](IMPORTER.md) ·
[WIKIDOT_ANALYSIS.md](docs/WIKIDOT_ANALYSIS.md).

---

## Testes

```bash
# Parser, filtros e módulos do importer (sem banco)
python importer/tests.py

# Backend (precisa de PostgreSQL)
docker compose exec backend python manage.py test wiki

# Frontend
cd frontend && npm test && npm run typecheck
```

---

## Licença de conteúdo

O conteúdo oficial importado do Wikidot permanece sob CC-BY-SA 3.0.
O conteúdo homebrew e de campanha pertence ao GM.