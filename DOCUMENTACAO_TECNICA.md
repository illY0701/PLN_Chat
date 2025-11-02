# Documentação Técnica - Sistema PLN Chat

**Desenvolvido por: ANNA, CÉSAR E EVILY**

---

## 📚 Sumário

1. [Arquitetura do Sistema](#arquitetura-do-sistema)
2. [Componentes Principais](#componentes-principais)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Segurança e Ética](#segurança-e-ética)
5. [Decisões Técnicas](#decisões-técnicas)
6. [Limitações e Melhorias Futuras](#limitações-e-melhorias-futuras)

---

## 🏗️ Arquitetura do Sistema

### Visão Geral

O sistema segue uma arquitetura em camadas (layered architecture):

```
┌─────────────────────────────────────────┐
│         Camada de Apresentação          │
│  (Templates HTML, CSS, JavaScript)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Camada de Controle              │
│         (Django Views)                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Camada de Serviços              │
│  (NLPService, MongoRepository)          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Camada de Persistência             │
│  (MongoDB / SQLite Fallback)            │
└─────────────────────────────────────────┘
```

### Padrões de Projeto Utilizados

#### 1. Repository Pattern
- **MongoRepository**: Abstrai acesso aos dados
- Permite trocar banco de dados sem alterar lógica de negócio
- Implementa fallback automático SQLite → MongoDB

#### 2. Service Layer Pattern
- **NLPService**: Encapsula lógica de processamento NLP
- Separação de responsabilidades
- Facilita testes e manutenção

#### 3. Lazy Loading
- Modelos NLP carregados apenas quando necessário
- Reduz tempo de inicialização
- Economiza memória quando não usado

#### 4. Strategy Pattern
- Diferentes estratégias de processamento:
  - Respostas rápidas (quick responses)
  - Cálculos matemáticos
  - Modelo local
  - API Hugging Face

---

## 🔧 Componentes Principais

### 1. NLPService (`app/services/nlp_service.py`)

#### Responsabilidades
- Carregamento de modelos Hugging Face
- Processamento de prompts
- Detecção e correção de respostas ruins
- Fallback entre modelo local e API

#### Métodos Principais

##### `__init__()`
Inicializa o serviço com configurações do Django.

```python
def __init__(self):
    self.model_name = settings.HF_MODEL_NAME
    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
```

##### `_ensure_model_loaded()`
Carrega o modelo apenas quando necessário (lazy loading).

**Lógica:**
1. Verifica se já está carregado
2. Detecta tipo de modelo (causal vs encoder-decoder)
3. Carrega modelo apropriado
4. Move para GPU se disponível

##### `process_prompt(prompt: str) -> tuple[str, float]`
Processa um prompt e retorna resposta + tempo.

**Fluxo:**
1. Normaliza prompt
2. Verifica cálculos matemáticos
3. Verifica respostas rápidas
4. Processa com modelo se necessário
5. Limpa e valida resposta
6. Retorna resposta e tempo

##### `hf_inference(prompt: str) -> str | None`
Usa API de inferência da Hugging Face.

**Características:**
- Timeout de 30 segundos
- Retry automático em erro 503
- Tratamento de diferentes formatos de resposta

#### Detecção de Respostas Ruins

O serviço implementa heurísticas para detectar respostas de baixa qualidade:

```python
is_bad_response = (
    not cleaned or
    len(cleaned) < 3 or
    cleaned.lower() == prompt.lower() or
    similarity > 0.7 or
    starts_with_english_question or
    # ... mais condições
)
```

**Ações quando detectado:**
1. Tenta regenerar com prompt mais forte
2. Fallback para API Hugging Face
3. Retorna mensagem genérica se tudo falhar

---

### 2. MongoRepository (`app/services/mongo_repo.py`)

#### Responsabilidades
- Conexão com MongoDB
- CRUD de interações
- Fallback para SQLite

#### Métodos Principais

##### `__init__()`
Inicializa conexão com graceful degradation.

**Comportamento:**
- Tenta conectar ao MongoDB
- Se falhar, continua sem levantar exceção
- Permite que aplicação funcione sem MongoDB

##### `save_interaction(interaction_data: dict) -> str | int | None`
Salva interação no banco de dados.

**Estratégia:**
1. Tenta salvar no MongoDB
2. Se falhar, tenta SQLite
3. Retorna ID da interação ou None

##### `get_interactions(filters: dict = None) -> list`
Recupera interações com filtros opcionais.

**Filtros Suportados:**
```python
{
    'timestamp': {
        '$gte': '2024-01-01',  # Data inicial
        '$lte': '2024-12-31'   # Data final
    }
}
```

---

### 3. Views (`app/views.py`)

#### chat_view
**Métodos HTTP:** GET, POST

**GET:**
- Renderiza página do chat

**POST:**
- Recebe prompt JSON
- Valida entrada (tamanho, formato)
- Processa através do NLPService
- Salva no banco de dados
- Retorna JSON com resposta

**Validações:**
- Prompt não vazio
- Máximo 500 caracteres
- JSON válido

#### history_view
**Método HTTP:** GET

**Funcionalidades:**
- Exibe histórico paginado
- Filtros por data
- 10 itens por página

**Query Parameters:**
- `page`: Número da página
- `date_from`: Data inicial (YYYY-MM-DD)
- `date_to`: Data final (YYYY-MM-DD)

#### export_history
**Método HTTP:** GET

**Formatos:**
- JSON: `?format=json`
- CSV: `?format=csv`

**Características CSV:**
- BOM UTF-8 para compatibilidade Excel
- Headers em português
- Encoding UTF-8

---

## 🔄 Fluxo de Dados

### Fluxo de Processamento de Chat

```
1. Usuário envia mensagem
   ↓
2. Frontend (JavaScript) faz POST para / (chat_view)
   ↓
3. chat_view valida entrada
   ↓
4. chat_view chama nlp_service.process_prompt()
   ↓
5. NLPService:
   - Verifica cálculos matemáticos
   - Verifica respostas rápidas
   - Se não encontrou, processa com modelo
   ↓
6. NLPService retorna (resposta, tempo)
   ↓
7. chat_view salva no MongoDB (via mongo_repo)
   ↓
8. chat_view retorna JSON para frontend
   ↓
9. Frontend exibe resposta ao usuário
```

### Fluxo de Persistência

```
1. mongo_repo.save_interaction() chamado
   ↓
2. MongoDB disponível?
   ├─ SIM → Salva no MongoDB
   │         ↓
   │      Sucesso? → Retorna ID
   │         ↓
   │      Erro → Tenta SQLite
   │
   └─ NÃO → Salva no SQLite
              ↓
           Retorna ID ou None
```

### Fluxo de Recuperação de Histórico

```
1. history_view recebe GET com filtros opcionais
   ↓
2. Constrói filtros MongoDB a partir de query params
   ↓
3. mongo_repo.get_interactions(filters)
   ↓
4. MongoDB disponível?
   ├─ SIM → Busca no MongoDB com filtros
   │
   └─ NÃO → Busca no SQLite com filtros SQL
   ↓
5. Pagina resultados (10 por página)
   ↓
6. Renderiza template com dados
```

---

## 🔒 Segurança e Ética

### Medidas de Segurança Implementadas

#### 1. Validação de Entrada

**Prompt:**
- Máximo 500 caracteres
- Não pode estar vazio
- Sanitização automática

**Query Parameters:**
- Validação de formato de data
- Proteção contra SQL injection (ORM Django)
- Proteção contra NoSQL injection (sanitização de filtros)

#### 2. Proteção CSRF

- Django CSRF middleware ativo
- Exceção apenas para endpoint JSON (necessário para AJAX)
- Tokens CSRF em formulários HTML

#### 3. Logging Seguro

- Não loga dados sensíveis
- Erros genéricos para usuários
- Detalhes apenas em logs do servidor

#### 4. Variáveis de Ambiente

- Credenciais em `.env` (não versionado)
- SECRET_KEY com fallback seguro
- Tokens não expostos no código

### Considerações Éticas

#### 1. Uso Responsável de IA

- Sistema educacional/acadêmico
- Respostas limitadas a contexto apropriado
- Detecção e prevenção de respostas inadequadas

#### 2. Privacidade de Dados

- Histórico armazenado localmente (não compartilhado)
- Dados não são usados para treinamento
- Usuário pode exportar seus dados

#### 3. Transparência

- Logging completo de operações
- Metadados de processamento (tempo, modelo)
- Código fonte disponível

#### 4. Prevenção de Uso Indevido

- Validação de entrada previne injeção
- Rate limiting (pode ser adicionado)
- Detecção de prompts maliciosos

---

## 💡 Decisões Técnicas

### Por que Django?

**Vantagens:**
- Framework maduro e estável
- ORM robusto
- Sistema de templates
- Admin interface (não usada, mas disponível)
- Comunidade ativa

**Alternativas consideradas:**
- Flask: Mais simples, mas menos recursos
- FastAPI: Melhor para APIs, mas mais complexo para templates

### Por que MongoDB?

**Vantagens:**
- Schema flexível (ideal para dados não estruturados)
- Suporte nativo a documentos JSON
- Escalabilidade horizontal
- Integração fácil com Python

**Fallback SQLite:**
- Funciona sem servidor de banco
- Ideal para desenvolvimento
- Garante funcionamento mesmo sem MongoDB

### Por que Hugging Face Transformers?

**Vantagens:**
- Biblioteca padrão da indústria
- Modelos pré-treinados disponíveis
- Suporte a GPU e CPU
- API de inferência como fallback

**Modelo escolhido: `google/flan-t5-small`**
- Pequeno (60M parâmetros)
- Rápido para inferência
- Boa qualidade para português
- Baixo uso de memória

### Por que Lazy Loading?

**Benefícios:**
- Inicialização rápida do servidor
- Economia de memória quando não usado
- Permite servidor rodar sem modelo carregado

**Desvantagens:**
- Primeira requisição mais lenta
- Complexidade adicional no código

### Por que Graceful Degradation?

**Benefícios:**
- Sistema funciona mesmo com falhas
- Melhor experiência do usuário
- Facilita desenvolvimento e testes

**Implementação:**
- MongoDB → SQLite → Continuar sem banco
- Modelo local → API Hugging Face → Mensagem genérica
- Todas as falhas são logadas

---

## ⚠️ Limitações e Melhorias Futuras

### Limitações Atuais

#### 1. Performance
- Modelo pequeno tem qualidade limitada
- Processamento síncrono (bloqueia requisição)
- Sem cache de respostas

#### 2. Funcionalidades
- Sem autenticação de usuários
- Sem rate limiting
- Sem suporte a múltiplos idiomas simultâneos
- Sem histórico de sessão

#### 3. Segurança
- Sem HTTPS obrigatório
- Sem validação de origem (CORS)
- Sem sanitização avançada de output

### Melhorias Futuras Sugeridas

#### Curto Prazo
1. **Cache de Respostas**
   - Redis para cache
   - Reduz latência para perguntas repetidas

2. **Rate Limiting**
   - Limitar requisições por IP
   - Prevenir abuso

3. **Melhor Detecção de Idiomas**
   - Suporte explícito a múltiplos idiomas
   - Detecção automática

#### Médio Prazo
1. **Processamento Assíncrono**
   - Celery para tarefas pesadas
   - WebSockets para atualizações em tempo real

2. **Modelo Maior**
   - `google/flan-t5-base` ou `large`
   - Melhor qualidade de respostas

3. **Autenticação**
   - Sistema de login
   - Histórico por usuário

#### Longo Prazo
1. **Fine-tuning**
   - Treinar modelo em dados específicos
   - Melhorar respostas para domínio específico

2. **Multi-modelo**
   - Vários modelos disponíveis
   - Seleção automática por tipo de pergunta

3. **Análise de Sentimento**
   - Detectar emoção nas perguntas
   - Adaptar respostas

---

## 📊 Métricas e Monitoramento

### Métricas Atuais

**Implementadas:**
- Tempo de processamento por requisição
- Modelo usado para cada resposta
- Logging de erros

**Podem ser adicionadas:**
- Número de requisições por dia
- Taxa de erro
- Tempo médio de resposta
- Uso de GPU vs CPU

### Logging

**Níveis de Log:**
- DEBUG: Detalhes técnicos
- INFO: Operações normais
- WARNING: Avisos (ex: MongoDB indisponível)
- ERROR: Erros não críticos
- CRITICAL: Erros críticos

**Logs salvos em:**
- Console (durante desenvolvimento)
- `debug.log` (arquivo)

---

## 🧪 Testes

### Cobertura

**Testes Implementados:**
- ✅ Processamento de prompts
- ✅ Respostas rápidas
- ✅ Cálculos matemáticos
- ✅ Conexão MongoDB
- ✅ Fallback SQLite
- ✅ Views HTTP
- ✅ Exportação de dados

**Estrutura de Testes:**
```
app/tests/
├── test_nlp_service.py    # Testes do serviço NLP
├── test_mongo_repo.py     # Testes do repositório
├── test_views.py          # Testes das views
└── test_hf_inference.py   # Testes da API HF
```

### Executar Testes

```bash
# Todos os testes
python manage.py test

# Teste específico
python manage.py test app.tests.test_nlp_service

# Com verbosidade
python manage.py test --verbosity=2
```

---

## 📝 Conclusão

Este sistema implementa uma arquitetura sólida e escalável para chat com IA, seguindo boas práticas de desenvolvimento, segurança e ética. O código está documentado, testado e pronto para produção (após configurações de segurança adequadas).

**Desenvolvido por: ANNA, CÉSAR E EVILY**  
**Versão:** 1.0.0  
**Data:** Novembro 2024


