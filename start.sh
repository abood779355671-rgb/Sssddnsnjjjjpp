#!/usr/bin/env bash
  set -e
  mkdir -p /tmp/mongodb_data /tmp/tgbot_downloads
  if ! pgrep -x mongod > /dev/null; then
      echo "🍃 تشغيل MongoDB..."
      mongod --dbpath /tmp/mongodb_data --logpath /tmp/mongodb.log --fork --bind_ip 127.0.0.1
      sleep 2
  fi
  echo "🤖 تشغيل البوت..."
  [ -d venv ] && source venv/bin/activate
  python run.py
  