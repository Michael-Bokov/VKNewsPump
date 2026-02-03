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
    # tone: str = Field(
    #     default="professional",
    #     description="Тон поста: 'professional', 'casual', 'enthusiastic', 'technical', 'clickbait'"
    # )
    # max_length: int = Field(
    #     default=600,
    #     description="Максимальная длина поста в символах"
    # )
    # include_hashtags: bool = Field(
    #     default=True,
    #     description="Включать ли хештеги"
    # )
    # include_questions: bool = Field(
    #     default=True,
    #     description="Включать ли вопросы для вовлечения"
    # )

class GeneratePostTool(BaseTool):
    name: str = "generate_social_post"
    description: str = "Генерирует пост для социальных сетей на основе статьи. Поддерживает VK, Telegram, Twitter, LinkedIn"
    args_schema: Type[BaseModel] = PostGenerationInput
    
    # Используем PrivateAttr для кастомных полей
    _generator: PostGenerator = PrivateAttr()
    def __init__(self, model_name: str = "qwen2.5:7b"):
        super().__init__()
        self._generator = PostGenerator(model_name=model_name)
        
        # # Системные промпты для разных платформ
        # self.platform_prompts = {
        #     "vk": {
        #         "system": "Ты копирайтер для ВКонтакте. Пиши ярко, эмоционально, используй эмодзи.",
        #         "length": "400-600 символов",
        #         "hashtags": True,
        #         "call_to_action": "Обсуждаем в комментариях!"
        #     },
        #     "telegram": {
        #         "system": "Ты автор Telegram-канала о технологиях. Пиши информативно, но с долей юмора.",
        #         "length": "800-1200 символов",
        #         "hashtags": True,
        #         "call_to_action": "Перешлите канал, если было полезно!"
        #     },
        #     "twitter": {
        #         "system": "Ты создатель твитов о AI. Будь максимально лаконичен и точен.",
        #         "length": "280 символов макс.",
        #         "hashtags": True,
        #         "call_to_action": "Ретвит, если интересно!"
        #     },
        #     "linkedin": {
        #         "system": "Ты профессионал, пишущий для LinkedIn. Формальный, информативный, деловой стиль.",
        #         "length": "1000-1500 символов",
        #         "hashtags": False,
        #         "call_to_action": "Жду ваши мысли в комментариях."
        #     }
        # }
        
        # # Промпты для разных тонов
        # self.tone_prompts = {
        #     "professional": "Профессиональный, формальный, информативный стиль.",
        #     "casual": "Неформальный, дружелюбный, разговорный стиль.",
        #     "enthusiastic": "Энтузиастичный, восторженный, эмоциональный стиль.",
        #     "technical": "Технический, детальный, с упором на специфику.",
        #     "clickbait": "Привлекающий внимание, интригующий, с элементами кликбейта."
        # }
    
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
            post = self._generator.generate_vk_post(article)
            return post
            
        except json.JSONDecodeError:
            return "❌ Ошибка: Некорректный JSON формат статьи"
        except Exception as e:
            return f"❌ Ошибка генерации поста: {str(e)}"
    
    # async def _arun(
    #     self,
    #     article_data: str,
    #     platform: str = "vk",
    #     tone: str = "professional",
    #     max_length: int = 600,
    #     include_hashtags: bool = True,
    #     include_questions: bool = True
    # ) -> str:
    #     """Асинхронная генерация поста"""
    #     try:
    #         import asyncio
    #         return await asyncio.to_thread(
    #             self._run,
    #             article_data,
    #             platform,
    #             tone,
    #             max_length,
    #             include_hashtags,
    #             include_questions
    #         )
    #     except Exception as e:
    #         return f"❌ Ошибка генерации поста: {str(e)}"
    
    # def _generate_post_for_platform(
    #     self,
    #     article: Dict[str, Any],
    #     platform: str,
    #     tone: str,
    #     max_length: int,
    #     include_hashtags: bool,
    #     include_questions: bool
    # ) -> str:
    #     """Генерирует пост для конкретной платформы"""
    #     platform_info = self.platform_prompts[platform]
    #     tone_info = self.tone_prompts.get(tone, "Профессиональный стиль.")
        
    #     # Получаем текст и заголовок
    #     title = article.get('title_ru', article.get('title', ''))
    #     text = article.get('text_ru', article.get('full_text', ''))
        
    #     # Строим расширенный промпт
    #     prompt = f"""
    #     {platform_info['system']}
        
    #     ТОН: {tone_info}
        
    #     ЗАДАЧА: Создать пост для {platform.upper()}
        
    #     ТРЕБОВАНИЯ:
    #     1. Длина: {platform_info['length']} (желательно {max_length} символов)
    #     2. Язык: строго русский
    #     3. Начни с цепляющего заголовка с эмодзи
    #     4. Кратко изложи суть (2-3 ключевых пункта)
    #     5. {f"Включи 1-2 вопроса для вовлечения" if include_questions else "Не задавай вопросов"}
    #     6. {f"Добавь 3-5 релевантных хештегов" if include_hashtags else "Без хештегов"}
    #     7. Закончи призывом к действию: {platform_info['call_to_action']}
        
    #     НЕЛЬЗЯ:
    #     - Копировать текст статьи дословно
    #     - Превышать {max_length * 1.2} символов
    #     - Использовать сложный жаргон без объяснения
        
    #     ДАННЫЕ:
    #     Заголовок: {title}
    #     Текст статьи: {text[:1500]}
        
    #     ПОСТ ДЛЯ {platform.upper()}:
    #     """
        
    #     # Используем существующий генератор с модифицированным промптом
    #     response = self.generator.generate_vk_post(article)  # Используем базовый метод
        
    #     # Адаптируем под платформу
    #     adapted_post = self._adapt_post_to_platform(response, platform, platform_info, max_length)
        
    #     return adapted_post
    
    # def _adapt_post_to_platform(self, post: str, platform: str, platform_info: Dict, max_length: int) -> str:
    #     """Адаптирует пост под требования платформы"""
    #     if platform == "twitter" and len(post) > 280:
    #         post = post[:275] + "..."
        
    #     elif platform == "telegram":
    #         # Telegram любит абзацы
    #         post = post.replace('\n\n', '\n').replace('\n', '\n\n')
        
    #     elif platform == "linkedin":
    #         # LinkedIn предпочитает без эмодзи в начале
    #         if post.startswith(('🤖', '🚀', '🔥', '💡')):
    #             post = post[2:].strip()
        
    #     # Обеспечиваем максимальную длину
    #     if len(post) > max_length:
    #         post = post[:max_length-3] + "..."
        
    #     return post
    
    # def _generate_all_platforms(self, article: Dict, tone: str, max_length: int) -> str:
    #     """Генерирует посты для всех платформ"""
    #     results = []
        
    #     for platform in self.platform_prompts.keys():
    #         try:
    #             post = self._generate_post_for_platform(
    #                 article, 
    #                 platform, 
    #                 tone, 
    #                 max_length, 
    #                 include_hashtags=True,
    #                 include_questions=True
    #             )
                
    #             results.append(f"\n{'='*60}")
    #             results.append(f"📱 {platform.upper()}:")
    #             results.append(f"{post}")
    #             results.append(f"Длина: {len(post)} символов")
                
    #         except Exception as e:
    #             results.append(f"\n⚠️ Ошибка для {platform}: {str(e)}")
        
    #     return "\n".join(results)


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
            
        #     variations = [
        #         {"name": "Профессиональный", "tone": "professional", "emoji": "🎯"},
        #         {"name": "Эмоциональный", "tone": "enthusiastic", "emoji": "🔥"},
        #         {"name": "Технический", "tone": "technical", "emoji": "⚙️"},
        #     ]
            
        #     results = [f"📝 Варианты постов для: {title[:50]}...\n"]
            
        #     for i, variation in enumerate(variations, 1):
        #         # Временно изменяем тон в статье для передачи в генератор
        #         article_with_tone = article.copy()
        #         article_with_tone['tone'] = variation['tone']
                
        #         post = self.generator.generate_vk_post(article_with_tone)
                
        #         results.append(f"\n{variation['emoji']} Вариант {i}: {variation['name']}")
        #         results.append(f"{post}")
        #         results.append(f"─" * 40)
            
        #     results.append(f"\n✅ Сгенерировано {len(variations)} варианта")
            
        #     return "\n".join(results)
            
        # except Exception as e:
        #     return f"❌ Ошибка генерации вариантов: {str(e)}"
                # Просто используем один вариант для простоты
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

