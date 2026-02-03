# translation_tool.py
from typing import Type, Optional
from pydantic import BaseModel, Field,PrivateAttr
from langchain.tools import BaseTool
from direct_translation_agent import TranslationAgent

class TranslationInput(BaseModel):
    """Входные данные для перевода"""
    article_text: str = Field(description="Текст статьи для перевода на русский")
    max_length: int = Field(default=2000, description="Максимальная длина текста для перевода")

class TranslationTool(BaseTool):
    name: str = "translate_article"
    description: str = "Переводит текст статьи с английского на русский язык"
    args_schema: Type[BaseModel] = TranslationInput
    
    # Используем PrivateAttr для кастомных полей
    _agent: TranslationAgent  = PrivateAttr()

    def __init__(self, model_name: str = "qwen2.5:7b"):
        super().__init__()
        self._agent = TranslationAgent(model_name=model_name)
        
    def _run(self, article_text: str, max_length: int = 2000) -> str:
        """Синхронный вызов"""
        try:
            text_to_translate = article_text[:max_length]
            return self._agent.translate_to_russian(text_to_translate)
        except Exception as e:
            return f"Ошибка перевода: {str(e)}"
    # async def _arun(
    #     self, 
    #     article_text: str, 
    #     max_length: int = 3000,
    #     title: str = ""
    # ) -> str:
    #     """Асинхронный вызов - для использования в LangGraph"""
    #     try:
    #         # Используем асинхронную обертку или синхронный метод в отдельном потоке
    #         import asyncio
    #         return await asyncio.to_thread(
    #             self.agent.translate_to_russian,
    #             text=article_text,
    #             title=title,
    #             max_length=max_length
    #         )
    #     except Exception as e:
    #         return f"Ошибка перевода: {str(e)}\nОригинальный текст: {article_text[:500]}..."

# Дополнительный инструмент для перевода всей статьи (если нужно)
# class TranslateFullArticleTool(BaseTool):
#     name = "translate_full_article"
#     description = "Переводит всю статью (заголовок и текст) с английского на русский"
    
#     def __init__(self, model_name: str = "qwen2.5:7b"):
#         super().__init__()
#         self.agent = TranslationAgent(model_name=model_name)
    
#     def _run(self, article_dict: dict) -> dict:
#         """Переводит статью в формате словаря"""
#         try:
#             return self.agent.translate_article(article_dict)
#         except Exception as e:
#             return {
#                 "error": str(e),
#                 "original_article": article_dict
#             }