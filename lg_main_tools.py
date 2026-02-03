#lg_main_tools.py
import os
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Конфигурация приложения"""
    VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN', '')
    VK_GROUP_ID = int(os.getenv('VK_GROUP_ID', 0))
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
    
    @classmethod
    def validate(cls):
        """Проверяет обязательные настройки"""
        if not cls.VK_ACCESS_TOKEN:
            print("⚠️ VK_ACCESS_TOKEN не установлен")
        if not cls.VK_GROUP_ID:
            print("⚠️ VK_GROUP_ID не установлен")
        return True
    
    @classmethod
    def print_summary(cls):
        """Выводит сводку конфигурации"""
        print("📋 Конфигурация:")
        print(f"  VK Group ID: {cls.VK_GROUP_ID}")
        print(f"  VK Token: {'✓' if cls.VK_ACCESS_TOKEN else '✗'}")
        print(f"  Ollama Model: {cls.OLLAMA_MODEL}")

# Импортируем инструменты
from lg_publisher_tool import create_vk_tools
from lg_rss_tool import RssFetchTool
from lg_translation_tool import TranslationTool
from lg_post_tool import GeneratePostTool, GenerateMultiplePostsTool


def get_all_tools() -> List:
    """Возвращает все доступные инструменты"""
    
    # Проверяем конфигурацию
    Config.validate()
    
    # Создаем инструменты VK
    vk_tools = []
    try:
        vk_tools = create_vk_tools(
            access_token=Config.VK_ACCESS_TOKEN,
            group_id=Config.VK_GROUP_ID
        )
    except Exception as e:
        print(f"⚠️ Не удалось создать инструменты VK: {e}")
    
    # Создаем остальные инструменты
    content_tools = [
        RssFetchTool(),
        TranslationTool(model_name=Config.OLLAMA_MODEL),
        GeneratePostTool(model_name=Config.OLLAMA_MODEL),
        GenerateMultiplePostsTool(model_name=Config.OLLAMA_MODEL),
    ]
    
    # Объединяем все инструменты
    return vk_tools + content_tools


if __name__ == "__main__":
    # Простой тест
    print("🔧 Тестирование загрузки инструментов...")
    try:
        tools = get_all_tools()
        print(f"✅ Загружено инструментов: {len(tools)}")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")