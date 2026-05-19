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



🔗 Добавлена ссылка: https://techcrunch.com/2026/05/19/gamified-social-media-network-status-announces-17m-funding-to-help-usher-in-new-era-of-social-networking/
📝 Публикую пост с параметрами: owner_id=-235704834, attachments=https://techcrunch.com/2026/05/19/gamified-social-media-network-status-announces-17m-funding-to-help-usher-in-new-era-of-social-networking/
❌ Ошибка VK API: [100] One of the parameters specified was missing or invalid: Violated: link_photo_sizing_rule. No photo given
🔄 Пробую опубликовать без вложений...
✅ Пост опубликован без вложений! ID: 33
📰 Добавляем новость: Forget the feed: Status AI raises $17M to turn soc...
✓ Новость добавлена в базу (ID: fb8f72c2...)

============================================================
📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:
============================================================

📝 Логи выполнения:
  Новая статья: Apple announces Apple Intelligence powered accessi...
  Дубликат: ‘Survivor’ stars Kyle Fraser and Kamilla Karthiges...
  Новая статья: Forget the feed: Status AI raises $17M to turn soc...
  Выбрана статья: Forget the feed: Status AI raises $17M to turn soc...
  Длина: 5011 символов
  Источник: https://techcrunch.com/feed/
  Статья переведена (4743 символов)
  Пост создан (617 символов)
  Публикация: ✅ Пост успешно опубликован в VK!
📝 ID поста: 33
🔗 Ссылка: https://vk.com/wall-235704834_33
📏 Длина: 617 символов
👥 Группа ID: 235704834
  Добавлено в базу: fb8f72c2-9e4e-4d93-959d-4c85e98433f3

📊 Статистика:
  • Всего статей собрано: 6
  • Новых статей (не дубликаты): 2
  • Статья выбрана: ✅ Да
  • Перевод готов: ✅ Да
  • Пост создан: ✅ Да
  • Опубликовано: ✅ Да
  • Общее время выполнения: 465.19 секунд

📊 Статистика БД после выполнения:
  • json_archive_count: 5
  • chroma_collection_count: 5
  • chroma_db_size_mb: 0.36
  • json_archive_size_mb: 0.02
  • embedding_model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  • similarity_threshold: 0.75

📄 Созданный пост:
----------------------------------------
🎉 Forget the feed: Status AI привнесет новую волну интерактивного развлечения на социальные сети! 🌟

Фай Нур, Амит Бхатнагар и Притеш Кадивал создали приложение, которое превращает обычные соцсети в живые игры. Здесь ты можешь стать знаменитостью, зрителем любимого сериала или даже президентом! 🌐✨

...
----------------------------------------

📰 Информация о статье:
  • Заголовок: Forget the feed: Status AI raises $17M to turn social media into interactive ent...
  • Источник: https://techcrunch.com/feed/
  • Дата: Tue, 19 Ma
  • URL: https://techcrunch.com/2026/05/19/gamified-social-media-netw...

🔗 Ссылка на трассировку: https://cloud.langfuse.com/trace/news_pipeline_20260519_175219_1
