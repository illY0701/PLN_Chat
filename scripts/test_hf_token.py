import os
from dotenv import load_dotenv
from huggingface_hub import HfApi

load_dotenv('.env')

token = os.getenv('HF_API_TOKEN')
model = os.getenv('HF_MODEL_NAME', 'gpt2')

if not token or 'your-' in token:
    print('HF_API_TOKEN aparentemente nao configurado no .env (placeholder detectado).')
    raise SystemExit(1)

api = HfApi()
try:
    user = api.whoami(token=token)
    print('Token válido. Usuário Hugging Face:', user.get('name') or user.get('user', {}).get('name') or user)
except Exception as e:
    print('Erro ao validar token Hugging Face:', str(e))
    raise
