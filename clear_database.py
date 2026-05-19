# clear_database.py
import shutil
from pathlib import Path 
import json 

def clear_database():
    # Пути
    base_dir = Path(__file__).parent
    chroma_db_path = base_dir / "chroma_db"
    news_json_path = base_dir / "data" / "news_archive.json"
    
    # Удаляем ChromaDB
    if chroma_db_path.exists():
        shutil.rmtree(chroma_db_path)
        print(f"🗑️ Удалена ChromaDB: {chroma_db_path}")
    
    # Очищаем JSON архив
    if news_json_path.exists():
        news_json_path.unlink()
        print(f"🗑️ Удален архив новостей: {news_json_path}")
    
    # Создаем пустые директории
    chroma_db_path.mkdir(exist_ok=True)
    news_json_path.parent.mkdir(exist_ok=True)
    
    # Создаем пустой JSON
    with open(news_json_path, 'w', encoding='utf-8') as f:
        json.dump([], f)
    
    print("✅ База данных очищена!")

if __name__ == "__main__":
    clear_database()