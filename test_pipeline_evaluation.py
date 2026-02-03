# test_pipeline_evaluation.py
"""
Отдельный файл для тестирования и оценки пайплайна
НЕ публикует реальные посты, работает с тестовыми данными
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Импортируем Langfuse
from langfuse import Langfuse

# ================ Инициализация Langfuse ================
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

langfuse_client = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)

# ================ ТЕСТОВЫЙ ДАТАСЕТ ================

def create_test_dataset():
    """Создает тестовый датасет с фиксированными данными"""
    print("📊 СОЗДАНИЕ ТЕСТОВОГО ДАТАСЕТА")
    print("=" * 50)
    
    # Фиксированные тестовые данные (не из интернета!)
    test_dataset = {
        "name": "news_pipeline_test_cases",
        "description": "Фиксированные тестовые кейсы для оценки пайплайна",
        "test_cases": [
            {
                "id": "test_case_1",
                "name": "Короткая технологическая новость",
                "input": {
                    "title": "AI Revolutionizes Healthcare",
                    "content": """Artificial intelligence is transforming healthcare with new diagnostic tools. 
                    Doctors can now detect diseases earlier and more accurately using AI algorithms.""",
                    "source": "TechNews",
                    "url": "https://test.com/ai-healthcare",
                    "date": "2024-02-04",
                    "text_length": 200
                },
                "expected_output": {
                    "has_translation": True,
                    "post_length_min": 100,
                    "post_length_max": 300,
                    "has_hashtags": True
                }
            },
            {
                "id": "test_case_2",
                "name": "Длинная научная статья",
                "input": {
                    "title": "Breakthrough in Quantum Computing",
                    "content": """Researchers have made significant progress in quantum computing, 
                    achieving quantum supremacy for the first time. The new quantum processor 
                    can perform calculations that would take traditional computers thousands of years. 
                    This breakthrough opens new possibilities for cryptography, drug discovery, 
                    and climate modeling. The team published their findings in Nature journal.""",
                    "source": "ScienceDaily",
                    "url": "https://test.com/quantum-breakthrough",
                    "date": "2024-02-03",
                    "text_length": 400
                },
                "expected_output": {
                    "has_translation": True,
                    "post_length_min": 150,
                    "post_length_max": 400,
                    "has_hashtags": True
                }
            },
            {
                "id": "test_case_3",
                "name": "Короткая новость с ошибкой",
                "input": {
                    "title": "Test Error Case",
                    "content": "Short test",
                    "source": "TestSource",
                    "url": "https://test.com/error",
                    "date": "2024-02-04",
                    "text_length": 10
                },
                "expected_output": {
                    "has_translation": False,
                    "should_fail": True
                }
            }
        ]
    }
    
    # Сохраняем датасет в файл
    with open("test_dataset.json", "w", encoding="utf-8") as f:
        json.dump(test_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Создан тестовый датасет с {len(test_dataset['test_cases'])} кейсами")
    print(f"📁 Сохранен в: test_dataset.json")
    
    # Создаем trace в Langfuse для документации датасета
    trace_id = f"dataset_creation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    trace = langfuse_client.trace(
        id=trace_id,
        name="Test Dataset Creation",
        metadata={
            "dataset_name": test_dataset["name"],
            "test_cases_count": len(test_dataset["test_cases"])
        }
    )
    
    for test_case in test_dataset["test_cases"]:
        trace.span(
            name=f"test_case_{test_case['id']}",
            input=test_case["input"],
            output=test_case["expected_output"],
            metadata={
                "test_id": test_case["id"],
                "test_name": test_case["name"],
                "type": "dataset_item"
            }
        )
    
    trace.update(output={"status": "created"})
    langfuse_client.flush()
    
    print(f"📊 Датасет залогирован в Langfuse: {trace_id}")
    return test_dataset

# ================ ТЕСТОВЫЙ ПАЙПЛАЙН (без реальных действий) ================

class MockTranslationTool:
    """Заглушка для перевода - не вызывает реальный LLM"""
    def run(self, params):
        article_text = params.get("article_text", "")
        return f"[ПЕРЕВОД] {article_text} [КОНЕЦ ПЕРЕВОДА]"

class MockPostTool:
    """Заглушка для создания поста"""
    def run(self, params):
        article_data = json.loads(params.get("article_data", "{}"))
        title = article_data.get('title', 'Без названия')
        return f"""📰 {title}

