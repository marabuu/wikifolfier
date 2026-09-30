# Importer do Wikidot

Importa conteúdo D&D 2024 do [dnd5e.wikidot.com](https://dnd5e.wikidot.com/) para
o compêndio local.

**Monstros, criaturas e stat blocks são excluídos em código** — nunca por
exclusão manual.

---

## Uso

```bash
# Dentro do container (produção)
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile tools \
  run --rm importer import

# Local, com seeds explícitas
python -m importer.cli import --seeds spell:fireball class:wizard

# Só ver o que seria excluído
python -m importer.cli list-excluded

# Último relatório
python -m importer.cli report
```

### Opções

| Flag | Descrição |
|---|---|
| `--seeds` | Páginas seed (ex.: `spell:fireball`, `class:wizard`) |
| `--base-url` | Origem (default `https://dnd5e.wikidot.com`) |
| `--delay` | Segundos entre requisições (default `1.0`) |
| `--max-pages` | Limite de páginas importadas |
| `--no-assets` | Não baixa imagens |
| `--report-path` | Onde gravar o JSON de relatório |
| `--verbose` | Log em nível DEBUG |

---

## Escopo

### Importado

classes, subclasses, species, backgrounds, feats, spells, magic items,
equipment, weapons, armor, adventuring gear, rules, conditions e demais páginas
relevantes que **não** sejam criaturas.

### Excluído (em código)

`importer/wikidot/filters.py` aplica duas camadas independentes:

1. **Namespace bloqueado** — `creature:`, `monster:`, `bestiary:`, `stat:`, `statblock:`,
   `npcstatblock:`, `srdmonster:`, `appendixmonster:`.
2. **Padrões de título** — `Appendix Z: ...`, `... (Monster)`,
   `... Statblock`, `Creature Type ...`.
3. **Namespace desconhecido** é descartado, a menos que o título seja
   claramente de regras (`Conditions`, `Combat`, `Movement`, ...).
4. **Verificação pós-parse** no CLI: mesmo que uma regra escape, a página é
   rechecada antes de ser salva.

Além disso, `EXCLUDED_PAGE_TYPES = {"monster", "creature", "stat_block"}` não
existe como `PageType` — não há modelo, template ou rota para esses tipos.

Verifique a configuração:

```bash
$ python -m importer.cli list-excluded
EXCLUDED  creature:adult-red-dragon         excluded namespace 'creature'
EXCLUDED  monster:goblin                   excluded namespace 'monster'
EXCLUDED  stat:commoner                    excluded namespace 'stat'
EXCLUDED  appendix:zombies                 excluded namespace 'appendix'
IMPORTED  spell:fireball
IMPORTED  class:wizard
IMPORTED  feat:alert
IMPORTED  item:bag-of-holding
```

---

## Arquitetura

```
WIKIDOT
   ↓
client.py     HTTP com retry, backoff e rate limit
   ↓
crawler.py    Descoberta a partir de seeds, seguindo links
   ↓
filters.py    Exclusão de monstros/criaturas/stat blocks
   ↓
parser.py     HTML → Markdown (um handler por construct)
modules.py    Constructs do Wikidot (spell, infobox, featured, footnote)
   ↓
converter.py  Markdown + dados estruturados → campos de Page
   ↓
assets.py     Download local e reescrita de URLs
links.py      Normalização de links internos
   ↓
services.save_page_with_derived_data()
   ↓
PostgreSQL
```

O parser **não** é uma coleção gigante de regex: cada construct tem seu próprio
handler (`_table_to_markdown`, `_list_to_markdown`, `_heading_to_markdown`,
`_cell_text`, ...).

---

## Conteúdo desconhecido

Nada é descartado silenciosamente. Um construct não suportado gera:

```
WARNING: unsupported Wikidot construct -> {"module":"..."}
```

e o texto original é preservado em `ParseResult.warnings`, contabilizado em
`unknown_constructs` no relatório.

---

## Idempotência

A importação é feita por `slug`. Rodar duas vezes:

```bash
python -m importer.cli import   # 1ª: pages_imported: 830
python -m importer.cli import   # 2ª: pages_updated: 830
```

Nunca cria duplicatas. Páginas finas (<200 caracteres) são puladas com aviso.

---

## Assets

As imagens são baixadas para `MEDIA_ROOT/wikidot/` e as URLs no Markdown são
reescritas para `/media/wikidot/...`. Após a importação, o sistema **não depende
do Wikidot** em uso normal.

---

## Relatório

```bash
=== Import Report ===
Pages Discovered: 1200
Pages In Scope: 850
Pages Excluded: 350
Pages Imported: 830
Pages Updated: 20
Assets Downloaded: 240
Broken Links: 8
Unknown Constructs: 5
Warnings: 13

Report written to import_report.json (ImportRun #1)
```

O relatório completo (incluindo exemplos de páginas excluídas e a lista de
warnings) é gravado no JSON e também em `ImportRun.report` no banco.

Consulte depois com:

```bash
python -m importer.cli report
GET /api/broken-links/
```

---

## Boas práticas

- Use `--delay` respeitoso (1.0 ou mais). O Wikidot é um serviço gratuito.
- Rode a importação inicial uma vez; depois use `seed_demo` / editor para o
  conteúdo da campanha.
- Reimportar atualiza `source_content`, mas **não** sobrescreve páginas
  homebrew (source diferente não colide por slug).
- Confira `Broken Links` no relatório e crie as páginas que faltam.