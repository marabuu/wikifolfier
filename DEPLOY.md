# Deploy em VPS

Alvo: uma VPS limpa com **Docker** e **Docker Compose** instalados.
Nada de Python, Node ou PostgreSQL na máquina.

## 1. Preparar a VPS

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y git curl ufw

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker

sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 2. Clonar e configurar

```bash
git clone <seu-repositorio> dnd-compendium
cd dnd-compendium

cp .env.example .env
```

Edite `.env`:

```env
POSTGRES_DB=compendium
POSTGRES_USER=compendium
POSTGRES_PASSWORD=<senha-forte>

DOMAIN=compendium.seudominio.com
ALLOWED_HOSTS=compendium.seudominio.com
CSRF_TRUSTED_ORIGINS=https://compendium.seudominio.com
CORS_ALLOWED_ORIGINS=https://compendium.seudominio.com
NEXT_PUBLIC_API_URL=https://compendium.seudominio.com
DJANGO_DEBUG=False
TZ=America/Sao_Paulo
```

Nada de domínio, senha ou secret fica no código — tudo vem do `.env`.

## 3. Apontar o domínio

No painel do seu provedor, crie um registro **A** para o IP da VPS:

```
compendium.seudominio.com.  A  <IP_DA_VPS>
```

Espere a propagação:

```bash
dig +short compendium.seudominio.com
```

## 4. Deploy

```bash
./scripts/deploy.sh
```

O script gera um `DJANGO_SECRET_KEY` se necessário, constrói as imagens, sobe os
serviços, aplica migrations, cria as categorias e coleta o static.

Ou manualmente:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py seed_categories
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 5. HTTPS (Let's Encrypt)

O serviço `certbot` já está definido no compose de produção. O `nginx.conf`
espera o certificado em `/etc/letsencrypt/live/compendium/`.

```bash
# 1. HTTP precisa responder antes da emissão
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx

# 2. Emissão inicial (webroot)
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm --entrypoint "" certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email seu@email.com \
  --agree-tos --no-eff-email

# 3. Recarregar o nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload

# 4. Subir o serviço de renovação (roda a cada 12h)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d certbot
```

Teste a renovação:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm --entrypoint "" \
  certbot renew --dry-run --webroot -w /var/www/certbot
```

## 6. Verificação

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
curl -I https://$DOMAIN/
curl https://$DOMAIN/api/health
```

## 7. Persistência

| Volume | Conteúdo |
|---|---|
| `postgres_data` | banco de dados |
| `media_data` | imagens importadas (`/app/media`) |
| `static_data` | arquivos estáticos do Django |
| `nginx_letsencrypt` | certificados TLS |
| `certbot_webroot` | desafio ACME |

`docker compose down` **não** apaga o banco. Use `down -v` apenas se quiser
apagar tudo de propósito.

## 8. Backup e restauração

```bash
# Backup (banco + media)
./scripts/backup.sh --media

# Listar
ls -lh backups/

# Restaurar (substitui o conteúdo atual)
./scripts/restore.sh backups/compendium-20240101-120000.dump.gz
```

Backup automático diário via cron:

```cron
0 3 * * * cd /caminho/dnd-compendium && ./scripts/backup.sh --media >> /var/log/compendium-backup.log 2>&1
```

## 9. Atualização

```bash
git pull
./scripts/update.sh     # faz backup, rebuild, migrate e reindexa
```

## 10. Logs

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f postgres
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx
```

Healthchecks já estão configurados em `postgres`, `backend` e `frontend`
(`docker compose ps` mostra `(healthy)`).

## 11. Importar conteúdo

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile tools \
  run --rm importer import --seeds spell:fireball class:wizard --delay 2
```

Detalhes em [IMPORTER.md](IMPORTER.md).

## 12. Checklist

- [ ] `.env` com senhas fortes e domínio correto
- [ ] `DJANGO_DEBUG=False`
- [ ] `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` com o domínio real
- [ ] Certificado emitido e renovação automática ativa
- [ ] Backup automático configurado e um restore testado
- [ ] `createsuperuser` criado