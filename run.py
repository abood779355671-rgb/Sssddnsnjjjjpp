#!/usr/bin/env python3
"""نقطة تشغيل البوت الرئيسية"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main
import asyncio

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║     بوت تحميل الوسائط العربي            ║
║     Arabic Media Downloader Bot          ║
║     Powered by aiogram 3.x + yt-dlp     ║
╚══════════════════════════════════════════╝
    """)
    asyncio.run(main())