# class PostAnalyzerTool(BaseTool):
#     """Анализирует пост и дает рекомендации"""
    
#     name:str = "analyze_social_post"
#     description:str = "Анализирует пост для социальных сетей: длина, тональность, вовлекающие элементы"
    
#     def __init__(self, model_name: str = "qwen2.5:7b"):
#         super().__init__()
#         self.model_name = model_name
    
#     def _run(self, post_text: str, platform: str = "vk") -> str:
#         """Анализирует пост"""
#         try:
#             # Простой анализ без LLM
#             analysis = []
            
#             # Длина
#             length = len(post_text)
#             analysis.append(f"📏 Длина: {length} символов")
            
#             if platform == "twitter" and length > 280:
#                 analysis.append("  ⚠️ Слишком длинно для Twitter (макс. 280)")
#             elif platform == "vk" and length > 1000:
#                 analysis.append("  ⚠️ Слишком длинно для VK (рекомендуется 400-600)")
            
#             # Эмодзи
#             emoji_count = sum(1 for c in post_text if ord(c) > 127 and c not in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
#             analysis.append(f"🎭 Эмодзи/символы: {emoji_count}")
            
#             # Вопросы
#             question_count = post_text.count('?')
#             analysis.append(f"❓ Вопросов: {question_count}")
            
#             # Хештеги
#             hashtag_count = post_text.count('#')
#             analysis.append(f"#️⃣ Хештегов: {hashtag_count}")
            
#             # Рекомендации
#             recommendations = []
            
#             if question_count == 0:
#                 recommendations.append("Добавьте 1-2 вопроса для вовлечения аудитории")
            
#             if hashtag_count == 0:
#                 recommendations.append("Добавьте релевантные хештеги")
            
#             if length < 200:
#                 recommendations.append("Пост слишком короткий, добавьте деталей")
#             elif length > 800 and platform == "vk":
#                 recommendations.append("Сократите пост для лучшего восприятия")
            
#             # Формируем результат
#             result = [
#                 "📊 АНАЛИЗ ПОСТА:",
#                 "\n".join(analysis),
#                 "\n💡 РЕКОМЕНДАЦИИ:",
#                 "\n".join(f"  • {rec}" for rec in recommendations) if recommendations else "  ✅ Отличный пост!"
#             ]
            
#             return "\n".join(result)
            
#         except Exception as e:
#             return f"❌ Ошибка анализа: {str(e)}"