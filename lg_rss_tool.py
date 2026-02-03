# rss_tool.py
from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field,PrivateAttr
from langchain.tools import BaseTool
from direct_hybridrss_agent import HybridRSSAgent
import json

class RssInput(BaseModel):
    """Входные данные для сбора новостей"""
    max_per_feed: int = Field(
        default=8, 
        description="Максимальное количество статей с каждого источника"
    )
    # custom_feeds: Optional[List[str]] = Field(
    #     default=None,
    #     description="Список пользовательских RSS фидов для парсинга"
    # )
    # strategy_override: Optional[Dict[str, List[str]]] = Field(
    #     default=None,
    #     description="Переопределение стратегий для фидов (опционально)"
    # )

class RssFetchTool(BaseTool):
    name: str = "fetch_tech_news"
    description: str = "Собирает свежие новости и статьи об AI и технологиях из RSS фидов"
    args_schema: Type[BaseModel] = RssInput
    
    # Используем PrivateAttr для кастомных полей
    _agent: HybridRSSAgent = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._agent = HybridRSSAgent()
    
    def _run(
        self, 
        max_per_feed: int = 8,
        #custom_feeds: Optional[List[str]] = None
    ) -> str:
        """Синхронный сбор новостей"""
        try:
            # if custom_feeds:
            #     self.agent.all_feeds = custom_feeds
            
            articles = self._agent.fetch_articles(max_per_feed=max_per_feed)
            # Возвращаем чистый JSON для парсинга в других узлах
            return json.dumps({
                "status": "success",
                "article_count": len(articles),
                "articles": articles
            }, ensure_ascii=False)
            
        except Exception as e:
            # В случае ошибки все равно возвращаем JSON
            return json.dumps({
                "status": "error",
                "error": str(e),
                "articles": []
            }, ensure_ascii=False)
    
    # async def _arun(
    #     self, 
    #     max_per_feed: int = 8,
    #     custom_feeds: Optional[List[str]] = None,
    #     strategy_override: Optional[Dict[str, List[str]]] = None
    # ) -> str:
    #     """Асинхронный сбор новостей"""
    #     try:
    #         import asyncio
            
    #         # Запускаем синхронный метод в отдельном потоке
    #         return await asyncio.to_thread(
    #             self._run,
    #             max_per_feed,
    #             custom_feeds,
    #             strategy_override
    #         )
    #     except Exception as e:
    #         return f"Ошибка при сборе новостей: {str(e)}"
    
    # def _update_feeds(
    #     self, 
    #     custom_feeds: List[str],
    #     strategy_override: Optional[Dict[str, List[str]]] = None
    # ) -> None:
    #     """Обновляет фиды в агенте"""
    #     if strategy_override:
    #         self.agent.feed_strategies = strategy_override
    #     else:
    #         # По умолчанию все фиды считаем требующими скачивания
    #         self.agent.feed_strategies = {
    #             'download': custom_feeds,
    #             'full_text_rss': [],
    #             'summary_only': []
    #         }
    #     self.agent.all_feeds = custom_feeds
    
    def _format_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Форматирует статьи в читаемый текст"""
        if not articles:
            return "⚠️ Статьи не найдены."
        
        result_lines = [f"📊 Найдено статей: {len(articles)}\n"]
        
        for i, article in enumerate(articles, 1):
            result_lines.append(f"\n{'='*60}")
            result_lines.append(f"{i}. {article['title']}")
            result_lines.append(f"   📍 Источник: {article['source']}")
            result_lines.append(f"   📅 Дата: {article['date']}")
            result_lines.append(f"   🔗 URL: {article['url']}")
            result_lines.append(f"\n   📝 Текст (первые 500 символов):")
            result_lines.append(f"   {article['full_text'][:500]}...")
        if 'full_text' in article and article['full_text']:
                preview = article['full_text'][:300] + "..." if len(article['full_text']) > 300 else article['full_text']
                result_lines.append(f"\n   📝 Превью:")
                result_lines.append(f"   {preview}")
        return "\n".join(result_lines)
        
        # # Также возвращаем структурированные данные для последующей обработки
        # structured_data = {
        #     "summary": f"Собрано {len(articles)} статей",
        #     "articles": [
        #         {
        #             "id": article["id"],
        #             "title": article["title"],
        #             "source": article["source"],
        #             "text_preview": article["full_text"][:300],
        #             "text_length": article["text_length"],
        #             "date": article["date"],
        #             "url": article["url"]
        #         }
        #         for article in articles
        #     ]
        # }
        
        # # Добавляем JSON для машинной обработки
        # result_lines.append(f"\n{'='*60}")
        # result_lines.append("📋 Структурированные данные (для последующей обработки):")
        # result_lines.append(json.dumps(structured_data, ensure_ascii=False, indent=2))
        
        # return "\n".join(result_lines)


# Дополнительные инструменты для работы с RSS
# class ListFeedsTool(BaseTool):
#     """Инструмент для просмотра доступных RSS фидов"""
    
#     name = "list_available_feeds"
#     description = "Показывает список всех доступных RSS фидов и их стратегии"
    
#     def __init__(self):
#         super().__init__()
#         self.agent = HybridRSSAgent()
    
#     def _run(self) -> str:
#         """Показывает список фидов"""
#         result = ["📋 Доступные RSS фиды и стратегии:"]
        
#         for strategy, feeds in self.agent.feed_strategies.items():
#             result.append(f"\n📌 Стратегия: {strategy}")
#             for feed in feeds:
#                 feed_name = self.agent._get_feed_name(feed)
#                 result.append(f"   • {feed_name}: {feed}")
        
#         return "\n".join(result)
    
#     async def _arun(self) -> str:
#         return self._run()


# class CheckFeedTool(BaseTool):
#     """Инструмент для проверки RSS фида"""
    
#     name = "check_rss_feed"
#     description = "Проверяет доступность RSS фида и показывает пример статей"
#     args_schema: Type[BaseModel] = RssInput
    
#     def __init__(self):
#         super().__init__()
#         self.agent = HybridRSSAgent()
    
#     def _run(self, custom_feeds: List[str], max_per_feed: int = 3) -> str:
#         """Проверяет указанные фиды"""
#         if not custom_feeds:
#             return "⚠️ Укажите хотя бы один RSS фид для проверки"
        
#         result = []
        
#         for feed_url in custom_feeds[:3]:  # Проверяем до 3 фидов
#             result.append(f"\n🔍 Проверка фида: {feed_url}")
            
#             try:
#                 # Временно изменяем стратегию на summary_only для быстрой проверки
#                 original_strategy = self.agent._get_strategy(feed_url)
#                 self.agent.feed_strategies = {
#                     'summary_only': [feed_url],
#                     'download': [],
#                     'full_text_rss': []
#                 }
#                 self.agent.all_feeds = [feed_url]
                
#                 # Собираем статьи
#                 articles = self.agent.fetch_articles(max_per_feed=max_per_feed)
                
#                 if articles:
#                     result.append(f"✅ Фид рабочий, найдено статей: {len(articles)}")
#                     for article in articles[:2]:  # Показываем 2 примера
#                         result.append(f"   • {article['title'][:50]}...")
#                 else:
#                     result.append("⚠️ Фид не содержит статей или произошла ошибка")
                
#                 # Восстанавливаем стратегию
#                 self.agent.feed_strategies['summary_only'].remove(feed_url)
#                 if original_strategy in self.agent.feed_strategies:
#                     self.agent.feed_strategies[original_strategy].append(feed_url)
                    
#             except Exception as e:
#                 result.append(f"❌ Ошибка при проверке: {str(e)}")
        
#         return "\n".join(result)