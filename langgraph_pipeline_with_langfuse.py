# langgraph_pipeline_with_langfuse.py
import json
import hashlib
import os
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from datetime import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем Langfuse
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
import langfuse

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Импортируем инструменты
from lg_rss_tool import RssFetchTool
from lg_translation_tool import TranslationTool
from lg_post_tool import GeneratePostTool
from lg_publisher_tool import VKPublishTool

from database import NewsDatabase

# ================ Инициализация Langfuse ================
# Получаем ключи из переменных окружения
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Инициализируем Langfuse клиент
try:
    langfuse_client = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    print(f"✅ Langfuse инициализирован: {LANGFUSE_HOST}")
except Exception as e:
    print(f"⚠️  Ошибка инициализации Langfuse: {e}")
    langfuse_client = None

# Глобальный счетчик для уникальных ID трассировок
trace_counter = 0

# ================ State Definition ================
class PipelineState(TypedDict):
    """Состояние пайплайна"""
    all_articles: List[Dict[str, Any]]
    new_articles: List[Dict[str, Any]]
    selected_article: Optional[Dict[str, Any]]
    translated_text: Optional[str]
    generated_post: Optional[str]
    published: bool
    logs: List[str]
    current_step: str
    skip_reason: Optional[str]
    trace_id: Optional[str]
    langfuse_handler: Optional[CallbackHandler]
    trace_object: Optional[Any]  # Объект trace для текущего выполнения

# Инициализируем базу данных
db = NewsDatabase()

# ================ Вспомогательные функции для Langfuse 2.x ================

def create_trace(metadata: Dict[str, Any] = None) -> tuple:
    """Создает новую трассировку в Langfuse"""
    global trace_counter
    
    if not langfuse_client:
        return None, None
    
    trace_counter += 1
    trace_id = f"news_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trace_counter}"
    
    try:
        # В версии 2.x trace создается с id
        trace = langfuse_client.trace(
            id=trace_id,
            name="News Processing Pipeline",
            metadata=metadata or {},
            input={"timestamp": datetime.now().isoformat()}
        )
        
        print(f"📊 Создан Trace: {trace_id}")
        return trace_id, trace
        
    except Exception as e:
        print(f"❌ Ошибка создания trace: {e}")
        return None, None

def log_span(trace: Any, name: str, input_data: Any = None, output_data: Any = None, 
             metadata: Dict = None) -> Optional[Any]:
    """Логирует span в Langfuse"""
    if not trace:
        return None
        
    try:
        # В версии 2.x input и output передаются отдельно
        span = trace.span(
            name=name,
            input=input_data,
            output=output_data,
            metadata=metadata or {}
        )
        return span
    except Exception as e:
        print(f"❌ Ошибка создания span '{name}': {e}")
        return None

def create_generation(trace: Any, name: str, input_data: Any = None, output_data: Any = None,
                      model: str = None, tokens_used: int = None, metadata: Dict = None) -> Optional[Any]:
    """Создает LLM generation в Langfuse"""
    if not trace:
        return None
        
    try:
        # В версии 2.x generation создается с input/output
        generation = trace.generation(
            name=name,
            input=input_data,
            output=output_data,
            model=model,
            metadata=metadata or {}
        )
        
        # Обновляем usage если указано
        if tokens_used and hasattr(generation, 'update'):
            try:
                generation.update(
                    usage={
                        "input": tokens_used,
                        "output": 0,
                        "total": tokens_used
                    }
                )
            except:
                pass
                
        return generation
    except Exception as e:
        print(f"❌ Ошибка создания generation '{name}': {e}")
        return None

def log_event(trace: Any, name: str, metadata: Dict = None) -> Optional[Any]:
    """Логирует событие в Langfuse"""
    if not trace:
        return None
        
    try:
        event = trace.event(
            name=name,
            metadata=metadata or {}
        )
        return event
    except Exception as e:
        print(f"❌ Ошибка создания event '{name}': {e}")
        return None

def log_score(trace: Any, name: str, value: float, comment: str = None) -> Optional[Any]:
    """Логирует оценку в Langfuse"""
    if not trace:
        return None
        
    try:
        score = trace.score(
            name=name,
            value=value,
            comment=comment
        )
        return score
    except Exception as e:
        print(f"❌ Ошибка создания score '{name}': {e}")
        return None

