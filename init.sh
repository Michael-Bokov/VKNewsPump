#!/bin/bash
# init.sh

#!/bin/bash
echo "=== Ollama Initialization ==="

# Запускаем сервер
echo "🚀 Запускаем сервер..."
ollama serve &
PID=$!
sleep 15

# Скачиваем модель через API
echo "📥 Скачиваем модель..."
# curl -X POST http://localhost:11434/api/pull \
#   -H "Content-Type: application/json" \
#   -d '{"name": "qwen2.5:7b", "stream": false}' \
#   --silent && echo "✅ Модель загружается..."
echo "📥 Пробуем скачать модель qwen2.5:7b..."
if ollama pull qwen2.5:7b 2>/dev/null; then
    echo "✅ Модель загружается..."
else
    echo "⚠️  Не удалось скачать модель через ollama pull"
    echo "ℹ️  Можно скачать позже: docker exec ollama-7b ollama pull qwen2.5:7b"
fi
echo "✅ Сервер запущен, модель загружается в фоне"
echo "🔍 Проверьте: curl http://localhost:11434/api/tags"

# Держим процесс живым
wait $PID