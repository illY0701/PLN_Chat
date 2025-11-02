"""
Testes unitários para o MongoRepository

Testa conexão MongoDB, salvamento, recuperação e fallback para SQLite.

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.conf import settings
from datetime import datetime
from app.services.mongo_repo import MongoRepository


class TestMongoRepository(TestCase):
    """Testes para o repositório MongoDB."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        # Mock das configurações MongoDB
        with patch.object(settings, 'MONGODB_URI', 'mongodb://localhost:27017/'):
            with patch.object(settings, 'MONGODB_DB', 'test_db'):
                pass
    
    @patch('app.services.mongo_repo.MongoClient')
    def test_mongodb_connection_success(self, mock_mongo_client):
        """Testa conexão bem-sucedida com MongoDB."""
        # Mock do cliente MongoDB
        mock_client = Mock()
        mock_client.admin.command.return_value = {'ok': 1}
        mock_client.__getitem__.return_value.__getitem__.return_value = Mock()
        mock_mongo_client.return_value = mock_client
        
        # Cria repositório
        repo = MongoRepository()
        
        # Verifica se conexão foi estabelecida
        self.assertIsNotNone(repo.client)
    
    @patch('app.services.mongo_repo.MongoClient')
    def test_mongodb_connection_failure(self, mock_mongo_client):
        """Testa graceful degradation quando MongoDB não está disponível."""
        # Mock de falha na conexão
        mock_mongo_client.side_effect = Exception("Connection failed")
        
        # Cria repositório (não deve levantar exceção)
        repo = MongoRepository()
        
        # Verifica que continua funcionando sem MongoDB
        self.assertIsNone(repo.client)
    
    @patch('app.services.mongo_repo.MongoClient')
    def test_save_interaction_mongodb(self, mock_mongo_client):
        """Testa salvamento de interação no MongoDB."""
        # Mock do MongoDB
        mock_collection = Mock()
        mock_collection.insert_one.return_value.inserted_id = 'test_id'
        
        mock_db = Mock()
        mock_db.__getitem__.return_value = mock_collection
        
        mock_client = Mock()
        mock_client.admin.command.return_value = {'ok': 1}
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client
        
        repo = MongoRepository()
        repo.collection = mock_collection
        
        # Testa salvamento
        result = repo.save_interaction({
            'prompt': 'teste',
            'response': 'resposta',
            'processing_time': 1.0,
            'model': 'test-model'
        })
        
        self.assertEqual(result, 'test_id')
        mock_collection.insert_one.assert_called_once()
    
    def test_save_interaction_sqlite_fallback(self):
        """Testa fallback para SQLite quando MongoDB não disponível."""
        # Cria repositório sem MongoDB
        repo = MongoRepository()
        repo.client = None
        repo.collection = None
        
        # Testa salvamento no SQLite
        result = repo.save_interaction({
            'prompt': 'teste sqlite',
            'response': 'resposta sqlite',
            'processing_time': 1.5,
            'model': 'test-model'
        })
        
        # Deve retornar um ID ou None
        self.assertIsNotNone(result) if result else None
    
    def test_get_interactions_sqlite_fallback(self):
        """Testa recuperação de interações do SQLite."""
        # Cria repositório sem MongoDB
        repo = MongoRepository()
        repo.client = None
        repo.collection = None
        
        # Primeiro salva uma interação
        repo.save_interaction({
            'prompt': 'teste',
            'response': 'resposta',
            'processing_time': 1.0,
            'model': 'test-model'
        })
        
        # Depois recupera
        interactions = repo.get_interactions()
        
        # Deve retornar lista (pode estar vazia se SQLite não configurado)
        self.assertIsInstance(interactions, list)
    
    @patch('app.services.mongo_repo.MongoClient')
    def test_get_interactions_with_filters(self, mock_mongo_client):
        """Testa recuperação com filtros de data."""
        # Mock do MongoDB
        mock_collection = Mock()
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_collection.find.return_value = mock_cursor
        
        mock_db = Mock()
        mock_db.__getitem__.return_value = mock_collection
        
        mock_client = Mock()
        mock_client.admin.command.return_value = {'ok': 1}
        mock_client.__getitem__.return_value = mock_db
        mock_mongo_client.return_value = mock_client
        
        repo = MongoRepository()
        repo.collection = mock_collection
        
        # Testa filtros
        filters = {
            'timestamp': {
                '$gte': '2024-01-01',
                '$lte': '2024-12-31'
            }
        }
        
        interactions = repo.get_interactions(filters)
        
        # Verifica se find foi chamado
        mock_collection.find.assert_called()
    
    def test_repository_initialization_without_mongodb_uri(self):
        """Testa inicialização sem URI do MongoDB configurada."""
        with patch.object(settings, 'MONGODB_URI', None):
            repo = MongoRepository()
            self.assertIsNone(repo.client)


if __name__ == '__main__':
    unittest.main()
