"""
Views da aplicação PLN Chat

Gerencia as requisições HTTP e interage com os serviços de NLP e MongoDB.

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

import json
import csv
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .services.nlp_service import NLPService
from .services.mongo_repo import MongoRepository
import logging

logger = logging.getLogger(__name__)

# ============================================
# INICIALIZAÇÃO DOS SERVIÇOS
# ============================================

# Inicializa o serviço NLP de forma lazy para evitar erros na inicialização
try:
    nlp_service = NLPService()
    logger.info("Serviço NLP inicializado com sucesso")
except Exception as e:
    logger.error(f"Falha ao inicializar serviço NLP: {e}")
    nlp_service = None

# Inicializa o repositório MongoDB com graceful degradation
try:
    mongo_repo = MongoRepository()
    if mongo_repo.client:
        logger.info("Repositório MongoDB inicializado com sucesso")
except Exception as e:
    logger.warning(f"Falha na conexão MongoDB na inicialização: {e}. A aplicação continuará sem MongoDB.")
    mongo_repo = None


@csrf_exempt
def chat_view(request):
    """
    View principal do chat.
    
    GET: Renderiza a página do chat
    POST: Processa mensagens e retorna respostas JSON
    
    Args:
        request: HttpRequest do Django
        
    Returns:
        HttpResponse: Template renderizado (GET) ou JSON response (POST)
    """
    if request.method == 'POST':
        try:
            # Verifica se o serviço NLP está disponível
            if nlp_service is None:
                return JsonResponse({
                    'error': 'Serviço NLP não disponível. Verifique os logs do servidor.'
                }, status=503)
            
            # Parse do JSON do body da requisição
            data = json.loads(request.body)
            prompt = data.get('prompt', '').strip()
            
            # Validação do prompt
            if not prompt:
                return JsonResponse({
                    'error': 'Prompt não pode estar vazio'
                }, status=400)
            
            if len(prompt) > 500:
                return JsonResponse({
                    'error': 'Prompt muito longo. Máximo de 500 caracteres.'
                }, status=400)
            
            logger.debug(f"Prompt recebido: {prompt}")
            
            # Processa o prompt através do modelo NLP
            response, processing_time = nlp_service.process_prompt(prompt)
            logger.debug(f"Resposta do modelo: {response} (tempo={processing_time:.2f}s)")
            
            # Salva a interação no banco de dados
            if mongo_repo:
                try:
                    mongo_repo.save_interaction({
                        'prompt': prompt,
                        'response': response,
                        'processing_time': processing_time,
                        'model': nlp_service.model_name,
                    })
                    logger.debug("Interação salva no banco de dados")
                except Exception as e:
                    # Registra erro mas não falha a requisição se MongoDB temporariamente indisponível
                    logger.error(f"Falha ao salvar interação no MongoDB: {e}")
            
            # Retorna resposta JSON com os dados da interação
            return JsonResponse({
                'response': response,
                'processing_time': processing_time,
                'model': nlp_service.model_name
            })
            
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON do body")
            return JsonResponse({
                'error': 'Formato JSON inválido'
            }, status=400)
            
        except Exception as e:
            logger.exception(f"Erro ao processar requisição de chat: {str(e)}")
            return JsonResponse({
                'error': 'Ocorreu um erro ao processar sua solicitação'
            }, status=500)
    
    # GET: Renderiza o template do chat
    return render(request, 'chat.html')


def history_view(request):
    """
    View para exibir o histórico de conversas.
    
    Suporta filtros por data e paginação.
    
    Args:
        request: HttpRequest do Django com query parameters opcionais:
            - page: número da página (padrão: 1)
            - date_from: data inicial (formato: YYYY-MM-DD)
            - date_to: data final (formato: YYYY-MM-DD)
        
    Returns:
        HttpResponse: Template renderizado com histórico paginado
    """
    # Obtém o número da página da query string
    page = request.GET.get('page', 1)
    filters = {}
    
    # Aplica filtros de data dos parâmetros da query
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Constrói filtros para o MongoDB
    if date_from:
        filters['timestamp'] = {'$gte': date_from}
    if date_to:
        if 'timestamp' in filters:
            filters['timestamp']['$lte'] = date_to
        else:
            filters['timestamp'] = {'$lte': date_to}
    
    # Busca interações do MongoDB (ou SQLite se MongoDB não disponível)
    interactions = []
    if mongo_repo:
        try:
            interactions = mongo_repo.get_interactions(filters)
        except Exception as e:
            logger.error(f"Falha ao recuperar interações do MongoDB: {e}")
            interactions = []
    
    # Implementa paginação (10 itens por página)
    paginator = Paginator(interactions, 10)
    try:
        page_obj = paginator.get_page(page)
    except:
        page_obj = paginator.get_page(1)
    
    # Renderiza template com histórico paginado
    return render(request, 'history.html', {
        'page_obj': page_obj,
        'date_from': date_from,
        'date_to': date_to
    })


def export_history(request):
    """
    View para exportar histórico de conversas.
    
    Suporta exportação em JSON ou CSV.
    
    Args:
        request: HttpRequest com query parameter:
            - format: 'json' ou 'csv' (padrão: 'json')
        
    Returns:
        HttpResponse: Arquivo para download (JSON ou CSV)
    """
    format_type = request.GET.get('format', 'json').lower()
    
    # Valida formato
    if format_type not in ['json', 'csv']:
        format_type = 'json'
    
    # Busca todas as interações
    interactions = []
    if mongo_repo:
        try:
            interactions = mongo_repo.get_interactions({})
        except Exception as e:
            logger.error(f"Falha ao recuperar interações para exportação: {e}")
            interactions = []
    
    # Prepara dados para serialização
    export_data = []
    for interaction in interactions:
        export_data.append({
            'timestamp': interaction.get('timestamp').isoformat() if hasattr(interaction.get('timestamp'), 'isoformat') else str(interaction.get('timestamp')),
            'prompt': interaction.get('prompt', ''),
            'response': interaction.get('response', ''),
            'processing_time': interaction.get('processing_time', 0),
            'model': interaction.get('model', 'local')
        })
    
    # Exporta em JSON
    if format_type == 'json':
        response = HttpResponse(content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="chat_history.json"'
        json.dump(export_data, response, ensure_ascii=False, indent=2)
        return response
    
    # Exporta em CSV
    else:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="chat_history.csv"'
        response.write('\ufeff')  # BOM para Excel reconhecer UTF-8
        
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Prompt', 'Response', 'Processing Time (s)', 'Model'])
        
        for interaction in export_data:
            writer.writerow([
                interaction['timestamp'],
                interaction['prompt'],
                interaction['response'],
                interaction['processing_time'],
                interaction['model']
            ])
        
        return response
