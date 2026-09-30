# Arquitetura

## Diagrama

```
                         INTERNET
                            │
                            ▼
                    ┌──────────────┐
                    │    NGINX     │  TLS, ACME, proxy
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
           ┌─────────────┐   ┌─────────────┐
           │   NEXT.JS   │   │   DJANGO    │
           │  FRONTEND   │──▶│     API     │
           └─────────────┘   └──────┬──────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │ POSTGRESQL  │  volume: postgres_data
                            └─────────────┘

                         IMPORTER (on demand)
                            │
                     WIKIDOT → PARSER → DATABASE
```

## Componentes

### Backend (`backend/`)

| Arquivo | Responsabilidade |
|---|---|
| `wiki/models.py` | `Page`, `Category`, `Tag`, `PageLink`, `BrokenLink`, `ImportRun` |
| `wiki/rendering.py` | Markdown → HTML sanitizado + extração de links internos |
| `wiki/services.py` | `save_page_with_derived_data()`: render, tags, links |
| `wiki/search.py` | Busca full text (PostgreSQL, ranked) |
| `wiki/serializers.py` | Serializers DRF |
| `wiki/views.py` | ViewSets, `/search`, `/navigation`, `/health` |
| `wiki/permissions.py` | Leitura pública, escrita para staff |
| `wiki/admin.py` | Django Admin para edição interna |

`services.save_page_with_derived_data()` é o **único** caminho de escrita usado
pela API, pelo admin e pelo importer — assim todos produzem o mesmo resultado.

### Frontend (`frontend/`)

```
app/
├── layout.tsx           # root layout
├── page.tsx             # homepage = índice do compêndio
├── [...slug]/page.tsx   # /classes (índice) e /classes/wizard (página)
├── search/page.tsx      # busca com filtros
└── admin/editor/        # editor Markdown + preview
components/
├── layout/              # Header, AppLayout
├── navigation/          # Sidebar, Breadcrumbs
├── pages/               # PageView (template único)
├── dnd/                 # InfoBlock (spell/item header)
├── tables/              # DndTable reutilizável
└── editor/              # MarkdownEditor
lib/
├── types.ts             # tipos TypeScript
├── api.ts               # cliente da API
└── pageTemplates.tsx    # helpers de template (ordinais, info blocks)
```

### Importer (`importer/`)

```
importer/
├── cli.py               # comandos: import, report, list-excluded
└── wikidot/
    ├── client.py        # HTTP com retry/backoff e rate limit
    ├── crawler.py       # descoberta por seeds + filtro de escopo
## Modelo de dados

```
Category (self-referential, sidebar_group = core|campaign)
    │
    └──< Page
            │  ├── source_content   (Markdown editável)
            │  ├── rendered_content (HTML sanitizado)
            │  ├── structured_data  (JSON: campos de spell/item)
            │  ├── visibility       (public | gm_only)
            │  ├── source           (official|wikidot|homebrew|campaign|custom)
            │  ├── search_vector    (tsvector, GIN)
            │  └── parent_page      (subclasse → classe)
            │
            ├──< Tag >──
            ├──< PageLink >── Page   (backlinks)
            └──< BrokenLink          (referência para página inexistente)
```

### Decisões

- **`source` é apenas metadado.** Não cria árvore de categorias separada, não
  gera seção de navegação, não altera o template. Só aparece como rótulo
  discreto na página e como filtro de busca.
- **`visibility` também é metadado.** `gm_only` retorna 404 para anônimos.
- **Busca sem dependências extras.** `SearchVectorField` + GIN do PostgreSQL
  bastam; nada de Elasticsearch.
- **Links como objetos.** `PageLink` permite backlinks reais; `BrokenLink`
  mantém as referências não resolvidas para não perder conteúdo.

## API

| Endpoint | Descrição |
|---|---|
| `GET /api/pages/` | Lista com filtros (`page_type`, `source`, `category`, `visibility`) |
| `GET /api/pages/{slug}/` | Detalhe + tags + pai |
| `POST/PATCH /api/pages/` | Escrita (staff) |
| `GET /api/pages/{slug}/backlinks/` | Referências de entrada |
| `GET /api/pages/{slug}/outlinks/` | Referências de saída |
| `GET /api/pages/{slug}/children/` | Subclasses / páginas filhas |
| `POST /api/pages/preview/` | Preview Markdown (mesmo renderer da página) |
| `GET /api/categories/` · `/tree/` | Categorias e árvore da sidebar |
| `GET /api/tags/` | Tags |
| `GET /api/search?q=&type=&source=&tag=` | Busca full text com filtros |
| `GET /api/navigation` | Payload da sidebar (core + campaign) |
| `GET /api/health` | Healthcheck (verifica o banco) |

Autenticação: JWT em `/api/auth/token/` + sessão Django. Leitura é pública;
escrita exige usuário staff (o GM).

## Decisões visuais

Todos os tokens estão em `frontend/app/globals.css` e derivam da análise da
Fase 0 ([docs/WIKIDOT_ANALYSIS.md](docs/WIKIDOT_ANALYSIS.md)).

| Token | Valor |
|---|---|
| Fonte | Georgia / Times (serifada) |
| Link | `#3b6ea5` |
| Borda | `#c8c8c8` |
| Cabeçalho de tabela | `#f2f2f2` |
| Sidebar | 230px |
| Conteúdo | 940px |
| Corpo | 15px / line-height 1.62 |

`services.save_page_with_derived_data()` garante que a página final e o preview
do editor sejam renderizados pelo **mesmo** código.

## Fora de escopo

Sem marketing, vendas, SEO comercial, analytics, landing pages, SaaS, rede
social, comentários, likes ou perfis públicos.

**Monstros, criaturas, NPCs com stat block e qualquer stat block** não possuem
modelo, template, tipo de página nem rota de importação. A exclusão é feita em
código por `importer/wikidot/filters.py`, em duas camadas independentes
(descoberta + verificação pós-parse), não por exclusão manual.
    ├── filters.py       # EXCLUSÃO de monstros/criaturas/stat blocks
    ├── parser.py        # HTML → Markdown (modular por construct)
    ├── modules.py       # constructs do Wikidot
    ├── converter.py     # → campos de Page (tipo, categoria, estruturado)
    ├── links.py         # normalização de links
    └── assets.py        # download local + reescrita de URLs
```

Fluxo:

```
WIKIDOT → client → crawler (+filters) → parser (+modules) → converter
       → assets → services.save_page_with_derived_data() → PostgreSQL
```