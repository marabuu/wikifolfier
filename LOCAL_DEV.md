# Desenvolvimento local (sem Docker)

Guia para rodar o compêndio direto na máquina, Useful enquanto você itera.
Docker continua sendo o caminho de deploy — veja [DEPLOY.md](DEPLOY.md).

---

## 1. Pré-requisitos

| Item | Status |
|---|---|
| Python 3.12+ | ✅ instalado (usei 3.13) |
| Node 20+ | ✅ instalado (usei 22) |
| PostgreSQL 16 | ⚠️ **precisa instalar** |

O PostgreSQL é obrigatório porque a busca usa `tsvector` + índice GIN,
que são recursos do Postgres e não existem em SQLite. Se preferir evitar a
instalação, use Docker só para o banco.

### Instalando o PostgreSQL no Windows

Baixe em <https://www.postgresql.org/download/windows/> (ou
`winget install PostgreSQL.PostgreSQL.16`). No instalador:

- porta `5432`
- senha do superusuário: escolha uma e anote

Depois crie o usuário e o banco:

```sql
CREATE USER compendium WITH PASSWORD 'compendium_local';
CREATE DATABASE compendium OWNER compendium;
```

---

## 2. Setup único

```bash
cd E:\dev\wikifolfier2
scripts\local-setup.cmd
```

Esse script:
1. cria `.venv` (se ainda não existir);
2. instala `backend/requirements.txt`;
3. cria `.env` a partir de `.env.example.local`;
4. roda as migrations;
5. roda `seed_categories`.

Já rodei os passos 1–3 aqui; só falta o Postgres para o 4.

---

## 3. Subir

```bash
scripts\local-start.cmd
```

Abre duas janelas:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api |
| Health | http://localhost:8000/api/health |
| Admin | http://localhost:8000/admin |

Para parar: `scripts\local-stop.cmd` (ou feche as janelas).

---

## 4. Comandos úteis

```bash
# Verificar o ambiente
.venv\Scripts\python.exe scripts\local_doctor.py

# Shell do Django
cd backend && ..\.venv\Scripts\python.exe manage.py shell

# Criar o usuário GM
cd backend && ..\.venv\Scripts\python.exe manage.py createsuperuser

# Conteúdo de exemplo (Wizard, Rune Mage, Fireball, Rune Blast,_locations)
cd backend && ..\.venv\Scripts\python.exe manage.py seed_demo

# Testes
cd backend && ..\.venv\Scripts\python.exe manage.py test wiki
.venv\Scripts\python.exe importer\tests.py
cd frontend && npm test

# Importar do Wikidot (precisa do backend rodando? não — usa o banco direto)
.venv\Scripts\python.exe -m importer.cli import --seeds spell:fireball class:wizard
.venv\Scripts\python.exe -m importer.cli list-excluded
```

---

## Nota sobre GitHub Pages

Você mencionou GitHub Pages. **Não vai funcionar para este projeto**, e é
importante entender por quê antes de investir tempo nisso:

- GitHub Pages serve **apenas arquivos estáticos**. Não roda Node, nem Python,
  nem banco de dados.
- O compêndio precisa de backend Django (API REST), busca full-text e
  escrita de páginas — nada disso existe como arquivo estático.
- O `output: 'standalone'` do Next.js gera um servidor Node, que o Pages não
  executa.

Se a ideia é só ter uma URL pública e barata, as alternativas que funcionam
com esta arquitetura são:

| Opção | Serve frontend | Serve backend | Custo |
|---|---|---|---|
| **VPS** (já documentado) | ✅ | ✅ | ~US$ 4/mês |
| Render / Railway | ✅ | ✅ | free tier limitado |
| Fly.io | ✅ | ✅ | free tier limitado |
| GitHub Pages | ✅ | ❌ | grátis |
| Netlify/Vercel | ✅ (grátis) | ❌ (Python) | — |

**Recomendação:** siga com a VPS — ela é a única opção que mantém o compêndio
completo (backend + banco + busca + editor) exatamente como está, sem
reescrever a arquitetura. Se o custo for o problema, Render/Fly.io free tier
dá conta para uso pessoal de campanha.

Se quiser, posso deixar o frontend com `output: 'export'` (build estático) para
ele rodar no Pages **em modo somente-leitura**, com os dados exportados como
JSON no momento do build. Mas isso implicaria: sem busca, sem editor, sem
conteúdo novo entre builds. Me avise se quiser essa via.