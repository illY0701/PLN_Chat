# 🚀 Início Rápido - Sistema PLN Chat

## Sistema Configurado e Funcionando! ✅

### Para Iniciar o Sistema:

```bash
# 1. Entre no diretório do projeto
cd "c:\Users\csarf\OneDrive\Desktop\cursor aqui\PLN\PLN"

# 2. Ative o ambiente virtual (opcional)
venv\Scripts\activate

# 3. Inicie o servidor
python manage.py runserver
```

### Acesse no navegador:
**http://localhost:8000**

---

## ✅ O que já está configurado:

- 🗄️ **MongoDB Atlas**: Conectado e funcionando
- 💾 **Banco de Dados**: `cesinhafit_db`
- 🔐 **Credenciais**: Configuradas no arquivo `.env`
- 📝 **Salvamento**: Todas as interações são salvas automaticamente
- 🔄 **Fallback**: Sistema usa SQLite se MongoDB não disponível
- 🖥️ **Interface Web**: Totalmente funcional

---

## 🧪 Para Testar a Conexão:

```bash
# Teste rápido de conexão MongoDB
python scripts/test_mongo.py
```

**Resultado esperado:**
```
Checking MONGODB_URI and MONGODB_DB...
Conectado ao MongoDB Atlas com sucesso.
Collections: ['chat_interactions']
```

---

## 📊 Informações do Banco:

- **Servidor**: MongoDB Atlas
- **Cluster**: pln.wxcvyf4.mongodb.net
- **Database**: cesinhafit_db
- **Collection**: chat_interactions
- **Status**: ✅ Online e Operacional

---

## 📁 Arquivos Importantes:

- `.env` - Configurações e credenciais (NÃO commitar!)
- `app/services/mongo_repo.py` - Gerenciador MongoDB
- `CONFIGURACAO_MONGODB.md` - Documentação completa
- `RESUMO_CONFIGURACAO.txt` - Resumo da configuração

---

## ⚠️ Importante:

O arquivo `.env` contém informações sensíveis e **NÃO deve ser commitado no Git**.

---

## 🎉 Sistema Pronto Para Uso!

Desenvolvido por: **ANNA, CÉSAR E EVILY**

