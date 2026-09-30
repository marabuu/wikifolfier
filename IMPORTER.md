# Importer do Wikidot

Importa conteúdo D&D 2024 do
[dnd2024.wikidot.com](https://dnd2024.wikidot.com/) para o compêndio local.

**Monstros, criaturas e stat blocks são excluídos em código** — nunca por
exclusão manual.

> **Qual wiki?** Existem dois: `dnd5e.wikidot.com` (regras de **2014**, 2666
> páginas) e `dnd2024.wikidot.com` (**2024**, o correto para este projeto).
> Verifiquei o corpo das páginas do `dnd5e` e **não há nenhuma menção a 2024**
> — é conteúdo 2014. O importer usa `dnd2024` como padrão. Para importar o
> 2014, use `--base-url https://dnd5e.wikidot.com`.

---

## Uso

```bash
# 1. Descobrir as páginas (sem buscar cada página, sem banco)
python -m importer.cli plan

# 2. Testar o parsing numa amostra (sem banco)
python -m importer.cli dry-run --sample 40

# 3. Gravar no banco
python -m importer.cli import

# Ver o que seria excluído
python -m importer.cli list-excluded
```

### Opções

| Flag | Descrição |
|---|---|
| `--base-url` | Origem (padrão `dnd2024.wikidot.com`) |
| `--delay` | Segundos entre requisições (padrão `1.0`) |
| `--sample N` | Processa só as N primeiras (dry-run) |
| `--show N` | Quantas páginas detalhar na saída |
| `--indexes ...` | Páginas-índice a usar na descoberta |
| `--no-seeds` | Não seguir as páginas de classe |
| `--sitemap` | Descoberta por sitemap (funciona no wiki 2014) |
| `--save FILE` | Salva a lista de caminhos em escopo |

---

## Escopo atual (medido no site 2024)

```
Discovered : 1351
In scope   : 1341
Excluded   : 10

  magic_item             466
  spell                  464
  feat                   206
  background              71
  species                 25
  subclass                75
  class                   13
  equipment               11
```

---

## Descoberta

O wiki 2024 **não tem sitemap utilizável** (retorna HTTP 503), então a
descoberta usa os próprios índices do site, que são autoritativos:

| Índice | Conteúdo |
|---|---|
| `spell` | todas as spells |
| `feat:all` | todos os feats |
| `background:all` | todos os backgrounds |
| `species:all` | todas as species |
| `magic-item:all` | todos os itens mágicos |
| `class:all` | todas as classes |
| `equipment:all` | sub-índices de equipamento |

As 13 páginas `<classe>:main` são usadas como seeds para pegar as subclasses.

No wiki 2014 o sitemap funciona e é usado automaticamente com `--sitemap`.

---

## Escopo

### Importado

classes, subclasses, species, backgrounds, feats, spells, magic items,
equipment, weapons, armor, adventuring gear, rules e conditions.

### Excluído (em código, duas camadas)

`importer/wikidot/filters.py`:

1. **Namespaces de criatura**: `creature`, `monster`, `bestiary`, `stat`,
   `statblock`, `npcstatblock`, `encounter`, `cult`, `appendixmonster`.
2. **Padrões de título**: `Statblock`, `(Monster)`, `Appendix Z: ...`,
   `Creature Type ...`, `Large Dragon ...`.
3. **Chrome do site**: `system`, `help`, `legal`, `forum`, `css`, `nav`.
4. **Namespace desconhecido** é descartado por padrão (deny-by-default).
5. **Rechecagem pós-parse** no CLI, antes de gravar.

`EXCLUDED_PAGE_TYPES = {"monster", "creature", "stat_block"}` não existe como
`PageType` — não há modelo, template ou rota para esses tipos.

```bash
$ python -m importer.cli list-excluded
EXCLUDED  creature:adult-red-dragon        creature namespace 'creature'
EXCLUDED  stat:commoner                   creature namespace 'stat'
IMPORTED  spell:fireball                   spell
IMPORTED  wizard                           class
IMPORTED  artificer:alchemist              subclass
```

---

## Arquitetura

```
WIKIDOT (dnd2024)
   ↓
discovery.py   índices do site (o sitemap 2024 retorna 503)
   ↓
extract.py     isola #page-content, remove chrome/ads/scripts, extrai título e tags
   ↓
filters.py     escopo + exclusão de monstros
   ↓
parser.py      HTML → Markdown (um handler por construct)
modules.py     constructs do Wikidot
   ↓
converter.py   → Page: tipo, categoria, structured_data (spell/item)
   ↓
links.py assets.py
   ↓
services.save_page_with_derived_data() → PostgreSQL
```

### Parsing

Um handler por construct: `_table`, `_list`, `_heading`, `_paragraph`,
`_block_quote`, `_cell`. Nada de regex gigante.

Detalhes verificados em páginas reais:

- **Artigo isolado**: `#page-content` → fim em `#action-area` / `.page-tags`.
- **Ads e JS removidos**: o site injeta `nitroAds` e `$j(...)` fora do artigo.
- **Spell 2024**: `*Level 3 Evocation (Sorcerer, Wizard)*` +
  `**Casting Time:** Action` etc. → `structured_data`.
- **Spell 2014**: `*3rd-level evocation*` — ambos os formatos são suportados.
- **Tabelas** com `<th colspan>` são achatadas em uma linha de cabeçalho.
- **Ênfase preservada**: `*itálico*` seguido de `**negrito**` não é colapsado.

### Conteúdo desconhecido

Construct não suportado gera `WARNING: unsupported Wikidot construct` e o texto
original é preservado em `ParseResult.warnings`, contabilizado em
`unknown_constructs`.

---

## Idempotência

A importação é feita por `slug`. Rodar duas vezes atualiza em vez de duplicar:

```bash
python -m importer.cli import   # 1ª: pages_imported: 1341
python -m importer.cli import   # 2ª: pages_updated: 1341
```

Páginas com menos de 120 caracteres são puladas com aviso.

---

## Assets

Imagens são baixadas para `MEDIA_ROOT/wikidot/` e as URLs são reescritas para
`/media/wikidot/...`. Após a importação o sistema não depende do Wikidot.

---

## Boas práticas

- Use `--delay` respeitoso (1.0 ou mais). O site responde 503 se abuso.
- Rode `plan` e `dry-run` antes de gravar.
- Reimportar atualiza `source_content`, mas não sobrescreve conteúdo homebrew
  (source diferente não colide por slug).