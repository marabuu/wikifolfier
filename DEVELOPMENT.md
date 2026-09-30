# Desenvolvimento

## Ambiente com Docker (recomendado)

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
docker compose exec backend python manage.py seed_categories
docker compose exec backend python manage.py seed_demo
```

---

## Backend

```bash
# Shell
docker compose exec backend bash

# Testes
docker compose exec backend python manage.py test wiki

# Só os testes de rendering (não exigem banco)
docker compose exec backend python manage.py test wiki.tests.RenderingTests

# Migrations
docker compose exec backend python manage.py makemigrations wiki
docker compose exec backend python manage.py migrate

# Reindexar busca
docker compose exec backend python manage.py reindex
```

### Escrever uma página

Sempre use `save_page_with_derived_data()` — ele renderiza o Markdown, sincroniza
as tags e reconstrói `PageLink` / `BrokenLink`:

```python
from wiki.models import Category, Page
from wiki.services import save_page_with_derived_data

page = Page(title="Rune Mage", page_type="class", source="homebrew")
page.category = Category.objects.get(slug="classes")
page.source_content = """## Hit Points

Hit Dice: 1d8 por nível
"""

save_page_with_derived_data(page, ["rune", "caster", "homebrew"])
```

### Fields estruturados

Spells e itens usam `structured_data` (JSON):

```python
page.structured_data = {
    "level": 2, "school": "Evocation",
    "casting_time": "1 action", "range": "60 feet",
    "components": "V, M (a carved rune)", "duration": "Instantaneous",
    "classes": ["Rune Mage"],
}
```

Itens:

```python
page.structured_data = {
    "item_type": "Wondrous item", "rarity": "Rare", "requires_attunement": True,
}
```

### Ligar uma subclasse à classe

```python
subclass.parent_page = Page.objects.get(slug="rune-mage")
```

O `PageView` usa isso para listar "Subclasses" automaticamente.

---

## Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:3000
npm run typecheck
npm test
npm run build
```

O frontend fala com a API via `NEXT_PUBLIC_API_URL`. Em desenvolvimento local
aponte para `http://localhost:8000`.

### Adicionar uma rota de índice

O catch-all `app/[...slug]/page.tsx` resolve:

- `/classes` → índice da categoria;
- `/classes/wizard` → página individual.

Para rotas especiais (busca, editor) crie uma pasta própria em `app/`.

---

## Criando conteúdo homebrew

1. Crie a página em `/admin/editor` ou pelo Django Admin.
2. Escolha a **categoria** (`Classes`, `Spells`, ...) — o homebrew entra junto
   do conteúdo oficial.
3. Escolha o **source** (`homebrew`) — é só metadado.
4. Escreva em Markdown.
5. Use `[[Nome da Página]]`? Não — use `[Nome da Página](/slug-da-pagina)`.
   O backend converte isso em `PageLink` e gera backlinks automaticamente.

Links para páginas que ainda não existem viram `BrokenLink` e são reportados
pelo importer, em vez de sumir.

---

## Acessibilidade

- HTML semântico (`header`, `nav`, `main`, `article`, `footer`).
- `<nav aria-label>` na sidebar e nos breadcrumbs.
- Foco visível via `:focus-visible`.
- Sidebar vira menu em telas menores.
- Rotas dinâmicas (`export const dynamic = 'force-dynamic'`).

---

## Convenções

- Português no texto de interface; inglês nos identificadores.
- Slugs em `kebab-case` (`rune-mage`, `terra-das-estranhezas`).
- Nada hardcoded: domínio, senhas e URLs vêm do `.env`.
- Todo novo campo de `Page` precisa de migration.