# ================ Nodes (Узлы графа) с исправленной инструментацией ================

def fetch_news_node(state: PipelineState) -> PipelineState:
    """Сбор новостей с инструментацией"""
    print("\n📡 Шаг 1: Сбор новостей...")
    trace = state.get("trace_object")
    logs = state.get("logs", [])
    
    # Начинаем span для этого шага
    start_time = datetime.now()
    log_event(trace, "fetch_news_started", {"start_time": start_time.isoformat()})
    
    try:
        tool = RssFetchTool()
        result = tool.run({"max_per_feed": 3})
        data = json.loads(result)
        articles = data.get("articles", [])
        
        # Завершаем span с результатами
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_span(
            trace=trace,
            name="fetch_news",
            input_data={"max_per_feed": 3},
            output_data={"article_count": len(articles)},
            metadata={
                "duration_seconds": duration,
                "articles_fetched": len(articles),
                "step": "fetch_news"
            }
        )
        
        # Логируем оценку производительности
        log_score(trace, "fetch_speed", min(10, 10 - duration), 
                 f"Сбор {len(articles)} статей за {duration:.2f} секунд")
        
        logs.append(f"{datetime.now().strftime('%H:%M:%S')} - Собрано {len(articles)} статей")
        
        return {
            "all_articles": articles,
            "logs": logs,
            "current_step": "fetched",
            "skip_reason": None,
            "trace_object": trace
        }
        
    except Exception as e:
        log_event(trace, "fetch_news_error", {"error": str(e)})
        logs.append(f"Ошибка сбора: {e}")
        return {
            "all_articles": [],
            "logs": logs,
            "current_step": "error",
            "skip_reason": f"Ошибка сбора: {e}",
            "trace_object": trace
        }

def deduplicate_node(state: PipelineState) -> PipelineState:
    """Дедупликация статей с инструментацией"""
    print("\n🔍 Шаг 2: Дедупликация...")
    trace = state.get("trace_object")
    logs = state.get("logs", [])
    
    start_time = datetime.now()
    log_event(trace, "deduplication_started")
    
    all_articles = state.get("all_articles", [])
    new_articles = []
    duplicate_count = 0
    
    for article in all_articles:
        is_dup, reason, similarity = db.is_duplicate(article)
        if not is_dup:
            article['duplicate_check'] = {
                'is_duplicate': False,
                'reason': reason,
                'similarity': similarity
            }
            new_articles.append(article)
            logs.append(f"Новая статья: {article['title'][:50]}...")
        else:
            duplicate_count += 1
            logs.append(f"Дубликат: {article['title'][:50]}...")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log_span(
        trace=trace,
        name="deduplication",
        input_data={"total_articles": len(all_articles)},
        output_data={
            "new_articles": len(new_articles),
            "duplicates_found": duplicate_count
        },
        metadata={
            "duration_seconds": duration,
            "step": "deduplication"
        }
    )
    
    # Логируем оценку качества дедупликации
    if all_articles:
        unique_ratio = len(new_articles) / len(all_articles)
        log_score(trace, "uniqueness_ratio", unique_ratio * 10,
                 f"{len(new_articles)} уникальных из {len(all_articles)} статей")
    
    return {
        "new_articles": new_articles,
        "logs": logs,
        "current_step": "deduplicated" if new_articles else "no_new_articles",
        "skip_reason": None if new_articles else "Нет новых статей после дедупликации",
        "trace_object": trace
    }

