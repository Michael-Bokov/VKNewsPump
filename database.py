import json
import hashlib
from pathlib import Path
import chromadb 
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Tuple
import uuid

from config import Config

class NewsDatabase:
    def __init__(self):
        """Инициализация базы данных новостей"""
        # Создаем директории если их нет
        Config.CHROMA_DB_PATH.mkdir(exist_ok=True)
        Config.NEWS_JSON_PATH.parent.mkdir(exist_ok=True)
        
        # Инициализируем ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(Config.CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Создаем/получаем коллекцию для новостей
        self.collection = self.chroma_client.get_or_create_collection(
            name="news_articles",
            metadata={"hnsw:space": "cosine"}  # для косинусного сходства
        )
        
        # Загружаем модель для эмбеддингов
        print(f"Загружаем модель эмбеддингов: {Config.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        print(f"✓ Модель загружена. Размерность: {self.embedding_model.get_sentence_embedding_dimension()}")
        
        # Загружаем JSON архив
        self.news_archive = self._load_news_archive()
        
        print(f"База инициализирована. Новостей в архиве: {len(self.news_archive)}")
    
    def _load_news_archive(self) -> List[Dict]:
        """Загружаем архив новостей из JSON"""
        if Config.NEWS_JSON_PATH.exists():
            try:
                with open(Config.NEWS_JSON_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    else:
                        print("⚠️ JSON не является списком. Создаю новый архив.")
                        return []
            except Exception as e:
                print(f"⚠️ Ошибка загрузки JSON: {e}. Создаю новый архив.")
                return []
        return []
    
    def _save_news_archive(self):
        """Сохраняем архив новостей в JSON"""
        try:
            with open(Config.NEWS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.news_archive, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения JSON: {e}")
    
    def _calculate_hash(self, text: str) -> str:
        """Вычисляем MD5 хэш текста для быстрой проверки дубликатов"""
        return hashlib.md5(text.strip().encode()).hexdigest()
    
    def _get_embedding(self, text: str) -> List[float]:
        """Получаем эмбеддинг для текста"""
        # Обрезаем текст для скорости
        text = text[:2000]
        return self.embedding_model.encode(text).tolist()
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисляем косинусное сходство между двумя векторами"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    
    def is_duplicate(self, news_item: Dict) -> Tuple[bool, str, float]:
        """
        Проверяем, есть ли такая новость уже
        Возвращает (is_duplicate, reason, best_similarity)
        """
        title = news_item.get("title", "")
        text = news_item.get("full_text", "")
        
        if not text and not title:
            return False, "No text to check", 0.0
        
        # 1. Быстрая проверка по хэшу заголовка + начала текста
        combined_text = f"{title}\n{text[:500]}"
        news_hash = self._calculate_hash(combined_text)
        
        for existing_news in self.news_archive:
            if existing_news.get("hash") == news_hash:
                return True, "Exact hash match", 1.0
        
        # 2. Векторный поиск похожих новостей
        try:
            # Генерируем эмбеддинг для поиска
            search_text = f"{title}\n{text[:1000]}" if text else title
            query_embedding = self._get_embedding(search_text)
            
            # Ищем в ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["embeddings", "metadatas", "distances"]
            )
            
            if results["distances"] and len(results["distances"][0]) > 0:
                # ChromaDB возвращает расстояния (чем меньше, тем ближе)
                # Преобразуем расстояние в сходство: similarity = 1 - distance
                distances = results["distances"][0]
                best_distance = min(distances)
                best_similarity = 1 - best_distance
                
                if best_similarity > Config.SIMILARITY_THRESHOLD:
                    return True, f"Similar article found", best_similarity
                
                return False, "Not similar enough", best_similarity
            
        except Exception as e:
            print(f"⚠️ Ошибка векторного поиска: {e}")
        
        return False, "No similar articles found", 0.0
    
    def add_news(self, news_item: Dict) -> str:
        """Добавляем новую новость в оба хранилища"""
        # Генерируем уникальный ID
        news_id = str(uuid.uuid4())
        news_item["id"] = news_id
        news_item["created_at"] = news_item.get("date", "")
        
        # Добавляем хэш
        title = news_item.get("title", "")
        text = news_item.get("full_text", "")
        combined_text = f"{title}\n{text[:500]}"
        news_item["hash"] = self._calculate_hash(combined_text)
        
        print(f"📰 Добавляем новость: {title[:50]}...")
        
        # 1. Добавляем в JSON архив
        self.news_archive.append(news_item)
        self._save_news_archive()
        
        # 2. Добавляем в ChromaDB
        try:
            # Текст для эмбеддинга
            embedding_text = f"{title}\n{text[:2000]}" if text else title
            embedding = self._get_embedding(embedding_text)
            
            # Метаданные для ChromaDB
            metadata = {
                "id": news_id,
                "title": title,
                "url": news_item.get("url", ""),
                "date": news_item.get("date", ""),
                "source": news_item.get("source", ""),
                "hash": news_item["hash"],
                "added_at": str(uuid.uuid1())  # для уникальности
            }
            
            # Добавляем в коллекцию
            self.collection.add(
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[news_id]
            )
            
            print(f"✓ Новость добавлена в базу (ID: {news_id[:8]}...)")
            
        except Exception as e:
            print(f"✗ Ошибка добавления в ChromaDB: {e}")
            import traceback
            traceback.print_exc()
        
        return news_id
    
    def get_recent_news(self, limit: int = 10) -> List[Dict]:
        """Получаем последние новости"""
        return sorted(
            self.news_archive,
            key=lambda x: x.get("date", "0000-00-00"),
            reverse=True
        )[:limit]
    
    def get_stats(self) -> Dict:
        """Статистика базы данных"""
        try:
            chroma_count = self.collection.count()
        except:
            chroma_count = 0
            
        # Получаем размеры
        chroma_size = 0
        if Config.CHROMA_DB_PATH.exists():
            chroma_size = sum(f.stat().st_size for f in Config.CHROMA_DB_PATH.rglob('*') if f.is_file())
        
        json_size = Config.NEWS_JSON_PATH.stat().st_size if Config.NEWS_JSON_PATH.exists() else 0
        
        return {
            "json_archive_count": len(self.news_archive),
            "chroma_collection_count": chroma_count,
            "chroma_db_size_mb": round(chroma_size / 1024 / 1024, 2),
            "json_archive_size_mb": round(json_size / 1024 / 1024, 2),
            "embedding_model": Config.EMBEDDING_MODEL,
            "similarity_threshold": Config.SIMILARITY_THRESHOLD
        }
    
    def cleanup_old_news(self, days_old: int = 30):
        """Удаляем старые новости (опционально)"""
        # TODO: Реализовать при необходимости
        pass