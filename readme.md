# Линейный пайплайн
rss_agent → translator → post_generator → publisher

[RSS Agent] -> [Translation Agent] -> [Post Generator] -> [VK Publisher]
      ↓               ↓                   ↓                   ↓
[ChromaDB]      [Ollama]             [Ollama]           [VK API]


# LangGraph: Граф состояний
[State] → (RSS Node) → (Deduplication Node) → (select_article Node) →(Translation Node) → ...
                                             
     ... →  (generate_post) →  (publish Node)

database.py - Создание локальной ChromaDB (Хранение опубликованных новостей)
clear_database.py - Очистка базы
direct_ * - Агенты
direct_pipeline.py -  Прямой линейный пайплайн

lg_ * - LangGraph версия, обертки на агенты
langgraph_pipeline_with_langfuse.py - LangGraph пайплайн

docker-compose.yml -  Контейнер для Ollama c исполняемым init.sh для развертывания qwen2.5-7b внутри контейнера