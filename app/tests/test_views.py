"""
Testes unitários para as Views

Testa endpoints HTTP, validação de entrada, exportação e paginação.

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

import json
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from unittest.mock import Mock, patch, MagicMock
from app.views import chat_view, history_view, export_history
from app.services.nlp_service import NLPService
from app.services.mongo_repo import MongoRepository


class TestChatView(TestCase):
    """Testes para a view de chat."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.factory = RequestFactory()
        self.client = Client()
        
        # Mock do serviço NLP
        self.mock_nlp_service = Mock(spec=NLPService)
        self.mock_nlp_service.model_name = 'test-model'
        self.mock_nlp_service.process_prompt.return_value = ('Resposta de teste', 1.5)
        
        # Mock do repositório MongoDB
        self.mock_mongo_repo = Mock(spec=MongoRepository)
        self.mock_mongo_repo.save_interaction.return_value = 'test_id'
    
    def test_chat_view_get(self):
        """Testa renderização da página de chat (GET)."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')
    
    @patch('app.views.nlp_service')
    @patch('app.views.mongo_repo')
    def test_chat_view_post_success(self, mock_repo, mock_nlp):
        """Testa processamento bem-sucedido de mensagem (POST)."""
        mock_nlp.model_name = 'test-model'
        mock_nlp.process_prompt.return_value = ('Resposta teste', 1.5)
        mock_repo.save_interaction.return_value = 'test_id'
        mock_repo.client = Mock()  # Simula MongoDB disponível
        
        response = self.client.post(
            '/',
            data=json.dumps({'prompt': 'teste'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('response', data)
        self.assertIn('processing_time', data)
        self.assertIn('model', data)
    
    @patch('app.views.nlp_service')
    def test_chat_view_post_empty_prompt(self, mock_nlp):
        """Testa validação de prompt vazio."""
        mock_nlp.model_name = 'test-model'
        
        response = self.client.post(
            '/',
            data=json.dumps({'prompt': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    @patch('app.views.nlp_service')
    def test_chat_view_post_long_prompt(self, mock_nlp):
        """Testa validação de prompt muito longo."""
        mock_nlp.model_name = 'test-model'
        
        long_prompt = 'a' * 501
        response = self.client.post(
            '/',
            data=json.dumps({'prompt': long_prompt}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    @patch('app.views.nlp_service')
    def test_chat_view_post_invalid_json(self, mock_nlp):
        """Testa tratamento de JSON inválido."""
        response = self.client.post(
            '/',
            data='{invalid json}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('app.views.nlp_service', None)
    def test_chat_view_post_nlp_unavailable(self):
        """Testa quando serviço NLP não está disponível."""
        response = self.client.post(
            '/',
            data=json.dumps({'prompt': 'teste'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertIn('error', data)


class TestHistoryView(TestCase):
    """Testes para a view de histórico."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.client = Client()
        
        # Mock do repositório
        self.mock_repo = Mock(spec=MongoRepository)
        self.mock_repo.get_interactions.return_value = []
    
    @patch('app.views.mongo_repo')
    def test_history_view_get(self, mock_repo):
        """Testa renderização da página de histórico (GET)."""
        mock_repo.get_interactions.return_value = []
        
        response = self.client.get('/history/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'history.html')
    
    @patch('app.views.mongo_repo')
    def test_history_view_with_filters(self, mock_repo):
        """Testa histórico com filtros de data."""
        mock_repo.get_interactions.return_value = []
        
        response = self.client.get('/history/', {
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        })
        
        self.assertEqual(response.status_code, 200)
        # Verifica se get_interactions foi chamado
        mock_repo.get_interactions.assert_called()
    
    @patch('app.views.mongo_repo')
    def test_history_view_pagination(self, mock_repo):
        """Testa paginação do histórico."""
        # Cria interações mock para testar paginação
        mock_interactions = [
            {'_id': i, 'prompt': f'teste {i}', 'response': 'resposta', 
             'processing_time': 1.0, 'model': 'test', 'timestamp': '2024-01-01'}
            for i in range(15)
        ]
        mock_repo.get_interactions.return_value = mock_interactions
        
        response = self.client.get('/history/', {'page': 1})
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/history/', {'page': 2})
        self.assertEqual(response.status_code, 200)


class TestExportHistory(TestCase):
    """Testes para exportação de histórico."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.client = Client()
    
    @patch('app.views.mongo_repo')
    def test_export_json(self, mock_repo):
        """Testa exportação em formato JSON."""
        from datetime import datetime
        mock_repo.get_interactions.return_value = [
            {
                '_id': 1,
                'prompt': 'teste',
                'response': 'resposta',
                'processing_time': 1.5,
                'model': 'test-model',
                'timestamp': datetime.now()
            }
        ]
        
        response = self.client.get('/export/', {'format': 'json'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertIn('attachment', response['Content-Disposition'])
        
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
    
    @patch('app.views.mongo_repo')
    def test_export_csv(self, mock_repo):
        """Testa exportação em formato CSV."""
        from datetime import datetime
        mock_repo.get_interactions.return_value = [
            {
                '_id': 1,
                'prompt': 'teste',
                'response': 'resposta',
                'processing_time': 1.5,
                'model': 'test-model',
                'timestamp': datetime.now()
            }
        ]
        
        response = self.client.get('/export/', {'format': 'csv'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(b'Timestamp', response.content)
        self.assertIn(b'Prompt', response.content)
    
    @patch('app.views.mongo_repo')
    def test_export_default_format(self, mock_repo):
        """Testa exportação com formato padrão (JSON)."""
        mock_repo.get_interactions.return_value = []
        
        response = self.client.get('/export/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
    
    @patch('app.views.mongo_repo')
    def test_export_invalid_format(self, mock_repo):
        """Testa exportação com formato inválido (deve usar JSON)."""
        mock_repo.get_interactions.return_value = []
        
        response = self.client.get('/export/', {'format': 'invalid'})
        
        # Deve retornar JSON mesmo com formato inválido
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')


if __name__ == '__main__':
    unittest.main()