def select_article_node(state: PipelineState) -> PipelineState:
    """Выбор статьи для публикации с инструментацией"""
    print("\n🎯 Шаг 3: Выбор статьи...")
    trace = state.get("trace_object")
    logs = state.get("logs", [])
    
    start_time = datetime.now()
    log_event(trace, "article_selection_started")
    
    new_articles = state.get("new_articles", [])
    
    if not new_articles:
        log_event(trace, "no_articles_available")
        logs.append("Нет новых статей для публикации")
        return {
            "selected_article": None,
            "logs": logs,
            "current_step": "no_articles",
            "skip_reason": "Нет новых статей для публикации",
            "trace_object": trace
        }
    
    # Выбираем самую длинную статью
    selected = max(new_articles, key=lambda x: x.get('text_length', 0))
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log_span(
        trace=trace,
        name="article_selection",
        input_data={"available_articles": len(new_articles)},
        output_data={
            "selected_article_title": selected.get('title', '')[:100],
            "selected_article_length": selected.get('text_length', 0)
        },
        metadata={
            "duration_seconds": duration,
            "selection_criteria": "longest_article",
            "step": "selection"
        }
    )
    
    logs.append(f"Выбрана статья: {selected['title'][:50]}...")
    logs.append(f"Длина: {selected.get('text_length', 0)} символов")
    logs.append(f"Источник: {selected.get('source', 'неизвестно')}")

    return {
        "selected_article": selected,
        "logs": logs,
        "current_step": "selected",
        "skip_reason": None,
        "trace_object": trace
    }

def translate_node(state: PipelineState) -> PipelineState:
    """Перевод статьи с инструментацией"""
    print("\n🔤 Шаг 4: Перевод статьи...")
    trace = state.get("trace_object")
    logs = state.get("logs", [])
    
    start_time = datetime.now()
    log_event(trace, "translation_started")
    
    selected_article = state.get("selected_article")
    if not selected_article:
        log_event(trace, "no_article_to_translate")
        logs.append("Нет статьи для перевода")
        return {
            "logs": logs,
            "current_step": "no_article_to_translate",
            "skip_reason": "Нет статьи для перевода",
            "trace_object": trace
        }
    
    try:
        tool = TranslationTool()
        article_text = selected_article.get('full_text', '')
        
        translated = tool.run({
            "article_text": article_text,
            "max_length": 2000
        })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Логируем LLM generation
        create_generation(
            trace=trace,
            name="translation_generation",
            input_data={"original_text_length": len(article_text)},
            output_data={"translated_text_length": len(translated)},
            model="ollama/llama3.2",
            tokens_used=len(article_text) // 4 + len(translated) // 4,
            metadata={
                "source_language": "en",
                "target_language": "ru",
                "compression_ratio": len(translated) / len(article_text) if article_text else 0,
                "step": "translation",
                "duration_seconds": duration
            }
        )
        
        log_span(
            trace=trace,
            name="translation_process",
            input_data={"original_length": len(article_text)},
            output_data={"translated_length": len(translated)},
            metadata={
                "duration_seconds": duration,
                "source": selected_article.get('source', 'unknown'),
                "step": "translation"
            }
        )
        
        # Логируем оценку качества перевода
        if article_text and translated:
            compression_ratio = len(translated) / len(article_text)
            quality_score = 10 - abs(1 - compression_ratio) * 5
            log_score(trace, "translation_quality", max(0, quality_score),
                     f"Коэффициент сжатия: {compression_ratio:.2f}")
        
        logs.append(f"Статья переведена ({len(translated)} символов)")
        
        return {
            "translated_text": translated,
            "logs": logs,
            "current_step": "translated",
            "skip_reason": None,
            "trace_object": trace
        }
    except Exception as e:
        log_event(trace, "translation_error", {"error": str(e)})
        logs.append(f"Ошибка перевода: {e}")
        return {
            "logs": logs,
            "current_step": "translation_error",
            "skip_reason": f"Ошибка перевода: {e}",
            "trace_object": trace
        }