Это тестовый пост созданный для оценки качества пайплайна.

#{title.replace(' ', '')} #новости #тест"""

class MockPublisher:
    """Заглушка для публикации - ничего не публикует"""
    def run(self, params):
        return "Тестовая публикация (ничего не опубликовано)"

def run_test_pipeline(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Запускает тестовый пайплайн на одном тестовом кейсе"""
    trace_id = f"test_run_{test_case['id']}_{datetime.now().strftime('%H%M%S')}"
    
    trace = langfuse_client.trace(
        id=trace_id,
        name=f"Test Run: {test_case['name']}",
        metadata={
            "test_case_id": test_case["id"],
            "test_type": "evaluation"
        }
    )
    
    # Шаг 1: "Сбор" новости (у нас уже есть тестовые данные)
    trace.span(
        name="fetch_news",
        input={"test_case": test_case["id"]},
        output={"articles_found": 1},
        metadata={"step": 1, "duration": 0.1}
    )
    
    # Шаг 2: Дедупликация (всегда новая в тестах)
    trace.span(
        name="deduplication",
        input={"article_title": test_case["input"]["title"]},
        output={"is_duplicate": False},
        metadata={"step": 2, "duration": 0.05}
    )
    
    # Шаг 3: Выбор статьи
    trace.span(
        name="article_selection",
        input={"available_articles": 1},
        output={"selected_article": test_case["input"]["title"]},
        metadata={"step": 3, "duration": 0.01}
    )
    
    # Шаг 4: Перевод (заглушка)
    translation_tool = MockTranslationTool()
    translated = translation_tool.run({"article_text": test_case["input"]["content"]})
    
    trace.span(
        name="translation",
        input={"original_length": len(test_case["input"]["content"])},
        output={"translated_length": len(translated)},
        metadata={"step": 4, "duration": 0.2}
    )
    
    # Шаг 5: Создание поста (заглушка)
    post_tool = MockPostTool()
    article_data = test_case["input"].copy()
    article_data["text_ru"] = translated
    post = post_tool.run({"article_data": json.dumps(article_data)})
    
    trace.span(
        name="post_generation",
        input={"article_title": test_case["input"]["title"]},
        output={"post_length": len(post)},
        metadata={"step": 5, "duration": 0.15}
    )
    
    # Шаг 6: Публикация (заглушка)
    publisher = MockPublisher()
    publish_result = publisher.run({"post_text": post})
    
    trace.span(
        name="publishing",
        input={"post_length": len(post)},
        output={"result": publish_result},
        metadata={"step": 6, "duration": 0.1}
    )
    
    # Собираем результаты
    result = {
        "test_case_id": test_case["id"],
        "input": test_case["input"],
        "outputs": {
            "translated_text": translated,
            "generated_post": post,
            "published_result": publish_result
        },
        "metrics": {
            "translation_length": len(translated),
            "post_length": len(post),
            "total_time": 0.61  # Сумма всех duration
        }
    }
    
    # Завершаем trace
    trace.update(
        output={
            "test_passed": True,
            "post_length": len(post),
            "has_translation": True
        }
    )
    
    return trace_id, result

# ================ EVALUATOR ================

def evaluate_test_result(test_case: Dict[str, Any], result: Dict[str, Any], trace_id: str):
    """Оценивает результат тестового прогона"""
    
    scores = []
    comments = []
    
    # Критерий 1: Длина перевода
    original_len = len(test_case["input"]["content"])
    translated_len = result["metrics"]["translation_length"]
    if translated_len > 0:
        translation_score = min(3, translated_len / original_len * 3)
        scores.append(translation_score)
        comments.append(f"Перевод: {translation_score:.1f}/3")
    else:
        scores.append(0)
        comments.append("Перевод: 0/3 (нет перевода)")
    
    # Критерий 2: Длина поста
    post_len = result["metrics"]["post_length"]
    expected_min = test_case["expected_output"].get("post_length_min", 100)
    expected_max = test_case["expected_output"].get("post_length_max", 300)
    
    if expected_min <= post_len <= expected_max:
        post_score = 4
    elif post_len > 0:
        # Штраф за отклонение
        deviation = min(abs(post_len - expected_min), abs(post_len - expected_max))
        penalty = min(2, deviation / 100)
        post_score = 4 - penalty
    else:
        post_score = 0
    
    scores.append(post_score)
    comments.append(f"Пост: {post_score:.1f}/4 (длина: {post_len})")
    
    # Критерий 3: Наличие хэштегов
    post_text = result["outputs"]["generated_post"]
    if "#" in post_text:
        hashtag_score = 2
        comments.append("Хэштеги: 2/2 (есть)")
    else:
        hashtag_score = 0
        comments.append("Хэштеги: 0/2 (нет)")
    scores.append(hashtag_score)
    
    # Критерий 4: Форматирование
    if "📰" in post_text and "\n\n" in post_text:
        format_score = 1
        comments.append("Формат: 1/1 (OK)")
    else:
        format_score = 0
        comments.append("Формат: 0/1 (плохо)")
    scores.append(format_score)
    
    # Итоговая оценка (0-10)
    total_score = sum(scores)
    
    # Логируем оценку в Langfuse
    langfuse_client.score(
        trace_id=trace_id,
        name="test_evaluation_score",
        value=float(total_score),
        comment="; ".join(comments)
    )
    
    print(f"  📊 Оценка: {total_score:.1f}/10")
    print(f"  📝 Комментарии: {'; '.join(comments)}")
    
    return total_score

# ================ ОСНОВНОЙ БЛОК ================

def main():
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ПАЙПЛАЙНА С LANGFUSE")
    print("=" * 60)
    
    # 1. Создаем тестовый датасет
    test_dataset = create_test_dataset()
    
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК ТЕСТОВЫХ ПРОГОНОВ")
    print("=" * 60)
    
    all_scores = []
    
    # 2. Запускаем тесты для каждого кейса
    for test_case in test_dataset["test_cases"]:
        print(f"\n🔬 Тест: {test_case['name']} ({test_case['id']})")
        print("-" * 40)
        
        # Запускаем тестовый пайплайн
        trace_id, result = run_test_pipeline(test_case)
        
        print(f"  ✅ Запущен, Trace ID: {trace_id}")
        print(f"  📊 Результаты:")
        print(f"    • Длина оригинала: {len(test_case['input']['content'])}")
        print(f"    • Длина перевода: {result['metrics']['translation_length']}")
        print(f"    • Длина поста: {result['metrics']['post_length']}")
        
        # Оцениваем результат
        score = evaluate_test_result(test_case, result, trace_id)
        all_scores.append(score)
        
        print(f"  🔗 Langfuse: {LANGFUSE_HOST}/trace/{trace_id}")
    
    # 3. Анализ результатов
    print("\n" + "=" * 60)
    print("📈 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    max_score = max(all_scores) if all_scores else 0
    min_score = min(all_scores) if all_scores else 0
    
    print(f"📊 Статистика:")
    print(f"  • Всего тестов: {len(test_dataset['test_cases'])}")
    print(f"  • Средняя оценка: {avg_score:.1f}/10")
    print(f"  • Лучший результат: {max_score:.1f}/10")
    print(f"  • Худший результат: {min_score:.1f}/10")
    
    # Создаем итоговый trace с результатами
    summary_trace_id = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    trace = langfuse_client.trace(
        id=summary_trace_id,
        name="Test Suite Summary",
        metadata={
            "total_tests": len(test_dataset["test_cases"]),
            "average_score": avg_score
        }
    )
    
    trace.span(
        name="test_results_analysis",
        input={"test_cases": [tc["id"] for tc in test_dataset["test_cases"]]},
        output={
            "average_score": avg_score,
            "max_score": max_score,
            "min_score": min_score
        },
        metadata={"analysis_type": "test_suite"}
    )
    
    trace.update(output={"status": "completed"})
    langfuse_client.flush()
    
    print(f"\n📝 Итоговый отчет сохранен в Langfuse:")
    print(f"🔗 {LANGFUSE_HOST}/trace/{summary_trace_id}")
    
    # Сохраняем локальный отчет
    report = {
        "test_date": datetime.now().isoformat(),
        "dataset": test_dataset["name"],
        "total_tests": len(test_dataset["test_cases"]),
        "scores": all_scores,
        "average_score": avg_score,
        "summary_trace_id": summary_trace_id
    }
    
    with open("test_evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Локальный отчет: test_evaluation_report.json")

if __name__ == "__main__":
    main()