# Fase 0 — Análise do dnd5e.wikidot.com

Objetivo: extrair os padrões visuais e estruturais do site de referência **antes**
de escrever o frontend definitivo, para que a interface já nasça resemble o compêndio
e não um dashboard genérico.

## 1. Estrutura do site de referência

```
┌───────────────────────────────────────────────────────────────┐
│ HEADER (barra superior escura, links de conta/utilidades)     │
├──────────────┬────────────────────────────────────────────────┤
│ SIDEBAR      │ MAIN                                            │
│              │  Title bar (nome da página + subtítulo/tag)     │
│  Site Nav    │  Breadcrumbs                                    │
│  (lista de   │  Conteúdo (texto, tabelas, info boxes)         │
│   páginas)   │  Índice / links relacionados no fim            │
│              │  Footer (categorias, licença,wikidot)           │
└──────────────┴────────────────────────────────────────────────┘
```

Elementos canônicos observados:

| Elemento | Comportamento no Wikidot |
|---|---|
| Header | Branco, fino, com logo à esquerda e links pequenos à direita. |
| Sidebar | Coluna fixa à esquerda, largura ~ 200–240px, links em lista simples, sem cards. |
| Breadcrumb | Linha pequena e discreta acima do título (`D&D 5e / Wizard`). |
| Título | H1 grande, centralizado ou à esquerda, com subtítulo pequeno ("Wizards" para Wizard). |
| Corpo | Texto justificado, parágrafos curtos, listas, tabelas largas com bordas. |
| Índice | Box ao final "Spell Lists", "Subclasses", "Related Pages" — listas de links internos. |
| Footer | Bloco de categorias + licença CC-BY-SA, links pequenos e cinzas. |
| Busca | Busca no topo, resultados em lista de títulos + snippets. |

## 2. Página de classe (ex.: Wizard)

1. Título + subtítulo descritivo.
2. Parágrafo introdutório.
3. **Tabela de progressão de nível** — tabela densa, cabeçalho fixo, muitas colunas
   numéricas (nível, bônus de proficiência, features, cantrips, slots por nível).
4. Seção "Class Features" com H2/H3.
5. Blocos curtos de texto (Hit Points, Proficiencies, Equipment).
6. Ao final: lista de subclasses com a fonte de cada uma (`Player's Handbook`,
   `Tasha's Cauldron of Everything`, ...).

## 3. Página de spell (ex.: Fireball)

```
FIREBALL
3rd-level evocation

Casting Time: 1 action
Range: 150 feet
Components: V, S, M (a tiny ball of bat guano and sulfur)
Duration: Instantaneous
```

- A linha "Nth-level <school>" fica logo abaixo do título.
- Os campos (Casting Time/Range/Components/Duration) são um bloco de info denso,
  alinhado à esquerda, com rótulos em negrito.
- Corpo: descrição em prosa.
- Seção "At Higher Levels." quando aplicável.
- Seção "Spell Lists." com links para as classes.

## 4. Tabelas

- Cabeçalho com fundo cinza claro (`#f0f0f0`-ish) e texto em negrito.
- Bordas finas em todas as células.
- Centralização para colunas numéricas; alinhamento à esquerda para texto.
- `border-collapse: collapse`, cellpadding pequeno (~4px).
- Tabelas longas rolam dentro da largura do conteúdo, nunca estouram o layout.

## 5. Info boxes / blocos informativos

- Fundo levemente distinto do branco da página.
- Borda fina.
- Título em negrito dentro do box.
- Usados para "Casting Time", "Requirements", "Triggers", "Downtime".

## 6. Tipografia

- Serifada nos títulos e no corpo (Wikidot usa Georgia/serif padrão do tema).
- Corpo ~ 14–15px, `line-height` ~ 1.6.
- H1 ~ 28–32px, H2 ~ 22px, H3 ~ 17px.
- Links: azul, sublinhados no hover.
- Nomes de subclasses/spells aparecem como links internos.

## 7. Decisões de design derivadas (implementadas no frontend)

Tokens CSS em `frontend/app/globals.css`:

- `--font-serif: Georgia, 'Times New Roman', serif`
- `--color-link: #3b6ea5` (azul Wikidot)
- `--color-border: #c8c8c8`
- `--color-table-head: #f2f2f2`
- `--color-page-bg: #ffffff`
- largura de conteúdo ~ 900px, sidebar 230px.

Regra de ouro: **nenhum card, nenhum gradiente, nenhuma sombra suave, nenhum botão
primário grande**. Tudo é texto, link, tabela e caixa com borda.

## 8. O que NÃO reproduzir do Wikidot

- Login / conta / assinatura / "Report a bug" / fórum / menu do Wikidot.com.
- Bloco de edição de páginas (`Click here to edit contents of this page`).
- Publicidade e rodapé do Wikidot.com.

O que reproduzir: **a lógica visual de compêndio** — sidebar de categorias,
breadcrumbs, título, tabelas, info boxes, índice de links relacionados, footer.