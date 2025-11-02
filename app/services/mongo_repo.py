"""
Repositório MongoDB para persistência de interações de chat

Gerencia conexão e operações no banco de dados MongoDB.
Implementa fallback para SQLite quando MongoDB não está disponível.

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

from pymongo import MongoClient
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoRepository:
    """
    Repositório para gerenciar interações de chat no MongoDB.
    
    Suporta graceful degradation: se MongoDB não estiver disponível,
    usa SQLite como fallback para garantir que os dados sejam salvos.
    """
    
    def __init__(self):
        """
        Inicializa a conexão com MongoDB.
        
        Se a conexão falhar, o repositório continua funcionando
        mas sem persistência (graceful degradation).
        """
        self.client = None
        self.db = None
        self.collection = None
        
        try:
            if not settings.MONGODB_URI:
                logger.warning("MONGODB_URI não configurado nas settings")
                return
            
            # Tenta conectar ao MongoDB com timeout curto
            self.client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[settings.MONGODB_DB]
            self.collection = self.db['chat_interactions']
            
            # Testa a conexão
            self.client.admin.command('ping')
            logger.info("Conexão com MongoDB estabelecida com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao MongoDB: {str(e)}")
            # Não levanta exceção - permite graceful degradation
            self.client = None
            self.db = None
            self.collection = None

    def save_interaction(self, interaction_data):
        """
        Salva uma interação de chat no banco de dados.
        
        Tenta salvar no MongoDB primeiro. Se falhar, usa SQLite como fallback.
        
        Args:
            interaction_data (dict): Dicionário contendo:
                - prompt: pergunta do usuário
                - response: resposta do modelo
                - processing_time: tempo de processamento em segundos
                - model: nome do modelo usado
                
        Returns:
            str/int: ID da interação salva ou None se falhar completamente
        """
        if self.collection is None:
            logger.debug("MongoDB não disponível, tentando fallback SQLite")
            return self._save_to_sqlite(interaction_data)
        
        try:
            # Adiciona timestamp
            interaction_data['timestamp'] = datetime.now()
            
            # Insere no MongoDB
            result = self.collection.insert_one(interaction_data)
            logger.info(f"Interação salva no MongoDB com ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Erro ao salvar interação no MongoDB: {str(e)}")
            # Tenta fallback para SQLite
            return self._save_to_sqlite(interaction_data)

    def _save_to_sqlite(self, interaction_data):
        """
        Salva interação no SQLite como fallback.
        
        Args:
            interaction_data (dict): Dados da interação
            
        Returns:
            int: ID da interação salva ou None se falhar
        """
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Cria tabela se não existir
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        processing_time REAL,
                        model TEXT,
                        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insere a interação
                cursor.execute("""
                    INSERT INTO chat_interactions (prompt, response, processing_time, model, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    interaction_data.get('prompt', ''),
                    interaction_data.get('response', ''),
                    interaction_data.get('processing_time', 0),
                    interaction_data.get('model', ''),
                    datetime.now()
                ])
                
                logger.info("Interação salva no SQLite (fallback)")
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Erro ao salvar no SQLite: {e}")
            return None

    def get_interactions(self, filters=None):
        """
        Recupera interações de chat com filtros opcionais.
        
        Tenta buscar no MongoDB primeiro. Se não disponível, usa SQLite.
        
        Args:
            filters (dict, optional): Filtros de busca. Pode conter:
                - timestamp: dict com $gte e/ou $lte para filtro por data
                
        Returns:
            list: Lista de interações encontradas
        """
        if self.collection is None:
            logger.debug("MongoDB não disponível, buscando no SQLite")
            return self._get_from_sqlite(filters)
        
        try:
            if filters is None:
                filters = {}
            
            # Converte filtros de data para objetos datetime do MongoDB
            mongo_filters = {}
            if 'timestamp' in filters and isinstance(filters['timestamp'], dict):
                from datetime import datetime as dt
                if '$gte' in filters['timestamp']:
                    mongo_filters['timestamp'] = {'$gte': dt.fromisoformat(filters['timestamp']['$gte'])}
                if '$lte' in filters['timestamp']:
                    if 'timestamp' in mongo_filters:
                        mongo_filters['timestamp']['$lte'] = dt.fromisoformat(filters['timestamp']['$lte'])
                    else:
                        mongo_filters['timestamp'] = {'$lte': dt.fromisoformat(filters['timestamp']['$lte'])}
            
            # Busca no MongoDB ordenado por timestamp (mais recente primeiro)
            cursor = self.collection.find(mongo_filters if mongo_filters else filters).sort('timestamp', -1)
            interactions = list(cursor)
            
            logger.info(f"Recuperadas {len(interactions)} interações do MongoDB")
            return interactions
            
        except Exception as e:
            logger.error(f"Erro ao recuperar interações do MongoDB: {str(e)}")
            # Fallback para SQLite
            return self._get_from_sqlite(filters)

    def _get_from_sqlite(self, filters=None):
        """
        Recupera interações do SQLite com filtros opcionais.
        
        Args:
            filters (dict, optional): Filtros de busca
            
        Returns:
            list: Lista de interações encontradas
        """
        try:
            from django.db import connection
            from datetime import datetime as dt
            
            with connection.cursor() as cursor:
                # Cria tabela se não existir
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        processing_time REAL,
                        model TEXT,
                        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Monta query com filtros
                query = "SELECT id, prompt, response, processing_time, model, timestamp FROM chat_interactions WHERE 1=1"
                params = []
                
                if filters:
                    date_from = filters.get('timestamp', {}).get('$gte') if isinstance(filters.get('timestamp'), dict) else None
                    date_to = filters.get('timestamp', {}).get('$lte') if isinstance(filters.get('timestamp'), dict) else None
                    
                    if date_from:
                        query += " AND DATE(timestamp) >= ?"
                        params.append(date_from)
                    if date_to:
                        query += " AND DATE(timestamp) <= ?"
                        params.append(date_to)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Converte resultados para formato compatível com MongoDB
                interactions = []
                for row in rows:
                    try:
                        # Tenta parsear timestamp com diferentes formatos
                        timestamp_str = row[5]
                        if '.' in timestamp_str:
                            timestamp = dt.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            timestamp = dt.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        timestamp = dt.now()
                    
                    interactions.append({
                        '_id': row[0],
                        'prompt': row[1],
                        'response': row[2],
                        'processing_time': row[3] or 0,
                        'model': row[4] or 'local',
                        'timestamp': timestamp
                    })
                
                logger.info(f"Recuperadas {len(interactions)} interações do SQLite")
                return interactions
                
        except Exception as e:
            logger.error(f"Erro ao recuperar do SQLite: {e}")
            return []

    def __del__(self):
        """Fecha a conexão com MongoDB quando o objeto é destruído."""
        try:
            if self.client:
                self.client.close()
        except:
            pass
