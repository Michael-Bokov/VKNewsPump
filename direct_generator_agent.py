# post_generator.py
import ollama
import re
from typing import Dict, Any
import time

class PostGenerator: 
    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.model_name = model_name
        
    def generate_vk_post(self, article: Dict[str, Any]) -> str:
        """
        Генерирует пост для ВКонтакте на основе статьи
        """
        # Используем русский перевод, если есть, иначе оригинал
        title = article.get('title_ru', article['title'])
        text = article.get('text_ru', article['full_text'])
        
        # Подготовка промпта
        prompt = f"""
        Ты создатель контента для социальной сети ВКонтакте.
        Создай интересный пост на основе этой статьи.
        
        ТРЕБОВАНИЯ К ПОСТУ:
        0. Строго русский язык.
        1. Длина: 500-600 символов (оптимально для VK)
        2. Начни с привлекающего внимания заголовка с эмодзи
        3. Кратко изложи суть статьи (2-3 ключевых момента)
        4. Добавь эмоциональную окраску, задай вопрос читателям
        5. Закончи призывом к обсуждению
        6. Добавь релевантные хештеги (3-5 шт)
        7. В конце допиши: "Ссылка на источник"
        
        НЕЛЬЗЯ:
        - Копировать текст статьи дословно
        - Делать слишком длинный пост
        - Использовать сложные технические термины без объяснения
        
        Заголовок статьи: {title}
        
        Текст статьи (для справки):
        {text[:2000]}
        
        Пост для ВКонтакте:
        """
        
        try:
            print(f"✍️ Генерация поста для VK...")
            
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Ты опытный копирайтер для социальных сетей. Пишешь ярко, интересно, с эмодзи.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.7,  # Средняя температура для креативности
                    'num_predict': 800   # Ограничение длины
                }
            )
            
            post = response['message']['content'].strip()
            
            # Пост-обработка
            post = self._clean_post(post)
            
            # Проверяем длину
            if len(post) > 1000:
                post = post[:1000] + "..."
                
            print(f"✅ Пост сгенерирован ({len(post)} символов)")
            return post
            
        except Exception as e:
            print(f"❌ Ошибка генерации поста: {e}")
            # Возвращаем запасной вариант
            return self._generate_fallback_post(title, text[:500])
    
    def _clean_post(self, post: str) -> str:
        """Очистка и форматирование поста"""
        # Убираем лишние переносы строк
        post = re.sub(r'\n\s*\n', '\n\n', post)
        
        # Убедимся, что есть хештеги
        if '#' not in post:
            post += "\n\n#ИИ #ИскусственныйИнтеллект #Нейросети"
        
        return post.strip()
    
    def _generate_fallback_post(self, title: str, text: str) -> str:
        """Запасной вариант поста (если LLM не работает)"""
        return f"""🤖 {title}

{text[:300]}...

Читать полностью: [ссылка]

Что думаете об этом? Обсуждаем в комментариях!

#ИИ #НовостиТехнологий #ИскусственныйИнтеллект"""
    
    def generate_post_for_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Генерирует пост для статьи"""
        post_text = self.generate_vk_post(article)
        
        return {
            **article,
            'vk_post': post_text,
            'post_generated_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'post_length': len(post_text)
        }
    