"""
Serviço de Processamento de Linguagem Natural (NLP)
Gerencia o carregamento e processamento de modelos da Hugging Face

Desenvolvido por: ANNA, CÉSAR E EVILY
"""

import time
import json
import re
import urllib.request
import urllib.error
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NLPService:
    """
    Serviço responsável pelo processamento de linguagem natural.
    
    Carrega modelos da Hugging Face localmente ou usa a API de inferência como fallback.
    Suporta modelos causais (GPT-like) e encoder-decoder (T5/Flan-like).
    """
    
    def __init__(self):
        """Inicializa o serviço NLP com configurações do Django settings."""
        self.model_name = settings.HF_MODEL_NAME
        self.api_token = settings.HF_API_TOKEN
        self.inference_model = getattr(settings, 'HF_INFERENCE_MODEL', 'google/flan-t5-small')
        
        self.model = None
        self.tokenizer = None
        self._model_loaded = False
        self.is_encoder_decoder = False
        
        # Detecta se há GPU disponível, caso contrário usa CPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"NLPService inicializado. Device: {self.device}")

    def _ensure_model_loaded(self):
        """
        Carrega o modelo e tokenizer apenas quando necessário (lazy loading).
        
        Detecta automaticamente o tipo de modelo (causal ou encoder-decoder)
        e carrega o modelo apropriado.
        """
        if self._model_loaded:
            return
        
        if not self.model_name:
            logger.error("HF_MODEL_NAME não configurado nas settings")
            raise RuntimeError('HF_MODEL_NAME não está configurado nas settings')
        
        try:
            logger.info(f"Carregando modelo: {self.model_name}")
            
            # Carrega o tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Detecta o tipo de modelo através da configuração
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(self.model_name)
            self.is_encoder_decoder = getattr(config, 'is_encoder_decoder', False)
            
            # Carrega o modelo apropriado baseado no tipo
            if self.is_encoder_decoder:
                logger.debug("Carregando modelo encoder-decoder (Seq2Seq)")
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            else:
                logger.debug("Carregando modelo causal (CausalLM)")
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Move o modelo para o dispositivo (GPU ou CPU)
            try:
                self.model.to(self.device)
            except Exception:
                # Fallback para CPU se falhar
                self.device = torch.device('cpu')
                self.model.to(self.device)
                logger.warning("Falha ao mover modelo para GPU, usando CPU")
            
            # Configura pad_token se não existir
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self._model_loaded = True
            logger.info(f"Modelo carregado com sucesso: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            self._model_loaded = False
            raise

    def hf_inference(self, prompt):
        """
        Usa a API de Inferência da Hugging Face para processar o prompt.
        
        Args:
            prompt (str): Texto a ser processado pelo modelo
            
        Returns:
            str: Resposta do modelo ou None em caso de erro
        """
        if not self.api_token:
            logger.warning("HF_API_TOKEN não configurado, API de inferência não disponível")
            return None
        
        try:
            api_url = f"https://api-inference.huggingface.co/models/{self.inference_model}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Formata o prompt para o modelo de inferência
            data = json.dumps({"inputs": prompt})
            data = data.encode('utf-8')
            
            req = urllib.request.Request(api_url, data=data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                
                # Extrai a resposta dependendo do formato retornado
                if isinstance(result, dict):
                    if 'generated_text' in result:
                        return result['generated_text']
                    elif 'summary_text' in result:
                        return result['summary_text']
                    elif isinstance(result.get('error'), str):
                        logger.error(f"Erro na API HF: {result['error']}")
                        return None
                
                if isinstance(result, list) and len(result) > 0:
                    first_item = result[0]
                    if isinstance(first_item, dict) and 'generated_text' in first_item:
                        return first_item['generated_text']
                    elif isinstance(first_item, str):
                        return first_item
                
                logger.warning(f"Formato de resposta inesperado da API: {result}")
                return None
                
        except urllib.error.HTTPError as e:
            logger.error(f"Erro HTTP na API de inferência: {e.code} - {e.reason}")
            if e.code == 503:
                logger.warning("Modelo ainda carregando na API, tentando novamente...")
                time.sleep(5)
                return self.hf_inference(prompt)  # Retry uma vez
            return None
        except Exception as e:
            logger.error(f"Erro ao chamar API de inferência: {e}")
            return None

    def process_prompt(self, prompt):
        """
        Processa um prompt e retorna a resposta do modelo.
        
        Implementa múltiplas camadas de processamento:
        1. Respostas rápidas para perguntas comuns
        2. Cálculos matemáticos automáticos
        3. Processamento pelo modelo local ou API
        
        Args:
            prompt (str): Texto de entrada do usuário
            
        Returns:
            tuple: (resposta, tempo_processamento) ou levanta RuntimeError
        """
        start_time = time.time()
        
        # Normaliza o prompt para comparações
        prompt_lower = prompt.lower().strip().replace('?', '').replace('.', '').replace(',', '')
        
        # ============================================
        # CÁLCULOS MATEMÁTICOS AUTOMÁTICOS
        # ============================================
        math_patterns = [
            # Multiplicação
            (r'quanto\s+é\s+(\d+)\s+vezes\s+(\d+)', lambda m: int(m.group(1)) * int(m.group(2))),
            (r'(\d+)\s+vezes\s+(\d+)', lambda m: int(m.group(1)) * int(m.group(2))),
            (r'(\d+)\s*[xX×]\s*(\d+)', lambda m: int(m.group(1)) * int(m.group(2))),
            # Adição
            (r'quanto\s+é\s+(\d+)\s+mais\s+(\d+)', lambda m: int(m.group(1)) + int(m.group(2))),
            (r'(\d+)\s+mais\s+(\d+)', lambda m: int(m.group(1)) + int(m.group(2))),
            (r'(\d+)\s*\+\s*(\d+)', lambda m: int(m.group(1)) + int(m.group(2))),
            # Subtração
            (r'quanto\s+é\s+(\d+)\s+menos\s+(\d+)', lambda m: int(m.group(1)) - int(m.group(2))),
            (r'(\d+)\s+menos\s+(\d+)', lambda m: int(m.group(1)) - int(m.group(2))),
            (r'(\d+)\s*-\s*(\d+)', lambda m: int(m.group(1)) - int(m.group(2))),
            # Divisão
            (r'quanto\s+é\s+(\d+)\s+dividido\s+por\s+(\d+)', lambda m: int(m.group(1)) / int(m.group(2)) if int(m.group(2)) != 0 else None),
            (r'(\d+)\s+dividido\s+por\s+(\d+)', lambda m: int(m.group(1)) / int(m.group(2)) if int(m.group(2)) != 0 else None),
            (r'(\d+)\s*/\s*(\d+)', lambda m: int(m.group(1)) / int(m.group(2)) if int(m.group(2)) != 0 else None),
        ]
        
        # Verifica se o prompt contém operação matemática
        for pattern, func in math_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                try:
                    result = func(match)
                    if result is None:
                        continue
                    # Formata resultado (remove .0 se for inteiro)
                    if isinstance(result, float) and result.is_integer():
                        result_str = str(int(result))
                    else:
                        result_str = f"{result:.2f}".rstrip('0').rstrip('.')
                    processing_time = time.time() - start_time
                    logger.info(f"Usando cálculo matemático para: {prompt[:50]}")
                    return f"O resultado é {result_str}", processing_time
                except Exception as e:
                    logger.debug(f"Erro no cálculo matemático: {e}")
                    continue
        
        # ============================================
        # RESPOSTAS RÁPIDAS PARA PERGUNTAS COMUNS
        # ============================================
        quick_responses = {
            # Saudações
            "oi": "Olá! Como posso ajudá-lo hoje?",
            "olá": "Olá! Em que posso ajudá-lo?",
            "bom dia": "Bom dia! Como posso ajudá-lo?",
            "boa tarde": "Boa tarde! Como posso ajudá-lo?",
            "boa noite": "Boa noite! Como posso ajudá-lo?",
            "oi tudo bem": "Tudo bem, obrigado! Como posso ajudá-lo?",
            "tudo bem": "Sim, tudo bem! Em que posso ajudá-lo?",
            "ping ping sam": "Ping pong! Sistema funcionando perfeitamente! 🏓",
            
            # Matemática comum
            "dois mais dois": "Quatro (4)",
            "2+2": "Quatro (4)",
            "dois vezes dois": "Quatro (4)",
            "2x2": "Quatro (4)",
            
            # Linguagem e Português
            "me dá as vogais": "As vogais do alfabeto português são: A, E, I, O, U.",
            "quais são as vogais": "As vogais são: A, E, I, O, U (e Y quando usado como vogal).",
            "me diga as vogais": "As vogais são: A, E, I, O, U.",
            "vogais": "As vogais do alfabeto português são: A, E, I, O, U.",
            
            # Animais
            "os leões tem quantas patas": "Os leões têm 4 patas.",
            "quantas patas tem um leão": "Um leão tem 4 patas.",
            "leão quantas patas": "Os leões têm 4 patas.",
            "quantas patas tem um cachorro": "Um cachorro tem 4 patas.",
            "quantas patas tem um gato": "Um gato tem 4 patas.",
            "quantas patas tem um cavalo": "Um cavalo tem 4 patas.",
            
            # Tecnologia
            "o que é python": "Python é uma linguagem de programação de alto nível, interpretada e de propósito geral, conhecida por sua simplicidade e legibilidade. É amplamente usada em desenvolvimento web, ciência de dados, automação e inteligência artificial.",
            "o que é django": "Django é um framework web de alto nível escrito em Python que facilita o desenvolvimento rápido de sites e aplicações web seguras e escaláveis.",
            "o que é javascript": "JavaScript é uma linguagem de programação usada principalmente para criar interatividade em páginas web. É uma das tecnologias fundamentais da web moderna.",
            
            # História e Geografia
            "quem descobriu o brasil": "Pedro Álvares Cabral descobriu o Brasil em 22 de abril de 1500.",
            "capital do brasil": "A capital do Brasil é Brasília, localizada no Distrito Federal.",
            "qual a capital da frança": "A capital da França é Paris.",
            "qual a capital da espanha": "A capital da Espanha é Madrid.",
            "qual a capital de portugal": "A capital de Portugal é Lisboa.",
            
            # Perguntas comuns
            "como você está": "Estou funcionando perfeitamente! Como posso ajudá-lo?",
            "qual seu nome": "Sou um assistente de IA especializado em Processamento de Linguagem Natural. Pode me chamar de PLN Assistant!",
            "quem é você": "Sou um assistente virtual inteligente desenvolvido para ajudar com perguntas e conversas em português.",
            
            # Sistema
            "fez o l": "Sim, fiz! O sistema está funcionando perfeitamente!",
            "teste": "Sistema funcionando! Estou pronto para ajudar.",
            "funciona": "Sim, o sistema está funcionando corretamente!",
            
            # Ciências
            "o que é água": "Água (H2O) é uma molécula composta por dois átomos de hidrogênio e um de oxigênio. É essencial para a vida e cobre cerca de 71% da superfície da Terra.",
            "quantos planetas existem": "No nosso Sistema Solar existem 8 planetas: Mercúrio, Vênus, Terra, Marte, Júpiter, Saturno, Urano e Netuno.",
            
            # Cultura
            "qual a maior cidade do brasil": "A maior cidade do Brasil é São Paulo, com aproximadamente 12 milhões de habitantes.",
            "quem escreveu romeu e julieta": "Romeu e Julieta foi escrita por William Shakespeare, o grande dramaturgo inglês.",
        }
        
        # Verifica se há resposta rápida disponível
        for key, response in quick_responses.items():
            if key in prompt_lower:
                processing_time = time.time() - start_time
                logger.info(f"Usando resposta rápida para: {prompt[:50]}")
                return response, processing_time
        
        # ============================================
        # USAR API DE INFERÊNCIA SE CONFIGURADO
        # ============================================
        if getattr(settings, 'USE_HF_FOR_ALL', False):
            logger.debug("USE_HF_FOR_ALL habilitado — usando API de Inferência HF")
            hf_resp = self.hf_inference(prompt)
            if hf_resp:
                processing_time = time.time() - start_time
                logger.info(f"Processado via API HF em {processing_time:.2f} segundos")
                return hf_resp, processing_time
            else:
                logger.debug("API HF não retornou resultado, usando modelo local")

        # ============================================
        # PROCESSAMENTO COM MODELO LOCAL
        # ============================================
        self._ensure_model_loaded()
        
        # Se o modelo não carregou, tenta usar API como fallback
        if not self._model_loaded or not self.model or not self.tokenizer:
            logger.warning("Modelo local não disponível, tentando API de inferência como fallback")
            hf_resp = self.hf_inference(prompt)
            if hf_resp:
                processing_time = time.time() - start_time
                logger.info(f"Processado via API HF (fallback) em {processing_time:.2f} segundos")
                return hf_resp, processing_time
            else:
                raise RuntimeError("Nem o modelo local nem a API de inferência estão disponíveis")
        
        try:
            # ============================================
            # FORMATAÇÃO DO PROMPT PARA O MODELO
            # ============================================
            instruction = (
                "Você é um assistente útil, educado e objetivo que SEMPRE responde APENAS em Português Brasileiro. "
                "NUNCA responda em inglês. Responda de forma direta, sem repetir a pergunta, "
                "sem usar palavras como 'question' ou 'questions', e forneça uma resposta clara e curta quando possível. "
                "Responda diretamente a pergunta sem ecoar o prompt."
            )

            if getattr(self, 'is_encoder_decoder', False):
                # Modelos encoder-decoder (T5, Flan-T5, etc.)
                if "flan" in self.model_name.lower() or "t5" in self.model_name.lower():
                    # Formato otimizado para Flan-T5
                    seq_input = f"Responda em português: {prompt}"
                else:
                    # Outros modelos seq2seq
                    seq_input = f"pergunta: {prompt} resposta:"
                
                # Tokeniza o input
                inputs = self.tokenizer(seq_input, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Gera a resposta
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=200,
                        min_length=10,
                        do_sample=True,
                        temperature=0.8,
                        top_k=50,
                        top_p=0.95,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.2,
                        pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id else self.tokenizer.eos_token_id,
                    )
                
                # Decodifica a resposta
                try:
                    response = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=True).strip()
                    
                    # Remove prefixos comuns que podem aparecer
                    prefixes_to_remove = ["resposta:", "Resposta:", "RESPOSTA:", "responda:", "Responda:", "RESPONDA:"]
                    for prefix in prefixes_to_remove:
                        if response.startswith(prefix):
                            response = response[len(prefix):].strip()
                    
                    # Detecta respostas ruins (mistura de idiomas)
                    has_english = any(word in response.lower() for word in ["what", "how", "does", "mean", "question"])
                    has_portuguese = any(word in response.lower() for word in ["que", "o", "a", "do", "da", "é"])
                    
                    if has_english and has_portuguese and len(response) < 50:
                        logger.warning(f"Resposta de baixa qualidade detectada: {response}")
                        if "does the question mean" in response.lower():
                            response = "Desculpe, não consegui processar essa pergunta adequadamente. Tente reformular ou ser mais específico."
                except Exception:
                    response = ""
                
                logger.debug(f"Input seq2seq: {seq_input}")
                logger.debug(f"Resposta gerada: {response}")
                
            else:
                # Modelos causais (GPT-like)
                formatted_prompt = f"{instruction}\nUser: {prompt}\nBot:"
                
                # Tokeniza o input
                inputs = self.tokenizer(formatted_prompt, return_tensors="pt", padding=True, truncation=True, return_attention_mask=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                input_ids = inputs["input_ids"]
                input_len = input_ids.shape[-1]

                # Gera a resposta
                with torch.no_grad():
                    outputs = self.model.generate(
                        input_ids,
                        attention_mask=inputs.get("attention_mask"),
                        max_new_tokens=150,
                        num_return_sequences=1,
                        do_sample=True,
                        temperature=0.7,
                        top_k=50,
                        top_p=0.95,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.1,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )

                # Decodifica apenas a parte gerada (não inclui o prompt)
                try:
                    full_decoded = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=True)
                except Exception:
                    full_decoded = ""

                generated_ids = outputs[0][input_len:]
                if generated_ids.shape[0] == 0:
                    response = full_decoded
                else:
                    response = self.tokenizer.decode(generated_ids.cpu(), skip_special_tokens=True).strip()

                logger.debug(f"Prompt formatado: {formatted_prompt}")
                logger.debug(f"Comprimento dos tokens: {input_len}")
                logger.debug(f"Resposta completa: {full_decoded}")
                logger.debug(f"Resposta gerada: {response}")

            # ============================================
            # TENTA REGENERAR SE A RESPOSTA FOR RUIM
            # ============================================
            if (not response) or (response.strip().lower() == prompt.strip().lower()) or (prompt.strip() in response):
                try:
                    alt_prompt = f"Por favor, responda de forma direta:\n{prompt}\nResposta:"
                    alt_inputs = self.tokenizer(alt_prompt, return_tensors="pt", padding=True, truncation=True, return_attention_mask=True)
                    alt_inputs = {k: v.to(self.device) for k, v in alt_inputs.items()}
                    alt_input_ids = alt_inputs['input_ids']
                    alt_input_len = alt_input_ids.shape[-1]
                    
                    with torch.no_grad():
                        alt_outputs = self.model.generate(
                            alt_input_ids,
                            attention_mask=alt_inputs.get('attention_mask'),
                            max_new_tokens=150,
                            num_return_sequences=1,
                            do_sample=True,
                            temperature=1.0,
                            top_k=50,
                            top_p=0.95,
                            no_repeat_ngram_size=3,
                            repetition_penalty=1.05,
                            pad_token_id=self.tokenizer.eos_token_id,
                        )
                    
                    try:
                        alt_full = self.tokenizer.decode(alt_outputs[0].cpu(), skip_special_tokens=True)
                    except Exception:
                        alt_full = ""
                    
                    alt_generated = alt_outputs[0][alt_input_len:]
                    if alt_generated.shape[0] > 0:
                        response = self.tokenizer.decode(alt_generated.cpu(), skip_special_tokens=True).strip()
                    
                    logger.debug(f"Resposta alternativa completa: {alt_full}")
                    logger.debug(f"Resposta alternativa gerada: {response}")
                except Exception:
                    pass

            # ============================================
            # LIMPEZA E PÓS-PROCESSAMENTO DA RESPOSTA
            # ============================================
            try:
                cleaned = response.strip()
                
                # Lista de padrões a remover (ecos de instruções)
                patterns_to_remove = [
                    instruction,
                    "Você é um assistente",
                    "Você é un assistente",
                    "assistente útil, educado e objetivo",
                    "Responda de forma direta",
                    "Responda em português",
                    "Responda em Português",
                    "responda:",
                    "Resposta:",
                    "resposta:",
                ]
                
                # Remove cada padrão
                for pattern in patterns_to_remove:
                    if pattern.lower() in cleaned.lower():
                        cleaned = cleaned.replace(pattern, "").replace(pattern.lower(), "").replace(pattern.upper(), "")
                        cleaned = cleaned.replace(pattern.capitalize(), "")
                
                # Remove o prompt original se aparecer no início
                if cleaned.lower().startswith(prompt.lower()):
                    cleaned = cleaned[len(prompt):].strip()
                
                # Para modelos seq2seq, remove prefixos específicos
                if getattr(self, 'is_encoder_decoder', False):
                    seq_prefixes = [
                        "Responda em português de forma clara e direta:",
                        "responda:",
                        "pergunta:",
                        "resposta:",
                        "Pergunta:",
                        "Resposta:"
                    ]
                    for prefix in seq_prefixes:
                        if cleaned.lower().startswith(prefix.lower()):
                            cleaned = cleaned[len(prefix):].strip()
                    
                    # Remove "Pergunta:" se aparecer
                    if cleaned.startswith("Pergunta:") or cleaned.startswith("pergunta:"):
                        if "Resposta:" in cleaned or "resposta:" in cleaned:
                            parts = cleaned.split("Resposta:") if "Resposta:" in cleaned else cleaned.split("resposta:")
                            if len(parts) > 1:
                                cleaned = parts[-1].strip()
                        else:
                            cleaned = cleaned.replace("Pergunta:", "").replace("pergunta:", "").replace(prompt, "").strip()
                
                # Remove ecos de 'User:'/'Bot:' para modelos causais
                if not getattr(self, 'is_encoder_decoder', False):
                    if 'formatted_prompt' in locals() and cleaned.startswith(formatted_prompt):
                        cleaned = cleaned[len(formatted_prompt):].strip()
                
                # Remove linhas que são apenas eco da instrução
                lines = cleaned.split('\n')
                filtered_lines = []
                for line in lines:
                    line_clean = line.strip()
                    skip = False
                    for pattern in patterns_to_remove:
                        if pattern.lower() in line_clean.lower() and len(line_clean) < 100:
                            skip = True
                            break
                    if not skip and line_clean:
                        filtered_lines.append(line)
                cleaned = '\n'.join(filtered_lines)
                
                # Limpa pontuação e espaços extras
                cleaned = cleaned.lstrip('\n\r :\t-')
                cleaned = cleaned.strip()
                
                # Se ainda contém muito da instrução, extrai apenas a parte significativa
                if len(cleaned) > 0 and (instruction[:20].lower() in cleaned.lower() or prompt.lower() in cleaned.lower()[:len(prompt)*2]):
                    parts = cleaned.split(prompt)
                    if len(parts) > 1:
                        cleaned = parts[-1].strip()
                
                # ============================================
                # DETECÇÃO DE RESPOSTAS DE BAIXA QUALIDADE
                # ============================================
                cleaned_lower = cleaned.lower()
                
                # Detecta inglês indesejado
                english_indicators = [
                    "question:", "questions:", "what", "how", "does", "are you", "is a", 
                    "is the", "the question", "does the question", "what does", "how does",
                    "are you a", "is it", "can you", "will you", "do you", "have you"
                ]
                has_english = any(indicator in cleaned_lower for indicator in english_indicators)
                has_question_words = any(word in cleaned_lower for word in ["question:", "questions:", "what", "how", "does", "mean"])
                has_unrelated_english = any(phrase in cleaned_lower for phrase in [
                    "how long", "does it take", "finish the", "the report", "to finish", "are you a", "is a"
                ])
                has_echo = any(phrase in cleaned_lower for phrase in ["pergunta:", "resposta:", "question:", "answer:", "questions:"])
                
                # Calcula similaridade com o prompt
                prompt_words = set(prompt_lower.split())
                response_words = set(cleaned_lower.split())
                similarity = len(prompt_words.intersection(response_words)) / max(len(prompt_words), 1)
                
                # Verifica se começa com perguntas em inglês
                starts_with_english_question = cleaned_lower.startswith(("question", "questions", "what", "how", "does", "are you", "is a"))
                
                # Determina se a resposta é ruim
                is_bad_response = (
                    not cleaned or
                    len(cleaned) < 3 or
                    cleaned.lower() == prompt.lower() or
                    similarity > 0.7 or
                    starts_with_english_question or
                    ("question:" in cleaned_lower or "questions:" in cleaned_lower) or
                    ("does the question mean" in cleaned_lower) or
                    (has_english and len(cleaned) < 60) or
                    (has_question_words and has_unrelated_english) or
                    (has_question_words and len(cleaned) < 40) or
                    (has_echo and len(cleaned) < 20) or
                    (has_english and "pata" in cleaned_lower) or
                    (any(word in cleaned_lower for word in ["what", "how", "does", "are you"]) and
                     any(word in cleaned_lower for word in ["que", "o", "a"]) and len(cleaned) < 50)
                )
                
                # Se a resposta é ruim, tenta melhorar
                if is_bad_response:
                    logger.warning(f"Resposta de baixa qualidade detectada (similaridade: {similarity:.2f}, tem_ingles: {has_english})")
                    
                    # Tenta regenerar se está em inglês
                    if has_english or starts_with_english_question:
                        try:
                            alt_seq = f"Responda APENAS em português brasileiro: {prompt}"
                            alt_inputs = self.tokenizer(alt_seq, return_tensors="pt", padding=True, truncation=True, max_length=512)
                            alt_inputs = {k: v.to(self.device) for k, v in alt_inputs.items()}
                            
                            with torch.no_grad():
                                alt_outputs = self.model.generate(
                                    **alt_inputs,
                                    max_new_tokens=150,
                                    min_length=10,
                                    do_sample=True,
                                    temperature=0.9,
                                    repetition_penalty=1.3,
                                    no_repeat_ngram_size=3,
                                    pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id else self.tokenizer.eos_token_id,
                                )
                            
                            alt_response = self.tokenizer.decode(alt_outputs[0].cpu(), skip_special_tokens=True).strip()
                            alt_lower = alt_response.lower()
                            
                            # Verifica se a nova resposta é melhor
                            if not any(word in alt_lower for word in ["question", "questions", "what", "how", "does", "are you"]):
                                cleaned = alt_response
                                logger.info("Resposta regenerada com sucesso sem inglês")
                        except Exception as e:
                            logger.debug(f"Falha ao regenerar resposta: {e}")
                    
                    # Se ainda está ruim, tenta API de inferência
                    if is_bad_response and (has_english or not cleaned or len(cleaned) < 5):
                        logger.warning("Tentando API de inferência como fallback")
                        hf_resp = self.hf_inference(prompt)
                        if hf_resp and hf_resp.strip() and hf_resp.lower() != prompt.lower() and len(hf_resp) > 10:
                            hf_lower = hf_resp.lower()
                            hf_similarity = len(prompt_words.intersection(set(hf_lower.split()))) / max(len(prompt_words), 1)
                            hf_has_english = any(word in hf_lower for word in ["question", "questions", "what", "how", "does", "are you"])
                            
                            if hf_similarity < 0.6 and not hf_has_english:
                                cleaned = hf_resp.strip()
                            else:
                                cleaned = "Desculpe, não consegui entender sua pergunta. Pode reformular de outra forma?"
                        elif not cleaned or len(cleaned) < 5:
                            cleaned = "Desculpe, não consegui gerar uma resposta adequada para essa pergunta. Poderia reformular de outra forma?"
                
                response = cleaned.strip()
                
            except Exception as e:
                logger.debug(f"Erro durante limpeza da resposta: {e}")
                response = "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente."

            processing_time = time.time() - start_time
            logger.info(f"Prompt processado em {processing_time:.2f} segundos")

            return response, processing_time
            
        except Exception as e:
            logger.exception(f"Erro ao processar prompt: {e}")
            # Último recurso: tenta API de inferência
            hf_resp = self.hf_inference(prompt)
            if hf_resp:
                processing_time = time.time() - start_time
                return hf_resp, processing_time
            raise
