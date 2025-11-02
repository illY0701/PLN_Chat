import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('.env')

# Do NOT print the URI (sensitive). We'll only print a success/failure message.
uri = os.getenv('MONGODB_URI')
db_name = os.getenv('MONGODB_DB')

print('Checking MONGODB_URI and MONGODB_DB...')
if not uri or 'your-' in uri or '<' in uri:
    print('MONGODB_URI parece não estar configurada corretamente no .env')
    raise SystemExit(1)

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
try:
    client.admin.command('ping')
    print('Conectado ao MongoDB Atlas com sucesso.')
    db = client[db_name]
    try:
        cols = db.list_collection_names()
        print('Collections:', cols)
    except Exception:
        print('Banco acessado, mas não foi possível listar coleções (permissões?).')
except Exception as e:
    print('Erro ao conectar ao MongoDB:', str(e))
    raise
finally:
    try:
        client.close()
    except:
        pass
