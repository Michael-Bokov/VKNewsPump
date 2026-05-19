# hybrid_rss_agent.py
import feedparser
import time
import re
import requests
from typing import List, Dict, Any
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup

class HybridRSSAgent:
    """Гибридный агент: для некоторых фидов скачивает, для других берет из RSS"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Разные стратегии для разных фидов
        self.feed_strategies = {
            # Фиды, требующие скачивания полного текста
            'download': [
                "https://research.google/blog/rss/",
                "https://techcrunch.com/feed/"
                #"https://www.deepmind.com/blog/rss.xml",
            ],
            # Фиды с полным текстом в RSS
            'full_text_rss': [
                #"https://www.marktechpost.com/feed/",
                
                #"https://techcrunch.com/feed/"
                #"https://machinelearningmastery.com/feed/",
                #"https://aws.amazon.com/blogs/machine-learning/feed/",
            ],
            # Фиды только с описаниями
            'summary_only': [
                #"https://techcrunch.com/feed/",
                #"https://blog.google/rss/",
            ]
        }
        
        # Все фиды
        self.all_feeds = []
        for feeds in self.feed_strategies.values(): 
            self.all_feeds.extend(feeds)
    
    def fetch_articles(self, max_per_feed: int = 8) -> List[Dict]:
        """Сбор статей с учетом стратегии для каждого фида"""
        all_articles = []
        
        print(f"📡 Собираем статьи с {len(self.all_feeds)} источников...")
        
        for feed_url in self.all_feeds:
            try:
                print(f"\n🔍 {self._get_feed_name(feed_url)}")
                
                # Определяем стратегию
                strategy = self._get_strategy(feed_url)
                print(f"   Стратегия: {strategy}")
                
                articles = self._parse_feed_with_strategy(feed_url, max_per_feed, strategy)
                all_articles.extend(articles)
                print(f"   ✅ Найдено: {len(articles)} статей")
                
                time.sleep(1)  # Вежливая пауза
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                continue
        
        print(f"\n🎯 Всего собрано статей: {len(all_articles)}")
        return all_articles
    
    def _get_feed_name(self, url: str) -> str:
        """Красивое имя фида"""
        names = {
            "research.google": "Google Research",
            "deepmind.com": "DeepMind",
            "marktechpost.com": "MarkTechPost",
            "machinelearningmastery.com": "ML Mastery",
            "aws.amazon.com": "AWS ML Blog",
            "techcrunch.com": "TechCrunch",
            "blog.google": "Google Blog",
        }
        
        for key, name in names.items():
            if key in url:
                return name
        
        return url
    
    def _get_strategy(self, feed_url: str) -> str:
        """Определяем стратегию для фида"""
        for strategy, feeds in self.feed_strategies.items():
            if feed_url in feeds:
                return strategy
        return 'summary_only'  # По умолчанию
    
    def _parse_feed_with_strategy(self, feed_url: str, max_articles: int, strategy: str) -> List[Dict]:
        """Парсим фид с учетом стратегии"""
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                print(f"   ⚠️ Предупреждение RSS: {feed.bozo_exception}")
            
            if not feed.entries:
                return articles
            
            for entry in feed.entries[:max_articles]:
                article = self._extract_article_with_strategy(entry, feed_url, strategy)
                if article:
                    articles.append(article)
        
        except Exception as e:
            print(f"   ❌ Ошибка парсинга: {e}")
        
        return articles
    
    def _extract_article_with_strategy(self, entry, source: str, strategy: str) -> Dict[str, Any]:
        """Извлекаем статью с учетом стратегии"""
        try:
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            link = entry.get('link', '').strip()
            date = self._extract_date_simple(entry)
            
            # Получаем текст в зависимости от стратегии
            if strategy == 'download':
                full_text = self._download_full_text(link)
                # Если не удалось скачать, используем summary
                if len(full_text) < 100:
                    summary = entry.get('summary', entry.get('description', ''))
                    full_text = self._clean_text(summary)
            
            elif strategy == 'full_text_rss':
                # Пробуем взять полный текст из RSS
                full_text = self._extract_from_rss(entry)
                if len(full_text) < 100:
                    summary = entry.get('summary', entry.get('description', ''))
                    full_text = self._clean_text(summary)
            
            else:  # summary_only
                summary = entry.get('summary', entry.get('description', ''))
                full_text = self._clean_text(summary)
            
            # Пропускаем слишком короткие
            if len(full_text) < 100:
                return None
            
            # ID
            article_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()[:12]
            
            return {
                'id': article_id,
                'title': title,
                'url': link,
                'date': date,
                'full_text': full_text[:4000],
                'source': source,
                'strategy': strategy,
                'text_length': len(full_text)
            }
            
        except Exception as e:
            print(f"      ⚠️ Ошибка: {e}")
            return None
    
    def _download_full_text(self, url: str) -> str:
        """Скачиваем полный текст статьи"""
        try:
            if not url or not url.startswith('http'):
                return ""
            
            print(f"      📥 Скачиваем: {url[:50]}...")
            
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Ищем основной контент
            article_content = ""
            
            # Для Google Research
            if "research.google" in url:
                # Ищем по специфичным селекторам
                selectors = [
                    {'class': 'post-content'},
                    {'role': 'main'},
                    {'id': 'main-content'},
                ]
                
                for selector in selectors:
                    elements = soup.find_all(attrs=selector)
                    for element in elements:
                        text = element.get_text(strip=True, separator=' ')
                        if len(text) > len(article_content):
                            article_content = text
            
            # Если не нашли, ищем article или параграфы
            if not article_content:
                article_elements = soup.find_all('article')
                for element in article_elements:
                    text = element.get_text(strip=True, separator=' ')
                    if len(text) > len(article_content):
                        article_content = text
            
            if not article_content:
                paragraphs = soup.find_all('p')
                article_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Очищаем
            article_content = re.sub(r'\s+', ' ', article_content).strip()
            
            print(f"      ✅ Скачано: {len(article_content)} символов")
            return article_content[:8000]
            
        except Exception as e:
            print(f"      ⚠️ Не удалось скачать: {e}")
            return ""
    
    def _extract_from_rss(self, entry) -> str:
        """Извлекаем полный текст из RSS (если есть)"""
        text = ""
        
        # Поле content
        if hasattr(entry, 'content'):
            for item in entry.content:
                if hasattr(item, 'value') and item.value:
                    content_text = self._clean_text(item.value)
                    if len(content_text) > len(text):
                        text = content_text
        
        # Поле encoded
        if hasattr(entry, 'encoded') and entry.encoded:
            encoded_text = self._clean_text(entry.encoded)
            if len(encoded_text) > len(text):
                text = encoded_text
        
        return text
    
    def _extract_date_simple(self, entry) -> str:
        """Простое извлечение даты"""
        for field in ['published', 'updated', 'created', 'pubDate']:
            if hasattr(entry, field) and getattr(entry, field):
                date_str = str(getattr(entry, field))
                # Ищем YYYY-MM-DD
                match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
                if match:
                    return match.group(0)
                # Или первые 10 символов
                if len(date_str) >= 10:
                    return date_str[:10]
        
        return datetime.now().strftime("%Y-%m-%d")
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста"""
        if not text:
            return ""
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Заменяем HTML сущности
        replacements = {
            '&nbsp;': ' ', '&lt;': '<', '&gt;': '>', '&amp;': '&',
            '&quot;': '"', "&apos;": "'", '&#8217;': "'",
        }
        
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text