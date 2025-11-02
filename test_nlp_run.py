import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','project.settings')

from app.services.nlp_service import NLPService

if __name__ == '__main__':
    s = NLPService()
    r, t = s.process_prompt('Olá, quem descobriu o Brasil?')
    print('Response:', r)
    print('Time:', t)
