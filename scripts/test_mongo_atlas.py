"""
Script para testar conexão com MongoDB Atlas

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configura variáveis de ambiente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

from django.conf import settings
from pymongo import MongoClient
from datetime import datetime

def test_mongodb_atlas():
    """Testa conexão com MongoDB Atlas."""
    print("=" * 60)
    print("🔍 TESTANDO CONEXÃO COM MONGODB ATLAS")
    print("=" * 60)
    print()
    
    # Exibe configurações (sem mostrar senha completa)
    uri = settings.MONGODB_URI
    safe_uri = uri.replace(uri.split('@')[0].split('//')[1], '***:***')
    print(f"📋 URI: {safe_uri}")
    print(f"📋 Banco de dados: {settings.MONGODB_DB}")
    print()
    
    try:
        # Tenta conectar
        print("⏳ Conectando ao MongoDB Atlas...")
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=10000)
        
        # Testa a conexão
        print("⏳ Testando conexão...")
        client.admin.command('ping')
        print("✅ Conexão estabelecida com sucesso!")
        print()
        
        # Acessa o banco de dados
        db = client[settings.MONGODB_DB]
        collection = db['chat_interactions']
        
        # Testa inserção
        print("⏳ Testando inserção de dados...")
        test_data = {
            'prompt': 'Teste de conexão MongoDB Atlas',
            'response': 'Conexão funcionando perfeitamente!',
            'processing_time': 0.5,
            'model': 'test',
            'timestamp': datetime.now()
        }
        
        result = collection.insert_one(test_data)
        print(f"✅ Documento inserido com ID: {result.inserted_id}")
        print()
        
        # Testa leitura
        print("⏳ Testando leitura de dados...")
        document = collection.find_one({'_id': result.inserted_id})
        print("✅ Documento recuperado com sucesso!")
        print(f"   Prompt: {document['prompt']}")
        print(f"   Response: {document['response']}")
        print()
        
        # Conta documentos
        count = collection.count_documents({})
        print(f"📊 Total de documentos na coleção: {count}")
        print()
        
        # Remove documento de teste
        print("⏳ Removendo documento de teste...")
        collection.delete_one({'_id': result.inserted_id})
        print("✅ Documento de teste removido")
        print()
        
        # Fecha conexão
        client.close()
        
        print("=" * 60)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print()
        print("✅ MongoDB Atlas está configurado e funcionando corretamente!")
        print("✅ Você pode iniciar o servidor: python manage.py runserver")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERRO NA CONEXÃO")
        print("=" * 60)
        print()
        print(f"Erro: {str(e)}")
        print()
        print("💡 Possíveis soluções:")
        print("  1. Verifique se as credenciais estão corretas no .env")
        print("  2. Verifique se o IP está na whitelist do MongoDB Atlas")
        print("  3. Verifique sua conexão com a internet")
        print("  4. Verifique se o cluster está ativo no MongoDB Atlas")
        print()
        
        return False

if __name__ == '__main__':
    test_mongodb_atlas()

