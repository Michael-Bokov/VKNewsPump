# translation_agent.py
import ollama
import re
from typing import Optional, Dict, Any
import time


class TranslationAgent:
    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.model_name = model_name
        self.max_retries = 3
        # self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11435')
        # self.client = ollama.Client(host=self.host)
        
    def detect_language(self, text: str) -> str:
        """Простое определение языка (английский или русский)"""
        # Считаем кириллические и латинские символы
        cyrillic_count = len(re.findall(r'[а-яА-ЯёЁ]', text[:500]))
        latin_count = len(re.findall(r'[a-zA-Z]', text[:500]))
        
        if cyrillic_count > latin_count:
            return "ru"
        else:
            return "en"
    
    def translate_to_russian(self, text: str, title: str = "") -> str:
        """
        Переводит текст на русский язык
        """
        # Если текст уже на русском или слишком короткий
        if self.detect_language(text) == "ru" or len(text) < 50:
            return text
        
        # Ограничиваем длину текста для перевода
        text_to_translate = text[:3000]  # Ограничиваем для скорости
        
        prompt = f"""
        Ты профессиональный переводчик технических текстов. 
        Переведи следующий текст с английского на русский язык.
        
        Сохрани:
        1. Технические термины на английском (в скобках укажи перевод)
        2. Имена собственные без изменений
        3. Стиль - научно-популярный, доступный
        4. Сократи текст до 500-700 слов, оставив ключевые идеи
        
        Заголовок: {title}
        
        Текст для перевода:
        {text_to_translate}
        
        Перевод на русский:
        """
        
        for attempt in range(self.max_retries):
            try:
                print(f"🔤 Перевод статьи... (попытка {attempt + 1})")
                
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Ты профессиональный переводчик технических статей.'
                        },
                        {
                            'role': 'user', 
                            'content': prompt
                        }
                    ],
                    options={
                        'temperature': 0.1,  # Низкая температура для точности
                        'num_predict': 1500  # Ограничение длины ответа
                    }
                )
                
                translated = response['message']['content'].strip()
                
                # Базовая валидация перевода
                if len(translated) > 100 and self.detect_language(translated) == "ru":
                    print(f"✅ Перевод готов ({len(translated)} символов)")
                    return translated
                else:
                    print(f"⚠️ Перевод слишком короткий или не на русском, пробуем снова...")
                    
            except Exception as e:
                print(f"❌ Ошибка перевода: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # Ждем перед повторной попыткой
                else:
                    print(f"⚠️ Не удалось перевести, возвращаю оригинал")
                    return text[:1000]  # Возвращаем часть оригинала
        
        return text[:1000]
    
    def translate_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Переводит всю статью"""
        print(f"🌐 Перевод статьи: {article['title'][:50]}...")
        
        # Переводим заголовок отдельно (он должен быть кратким и емким)
        title_translation = self.translate_to_russian(
            article['title'], 
            "Заголовок статьи"
        )
        
        # Переводим основной текст
        text_translation = self.translate_to_russian(
            article['full_text'],
            article['title']
        )
        
        return {
            **article,
            'title_ru': title_translation,
            'text_ru': text_translation,
            'translated_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'original_language': self.detect_language(article['full_text'])
        }