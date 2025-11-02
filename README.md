# Sistema PLN Chat - Processamento de Linguagem Natural

**Desenvolvido por: ANNA, CÉSAR E EVILY**

Sistema web completo de chat com IA utilizando modelos de Processamento de Linguagem Natural da Hugging Face, com persistência em MongoDB e interface premium.

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Requisitos](#requisitos)
4. [Instalação](#instalação)
5. [Configuração](#configuração)
6. [Uso](#uso)
7. [Arquitetura](#arquitetura)
8. [Testes](#testes)
9. [Segurança](#segurança)
10. [Documentação Técnica](#documentação-técnica)

---

## 🎯 Visão Geral

Sistema de chat inteligente desenvolvido em Django que integra modelos de NLP da Hugging Face. O sistema processa perguntas em português e fornece respostas inteligentes, armazenando todo o histórico de interações para análise posterior.

### Objetivos do Projeto

- ✅ Interface web moderna e responsiva para chat com IA
- ✅ Integração com modelos da Hugging Face (local ou API)
- ✅ Persistência de dados em MongoDB com fallback para SQLite
- ✅ Histórico completo de interações com filtros e exportação
- ✅ Respostas rápidas para perguntas comuns
- ✅ Cálculos matemáticos automáticos

---

## ✨ Funcionalidades

### Chat Inteligente
- 💬 Interface de chat em tempo real
- 🤖 Processamento por modelos de NLP (Flan-T5, GPT, etc.)
- ⚡ Respostas rápidas para perguntas frequentes
- 🧮 Cálculo automático de operações matemáticas
- 🔄 Fallback automático entre modelo local e API Hugging Face
- 🎨 Design premium com animações suaves

### Histórico e Persistência
- 📜 Visualização completa do histórico de conversas
- 🔍 Filtros por data (data inicial e final)
- 📄 Paginação de resultados (10 itens por página)
- 📥 Exportação em JSON e CSV
- 💾 Persistência em MongoDB com fallback para SQLite

### Qualidade e Confiabilidade
- 🛡️ Detecção e correção de respostas de baixa qualidade
- 🔒 Validação de entrada e sanitização
- 📊 Logging completo de operações
- ⚙️ Configuração flexível via variáveis de ambiente

---

## 🔧 Requisitos

### Software Necessário

- **Python**: 3.8 ou superior
- **Django**: 4.2 ou superior
- **MongoDB**: 4.0 ou superior (opcional, sistema funciona sem)
- **Node.js**: Não necessário (sem dependências frontend)

### Bibliotecas Python

Todas as dependências estão listadas em `requirements.txt`:

```
Django>=4.2.0
python-dotenv>=1.0.0
transformers>=4.30.0
torch>=2.0.0
pymongo>=4.3.3
django-crispy-forms>=2.0
```

---

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd PLN/PLN
```

### 2. Crie e Ative um Ambiente Virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (`PLN/PLN/.env`):

```env
# Django Settings
SECRET_KEY=sua-chave-secreta-aqui-gerada-automaticamente
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Settings (opcional)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=pln_chat

# Hugging Face Settings
HF_MODEL_NAME=google/flan-t5-small
HF_API_TOKEN=seu-token-huggingface-aqui
HF_INFERENCE_MODEL=google/flan-t5-small

# Opções
USE_HF_FOR_ALL=False
```

### 5. Execute Migrações

```bash
python manage.py migrate
```

### 6. Colete Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 7. Inicie o Servidor

```bash
python manage.py runserver
```

O sistema estará disponível em: **http://localhost:8000/**

---

## ⚙️ Configuração

### Variáveis de Ambiente

#### SECRET_KEY
Chave secreta do Django. **IMPORTANTE**: Altere em produção!

#### DEBUG
- `True`: Modo desenvolvimento (mostra erros detalhados)
- `False`: Modo produção

#### MONGODB_URI
URI de conexão do MongoDB. Exemplos:
- Local: `mongodb://localhost:27017/`
- Atlas: `mongodb+srv://usuario:senha@cluster.mongodb.net/`

#### MONGODB_DB
Nome do banco de dados MongoDB (padrão: `pln_chat`)

#### HF_MODEL_NAME
Nome do modelo da Hugging Face a ser carregado localmente.
Exemplos:
- `google/flan-t5-small` (pequeno, rápido)
- `google/flan-t5-base` (médio)
- `google/flan-t5-large` (grande, melhor qualidade)

#### HF_API_TOKEN
Token de acesso da Hugging Face (obtido em https://huggingface.co/settings/tokens)

#### HF_INFERENCE_MODEL
Modelo a ser usado na API de inferência da Hugging Face

#### USE_HF_FOR_ALL
- `False`: Usa modelo local, API como fallback
- `True`: Usa sempre a API de inferência

---

## 📖 Uso

### Interface do Chat

1. Acesse `http://localhost:8000/`
2. Digite sua pergunta no campo de entrada
3. Clique em "Enviar" ou pressione Enter
4. Aguarde a resposta da IA
5. Todas as interações são salvas automaticamente

### Histórico

1. Acesse `http://localhost:8000/history/`
2. Use os filtros de data para buscar interações específicas
3. Navegue pelas páginas usando a paginação
4. Exporte dados em JSON ou CSV

### Exemplos de Perguntas

- **Matemática**: "quanto é 5 vezes 3", "10 + 15", "20 - 8"
- **Conhecimento**: "quais são as vogais", "capital do brasil"
- **Tecnologia**: "o que é python", "o que é django"
- **Animais**: "quantas patas tem um leão"
- **Saudações**: "oi", "bom dia", "tudo bem"

---

## 🏗️ Arquitetura

### Estrutura do Projeto

```
PLN/
└── PLN/
    ├── app/
    │   ├── services/
    │   │   ├── nlp_service.py      # Serviço de processamento NLP
    │   │   └── mongo_repo.py       # Repositório de dados
    │   ├── templates/
    │   │   ├── base.html           # Template base
    │   │   ├── chat.html           # Página do chat
    │   │   └── history.html        # Página de histórico
    │   ├── static/
    │   │   └── css/
    │   │       └── premium.css     # Estilos premium
    │   ├── tests/                  # Testes automatizados
    │   ├── urls.py                 # URLs da aplicação
    │   └── views.py                # Views Django
├── project/
    │   ├── settings.py             # Configurações Django
    │   └── urls.py                 # URLs principais
    ├── .env                        # Variáveis de ambiente
    ├── requirements.txt            # Dependências
    └── manage.py                   # Script de gerenciamento
```

### Fluxo de Dados

```
Usuário → Chat View → NLP Service → Modelo Hugging Face
                              ↓
                        Resposta Processada
                              ↓
                    MongoRepository (salva)
                              ↓
                    JSON Response → Frontend
```

### Componentes Principais

#### 1. NLPService (`app/services/nlp_service.py`)
- Gerencia carregamento de modelos
- Processa prompts e gera respostas
- Implementa respostas rápidas e cálculos
- Fallback para API Hugging Face

#### 2. MongoRepository (`app/services/mongo_repo.py`)
- Gerencia conexão MongoDB
- Fallback para SQLite
- CRUD de interações
- Filtros e consultas

#### 3. Views (`app/views.py`)
- `chat_view`: Processa mensagens e retorna respostas
- `history_view`: Exibe histórico com filtros
- `export_history`: Exporta dados em JSON/CSV

---

## 🧪 Testes

### Executar Todos os Testes

```bash
python manage.py test
```

### Executar Testes Específicos

```bash
# Testes do serviço NLP
python manage.py test app.tests.test_nlp_service

# Testes do repositório MongoDB
python manage.py test app.tests.test_mongo_repo

# Testes das views
python manage.py test app.tests.test_views
```

### Cobertura de Testes

O projeto inclui testes para:
- ✅ Processamento de prompts pelo NLP Service
- ✅ Respostas rápidas e cálculos matemáticos
- ✅ Conexão e operações do MongoDB
- ✅ Fallback para SQLite
- ✅ Views e endpoints HTTP
- ✅ Validação de entrada
- ✅ Exportação de dados

---

## 🔒 Segurança

### Medidas Implementadas

1. **Validação de Entrada**
   - Limite de 500 caracteres por prompt
   - Sanitização de dados de entrada
   - Validação de tipos de dados

2. **Segurança de Dados**
   - Variáveis sensíveis em `.env`
   - SECRET_KEY com fallback seguro
   - Proteção CSRF (exceto endpoint API JSON)

3. **Tratamento de Erros**
   - Logging sem expor informações sensíveis
   - Mensagens de erro genéricas para usuários
   - Graceful degradation em falhas

4. **Ética e IA**
   - Respostas limitadas a contexto educacional
   - Detecção de respostas inadequadas
   - Fallback para mensagens genéricas quando necessário

### Recomendações para Produção

- ⚠️ Altere `SECRET_KEY` para valor seguro
- ⚠️ Defina `DEBUG=False`
- ⚠️ Configure `ALLOWED_HOSTS` corretamente
- ⚠️ Use HTTPS
- ⚠️ Configure firewall e rate limiting
- ⚠️ Faça backup regular do MongoDB

---

## 📚 Documentação Técnica

### API Endpoints

#### POST `/`
Processa uma mensagem e retorna resposta da IA.

**Request:**
```json
{
  "prompt": "sua pergunta aqui"
}
```

**Response:**
```json
{
  "response": "resposta da IA",
  "processing_time": 2.34,
  "model": "google/flan-t5-small"
}
```

#### GET `/history/`
Retorna página HTML com histórico de conversas.

**Query Parameters:**
- `page`: Número da página (padrão: 1)
- `date_from`: Data inicial (YYYY-MM-DD)
- `date_to`: Data final (YYYY-MM-DD)

#### GET `/export/?format=json`
Exporta histórico em JSON.

#### GET `/export/?format=csv`
Exporta histórico em CSV.

### Modelos de Dados

#### Interação de Chat (MongoDB)

```javascript
{
  "_id": ObjectId("..."),
  "prompt": "pergunta do usuário",
  "response": "resposta do modelo",
  "processing_time": 2.34,
  "model": "google/flan-t5-small",
  "timestamp": ISODate("2024-01-01T12:00:00Z")
}
```

### Logging

O sistema utiliza logging em múltiplos níveis:

- **DEBUG**: Informações detalhadas para desenvolvimento
- **INFO**: Operações normais do sistema
- **WARNING**: Avisos (ex: MongoDB indisponível)
- **ERROR**: Erros que não impedem funcionamento
- **CRITICAL**: Erros críticos

Logs são salvos em `debug.log` e também no console.

---

## 🎨 Design e Interface

### Características do Design

- **Design Premium**: Interface moderna com 2000+ linhas de CSS
- **Animações Suaves**: 15+ animações profissionais
- **Responsivo**: Funciona perfeitamente em mobile, tablet e desktop
- **Acessível**: Suporte a ARIA, high contrast e reduced motion
- **Glassmorphism**: Efeitos de vidro modernos
- **Gradientes Animados**: Paleta de cores premium

### Navegação

- **Chat**: Página principal para conversar com a IA
- **Histórico**: Visualização e filtros do histórico
- **Exportar**: Download de dados em JSON/CSV

---

## 🐛 Troubleshooting

### MongoDB não conecta

O sistema funciona normalmente sem MongoDB, usando SQLite como fallback. Para habilitar MongoDB:

1. Verifique se o MongoDB está rodando: `mongosh` ou `mongo`
2. Confira a URI no `.env`: `MONGODB_URI=mongodb://localhost:27017/`
3. Teste a conexão: `python scripts/test_mongo.py`

### Modelo não carrega

1. Verifique se `HF_MODEL_NAME` está correto no `.env`
2. Certifique-se de ter espaço em disco suficiente
3. Verifique conexão com internet (primeiro download)
4. Use modelo menor se tiver pouca RAM: `google/flan-t5-small`

### Erro de token Hugging Face

1. Obtenha token em: https://huggingface.co/settings/tokens
2. Garanta permissões de leitura e Inference API
3. Cole o token no `.env`: `HF_API_TOKEN=seu-token`

### Interface não carrega CSS

```bash
python manage.py collectstatic --noinput
```

---

## 📊 Critérios de Avaliação Atendidos

### ✅ Funcionalidade e Persistência (40%)
- Chat funcional com processamento NLP
- Persistência em MongoDB com fallback SQLite
- Histórico completo com filtros
- Exportação em múltiplos formatos

### ✅ Qualidade do Código (20%)
- Código limpo e organizado
- Comentários em português
- Arquitetura modular (services, views, templates)
- Tratamento de erros robusto

### ✅ Interface e UX (10%)
- Design premium e moderno
- Animações suaves
- Interface responsiva
- Experiência intuitiva

### ✅ Testes e Documentação (20%)
- Testes automatizados completos
- Documentação em português
- README detalhado
- Comentários no código

### ✅ Ética e Segurança (10%)
- Validação de entrada
- Proteção contra erros
- Logging adequado
- Configuração segura

---

## 👥 Autores

- **ANNA**
- **CÉSAR**
- **EVILY**

---

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos.

---

## 🙏 Agradecimentos

- Hugging Face por disponibilizar modelos e API
- Django pela excelente framework web
- Comunidade open source

---

**Versão**: 1.0.0  
**Última Atualização**: Novembro 2024
