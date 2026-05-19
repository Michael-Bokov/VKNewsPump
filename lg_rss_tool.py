# rss_tool.py
from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from direct_hybridrss_agent import HybridRSSAgent
import json

class RssInput(BaseModel):
    """Входные данные для сбора новостей"""
    max_per_feed: int = Field(
        default=8, 
        description="Максимальное количество статей с каждого источника"
    )
    
class RssFetchTool(BaseTool):
    name: str = "fetch_tech_news"
    description: str = "Собирает свежие новости и статьи об AI и технологиях из RSS фидов"
    args_schema: Type[BaseModel] = RssInput
    
        
    def _run(
        self, 
        max_per_feed: int = 8,
        #custom_feeds: Optional[List[str]] = None
    ) -> str:
        """Синхронный сбор новостей"""
        try:
            # if custom_feeds:
            #     self.agent.all_feeds = custom_feeds
            agent = HybridRSSAgent()
            articles = agent.fetch_articles(max_per_feed=max_per_feed)
            #articles = self._agent.fetch_articles(max_per_feed=max_per_feed)
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
    
    