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
    
      
    def _run(self, article_text: str, max_length: int = 2000) -> str:
        """Синхронный вызов"""
        try:
            agent = TranslationAgent(model_name="qwen2.5:7b")
            text_to_translate = article_text[:max_length]
            return agent.translate_to_russian(text_to_translate)
        except Exception as e:
            return f"Ошибка перевода: {str(e)}"
    