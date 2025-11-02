from unittest import TestCase
from unittest.mock import patch, MagicMock
from app.services.nlp_service import NLPService
import json

class DummyResponse:
    def __init__(self, data_bytes):
        self._data = data_bytes
    
    def read(self):
        return self._data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        return False


class TestHFInference(TestCase):
    @patch('app.services.nlp_service.urllib.request.urlopen')
    @patch('app.services.nlp_service.settings')
    def test_hf_inference_returns_text(self, mock_settings, mock_urlopen):
        # configure settings to have an API token and model id
        mock_settings.HF_API_TOKEN = 'fake-token'
        mock_settings.HF_INFERENCE_MODEL = 'org/fake-model'

        # mock response JSON from HF Inference
        response_obj = [{'generated_text': 'Resposta via HF'}]
        resp_bytes = json.dumps(response_obj).encode('utf-8')
        mock_urlopen.return_value = DummyResponse(resp_bytes)

        service = NLPService()
        result = service.hf_inference('Teste')

        self.assertEqual(result, 'Resposta via HF')