# CONTRU ESTOQUE — Sistema Corporativo de Gestão de Estoque

O **CONTRU ESTOQUE** é uma plataforma corporativa completa de Gestão de Estoque para médias empresas, com foco inicial em materiais de inclusão e construção civil, e arquitetura modular preparada para publicação na web e futura integração com PDV (Ponto de Venda).

---

## 🚀 Como Executar Localmente

### 1. Pré-requisitos
- Python 3.10 ou superior
- Dependências instaladas (Flask, SQLAlchemy, psycopg2-binary, python-dotenv, openpyxl, pandas)

### 2. Inicialização Imediata
Abra o terminal no diretório do projeto e execute:

```bash
python run.py
```

O servidor iniciará automaticamente na porta `5000`. Acesse no seu navegador:
👉 **[http://localhost:5000](http://localhost:5000)**

> [!NOTE]
> Na primeira execução, o sistema detecta se o banco está vazio e injeta automaticamente mais de 25 materiais reais (pisos táteis, barras de apoio inox, placas braille, cimentos, tubos, tintas, disjuntores, EPIs), movimentações históricas, reajustes de preços e perfis de usuários para demonstração imediata.

---

## ☁️ Conectando ao Supabase (PostgreSQL em Nuvem)

O **CONTRU ESTOQUE** foi projetado com suporte nativo a banco de dados em nuvem via **SQLAlchemy + PostgreSQL** (compatível com a camada gratuita do **Supabase**, **Neon** ou **Render**):

### Passo a Passo para Conectar ao Supabase Gratuito:
1. Acesse [https://supabase.com](https://supabase.com) e crie uma conta gratuita.
2. Clique em **"New Project"**, nomeie como `contru-estoque` e defina uma senha segura para o banco.
3. No painel do projeto, vá em:
   - **Project Settings** (ícone de engrenagem) &rarr; **Database** &rarr; Seção **Connection String** &rarr; Selecione a aba **URI**.
4. Copie a URI e cole no arquivo `.env` do seu projeto:

```env
DATABASE_URL=postgresql://postgres.[SEU-PROJECT-REF]:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

5. Execute novamente:
```bash
python seed_data.py
```
*Todas as tabelas, índices e dados demonstrativos serão criados instantaneamente no seu Supabase!*

> [!TIP]
> Caso prefira executar o script DDL diretamente no painel web do Supabase, utilize o arquivo `supabase_schema.sql` fornecido na raiz do projeto.

---

## 🌐 Publicação na Web (Deploy Gratuito no Render ou Railway)

O projeto já inclui `Procfile` e `requirements.txt` prontos para deploy:

### Deploy no Render (Plano Gratuito):
1. Suba o código para um repositório no GitHub.
2. No [Render.com](https://render.com), clique em **New +** &rarr; **Web Service**.
3. Conecte seu repositório.
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Na aba **Environment Variables**, adicione:
   - `DATABASE_URL` = sua connection string do Supabase.
   - `PYTHON_VERSION` = `3.13.2`
6. Clique em **Deploy Web Service**. Sua aplicação estará online com certificado SSL automático!

---

## 🛡️ Regras de Negócio Implementadas

1. **Movimentação Obrigatória**: O saldo físico nunca é alterado diretamente sem gerar uma movimentação correspondente (`ENTRADA`, `SAIDA`, `AJUSTE`, `INVENTARIO`, `PDV_VENDA`).
2. **Imutabilidade**: Movimentações e logs de auditoria nunca são excluídos ou alterados.
3. **Histórico de Preços**: Toda alteração de custo ou venda exige motivo registrado e gera histórico temporal.
4. **Justificativa em Ajustes**: Qualquer alteração manual de saldo exige justificativa fundamentada.
5. **Proteção de Exclusão**: Materiais que possuem histórico de movimentação não podem ser excluídos definitivamente (são inativados para resguardar a rastreabilidade contábil).
6. **Controle de Ruptura e Reposição**: Cálculo automático de quantidade sugerida (`Estoque Máximo - Estoque Atual`) e custo de compra para reposição.
7. **Estoque Negativo Bloqueado**: O sistema bloqueia saídas que tornem o saldo negativo por padrão.
8. **Auditoria com Snapshot**: Registro imutável de usuário, data/hora, ação e diff JSON de valores antes/depois.

---

## 🧪 Testes Automatizados

Para rodar a bateria de testes das regras de integridade e simulação do PDV:

```bash
python test_system.py
```

---

## 📁 Estrutura do Projeto

```
contru-estoque/
├── app.py                     # Servidor Flask, CORS e inicialização
---

## 🔐 Autenticação & Perfis de Acesso

O sistema conta com tela de login corporativo, senhas criptografadas com `werkzeug.security` (PBKDF2 SHA-256) e controle de permissões por perfil:

| Colaborador | E-mail Corporativo | Senha | Perfil | Escopo de Acesso |
| :--- | :--- | :--- | :--- | :--- |
| **Carlos Silva** | `carlos.admin@contruestoque.com.br` | `Admin@123` | **Administrador** | Acesso irrestrito + **Painel Admin** |
| **Mariana Souza** | `mariana.gestora@contruestoque.com.br` | `Gestor@123` | **Gestor de Estoque** | Materiais, Estoque, Preços e Relatórios |
| **Roberto Santos** | `roberto.estoque@contruestoque.com.br` | `Estoque@123` | **Estoquista** | Entradas, Saídas e Inventário Físico |
| **Juliana Lima** | `juliana.consulta@contruestoque.com.br` | `Consulta@123` | **Consulta** | Leitura de Catálogo e Posição de Estoque |
| **Fernando Rocha** | `fernando.financeiro@contruestoque.com.br` | `Financeiro@123` | **Financeiro** | Preços, Valoração de Estoque e Relatórios |

> [!TIP]
> Na tela de login há cartões de **Acesso Rápido em 1 Clique** para homologação instantânea de cada perfil.

---

## ⚙️ Painel de Gestão Corporativa (Admin)

Disponível exclusivamente para perfis de nível **Administrador**:
1. **Gestão de Colaboradores**: Cadastro de novos membros da equipe, alteração de perfis de acesso, bloqueio/desbloqueio e reset de senhas.
2. **Dados da Empresa & Políticas**: Configuração de Razão Social, CNPJ, Inscrição Estadual, política de bloqueio de estoque negativo, margem comercial padrão e frequência de inventário.
3. **Diagnóstico Cloud (Supabase/PostgreSQL)**: Status da conexão em tempo real, motor do banco, latência em milissegundos e volumetria por tabela.

---

## 📁 Estrutura do Projeto

```
contru-estoque/
├── app.py                     # Servidor Flask, registro de Blueprints e health check
├── database.py                # Modelagem relacional SQLAlchemy 2.0 (15 entidades)
├── seed_data.py               # Injeção de dados demonstrativos, usuários e senhas
├── test_system.py             # Testes unitários automatizados das regras de negócio
├── supabase_schema.sql        # DDL PostgreSQL para criação no Supabase
├── requirements.txt           # Dependências do projeto
├── Procfile                   # Configuração de deploy em nuvem (Gunicorn)
├── .env.example               # Exemplo de configuração do Supabase
├── routes/
│   ├── api_routes.py          # Endpoints REST (Itens, Estoque, Preços, Relatórios)
│   ├── pdv_routes.py          # Endpoints preparados para integração PDV
│   ├── auth_routes.py         # Login corporativo, logout e troca de senha
│   └── admin_routes.py        # Gestão de usuários, políticas e diagnóstico cloud
├── services/
│   ├── stock_service.py       # Regras de saldo, movimentações e travas
│   ├── price_service.py       # Gestão de preços, margem e evolução
│   ├── inventory_service.py   # Lógica de contagem física e divergências
│   ├── audit_service.py       # Trilha de auditoria com snapshot
│   ├── report_service.py      # KPIs de Dashboard e agregações
│   └── pdv_service.py         # Mapeamento e simulador de vendas PDV
├── static/
│   ├── css/custom.css         # Identidade visual em tons alaranjados
│   └── js/                    # Módulos SPA (auth, admin, dashboard, stock, items, etc.)
└── templates/
    └── index.html             # Interface SPA completa com tela de login e painel admin
```

