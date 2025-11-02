import os
import django

# Ensure Django settings are loaded
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.services.nlp_service import NLPService

if __name__ == '__main__':
    svc = NLPService()
    prompt = "Qual é a capital da França?"
    print("Prompt:", prompt)
    resp = svc.hf_inference(prompt)
    print("Resposta HF:", resp)
