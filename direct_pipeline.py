# production_pipeline.py
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict
import schedule

# Ваши существующие модули
from database import NewsDatabase
from direct_hybridrss_agent import HybridRSSAgent
from direct_translation_agent import TranslationAgent
from direct_generator_agent import PostGenerator
from direct_publisher_agent import VKPublisher
from config import Config

@dataclass
class PipelineStats:
    """Статистика выполнения пайплайна"""
    start_time: float
    end_time: Optional[float] = None
    articles_found: int = 0
    new_articles: int = 0
    translated: int = 0
    posts_generated: int = 0
    published: int = 0
    errors: list = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'duration': self.duration,
            'success_rate': self.published / max(self.new_articles, 1)
        }

class ProductionPipeline:
    """Минимальный production pipeline с мониторингом"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = self._setup_logging()
        self.stats = PipelineStats(start_time=time.time())
        
        # Инициализация компонентов
        self.db = NewsDatabase()
        self.rss_agent = HybridRSSAgent()
        self.translator = TranslationAgent(model_name="qwen2.5:7b")
        self.post_generator = PostGenerator(model_name="qwen2.5:7b")
        
        # Публикатор с retry логикой
        self.vk_publisher = RetryPublisher(
            access_token=Config.VK_ACCESS_TOKEN,
            group_id=Config.VK_GROUP_ID,
            max_retries=3
        )
        
        # Создаем необходимые директории
        Path("logs").mkdir(exist_ok=True)
        Path("results").mkdir(exist_ok=True)
        Path("backups").mkdir(exist_ok=True)
        
        self.logger.info("🚀 Production Pipeline initialized")
    
    def _setup_logging(self):
        """Настройка логирования в файл и консоль"""
        logger = logging.getLogger("vk_pipeline")
        logger.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Файловый хендлер
        file_handler = logging.FileHandler(
            f"logs/pipeline_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(formatter)
        
        # Консольный хендлер
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def run_single_cycle(self) -> Dict[str, Any]:
        """Один цикл выполнения пайплайна"""
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"Начало цикла: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. Сбор новостей
            articles = await self._fetch_news_with_retry()
            self.stats.articles_found = len(articles)
            
            if not articles:
                self.logger.warning("Новостей не найдено")
                return {"status": "no_articles"}
            
            # 2. Дедупликация
            new_articles = await self._deduplicate_articles(articles)
            self.stats.new_articles = len(new_articles)
            
            if not new_articles:
                self.logger.info("Нет новых статей для обработки")
                return {"status": "no_new_articles"}
            
            # 3. Выбор лучшей статьи
            article = self._select_best_article(new_articles)
            self.logger.info(f"Выбрана статья: {article['title'][:60]}...")
            
            # 4. Перевод (с fallback)
            translated = await self._translate_with_fallback(article)
            self.stats.translated = 1 if translated else 0
            
            # 5. Генерация поста
            post_data = await self._generate_post(translated or article)
            self.stats.posts_generated = 1 if post_data else 0
            
            if not post_data:
                self.logger.error("Не удалось сгенерировать пост")
                return {"status": "post_generation_failed"}
            
            # 6. Публикация
            published = await self._publish_with_retry(post_data)
            self.stats.published = 1 if published else 0
            
            # 7. Сохранение результата
            await self._save_result(post_data, published)
            
            return {
                "status": "success" if published else "partial_success",
                "published": published,
                "article_id": article.get('id')
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка в пайплайне: {e}", exc_info=True)
            self.stats.errors.append(str(e))
            return {"status": "error", "error": str(e)}
        finally:
            self.stats.end_time = time.time()
            self._log_stats()
    
    async def _fetch_news_with_retry(self, max_retries: int = 3) -> list:
        """Сбор новостей с повторными попытками"""
        for attempt in range(max_retries):
            try:
                articles = self.rss_agent.fetch_articles(max_per_feed=3)
                return articles
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return []
    
    async def _deduplicate_articles(self, articles: list) -> list:
        """Дедупликация статей"""
        new_articles = []
        for article in articles:
            is_dup, _, _ = self.db.is_duplicate(article)
            if not is_dup:
                article_id = self.db.add_news(article)
                article['id'] = article_id
                new_articles.append(article)
                self.logger.info(f"Новая статья: {article['title'][:50]}...")
        return new_articles
    
    def _select_best_article(self, articles: list) -> Dict[str, Any]:
        """Выбор лучшей статьи по нескольким критериям"""
        if not articles:
            return {}
        
        # Простой алгоритм выбора: самая длинная статья
        return max(articles, key=lambda x: x.get('text_length', 0))
    
    async def _translate_with_fallback(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Перевод с fallback на оригинальный текст"""
        try:
            translated = self.translator.translate_article(article)
            self.logger.info(f"Статья переведена ({len(translated.get('translated_text', ''))} символов)")
            return translated
        except Exception as e:
            self.logger.warning(f"Ошибка перевода: {e}. Использую оригинальный текст")
            self.stats.errors.append(f"translation_error: {e}")
            return None
    
    async def _generate_post(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерация поста"""
        try:
            post = self.post_generator.generate_post_for_article(article)
            
            # Сохраняем в базу
            post['processed'] = True
            self.db.add_news(post)
            
            self.logger.info(f"Пост сгенерирован ({len(post.get('vk_post', ''))} символов)")
            return post
        except Exception as e:
            self.logger.error(f"Ошибка генерации поста: {e}")
            self.stats.errors.append(f"generation_error: {e}")
            return None
    
    async def _publish_with_retry(self, article: Dict[str, Any]) -> bool:
        """Публикация с повторными попытками"""
        try:
            published = self.vk_publisher.publish_article(article)
            if published.get('vk_published'):
                self.logger.info(f"Пост опубликован! ID: {published.get('vk_post_id')}")
                return True
            else:
                self.logger.warning("Не удалось опубликовать пост")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка публикации: {e}")
            self.stats.errors.append(f"publish_error: {e}")
            return False
    
    async def _save_result(self, article: Dict[str, Any], published: bool):
        """Сохранение результатов"""
        result = {
            "article": article,
            "published": published,
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats.to_dict()
        }
        
        # Сохраняем в JSON
        filename = f"results/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Результат сохранен в {filename}")
    
    def _log_stats(self):
        """Логирование статистики"""
        self.logger.info("=" * 60)
        self.logger.info("📊 СТАТИСТИКА ВЫПОЛНЕНИЯ:")
        self.logger.info(f"   Найдено статей: {self.stats.articles_found}")
        self.logger.info(f"   Новых статей: {self.stats.new_articles}")
        self.logger.info(f"   Переведено: {self.stats.translated}")
        self.logger.info(f"   Сгенерировано постов: {self.stats.posts_generated}")
        self.logger.info(f"   Опубликовано: {self.stats.published}")
        self.logger.info(f"   Время выполнения: {self.stats.duration:.1f} сек")
        self.logger.info(f"   Ошибок: {len(self.stats.errors)}")
        if self.stats.errors:
            for error in self.stats.errors[-3:]:  # Последние 3 ошибки
                self.logger.warning(f"   - {error[:100]}")
        self.logger.info("=" * 60)

class RetryPublisher(VKPublisher):
    """VK Publisher с логикой повторных попыток"""
    
    def __init__(self, *args, max_retries: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
    
    def publish_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Публикация с повторными попытками"""
        for attempt in range(self.max_retries):
            try:
                result = super().publish_article(article)
                if result.get('vk_published'):
                    return result
                
                # Если не опубликовано, пробуем без изображения
                if attempt == 1:
                    self.logger.warning("Пробую публикацию без изображения...")
                    # Реализуйте fallback публикацию
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                self.logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
                time.sleep(2 ** attempt)
        
        return {
            **article,
            'vk_published': False,
            'error': 'max_retries_exceeded'
        }

# ==================== ЗАПУСК ====================

async def run_once():
    """Однократный запуск пайплайна"""
    pipeline = ProductionPipeline()
    result = await pipeline.run_single_cycle()
    return result

async def run_schedule(interval_hours: int = 6):
    """Запуск по расписанию"""
    #import schedule
    import threading
    
    pipeline = ProductionPipeline()
    
    def run_cycle():
        asyncio.run(pipeline.run_single_cycle())
    
    # Настройка расписания
    schedule.every(interval_hours).hours.do(
        lambda: threading.Thread(target=run_cycle).start()
    )
    
    # Первый запуск
    run_cycle()
    
    # Бесконечный цикл
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

def main():
    """CLI интерфейс"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Pipeline для VK')
    parser.add_argument('--mode', choices=['once', 'schedule'], default='once',
                       help='Режим запуска: once - один раз, schedule - по расписанию')
    parser.add_argument('--interval', type=int, default=6,
                       help='Интервал в часах для режима schedule')
    
    args = parser.parse_args()
    
    if args.mode == 'once':
        asyncio.run(run_once())
    else:
        asyncio.run(run_schedule(args.interval))

if __name__ == "__main__":
    main()