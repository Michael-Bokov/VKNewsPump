# Линейный пайплайн
rss_agent → translator → post_generator → publisher

[RSS Agent] -> [Translation Agent] -> [Post Generator] -> [VK Publisher]
      ↓               ↓                   ↓                   ↓
[ChromaDB]      [Ollama]             [Ollama]           [VK API]


# LangGraph: Граф состояний
[State] → (RSS Node) → (Deduplication Node) → (select_article Node) →(Translation Node) → ...
                                             
     ... →  (generate_post) →  (publish Node)
1. Создаем venv
python3 -m venv venv
2. Устанавливаем зависимости
pip install -r requirements.txt
3.   
python3 database.py - Создание локальной ChromaDB (Хранение опубликованных новостей)
4. Создаем .env - окружение со своими  
LANGFUSE_PUBLIC_KEY = ""
LANGFUSE_SECRET_KEY = ""
VK_ACCESS_TOKEN =""
VK_GROUP_ID = 
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_HOST="http://localhost:11435"
OLLAMA_BASE_URL = "http://localhost:11435"
По умолчанию ollama идет на порт 11344. В данном случае в docker-compose порт 11345  
5. docker-compose --profile 7b up -d  


clear_database.py - Очистка базы  
direct_ * - Агенты  
direct_pipeline.py -  Прямой линейный пайплайн  
lg_ * - LangGraph версия, обертки на агенты  
docker-compose.yml -  Контейнер для Ollama c исполняемым init.sh для развертывания qwen2.5-7b внутри контейнера  
6. langgraph_pipeline_with_langfuse.py - LangGraph пайплайн  
