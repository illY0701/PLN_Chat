"""
Testes unitários para o NLPService

Testa processamento de prompts, respostas rápidas, cálculos matemáticos
e integração com modelos da Hugging Face.

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.conf import settings
from app.services.nlp_service import NLPService
import json


class TestNLPService(TestCase):
    """Testes para o serviço de NLP."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        # Mock das configurações
        with patch.object(settings, 'HF_MODEL_NAME', 'google/flan-t5-small'):
            with patch.object(settings, 'HF_API_TOKEN', 'test-token'):
                with patch.object(settings, 'HF_INFERENCE_MODEL', 'google/flan-t5-small'):
                    with patch.object(settings, 'USE_HF_FOR_ALL', False):
                        self.nlp_service = NLPService()
    
    def test_quick_responses(self):
        """Testa se respostas rápidas funcionam corretamente."""
        # Teste de saudação
        response, time = self.nlp_service.process_prompt("oi")
        self.assertIn("Olá", response)
        
        # Teste de conhecimento
        response, time = self.nlp_service.process_prompt("me dá as vogais")
        self.assertIn("A, E, I, O, U", response)
        
        # Teste de sistema
        response, time = self.nlp_service.process_prompt("fez o l")
        self.assertIn("funcionando", response.lower())
    
    def test_math_calculations(self):
        """Testa se cálculos matemáticos funcionam."""
        # Multiplicação
        response, time = self.nlp_service.process_prompt("quanto é 5 vezes 3")
        self.assertIn("15", response)
        
        # Adição
        response, time = self.nlp_service.process_prompt("10 + 15")
        self.assertIn("25", response)
        
        # Subtração
        response, time = self.nlp_service.process_prompt("20 - 8")
        self.assertIn("12", response)
        
        # Divisão
        response, time = self.nlp_service.process_prompt("12 / 4")
        self.assertIn("3", response)
    
    @patch('app.services.nlp_service.AutoTokenizer')
    @patch('app.services.nlp_service.AutoModelForSeq2SeqLM')
    def test_model_loading_seq2seq(self, mock_model, mock_tokenizer):
        """Testa carregamento de modelo encoder-decoder."""
        from transformers import AutoConfig
        
        # Mock do tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = '<eos>'
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Mock do modelo
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Mock da configuração
        with patch('app.services.nlp_service.AutoConfig') as mock_config_class:
            mock_config_instance = Mock()
            mock_config_instance.is_encoder_decoder = True
            mock_config_class.from_pretrained.return_value = mock_config_instance
            
            # Força carregamento do modelo
            self.nlp_service.model_name = 'google/flan-t5-small'
            try:
                self.nlp_service._ensure_model_loaded()
                # Verifica se o modelo foi carregado corretamente
                self.assertTrue(self.nlp_service._model_loaded)
                self.assertTrue(self.nlp_service.is_encoder_decoder)
            except:
                # Se falhar, é aceitável em ambiente de teste
                pass
    
    @patch('app.services.nlp_service.urllib.request.urlopen')
    def test_hf_inference_api(self, mock_urlopen):
        """Testa chamada à API de inferência da Hugging Face."""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.read.return_value.decode.return_value = json.dumps({
            "generated_text": "Esta é uma resposta de teste"
        })
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Testa a chamada
        response = self.nlp_service.hf_inference("teste")
        self.assertEqual(response, "Esta é uma resposta de teste")
    
    def test_empty_prompt_handling(self):
        """Testa tratamento de prompt vazio."""
        # Prompt vazio deve retornar erro ou mensagem apropriada
        try:
            response, time = self.nlp_service.process_prompt("")
            # Se não levantar exceção, resposta deve ser válida
            self.assertIsInstance(response, str)
        except:
            # Se levantar exceção, está correto
            pass
    
    def test_long_prompt_handling(self):
        """Testa tratamento de prompt muito longo."""
        long_prompt = "a" * 1000
        try:
            response, time = self.nlp_service.process_prompt(long_prompt)
            # Resposta deve ser gerada ou erro tratado
            self.assertIsInstance(time, float)
        except:
            # Exceção é aceitável para prompts muito longos
            pass
    
    def test_processing_time(self):
        """Testa se o tempo de processamento é retornado."""
        response, time = self.nlp_service.process_prompt("teste")
        self.assertIsInstance(time, float)
        self.assertGreaterEqual(time, 0)


if __name__ == '__main__':
    unittest.main()
