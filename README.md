# 🤖 بوت تحميل الوسائط العربي

  ## المنصات المدعومة
  📷 Instagram | 🎵 TikTok | ▶️ YouTube | 🐦 X (Twitter) | 🎧 SoundCloud | 📌 Pinterest

  ## التثبيت
  ```bash
  pip install -r requirements.txt
  cp .env.example .env
  nano .env   # أضف BOT_TOKEN و ADMIN_IDS و MONGO_URI
  python run.py
  ```

  ## أوامر المستخدم
  | الأمر | الوصف |
  |-------|-------|
  | /start | بدء البوت |
  | /help | دليل الاستخدام |

  ## أوامر الإدارة
  | الأمر | الوصف |
  |-------|-------|
  | /stats | الإحصائيات |
  | /users | عدد المستخدمين |
  | /ban <id> | حظر مستخدم |
  | /unban <id> | رفع الحظر |
  | /broadcast <msg> | إرسال جماعي |
  | /logs | آخر الأخطاء |
  | /setforce @ch | إضافة قناة اشتراك إجباري |
  | /removeforce @ch | إزالة قناة اشتراك إجباري |
  | /forcesubs | عرض القنوات + حالة التفعيل |
  | /forceon | ✅ تفعيل الاشتراك الإجباري |
  | /forceoff | 🔴 تعطيل الاشتراك الإجباري |

  ## الاشتراك الإجباري
  - /forceon — تفعيل الاشتراك الإجباري
  - /forceoff — تعطيل الاشتراك الإجباري
  - /forcesubs — عرض الحالة مع زر تبديل سريع
  