def generate_post_node(state: PipelineState) -> PipelineState:
    """Создание поста с инструментацией"""
    print("\n✍️ Шаг 5: Создание поста...")
    trace = state.get("trace_object")
    logs = state.get("logs", [])
    
    start_time = datetime.now()
    log_event(trace, "post_generation_started")
    
    selected_article = state.get("selected_article")
    if not selected_article:
        log_event(trace, "no_article_for_post")
        logs.append("Нет статьи для создания поста")
        return {
            "logs": logs,
            "current_step": "no_article_for_post",
            "skip_reason": "Нет статьи для создания поста",
            "trace_object": trace
        }
    
    try:
        tool = GeneratePostTool()
        
        # Подготавливаем данные статьи
        article_data = selected_article.copy()
        if state.get("translated_text"):
            article_data['text_ru'] = state["translated_text"]
        
        post = tool.run({
            "article_data": json.dumps(article_data),
            "platform": "vk"
        })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Логируем LLM generation для создания поста
        create_generation(
            trace=trace,
            name="post_generation",
            input_data={
                "article_title": selected_article.get('title', '')[:100],
                "translated_text_length": len(state.get("translated_text", ""))
            },
            output_data={"post_length": len(post)},
            model="ollama/llama3.2",
            tokens_used=len(post) // 3,
            metadata={
                "platform": "vk",
                "step": "post_generation",
                "duration_seconds": duration
            }
        )
        
        log_span(
            trace=trace,
            name="post_generation_process",
            input_data={"article_title": selected_article.get('title', '')[:50]},
            output_data={"post_length": len(post)},
            metadata={
                "duration_seconds": duration,
                "step": "post_generation"
            }
        )
        
        # Логируем оценку качества поста
        post_score = min(10, len(post) / 100)
        log_score(trace, "post_quality", post_score,
                 f"Длина поста: {len(post)} символов")
        
        logs.append(f"Пост создан ({len(post)} символов)")
        
        return {
            "generated_post": post,
            "logs": logs,
            "current_step": "post_created",
            "skip_reason": None,
            "trace_object": trace
        }
    except Exception as e:
        log_event(trace, "post_generation_error", {"error": str(e)})
        logs.append(f"Ошибка создания поста: {e}")
        return {
            "logs": logs,
            "current_step": "post_error",
            "skip_reason": f"Ошибка создания поста: {e}",
            "trace_object": trace
        }

def publish_node(state: PipelineState) -> PipelineState:
    """Публикация поста с инструментацией"""
    print("\n📤 Шаг 6: Публикация в VK...")
    trace = state.get("trace_object")
    logs = state.get("logs", [])
    
    start_time = datetime.now()
    log_event(trace, "publish_started")
    
    post_text = state.get("generated_post")
    selected_article = state.get("selected_article")
    
    if not post_text:
        log_event(trace, "no_post_to_publish")
        logs.append("Нет поста для публикации")
        return {
            "published": False,
            "logs": logs,
            "current_step": "no_post_to_publish",
            "skip_reason": "Нет поста для публикации",
            "trace_object": trace
        }
    
    try:
        tool = VKPublishTool()
        result = tool.run({
            "post_text": post_text,
            "article_url": selected_article.get('url') if selected_article else None
        })
        
        # Добавляем в БД как опубликованную
        news_id = None
        if result and selected_article:
            news_id = db.add_news(selected_article)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Логируем событие публикации
        log_span(
            trace=trace,
            name="publish_to_vk",
            input_data={"post_length": len(post_text)},
            output_data={"result": str(result), "news_id": news_id},
            metadata={
                "duration_seconds": duration,
                "platform": "vk",
                "step": "publishing"
            }
        )
        
        # Логируем успешную публикацию как событие
        if result:
            log_event(trace, "publish_success", {
                "news_id": news_id,
                "post_length": len(post_text),
                "timestamp": datetime.now().isoformat()
            })
            
            # Финальная оценка успешности пайплайна
            log_score(trace, "pipeline_success", 10.0, 
                     "Пайплайн успешно завершен")
        else:
            log_event(trace, "publish_failed", {"error": str(result)})
            log_score(trace, "pipeline_success", 0.0, 
                     "Ошибка публикации")
        
        logs.append(f"Публикация: {result}")
        if news_id:
            logs.append(f"Добавлено в базу: {news_id}")
        
        return {
            "published": bool(result),
            "logs": logs,
            "current_step": "published" if result else "publish_error",
            "skip_reason": None if result else "Не удалось опубликовать пост",
            "trace_object": trace
        }
    except Exception as e:
        log_event(trace, "publish_error", {"error": str(e)})
        logs.append(f"Ошибка публикации: {e}")
        return {
            "published": False,
            "logs": logs,
            "current_step": "publish_error",
            "skip_reason": "Не удалось опубликовать пост",
            "trace_object": trace
        }

