# lg_content_tools.py
from lg_post_tool import GeneratePostTool, GenerateMultiplePostsTool, PostAnalyzerTool
from lg_translation_tool import TranslationTool
from typing import List, Dict, Any
import json

# Все инструменты для работы с контентом
CONTENT_TOOLS = [
    GeneratePostTool(),
    GenerateMultiplePostsTool(),
    PostAnalyzerTool(),
    TranslationTool()
]

def prepare_article_for_posts(article_dict: Dict[str, Any]) -> str:
    """Подготавливает статью для передачи в инструменты (JSON строка)"""
    # Убедимся, что есть все необходимые поля
    required_fields = ['title', 'full_text']
    for field in required_fields:
        if field not in article_dict:
            article_dict[field] = ""
    
    return json.dumps(article_dict, ensure_ascii=False, indent=2)

def generate_content_pipeline(article_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Полный пайплайн обработки статьи:
    1. Перевод (если нужно)
    2. Генерация постов для всех платформ
    3. Анализ постов
    """
    results = {
        "original_article": article_dict,
        "posts": {},
        "analysis": {}
    }
    
    # 1. Создаем инструменты
    translator = TranslationTool()
    post_generator = GeneratePostTool()
    analyzer = PostAnalyzerTool()
    
    # 2. Проверяем язык и переводим при необходимости
    # (Здесь должна быть логика определения языка)
    
    # Подготавливаем статью
    article_json = prepare_article_for_posts(article_dict)
    
    # 3. Генерируем посты для основных платформ
    platforms = ["vk", "telegram", "twitter"]
    
    for platform in platforms:
        post = post_generator.run({
            "article_data": article_json,
            "platform": platform,
            "tone": "professional" if platform == "linkedin" else "enthusiastic"
        })
        results["posts"][platform] = post
        
        # 4. Анализируем пост
        analysis = analyzer.run({"post_text": post, "platform": platform})
        results["analysis"][platform] = analysis
    
    # 5. Генерируем несколько вариантов
    variations_tool = GenerateMultiplePostsTool()
    variations = variations_tool.run({"article_data": article_json})
    results["variations"] = variations
    
    return results

# Утилиты для быстрого использования
def get_all_content_tools():
    """Возвращает все инструменты для работы с контентом"""
    return CONTENT_TOOLS

def get_tool_by_name(name: str):
    """Находит инструмент по имени"""
    for tool in CONTENT_TOOLS:
        if tool.name == name:
            return tool
    raise ValueError(f"Инструмент '{name}' не найден")