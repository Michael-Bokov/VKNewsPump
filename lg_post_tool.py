# post_tool.py
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field,PrivateAttr
from langchain.tools import BaseTool
from direct_generator_agent import PostGenerator
import json

class PostGenerationInput(BaseModel):
    """Входные данные для генерации поста"""
    article_data: str = Field(
        description="Данные статьи в формате JSON строки. Должны содержать title/title_ru и full_text/text_ru"
    )
    platform: str = Field(
        default="vk",
        description="Платформа для поста: 'vk', 'telegram', 'twitter', 'linkedin' или 'all'"
    )
    

class GeneratePostTool(BaseTool):
    name: str = "generate_social_post"
    description: str = "Генерирует пост для социальных сетей на основе статьи. Поддерживает VK, Telegram, Twitter, LinkedIn"
    args_schema: Type[BaseModel] = PostGenerationInput
    
        
    def _run(
        self,
        article_data: str,
        platform: str = "vk",
        #tone: str = "professional",
        # max_length: int = 600,
        # include_hashtags: bool = True,
        # include_questions: bool = True
    ) -> str:
        """Генерирует пост для социальной сети"""
        try:
            # Парсим данные статьи
            article = json.loads(article_data)
            
            # # Определяем платформу
            # if platform.lower() == "all":
            #     return self._generate_all_platforms(article, tone, max_length)
            
            # if platform.lower() not in self.platform_prompts:
            #     available = ", ".join(self.platform_prompts.keys())
            #     return f"⚠️ Платформа '{platform}' не поддерживается. Доступные: {available}"
            
            # Генерируем пост
            #post = self._generate_post_for_platform(article, platform, tone, max_length, include_hashtags, include_questions)
            generator = PostGenerator(model_name="qwen2.5:7b")
            post = generator.generate_vk_post(article)
            return post
            
        except json.JSONDecodeError:
            return "❌ Ошибка: Некорректный JSON формат статьи"
        except Exception as e:
            return f"❌ Ошибка генерации поста: {str(e)}"
    
class GenerateMultiplePostsTool(BaseTool):
    """Генерирует несколько вариантов постов для одной статьи"""
    
    name: str = "generate_post_variations"
    description: str = "Создает 3 разных варианта поста для статьи с разными тонами и стилями"
    
# Используем PrivateAttr для кастомных полей
    _generator: PostGenerator = PrivateAttr()

    def __init__(self, model_name: str = "qwen2.5:7b"):
        super().__init__()
        self._generator = PostGenerator(model_name=model_name)
    
    def _run(self, article_data: str) -> str:
        """Генерирует варианты постов"""
        try:
            article = json.loads(article_data)
            title = article.get('title_ru', article.get('title', ''))
            
        
            post = self._generator.generate_vk_post(article)
            
            result = [
                f"📝 Пост для статьи: {title[:50]}...",
                "",
                "🎯 Основной вариант:",
                post,
                "",
                f"📏 Длина: {len(post)} символов"
            ]
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Ошибка генерации вариантов: {str(e)}"
