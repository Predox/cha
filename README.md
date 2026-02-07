# Site de Chá de Panela (Catálogo + Reserva Anônima)

Este projeto implementa:

- Login por **código (OTP)**: SMS (Twilio) ou **e-mail** (fallback)
- Login por **senha** (opcional)
- **Painel do casal** (admin do evento) sem acesso a quem reservou
- **Reserva de presentes** (evita presente duplicado)
- Reserva com **mensagem anônima** (sem identificação)
- **Contador de dias** até a data do evento
- **Percentual** de presentes reservados (barra de progresso)
- **Catálogo** com imagem, título e descrição
- **Personalização de cores** pelo painel (aplica em todo o site)

> Importante: o painel do casal **não mostra** quem reservou cada presente.  
> Existe um admin técnico opcional em `/django-admin/` (use apenas para manutenção).

---

## Stack

- Backend: **Python + Django**
- Front: **Django Templates + Bootstrap 5 + FontAwesome**
- Banco: SQLite (dev) / Postgres (Railway)
- Uploads: `MEDIA_ROOT` (recomendado usar Volume no Railway)
- Static: Whitenoise

---

## 1) Rodar localmente

### Pré-requisitos
- Python 3.11+ (recomendado 3.12)
- pip

### Passo a passo

1. Clone/copiar a pasta do projeto
2. Crie e ative um venv (opcional, mas recomendado)
3. Instale dependências:

```bash
pip install -r requirements.txt
```

4. Crie um `.env` com base no `.env.example` (opcional em dev, mas recomendado).

5. Migrações:

```bash
python manage.py migrate
```

6. Crie um superusuário (opcional, apenas se você quiser usar `/django-admin/`):

```bash
python manage.py createsuperuser
```

7. Rode o servidor:

```bash
python manage.py runserver
```

Acesse:
- Login por código: `http://127.0.0.1:8000/login/`

---

## 2) Setup inicial do casal (uma única vez)

Para facilitar o deploy, há um setup inicial protegido por token.

1. Defina `SETUP_TOKEN` no `.env` (ou variáveis do Railway)
2. Acesse:

```
/setup/<SETUP_TOKEN>/
```

Exemplo (local):
```
http://127.0.0.1:8000/setup/SEU_TOKEN/
```

3. Preencha:
- Título do site
- Data do evento
- Telefone/e-mail do casal
- Senha (opcional)

Depois do setup, o casal poderá entrar e acessar o painel em:
- `/painel/`

---

## 3) Login por código (SMS / e-mail)

### Opção A: SMS (Twilio) – recomendado se você quiser SMS
Configure no ambiente:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`

> O usuário informa o telefone e recebe um código por SMS.

### Opção B: E-mail (fallback)
Configure SMTP no ambiente:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

> Se o SMS não estiver configurado, o usuário deve informar um e-mail para receber o código.

---

## 4) Como funciona a reserva (regras)

- Um presente pode ser reservado por **apenas uma pessoa** por vez.
- Um usuário pode reservar **um ou mais** presentes.
- O site exibe alerta quando o usuário reservou mais de um presente, para evitar bloqueio involuntário do catálogo.
- No momento da reserva, o usuário pode deixar uma **mensagem anônima** (sem nome).

---

## 5) Painel do casal (admin do evento)

URL: `/painel/`

Funcionalidades:
- Ver progresso (% reservados)
- Ver lista de presentes reservados/ disponíveis (**sem mostrar quem reservou**)
- Criar/editar/excluir presentes do catálogo
  - **Edição/exclusão só é permitida** para presentes que **ainda não foram reservados**
- Personalização de cores do site
- Ver mensagens anônimas deixadas pelos convidados

---

## 6) Deploy no Railway (recomendado)

### Passo a passo (caminho mais curto)

1. Suba este projeto para um repositório (GitHub/GitLab).
2. No Railway:
   - Create New → Deploy from GitHub Repo
3. Adicione um Postgres:
   - New → Database → Postgres
   - O Railway injeta `DATABASE_URL` automaticamente.

4. Variáveis de ambiente mínimas:
   - `SECRET_KEY` (obrigatório)
   - `DEBUG=0`
   - `ALLOWED_HOSTS=SEU_DOMINIO_RAILWAY`
   - `SETUP_TOKEN=um-token-longo`
   - `CSRF_TRUSTED_ORIGINS=https://SEU_DOMINIO_RAILWAY`

5. Uploads (imagens):
   - Crie um **Volume** no Railway (Add → Volume)
   - Monte em `/app/media` (ou outro caminho)
   - O Railway expõe `RAILWAY_VOLUME_MOUNT_PATH` automaticamente; você pode usar isso.
   - Defina `MEDIA_ROOT=/app/media` (ou `MEDIA_ROOT=${RAILWAY_VOLUME_MOUNT_PATH}`)

6. Start Command
O Railway atualmente usa **Railpack** (Procfile ainda funciona, mas o recomendado é configurar o Start Command nas Settings).

- Start Command sugerido: `bash scripts/start.sh`
- (Opcional) O projeto também inclui `Procfile` com `web: bash scripts/start.sh`

Esse script faz:
- `python manage.py migrate --noinput`
- `python manage.py collectstatic --noinput`
- inicia o Gunicorn

7. Execute o setup inicial:
   - Acesse `/setup/<SETUP_TOKEN>/`
   - Crie a conta do casal e defina a data do evento.

---

## 7) Segurança importante

- **Não dê acesso ao casal ao `/django-admin/`**.  
  O painel do casal é `/painel/` e é **anônimo**.
- Em produção, mantenha `DEBUG=0`.
- Use um `SECRET_KEY` forte.
- Configure `CSRF_TRUSTED_ORIGINS` com o domínio do Railway.

---

## 8) Personalizações rápidas

- Você pode alterar textos e layout nos templates em `templates/`
- CSS em `static/css/styles.css`
- Ícones são do FontAwesome (CDN)

---

## Suporte

Se você quiser que eu adapte:
- modo "somente SMS" (obrigatório),
- campos extras (categoria do presente, link de compra),
- ou um modo público (catálogo sem login),

é só me pedir.
