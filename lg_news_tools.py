# news_tools.py
from rss_tool import RssFetchTool, ListFeedsTool, CheckFeedTool
from translation_tool import TranslationTool, TranslateFullArticleTool

# Все инструменты для работы с новостями
NEWS_TOOLS = [
    RssFetchTool(),
    ListFeedsTool(),
    CheckFeedTool(),
    TranslationTool(),
    TranslateFullArticleTool()
]

# Утилита для удобного использования
def get_all_tools() -> list:
    """Возвращает все доступные инструменты"""
    return NEWS_TOOLS

def get_tool_by_name(name: str):
    """Возвращает инструмент по имени"""
    for tool in NEWS_TOOLS:
        if tool.name == name:
            return tool
    raise ValueError(f"Инструмент с именем '{name}' не найден")