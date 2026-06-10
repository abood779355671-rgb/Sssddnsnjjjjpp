#!/usr/bin/env bash
  set -e
  echo "=========================================="
  echo "   تثبيت بوت تحميل الوسائط العربي"
  echo "=========================================="
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip -q
  pip install -r requirements.txt -q
  [ ! -f .env ] && cp .env.example .env && echo "✅ تم إنشاء .env - عدّله الآن" || echo "ℹ️  .env موجود"
  echo ""
  echo "الخطوة التالية: عدّل .env ثم شغّل: python run.py"
  