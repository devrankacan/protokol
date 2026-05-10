#!/bin/bash
set -e

cd "$(dirname "$0")"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  .env dosyası oluşturuldu. Lütfen ANTHROPIC_API_KEY değerini girin."
  echo "    nano .env"
  exit 1
fi

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
  echo "📦 Bağımlılıklar yükleniyor..."
  pip install -r requirements.txt
fi

echo "🚀 Genexa CRO sunucusu başlatılıyor..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
