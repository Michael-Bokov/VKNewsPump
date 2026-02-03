#lg_console_pipeline.py
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from lg_main_tools import get_all_tools
import json

class InteractiveNewsAgent:
    def __init__(self):
        print("🤖 Запуск интерактивного новостного агента...")
        print("=" * 60)
        
        # Получаем инструменты
        print("🔧 Загружаем инструменты...")
        self.tools = get_all_tools()
        self.tool_dict = {tool.name: tool for tool in self.tools}
        
        print(f"✅ Загружено инструментов: {len(self.tools)}")
        
        # Текущие данные
        self.current_articles = []
        self.current_translation = ""
        self.current_post = ""
    
    def show_menu(self):
        print("\n" + "=" * 60)
        print("📰 НОВОСТНОЙ АГЕНТ - ГЛАВНОЕ МЕНЮ:")
        print("=" * 60)
        print("📡 1. Собрать свежие новости")
        print("🔤 2. Перевести текст на русский")
        print("✍️  3. Создать пост из статьи")
        print("📋 4. Показать несколько вариантов поста")
        print("📤 5. Опубликовать пост в VK")
        print("🚀 6. Полный цикл (автоматически)")
        print("📊 7. Показать статистику")
        print("❓ 8. Помощь")
        print("🚪 0. Выход")
        print("=" * 60)
    
    def run(self):
        self.show_menu()
        
        while True:
            try:
                choice = input("\n🎯 Выберите действие (0-8): ").strip()
                
                if choice == "0":
                    print("\n👋 До свидания!")
                    break
                
                elif choice == "1":
                    self.collect_news()
                
                elif choice == "2":
                    self.translate_text()
                
                elif choice == "3":
                    self.generate_post()
                
                elif choice == "4":
                    self.show_variations()
                
                elif choice == "5":
                    self.publish_to_vk()
                
                elif choice == "6":
                    self.full_cycle()
                
                elif choice == "7":
                    self.show_stats()
                
                elif choice == "8":
                    self.show_help()
                
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")
                
                # После выполнения действия показываем меню снова
                input("\n⏎ Нажмите Enter чтобы продолжить...")
                self.show_menu()
                
            except KeyboardInterrupt:
                print("\n\n👋 Завершение работы...")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                continue
    
    def collect_news(self):
        """Сбор новостей"""
        print("\n" + "=" * 60)
        print("📡 СБОР НОВОСТЕЙ")
        print("=" * 60)
        
        try:
            tool = self.tool_dict.get("fetch_tech_news")
            if not tool:
                print("❌ Инструмент сбора новостей не найден")
                return
            
            print("\n📊 Настройки сбора:")
            print("1. Быстрый сбор (3 статьи)")
            print("2. Стандартный сбор (5 статей)")
            print("3. Полный сбор (10 статей)")
            print("4. Настроить вручную")
            
            option = input("\nВыберите опцию (1-4): ").strip()
            
            if option == "1":
                max_articles = 3
            elif option == "2":
                max_articles = 5
            elif option == "3":
                max_articles = 10
            elif option == "4":
                max_articles = input("Сколько статей с каждого источника?: ").strip()
                max_articles = int(max_articles) if max_articles.isdigit() else 3
            else:
                max_articles = 3
            
            print(f"\n🔍 Собираю до {max_articles} статей с каждого источника...")
            result = tool.run({"max_per_feed": max_articles})
            
            # Сохраняем результат
            self.current_articles = [result]  # Упрощенно, в реальности нужно парсить
            self._save_to_file("latest_news.txt", result)
            
            print("\n✅ Новости собраны!")
            print(f"📁 Сохранено в: latest_news.txt")
            print(f"\n📝 Краткий обзор:")
            print("-" * 40)
            
            # Показываем превью
            lines = result.split('\n')
            for line in lines[:20]:  # Показываем первые 20 строк
                if line.strip():
                    print(f"  {line[:80]}{'...' if len(line) > 80 else ''}")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Ошибка сбора новостей: {e}")
    
    def translate_text(self):
        """Перевод текста"""
        print("\n" + "=" * 60)
        print("🔤 ПЕРЕВОД ТЕКСТА")
        print("=" * 60)
        
        tool = self.tool_dict.get("translate_article")
        if not tool:
            print("❌ Инструмент перевода не найден")
            return
        
        print("\n📝 Введите текст для перевода (или Enter для тестового текста):")
        text = input("> ").strip()
        
        if not text:
            text = """Artificial intelligence is transforming industries worldwide. 
                    Recent advances in deep learning and natural language processing 
                    have led to breakthroughs in healthcare, education, and automation."""
            print(f"\n📝 Использую тестовый текст:")
            print(text)
        
        try:
            print("\n🔄 Перевод...")
            result = tool.run({"article_text": text, "max_length": 2000})
            
            # Сохраняем
            self.current_translation = result
            self._save_to_file("translation.txt", f"Исходный текст:\n{text}\n\nПеревод:\n{result}")
            
            print("\n✅ Перевод готов!")
            print(f"📁 Сохранено в: translation.txt")
            print("\n📝 Результат:")
            print("-" * 60)
            print(result)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Ошибка перевода: {e}")
    
    def generate_post(self):
        """Создание поста"""
        print("\n" + "=" * 60)
        print("✍️  СОЗДАНИЕ ПОСТА")
        print("=" * 60)
        
        tool = self.tool_dict.get("generate_social_post")
        if not tool:
            print("❌ Инструмент генерации постов не найден")
            return
        
        print("\n📝 Введите данные статьи:")
        
        # Если есть перевод, предлагаем его использовать
        if self.current_translation:
            use_translation = input(f"Использовать последний перевод? (y/n): ").strip().lower()
            if use_translation == 'y':
                article_text = self.current_translation
            else:
                article_text = input("Текст статьи: ").strip()
        else:
            article_text = input("Текст статьи: ").strip()
        
        if not article_text:
            print("⚠️ Использую тестовый текст")
            article_text = "Искусственный интеллект меняет мир. Новые технологии появляются каждый день."
        
        title = input("Заголовок статьи (или Enter для пропуска): ").strip()
        if not title:
            title = "Новости искусственного интеллекта"
        
        print("\n📱 Выберите платформу:")
        print("1. VK (ВКонтакте)")
        print("2. Telegram")
        print("3. Twitter")
        print("4. LinkedIn")
        
        platform_choice = input("Выберите (1-4, по умолчанию 1): ").strip()
        platforms = { "1": "vk", "2": "telegram", "3": "twitter", "4": "linkedin" }
        platform = platforms.get(platform_choice, "vk")
        
        try:
            print(f"\n⚡ Создаю пост для {platform}...")
            
            article_data = {
                "title": title,
                "full_text": article_text,
                "text_ru": article_text
            }
            
            result = tool.run({
                "article_data": json.dumps(article_data),
                "platform": platform
            })
            
            # Сохраняем
            self.current_post = result
            self._save_to_file("generated_post.txt", result)
            
            print("\n✅ Пост создан!")
            print(f"📁 Сохранено в: generated_post.txt")
            print(f"📏 Длина: {len(result)} символов")
            print("\n📝 Пост:")
            print("-" * 60)
            print(result)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Ошибка создания поста: {e}")
    
    def show_variations(self):
        """Показать варианты поста"""
        print("\n" + "=" * 60)
        print("📋 ВАРИАНТЫ ПОСТА")
        print("=" * 60)
        
        tool = self.tool_dict.get("generate_post_variations")
        if not tool:
            print("❌ Инструмент создания вариантов не найден")
            return
        
        if not self.current_translation and not self.current_post:
            print("⚠️ Нет данных для создания вариантов")
            print("Сначала соберите новости или создайте пост")
            return
        
        try:
            print("\n🎨 Создаю варианты поста...")
            
            # Используем текущий перевод или создаем тестовую статью
            if self.current_translation:
                article_data = {
                    "title": "AI News",
                    "full_text": self.current_translation,
                    "text_ru": self.current_translation
                }
            else:
                article_data = {
                    "title": "Новости технологий",
                    "full_text": "Искусственный интеллект развивается быстрыми темпами.",
                    "text_ru": "Искусственный интеллект развивается быстрыми темпами."
                }
            
            result = tool.run({
                "article_data": json.dumps(article_data)
            })
            
            self._save_to_file("post_variations.txt", result)
            
            print("\n✅ Варианты созданы!")
            print(f"📁 Сохранено в: post_variations.txt")
            print("\n📝 Результат:")
            print("-" * 60)
            print(result[:1000] + "..." if len(result) > 1000 else result)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Ошибка создания вариантов: {e}")
    
    def publish_to_vk(self):
        """Публикация в VK"""
        print("\n" + "=" * 60)
        print("📤 ПУБЛИКАЦИЯ В VK")
        print("=" * 60)
        
        tool = self.tool_dict.get("publish_to_vk")
        if not tool:
            print("❌ Инструмент VK не найден")
            print("⚠️ Проверьте настройки .env файла")
            return
        
        # Проверяем, есть ли сохраненный пост
        post_text = ""
        if self.current_post:
            use_current = input(f"Использовать последний созданный пост? (y/n): ").strip().lower()
            if use_current == 'y':
                post_text = self.current_post
                print("\n📝 Использую последний созданный пост")
        
        if not post_text:
            try:
                with open("generated_post.txt", "r", encoding="utf-8") as f:
                    post_text = f.read().strip()
                print("\n📝 Загружен пост из файла generated_post.txt")
            except:
                print("\n📝 Созданного поста не найдено")
                post_text = input("Введите текст поста: ").strip()
        
        if not post_text:
            print("❌ Нет текста для публикации")
            return
        
        article_url = input("URL статьи (опционально): ").strip()
        if not article_url:
            article_url = None
        
        # Подтверждение
        print("\n⚠️  ПОДТВЕРЖДЕНИЕ ПУБЛИКАЦИИ")
        print("-" * 40)
        print(f"Текст поста ({len(post_text)} символов):")
        print(post_text[:200] + "..." if len(post_text) > 200 else post_text)
        print("-" * 40)
        
        confirm = input("\nОпубликовать этот пост? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Публикация отменена")
            return
        
        try:
            print("\n📤 Публикую в VK...")
            result = tool.run({
                "post_text": post_text,
                "article_url": article_url
            })
            
            self._save_to_file("vk_publication_log.txt", f"{result}\n\n")
            
            print("\n" + "=" * 60)
            print(result)
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Ошибка публикации: {e}")
    
    def full_cycle(self):
        """Полный автоматический цикл"""
        print("\n" + "=" * 60)
        print("🚀 ПОЛНЫЙ ЦИКЛ (АВТОМАТИЧЕСКИ)")
        print("=" * 60)
        
        print("\n📋 Этот процесс выполнит:")
        print("  1. 📡 Сбор новостей (2 статьи)")
        print("  2. 🔤 Перевод на русский")
        print("  3. ✍️  Создание поста для VK")
        print("  4. 📤 Публикация в VK")
        
        confirm = input("\nЗапустить полный цикл? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Отменено")
            return
        
        try:
            # 1. Сбор новостей
            print("\n1. 📡 Собираю новости...")
            news_tool = self.tool_dict.get("fetch_tech_news")
            if news_tool:
                news_result = news_tool.run({"max_per_feed": 2})
                print("   ✅ Новости собраны")
            else:
                print("   ❌ Инструмент сбора новостей не найден")
                return
            
            # 2. Перевод (упрощенно)
            print("\n2. 🔤 Перевожу текст...")
            translate_tool = self.tool_dict.get("translate_article")
            if translate_tool:
                # Используем тестовый текст для демо
                test_text = "AI research shows remarkable progress in language models."
                translated = translate_tool.run({"article_text": test_text})
                print("   ✅ Текст переведен")
            else:
                print("   ❌ Переводчик не найден")
                return
            
            # 3. Создание поста
            print("\n3. ✍️  Создаю пост...")
            post_tool = self.tool_dict.get("generate_social_post")
            if post_tool:
                article_data = {
                    "title": "AI Research Update",
                    "full_text": translated,
                    "text_ru": translated
                }
                
                post = post_tool.run({
                    "article_data": json.dumps(article_data),
                    "platform": "vk"
                })
                print(f"   ✅ Пост создан ({len(post)} символов)")
            else:
                print("   ❌ Генератор постов не найден")
                return
            
            # 4. Публикация
            print("\n4. 📤 Публикую в VK...")
            publish_tool = self.tool_dict.get("publish_to_vk")
            if publish_tool:
                confirm_publish = input("   Опубликовать пост в VK? (y/n): ").strip().lower()
                if confirm_publish == 'y':
                    result = publish_tool.run({
                        "post_text": post,
                        "article_url": "https://example.com"
                    })
                    print(f"   ✅ {result}")
                else:
                    print("   ⏭️ Публикация пропущена")
            else:
                print("   ❌ Инструмент VK не найден")
            
            print("\n" + "=" * 60)
            print("✅ Полный цикл завершен!")
            print("📁 Результаты сохранены в отдельных файлах")
            
        except Exception as e:
            print(f"❌ Ошибка в полном цикле: {e}")
    
    def show_stats(self):
        """Показать статистику"""
        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА")
        print("=" * 60)
        
        print(f"\n📋 Загружено инструментов: {len(self.tools)}")
        
        for tool in self.tools:
            print(f"\n🔸 {tool.name}")
            print(f"   Описание: {tool.description[:80]}...")
        
        print(f"\n💾 Данные в памяти:")
        print(f"   📰 Статей: {len(self.current_articles)}")
        print(f"   🔤 Перевод: {'Да' if self.current_translation else 'Нет'}")
        print(f"   📝 Пост: {'Да' if self.current_post else 'Нет'}")
        
        print(f"\n📁 Сохраненные файлы:")
        import os
        files = ["latest_news.txt", "translation.txt", "generated_post.txt", 
                "post_variations.txt", "vk_publication_log.txt"]
        
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"   ✓ {file} ({size} байт)")
            else:
                print(f"   ✗ {file} (отсутствует)")
    
    def show_help(self):
        """Показать справку"""
        print("\n" + "=" * 60)
        print("❓ ПОМОЩЬ")
        print("=" * 60)
        
        print("\n📖 Краткое руководство:")
        print("1. 📡 Сначала соберите новости - пункт 1")
        print("2. 🔤 Переведите интересную статью - пункт 2")
        print("3. ✍️  Создайте пост из перевода - пункт 3")
        print("4. 📤 Опубликуйте пост в VK - пункт 5")
        
        print("\n💡 Советы:")
        print("• Для тестирования можно использовать все функции по порядку")
        print("• Функция 'Полный цикл' (6) автоматизирует весь процесс")
        print("• Все результаты сохраняются в файлы")
        
        print("\n⚙️ Настройки:")
        print("• VK токен должен быть в .env файле")
        print("• Ollama должен быть запущен (ollama serve)")
        print("• Модель qwen2.5:7b должна быть загружена")
    
    def _save_to_file(self, filename, content):
        """Сохранить содержимое в файл"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"⚠️ Не удалось сохранить в {filename}: {e}")
            return False


def main():
    try:
        agent = InteractiveNewsAgent()
        agent.run()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️ Проверьте:")
        print("   1. Файл .env с VK_ACCESS_TOKEN и VK_GROUP_ID")
        print("   2. Запущен ли Ollama (ollama serve)")
        print("   3. Установлены ли все зависимости")


if __name__ == "__main__":
    main()