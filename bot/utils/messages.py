# ===== رسائل البوت العربية =====

class Messages:
    # --- عام ---
    WELCOME = (
        "🎉 <b>أهلاً بك في بوت تحميل الوسائط!</b>\n\n"
        "أرسل لي رابطاً من إحدى المنصات التالية وسأحمّله لك فوراً:\n\n"
        "📷 <b>Instagram</b> – Reels، Posts، Photos، Carousel\n"
        "🎵 <b>TikTok</b> – فيديو بدون علامة مائية\n"
        "▶️ <b>YouTube</b> – فيديو وصوت بأعلى جودة\n"
        "🐦 <b>X (Twitter)</b> – فيديو وصور\n"
        "🎧 <b>SoundCloud</b> – تحميل MP3\n"
        "📌 <b>Pinterest</b> – صور وفيديو\n\n"
        "⚡ <i>سريع • آمن • مجاني</i>"
    )

    HELP = (
        "📖 <b>دليل الاستخدام</b>\n\n"
        "ببساطة أرسل رابط من أي منصة مدعومة:\n\n"
        "• <code>https://www.instagram.com/reel/...</code>\n"
        "• <code>https://www.tiktok.com/@.../video/...</code>\n"
        "• <code>https://www.youtube.com/watch?v=...</code>\n"
        "• <code>https://x.com/.../status/...</code>\n"
        "• <code>https://soundcloud.com/.../...</code>\n"
        "• <code>https://www.pinterest.com/pin/...</code>\n\n"
        "💡 <b>ملاحظات:</b>\n"
        "• الحد الأقصى لحجم الملف: 50MB\n"
        "• يدعم البوت الروابط المختصرة\n"
        "• لـ YouTube ستظهر لك خيارات الجودة"
    )

    INVALID_URL = "❌ <b>رابط غير صالح</b>\n\nالرجاء إرسال رابط صحيح من المنصات المدعومة."
    UNSUPPORTED_PLATFORM = "⚠️ <b>منصة غير مدعومة</b>\n\nهذه المنصة غير مدعومة حالياً. أرسل /help لرؤية المنصات المدعومة."
    PROCESSING = "⏳ <b>جارٍ المعالجة...</b>\n\nيرجى الانتظار قليلاً."
    DOWNLOADING = "📥 <b>جارٍ التحميل...</b>\n\n🔗 {platform}"
    UPLOADING = "📤 <b>جارٍ الرفع...</b>"
    SUCCESS = "✅ <b>تم التحميل بنجاح!</b>"
    ERROR_GENERAL = "❌ <b>حدث خطأ أثناء التحميل</b>\n\nحاول مرة أخرى لاحقاً أو تحقق من الرابط."
    ERROR_PRIVATE = "🔒 <b>المحتوى خاص</b>\n\nلا يمكن تحميل المحتوى الخاص."
    ERROR_SIZE = "📦 <b>الملف كبير جداً</b>\n\nحجم الملف يتجاوز الحد المسموح به (50MB)."
    ERROR_TIMEOUT = "⏱️ <b>انتهى وقت التحميل</b>\n\nحاول مرة أخرى لاحقاً."
    RATE_LIMIT = "⏳ <b>طلبات كثيرة</b>\n\nانتظر {seconds} ثانية قبل الطلب التالي."
    BANNED = "🚫 <b>تم حظرك</b>\n\nللتواصل مع الدعم: @support"
    BOT_BLOCKED = "🤖 لا يمكن إرسال رسالة إلى هذا المستخدم."
    FLOOD_WAIT = "⚠️ <b>تجاوزت الحد المسموح</b>\n\nانتظر {seconds} ثانية."

    # --- YouTube ---
    YT_ANALYSIS = "🔍 <b>جارٍ تحليل الفيديو...</b>"
    YT_CHOOSE_QUALITY = (
        "📹 <b>{title}</b>\n\n"
        "⏱️ المدة: {duration}\n"
        "👁️ المشاهدات: {views}\n\n"
        "اختر جودة التحميل:"
    )
    YT_DOWNLOADING = "📥 جارٍ تحميل الفيديو بجودة {quality}..."
    YT_AUDIO_DOWNLOADING = "🎵 جارٍ تحميل الصوت بجودة {quality}..."

    # --- Force Sub ---
    FORCE_SUB = (
        "📢 <b>يجب الاشتراك في قناتنا أولاً!</b>\n\n"
        "اشترك في القنوات التالية ثم اضغط ✅ تحقق:\n\n"
        "{channels}"
    )
    FORCE_SUB_SUCCESS = "✅ <b>تم التحقق بنجاح!</b>\n\nيمكنك الآن استخدام البوت."
    FORCE_SUB_FAILED = "❌ <b>لم تشترك بعد!</b>\n\nاشترك في جميع القنوات ثم اضغط تحقق مجدداً."

    # --- Admin ---
    ADMIN_ONLY = "🔐 هذا الأمر للمديرين فقط."
    STATS_TEMPLATE = (
        "📊 <b>إحصائيات البوت</b>\n\n"
        "👥 المستخدمون: <b>{users}</b>\n"
        "📥 التحميلات الكلية: <b>{downloads}</b>\n"
        "📥 تحميلات اليوم: <b>{today_downloads}</b>\n"
        "🏆 أكثر منصة: <b>{top_platform}</b>\n"
        "🚫 المحظورون: <b>{banned}</b>\n\n"
        "💾 <b>قاعدة البيانات:</b>\n"
        "• MongoDB: {mongo_status}\n"
        "• Redis: {redis_status}\n\n"
        "🤖 <b>حالة البوت:</b>\n"
        "• وقت التشغيل: {uptime}\n"
        "• الطلبات النشطة: {active_tasks}"
    )
    BROADCAST_START = "📨 جارٍ الإرسال الجماعي..."
    BROADCAST_DONE = "✅ اكتمل الإرسال: {success} نجح، {failed} فشل."
    BAN_SUCCESS = "🚫 تم حظر المستخدم {user_id}."
    UNBAN_SUCCESS = "✅ تم رفع الحظر عن المستخدم {user_id}."
    USER_NOT_FOUND = "❌ المستخدم غير موجود في قاعدة البيانات."
    FORCE_SUB_SET = "✅ تم إضافة القناة {channel} إلى قائمة الاشتراك الإجباري."
    FORCE_SUB_REMOVED = "✅ تم إزالة القناة {channel} من قائمة الاشتراك الإجباري."
    FORCE_SUB_LIST = "📋 <b>قنوات الاشتراك الإجباري:</b>\n\n{channels}"
    FORCE_SUB_EMPTY = "📋 لا توجد قنوات اشتراك إجباري مُضافة."
    FORCE_SUB_ENABLED = (
        "✅ <b>تم تفعيل الاشتراك الإجباري</b>\n\n"
        "سيُطلب من المستخدمين الاشتراك في القنوات قبل استخدام البوت."
    )
    FORCE_SUB_DISABLED = (
        "🔴 <b>تم تعطيل الاشتراك الإجباري</b>\n\n"
        "يمكن لجميع المستخدمين استخدام البوت الآن بدون اشتراك."
    )
    FORCE_SUB_STATUS_ON = "✅ مفعّل"
    FORCE_SUB_STATUS_OFF = "🔴 معطّل"
    FORCE_SUB_STATUS = (
        "📋 <b>حالة الاشتراك الإجباري:</b> {status}\n\n"
        "<b>القنوات المُضافة:</b>\n{channels}"
    )

    # --- SoundCloud ---
    SC_INFO = (
        "🎧 <b>{title}</b>\n"
        "👤 الفنان: {artist}\n"
        "⏱️ المدة: {duration}\n"
        "💿 جارٍ التحميل..."
    )

    # --- Instagram ---
    IG_CAROUSEL = "📸 <b>Carousel</b> – جارٍ تحميل {count} وسائط..."

    # --- Platform names ---
    PLATFORM_NAMES = {
        "instagram": "Instagram 📷",
        "tiktok": "TikTok 🎵",
        "youtube": "YouTube ▶️",
        "twitter": "X (Twitter) 🐦",
        "soundcloud": "SoundCloud 🎧",
        "pinterest": "Pinterest 📌",
    }
