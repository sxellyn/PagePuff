# 🌸 PagePuff

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-%2300C7B7.svg?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-%2300758F.svg?logo=mysql&logoColor=white)
![React](https://img.shields.io/badge/React-%2361DAFB.svg?logo=react&logoColor=white)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-fcd5ce)

---

**PagePuff** é uma biblioteca pessoal online, o sistema oferece recomendações personalizadas com base nos gostos e hábitos de leitura de cada usuário. Mais do que uma simples biblioteca online, o PagePuff é um ✧ cantinho acolhedor ✧. 

Nosso sistema de recomendação combina algoritmos de **K-Means clustering** com **content-based filtering** para oferecer sugestões ✨

---

## 🧩 Tecnologias Utilizadas

- 🐍 **FastAPI (Python)** — back-end moderno, leve e rápido.
- 🐬 **MySQL** — banco de dados relacional robusto para armazenar tudo com carinho.
- 🌼 **SQLAlchemy** — ORM elegante para conectar o back-end ao banco de dados.
- 💠 **React** — front-end interativo, suave e responsivo.
- 🍡 **K-Means + Content-Based Filtering** — sistema de recomendação híbrido, feito sob medida para cada leitor.

---

## 🎀 Funcionalidades Planejadas

- ✨ Cadastro e autenticação de usuários
- 📚 Biblioteca pessoal (lidos, lendo, favoritos)
- 🌟 Avaliação de obras e marcação por tags
- 💌 Recomendação personalizada de mangás/manhwas
- 🔍 Busca por gênero, autor, título, status e mais
- 🎨 Interface super fofa e fácil de usar

---

## ✨ Como Rodar a Aplicação

### Pré-requisitos

- [Docker](https://www.docker.com/get-started) e Docker Compose instalados
- [Node.js](https://nodejs.org/) (versão 18 ou superior) e npm para o frontend

### Passo 1: Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd PagePuff
```

### Passo 2: Configurar Variáveis de Ambiente

#### Backend

Crie os arquivos `.env` nos seguintes diretórios (ou copie dos exemplos existentes):

**`backend/user_service/.env`**
```env
DATABASE_URL=mysql+pymysql://root:root@mysql/pagepuff
SECRET_KEY=MEUDEUSDOCEU
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**`backend/manga_service/.env`**
```env
DATABASE_URL=mysql+pymysql://root:root@mysql/pagepuff
```

**`backend/recom_service/.env`**
```env
DATABASE_URL=mysql+pymysql://root:root@mysql/pagepuff
RECOMMENDER_MODEL_PATH=./app/recom_service/model.pkl
```

**`backend/gateway/.env`**
```env
MANGA_SERVICE_URL=http://manga_service:8000
USER_SERVICE_URL=http://user_service:8000
RECOM_SERVICE_URL=http://recom_service:8000
ALLOWED_ORIGINS=["http://localhost:3000"]
```

#### Frontend

**`frontend/.env`**
```env
VITE_API_URL=http://localhost:8081
```

### Passo 3: Iniciar os Serviços Backend

No diretório `backend`, execute:

```bash
docker-compose up --build
```

Isso irá:
- Criar e iniciar o banco de dados MySQL
- Inicializar as tabelas e popular com dados iniciais
- Iniciar todos os microserviços (user_service, manga_service, recom_service)
- Iniciar o API Gateway na porta 8081

### Passo 4: Iniciar o Frontend

Em um novo terminal, no diretório `frontend`, execute:

```bash
npm install
npm run dev
```

O frontend estará disponível em `http://localhost:3000`

### Contas de Demonstração

Após subir o backend, use estas credenciais para testar login, favoritos e recomendações:

| Usuário | Senha | Perfil |
|---------|-------|--------|
| `demo` | `demo123` | Conta principal — favoritos de ação/aventura |
| `demo_user_1` | `demo123` | Fã de ação |
| `demo_user_2` | `demo123` | Fã de romance |
| `demo_user_3` | `demo123` | Fã de comédia |
| `demo_user_4` | `demo123` | Fã de horror/drama |
| `demo_user_5` | `demo123` | Fã de romance clássico |
| `demo_user_6` | `demo123` | Fã de ação clássica |

Os dados ficam em `backend/sql/populate_demo.sql` (30 mangás, 7 usuários e favoritos fixos).

### Acessos aos Serviços

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8081
- **User Service**: http://localhost:8000
- **Manga Service**: http://localhost:8001
- **Recommendation Service**: http://localhost:8003
- **MySQL**: localhost:3306 (usuário: `root`, senha: `root`, database: `pagepuff`)

### Parar os Serviços

Para parar todos os serviços:

```bash
# No diretório backend
docker-compose down
```

Para parar e remover volumes (limpar banco de dados):

```bash
docker-compose down -v
```

## 🌱 Em desenvolvimento...

O PagePuff está sendo construído com muito carinho e cuidado por quem ama mangás! 💕🍥

---