# ================ Conditional Edges ================

def check_condition(state: PipelineState) -> str:
    """Проверяет условие для перехода к следующему узлу"""
    current_step = state.get("current_step", "")
    trace = state.get("trace_object")
    
    if current_step in ["error", "no_new_articles", "no_articles", 
                       "no_article_to_translate", "translation_error",
                       "no_article_for_post", "post_error", 
                       "no_post_to_publish", "publish_failed", "publish_error"]:
        # Логируем завершение с ошибкой
        if trace:
            log_score(trace, "pipeline_success", 0.0, 
                     f"Пайплайн завершен с ошибкой: {current_step}")
            log_event(trace, "pipeline_failed", {"error_step": current_step})
        return "end"
    
    if current_step == "fetched":
        return "deduplicate"
    elif current_step == "deduplicated":
        return "select_article"
    elif current_step == "selected":
        return "translate"
    elif current_step == "translated":
        return "generate_post"
    elif current_step == "post_created":
        return "publish"
    elif current_step == "published":
        return "end"
    
    return "end"

# ================ Create Graph ================

def create_pipeline():
    """Создаем и компилируем граф"""
    graph = StateGraph(PipelineState)
    
    graph.add_node("fetch_news", fetch_news_node)
    graph.add_node("deduplicate", deduplicate_node)
    graph.add_node("select_article", select_article_node)
    graph.add_node("translate", translate_node)
    graph.add_node("generate_post", generate_post_node)
    graph.add_node("publish", publish_node)
    
    graph.set_entry_point("fetch_news")
    
    graph.add_conditional_edges(
        "fetch_news",
        check_condition,
        {
            "deduplicate": "deduplicate",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "deduplicate",
        check_condition,
        {
            "select_article": "select_article",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "select_article",
        check_condition,
        {
            "translate": "translate",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "translate",
        check_condition,
        {
            "generate_post": "generate_post",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "generate_post",
        check_condition,
        {
            "publish": "publish",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "publish",
        check_condition,
        {
            "end": END
        }
    )
    
    return graph.compile()

# ================ Run Pipeline ================

def run_pipeline():
    """Запуск пайплайна с инструментацией Langfuse"""
    print("=" * 60)
    print("🚀 ЗАПУСК НОВОСТНОГО ПАЙПЛАЙНА С LANGFUSE")
    print("=" * 60)
    
    # Создаем trace для всего пайплайна
    trace_id, trace = create_trace({
        "pipeline_name": "news_processing_pipeline",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    })
    
    if trace:
        print(f"📊 Trace ID: {trace_id}")
        print(f"🌐 Langfuse Dashboard: {LANGFUSE_HOST}")
    else:
        print("⚠️  Langfuse не настроен, запускаю без отслеживания")
    
    # Статистика БД до выполнения
    print(f"\n📊 Статистика БД до выполнения:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    pipeline = create_pipeline()
    
    initial_state = {
        "all_articles": [],
        "new_articles": [],
        "selected_article": None,
        "translated_text": None,
        "generated_post": None,
        "published": False,
        "logs": [],
        "current_step": "start",
        "skip_reason": None,
        "trace_id": trace_id,
        "trace_object": trace,
        "langfuse_handler": None
    }
    
    # Логируем начало пайплайна
    if trace:
        log_event(trace, "pipeline_started", {
            "start_time": datetime.now().isoformat(),
            "db_stats": stats
        })
    
    # Запускаем пайплайн
    print("\n🔄 Выполняю пайплайн...")
    start_time = datetime.now()
    
    result = pipeline.invoke(initial_state)
    
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    # Логируем завершение пайплайна
    if trace:
        log_span(
            trace,
            "complete_pipeline",
            input_data={"start_time": start_time.isoformat()},
            output_data={
            "published": result.get("published", False),
            "total_articles": len(result.get("all_articles", [])),
            "new_articles": len(result.get("new_articles", []))
            },
            metadata={
                "duration_seconds": total_duration,
                "end_time": end_time.isoformat(),
                "success": result.get("published", False)
            }
        )
        
        # Завершаем trace
        trace.update(output={
            "total_duration_seconds": total_duration,
            "articles_processed": len(result.get("all_articles", [])),
            "published_successfully": result.get("published", False)
        })
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 60)
    
    print(f"\n📝 Логи выполнения:")
    for log in result.get("logs", [])[-10:]:
        print(f"  {log}")
    
    print(f"\n📊 Статистика:")
    print(f"  • Всего статей собрано: {len(result.get('all_articles', []))}")
    print(f"  • Новых статей (не дубликаты): {len(result.get('new_articles', []))}")
    print(f"  • Статья выбрана: {'✅ Да' if result.get('selected_article') else '❌ Нет'}")
    print(f"  • Перевод готов: {'✅ Да' if result.get('translated_text') else '❌ Нет'}")
    print(f"  • Пост создан: {'✅ Да' if result.get('generated_post') else '❌ Нет'}")
    print(f"  • Опубликовано: {'✅ Да' if result.get('published', False) else '❌ Нет'}")
    print(f"  • Общее время выполнения: {total_duration:.2f} секунд")
    
    if result.get("skip_reason"):
        print(f"  • Причина пропуска: {result['skip_reason']}")
    
    # Статистика БД после выполнения
    print(f"\n📊 Статистика БД после выполнения:")
    stats_after = db.get_stats()
    for key, value in stats_after.items():
        print(f"  • {key}: {value}")
    
    # Показываем созданный пост если есть
    if result.get("generated_post"):
        print(f"\n📄 Созданный пост:")
        print("-" * 40)
        post_preview = result["generated_post"]
        if len(post_preview) > 300:
            print(post_preview[:300] + "...")
        else:
            print(post_preview)
        print("-" * 40)
    
    # Показываем информацию о статье если есть
    if result.get("selected_article"):
        article = result["selected_article"]
        print(f"\n📰 Информация о статье:")
        print(f"  • Заголовок: {article.get('title', '')[:80]}...")
        print(f"  • Источник: {article.get('source', 'неизвестно')}")
        print(f"  • Дата: {article.get('date', 'неизвестно')}")
        print(f"  • URL: {article.get('url', '')[:60]}...")
    
    if trace and trace_id:
        print(f"\n🔗 Ссылка на трассировку: {LANGFUSE_HOST}/trace/{trace_id}")
    
    # Флушим данные в Langfuse
    if langfuse_client:
        langfuse_client.flush()
    
    return result

# ================ Пример создания Dataset и Evaluator ================

def create_and_test_dataset():
    """Создает и тестирует датасет"""
    if not langfuse_client:
        print("❌ Langfuse не доступен")
        return
    
    # 1. Создаем датасет
    try:
        dataset_name = "news_pipeline_quality"
        
        # Проверяем, существует ли уже датасет
        try:
            # В новой версии API может отличаться
            # Создаем новый датасет или обновляем существующий
            print(f"🔄 Создаю датасет: {dataset_name}")
            
            # В Langfuse 2.x создание датасета может быть через другой API
            # Просто создадим trace для теста
            test_trace_id = f"dataset_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_trace = langfuse_client.trace(
                id=test_trace_id,
                name="Dataset Creation Test",
                metadata={"dataset_name": dataset_name}
            )
            
            print(f"✅ Создана тестовая трассировка для датасета: {test_trace_id}")
            
            # Добавляем тестовые кейсы как spans в trace
            test_cases = [
                {
                    "name": "technology_news_test",
                    "input": {
                        "sources": ["TechCrunch", "The Verge"],
                        "max_articles": 3,
                        "language": "en"
                    },
                    "expected_output": {
                        "success": True,
                        "min_post_length": 100,
                        "has_translation": True
                    }
                },
                {
                    "name": "science_news_test",
                    "input": {
                        "sources": ["Ars Technica"],
                        "max_articles": 2,
                        "language": "en"
                    },
                    "expected_output": {
                        "success": True,
                        "min_post_length": 150,
                        "has_translation": True
                    }
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                test_trace.span(
                    name=f"test_case_{i+1}",
                    input=test_case["input"],
                    output=test_case["expected_output"],
                    metadata={
                        "test_id": f"test_case_{i+1}",
                        "test_name": test_case["name"],
                        "type": "dataset_item"
                    }
                )
                print(f"✅ Добавлен тестовый кейс: {test_case['name']}")
            
            print(f"✅ Создано {len(test_cases)} тестовых кейсов в трассировке")
            
            # Завершаем trace
            test_trace.update(
                output={"test_cases_added": len(test_cases)},
                metadata={"completed": True}
            )
            
            return test_trace_id
            
        except Exception as e:
            print(f"⚠️  Альтернативный метод создания датасета: {e}")
            
            # Простой метод - логируем как обычные трассировки
            print("📝 Создаю тестовые трассировки для датасета...")
            
            for i in range(2):
                trace_id = f"dataset_item_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                trace = langfuse_client.trace(
                    id=trace_id,
                    name=f"Dataset Test Case {i+1}",
                    metadata={"dataset": dataset_name, "test_case": i+1}
                )
                
                # Добавляем тестовые данные
                if i == 0:
                    trace.span(
                        name="technology_test",
                        input={"sources": ["TechCrunch"], "max_articles": 3},
                        output={"expected_post_length": ">100"}
                    )
                else:
                    trace.span(
                        name="science_test",
                        input={"sources": ["Ars Technica"], "max_articles": 2},
                        output={"expected_post_length": ">150"}
                    )
                
                print(f"✅ Создан тестовый кейс {i+1}")
            
            return "dataset_created"
            
    except Exception as e:
        print(f"❌ Ошибка создания датасета: {e}")
        return None

def evaluate_pipeline_result(trace_id=None, result=None):
    """Оценивает результат выполнения пайплайна"""
    if not langfuse_client:
        print("⚠️  Langfuse не доступен, оценка пропущена")
        return
    
    if not trace_id or not result:
        print("⚠️  Не указаны trace_id или результат для оценки")
        return
    
    try:
        # Получаем данные о посте
        post_text = result.get("generated_post", "")
        published = result.get("published", False)
        articles_count = len(result.get("all_articles", []))
        new_articles = len(result.get("new_articles", []))
        
        # Рассчитываем оценку (0-10)
        score = 0
        
        # Критерий 1: длина поста (идеально 200-500 символов)
        post_length = len(post_text)
        if 200 <= post_length <= 500:
            score += 4  # Идеальная длина
        elif 100 <= post_length < 200 or 500 < post_length <= 800:
            score += 2  # Приемлемая длина
        elif post_length > 0:
            score += 1  # Хотя бы что-то есть
        else:
            score += 0  # Нет поста
        
        # Критерий 2: успешность публикации
        if published:
            score += 3
        
        # Критерий 3: наличие перевода
        if result.get("translated_text"):
            score += 2
        
        # Критерий 4: количество статей (чем больше, тем лучше, но не слишком)
        if 3 <= articles_count <= 10:
            score += 1
        
        # Нормализуем до 10 баллов
        final_score = min(10, score)
        
        # Комментарий с деталями
        comment_lines = [
            f"Длина поста: {post_length} символов",
            f"Опубликовано: {'Да' if published else 'Нет'}",
            f"Статей собрано: {articles_count}",
            f"Новых статей: {new_articles}",
            f"Есть перевод: {'Да' if result.get('translated_text') else 'Нет'}"
        ]
        comment = "; ".join(comment_lines)
        
        # Логируем оценку
        langfuse_client.score(
            trace_id=trace_id,
            name="pipeline_quality_score",
            value=float(final_score),
            comment=comment
        )
        
        # Также добавляем как span с деталями
        langfuse_client.span(
            trace_id=trace_id,
            name="manual_evaluation",
            input={
                "post_length": post_length,
                "published": published,
                "articles_count": articles_count
            },
            output={"quality_score": final_score},
            metadata={
                "evaluation_timestamp": datetime.now().isoformat(),
                "evaluator": "manual_evaluator"
            }
        )
        
        print(f"\n📊 РУЧНАЯ ОЦЕНКА КАЧЕСТВА:")
        print(f"  • Длина поста: {post_length} символов")
        print(f"  • Опубликовано: {'✅ Да' if published else '❌ Нет'}")
        print(f"  • Собрано статей: {articles_count}")
        print(f"  • Новых статей: {new_articles}")
        print(f"  • ИТОГОВАЯ ОЦЕНКА: {final_score}/10")
        print(f"  • Комментарий: {comment}")
        
        return final_score
        
    except Exception as e:
        print(f"❌ Ошибка оценки: {e}")
        return None

# ================ Запуск с оценкой ================

def run_pipeline_with_evaluation():
    """Запускает пайплайн с последующей оценкой"""
    print("=" * 60)
    print("🧪 ЗАПУСК ПАЙПЛАЙНА С ОЦЕНКОЙ КАЧЕСТВА")
    print("=" * 60)
    
    # Создаем trace для всего пайплайна
    trace_id, trace = create_trace({
        "pipeline_name": "news_processing_pipeline",
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "evaluation": "enabled"
    })
    
    if trace_id:
        print(f"📊 Trace ID: {trace_id}")
    else:
        print("⚠️  Langfuse не настроен, запускаю без отслеживания")
    
    # Запускаем пайплайн
    pipeline = create_pipeline()
    
    initial_state = {
        "all_articles": [],
        "new_articles": [],
        "selected_article": None,
        "translated_text": None,
        "generated_post": None,
        "published": False,
        "logs": [],
        "current_step": "start",
        "skip_reason": None,
        "trace_id": trace_id,
        "trace_object": trace
    }
    
    # Логируем начало
    if trace:
        log_event(trace, "pipeline_started", {
            "start_time": datetime.now().isoformat(),
            "mode": "with_evaluation"
        })
    
    # Запускаем
    start_time = datetime.now()
    result = pipeline.invoke(initial_state)
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    # Логируем завершение
    if trace:
        log_span(
            trace,
            "complete_pipeline",
            input_data={"start_time": start_time.isoformat()},
            output_data={
                "published": result.get("published", False),
                "total_articles": len(result.get("all_articles", [])),
                "new_articles": len(result.get("new_articles", []))
            },
            metadata={
                "duration_seconds": total_duration,
                "end_time": end_time.isoformat(),
                "success": result.get("published", False)
            }
        )
    
    # Выводим стандартные результаты
    print("\n" + "=" * 60)
    print("📊 ОСНОВНЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 60)
    
    print(f"  • Всего статей собрано: {len(result.get('all_articles', []))}")
    print(f"  • Новых статей: {len(result.get('new_articles', []))}")
    print(f"  • Статья выбрана: {'✅ Да' if result.get('selected_article') else '❌ Нет'}")
    print(f"  • Перевод готов: {'✅ Да' if result.get('translated_text') else '❌ Нет'}")
    print(f"  • Пост создан: {'✅ Да' if result.get('generated_post') else '❌ Нет'}")
    print(f"  • Опубликовано: {'✅ Да' if result.get('published', False) else '❌ Нет'}")
    print(f"  • Общее время: {total_duration:.2f} секунд")
    
    # Оцениваем результат
    if trace_id:
        print("\n" + "=" * 60)
        print("📈 ЗАПУСКАЮ ОЦЕНКУ КАЧЕСТВА...")
        print("=" * 60)
        evaluate_pipeline_result(trace_id, result)
    
    # Флушим данные
    if langfuse_client:
        langfuse_client.flush()
    
    return result, trace_id

if __name__ == "__main__":
    # Проверяем настройки Langfuse
    if not all([LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY]):
        print("⚠️  Внимание: Ключи Langfuse не настроены!")
        print("Добавьте в .env файл:")
        print("LANGFUSE_PUBLIC_KEY=your_public_key")
        print("LANGFUSE_SECRET_KEY=your_secret_key")
        print("LANGFUSE_HOST=https://cloud.langfuse.com")
        print("\nЗапускаю пайплайн без отслеживания...")
    
    # Создаем тестовый датасет (опционально)
    #create_and_test_dataset()
    
    # Запускаем тесты на датасете (опционально)
    #run_dataset_test()
    
    #evaluate_pipeline_result()
    # Запускаем пайплайн
    result = run_pipeline()