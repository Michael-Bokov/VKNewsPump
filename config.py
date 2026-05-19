# config.py
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

load_dotenv()

@dataclass
class Config:
    # Пути
    BASE_DIR = Path(__file__).parent
    CHROMA_DB_PATH = BASE_DIR / "chroma_db"
    NEWS_JSON_PATH = BASE_DIR / "data" / "news_archive.json"
    RESULTS_DIR = BASE_DIR / "results"
    
    # VK API
    VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
    VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", 0))
    
    # Langfuse (Cloud) - опционально
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_HOST = "https://cloud.langfuse.com"
    
    # LLM настройки
    #OLLAMA_MODEL = "qwen2.5:7b"  # Модель по умолчанию
    OLLAMA_HOST = "http://localhost:11435"
    # Ollama
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11435')
    
    # RSS источники (используются гибридным агентом)
    # Эти фиды передаются в HybridRSSAgent через его внутренние настройки
    
    # Настройки RAG
    SIMILARITY_THRESHOLD = 0.75
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Настройки парсинга
    MAX_NEWS_PER_RUN = 5
    MIN_NEWS_LENGTH = 100
    
    # Даты
    TODAY = datetime.now().strftime("%Y-%m-%d")
    
    # Логирование
    LOG_LEVEL = "INFO"
     
        
    # RSS фиды (по умолчанию)
    DEFAULT_RSS_FEEDS = [
        "https://research.google/blog/rss/",
        "https://techcrunch.com/feed/",
        #"https://www.deepmind.com/blog/rss.xml",
        #"https://www.marktechpost.com/feed/",
    ]
    
    # Папки
    BASE_DIR = Path(__file__).parent.absolute()
    IMAGES_DIR = BASE_DIR / "images"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Создаем необходимые папки
    for directory in [IMAGES_DIR, DATA_DIR, LOGS_DIR]:
        directory.mkdir(exist_ok=True)
    
    # Проверяем обязательные настройки
    @classmethod
    def validate(cls):
        """Проверяет обязательные настройки"""
        errors = []
        
        if not cls.VK_ACCESS_TOKEN:
            errors.append("Не установлен VK_ACCESS_TOKEN")
        
        if not cls.VK_GROUP_ID:
            errors.append("Не установлен VK_GROUP_ID")
        
        if errors:
            raise ValueError(f"Ошибки конфигурации:\n" + "\n".join(f"  • {e}" for e in errors))
        
        print("✅ Конфигурация загружена успешно")
        return True
    
    @classmethod
    def print_summary(cls):
        """Выводит сводку конфигурации"""
        summary = [
            "📋 Сводка конфигурации:",
            f"  VK Group ID: {cls.VK_GROUP_ID}",
            f"  VK Token: {'✓' if cls.VK_ACCESS_TOKEN else '✗'}",
            f"  Ollama Model: {cls.OLLAMA_MODEL}",
            f"  RSS Feeds: {len(cls.DEFAULT_RSS_FEEDS)}",
            f"  Images Dir: {cls.IMAGES_DIR}",
        ]
        
        print("\n".join(summary))