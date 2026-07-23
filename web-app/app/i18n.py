"""UI localisation for the user-mode reco screen.

The entry page (operator view) stays Japanese. The user-mode reco screen mimics
what a *specific* traveler sees in their own app, so its **chrome** is rendered in
that traveler's own language — derived from their nationality via the
country→language table in ``docs/profiles/users.md``. Only the surrounding chrome
is translated; the coupon data itself (shop / product / category names, discount,
price) stays English, per the product brief.

Supported UI languages are a fixed set; any nationality whose language isn't in the
set falls back to English (``DEFAULT_LANG``).
"""
from __future__ import annotations

DEFAULT_LANG = "en"

# Nationality (Japanese label, as stored in inbound_traveler.tsv) -> UI language
# code. Languages outside the supported set (Malay, Indonesian, the Nordic
# languages, Arabic, …) intentionally map to English via ``lang_for_nationality``.
NATIONALITY_LANG = {
    "韓国": "ko",
    "中国": "zh-Hans",
    "台湾": "zh-Hant",
    "香港": "zh-Hant",
    "タイ": "th",
    "シンガポール": "en",
    "マレーシア": "en",       # Malay — not in the supported set
    "インドネシア": "en",     # Indonesian — not in the supported set
    "フィリピン": "fil",
    "ベトナム": "vi",
    "インド": "hi",
    "豪州": "en",
    "ニュージーランド": "en",
    "米国": "en",
    "カナダ": "en",
    "メキシコ": "es",
    "ブラジル": "pt",
    "英国": "en",
    "フランス": "fr",
    "ドイツ": "de",
    "イタリア": "it",
    "スペイン": "es",
    "オランダ": "nl",
    "ベルギー": "nl",
    "スイス": "de",
    "スウェーデン": "en",     # Swedish — not in the supported set
    "デンマーク": "en",       # Danish — not in the supported set
    "ノルウェー": "en",       # Norwegian — not in the supported set
    "フィンランド": "en",     # Finnish — not in the supported set
    "イスラエル": "he",
    "トルコ": "tr",
    "サウジアラビア": "en",   # Arabic — not in the supported set
    "アラブ首長国連邦": "en",
    "バーレーン": "en",
    "オマーン": "en",
    "カタール": "en",
    "クウェート": "en",
}

# Languages written right-to-left (the reco container gets dir="rtl").
RTL_LANGS = {"he"}

# Chrome strings for the user-mode reco screen. Keys are shared across languages;
# ``en`` is the fallback for any missing key. Coupon data is never translated here.
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "back": "Back",
        "traveler": "Traveler",
        "you_are_here": "You are here",
        "coupons": "Coupons",
        "within_radius": "within 5 km",
        "map_shows_nearest": "map shows nearest",
        "no_coupons": "No active coupons within 5 km of your current location.",
        "concierge": "Concierge",
        "coming_soon": "Coming soon",
        "chat_hint": "Ask me anything about these coupons (coming soon).",
        "chat_placeholder": "Type a message… (coming soon)",
        "send": "Send",
        "prev": "Prev",
        "next": "Next",
        "category": "Category",
        "subcategory": "Subcategory",
        "all": "All",
        "loc_unavailable": "Your current location is unavailable.",
    },
    "ko": {
        "back": "뒤로",
        "traveler": "여행자",
        "you_are_here": "현재 위치",
        "coupons": "쿠폰",
        "within_radius": "5km 이내",
        "map_shows_nearest": "지도에는 가까운 순으로 표시",
        "no_coupons": "현재 위치에서 5km 이내에 사용 가능한 쿠폰이 없습니다.",
        "concierge": "컨시어지",
        "coming_soon": "준비 중",
        "chat_hint": "이 쿠폰에 대해 무엇이든 물어보세요 (준비 중).",
        "chat_placeholder": "메시지를 입력하세요… (준비 중)",
        "send": "보내기",
        "prev": "이전",
        "next": "다음",
        "category": "카테고리",
        "subcategory": "서브카테고리",
        "all": "전체",
        "loc_unavailable": "현재 위치를 사용할 수 없습니다.",
    },
    "zh-Hans": {
        "back": "返回",
        "traveler": "旅客",
        "you_are_here": "您的位置",
        "coupons": "优惠券",
        "within_radius": "5 公里内",
        "map_shows_nearest": "地图显示最近的",
        "no_coupons": "您当前位置 5 公里内没有可用的优惠券。",
        "concierge": "礼宾助手",
        "coming_soon": "敬请期待",
        "chat_hint": "关于这些优惠券，尽管问我（敬请期待）。",
        "chat_placeholder": "输入消息…（敬请期待）",
        "send": "发送",
        "prev": "上一页",
        "next": "下一页",
        "category": "类别",
        "subcategory": "子类别",
        "all": "全部",
        "loc_unavailable": "无法获取您的当前位置。",
    },
    "zh-Hant": {
        "back": "返回",
        "traveler": "旅客",
        "you_are_here": "您的位置",
        "coupons": "優惠券",
        "within_radius": "5 公里內",
        "map_shows_nearest": "地圖顯示最近的",
        "no_coupons": "您目前位置 5 公里內沒有可用的優惠券。",
        "concierge": "禮賓助手",
        "coming_soon": "敬請期待",
        "chat_hint": "關於這些優惠券，儘管問我（敬請期待）。",
        "chat_placeholder": "輸入訊息…（敬請期待）",
        "send": "傳送",
        "prev": "上一頁",
        "next": "下一頁",
        "category": "類別",
        "subcategory": "子類別",
        "all": "全部",
        "loc_unavailable": "無法取得您目前的位置。",
    },
    "th": {
        "back": "กลับ",
        "traveler": "นักท่องเที่ยว",
        "you_are_here": "ตำแหน่งของคุณ",
        "coupons": "คูปอง",
        "within_radius": "ภายใน 5 กม.",
        "map_shows_nearest": "แผนที่แสดงที่ใกล้ที่สุด",
        "no_coupons": "ไม่มีคูปองที่ใช้ได้ภายใน 5 กม. จากตำแหน่งปัจจุบันของคุณ",
        "concierge": "ผู้ช่วยส่วนตัว",
        "coming_soon": "เร็ว ๆ นี้",
        "chat_hint": "ถามฉันได้ทุกอย่างเกี่ยวกับคูปองเหล่านี้ (เร็ว ๆ นี้)",
        "chat_placeholder": "พิมพ์ข้อความ… (เร็ว ๆ นี้)",
        "send": "ส่ง",
        "prev": "ก่อนหน้า",
        "next": "ถัดไป",
        "category": "หมวดหมู่",
        "subcategory": "หมวดหมู่ย่อย",
        "all": "ทั้งหมด",
        "loc_unavailable": "ไม่สามารถระบุตำแหน่งปัจจุบันของคุณได้",
    },
    "vi": {
        "back": "Quay lại",
        "traveler": "Du khách",
        "you_are_here": "Vị trí của bạn",
        "coupons": "Phiếu giảm giá",
        "within_radius": "trong vòng 5 km",
        "map_shows_nearest": "bản đồ hiển thị gần nhất",
        "no_coupons": "Không có phiếu giảm giá nào khả dụng trong vòng 5 km từ vị trí hiện tại của bạn.",
        "concierge": "Trợ lý",
        "coming_soon": "Sắp ra mắt",
        "chat_hint": "Hỏi tôi bất cứ điều gì về các phiếu giảm giá này (sắp ra mắt).",
        "chat_placeholder": "Nhập tin nhắn… (sắp ra mắt)",
        "send": "Gửi",
        "prev": "Trước",
        "next": "Tiếp",
        "category": "Danh mục",
        "subcategory": "Danh mục con",
        "all": "Tất cả",
        "loc_unavailable": "Không thể xác định vị trí hiện tại của bạn.",
    },
    "fil": {
        "back": "Bumalik",
        "traveler": "Manlalakbay",
        "you_are_here": "Nandito ka",
        "coupons": "Mga kupon",
        "within_radius": "sa loob ng 5 km",
        "map_shows_nearest": "ipinapakita sa mapa ang pinakamalapit",
        "no_coupons": "Walang aktibong kupon sa loob ng 5 km mula sa iyong kasalukuyang lokasyon.",
        "concierge": "Concierge",
        "coming_soon": "Malapit na",
        "chat_hint": "Magtanong sa akin tungkol sa mga kupon na ito (malapit na).",
        "chat_placeholder": "Mag-type ng mensahe… (malapit na)",
        "send": "Ipadala",
        "prev": "Nakaraan",
        "next": "Susunod",
        "category": "Kategorya",
        "subcategory": "Subkategorya",
        "all": "Lahat",
        "loc_unavailable": "Hindi available ang iyong kasalukuyang lokasyon.",
    },
    "hi": {
        "back": "वापस",
        "traveler": "यात्री",
        "you_are_here": "आप यहाँ हैं",
        "coupons": "कूपन",
        "within_radius": "5 किमी के भीतर",
        "map_shows_nearest": "मानचित्र निकटतम दिखाता है",
        "no_coupons": "आपके वर्तमान स्थान से 5 किमी के भीतर कोई सक्रिय कूपन नहीं है।",
        "concierge": "कंसीयज",
        "coming_soon": "जल्द आ रहा है",
        "chat_hint": "इन कूपनों के बारे में मुझसे कुछ भी पूछें (जल्द आ रहा है)।",
        "chat_placeholder": "संदेश लिखें… (जल्द आ रहा है)",
        "send": "भेजें",
        "prev": "पिछला",
        "next": "अगला",
        "category": "श्रेणी",
        "subcategory": "उपश्रेणी",
        "all": "सभी",
        "loc_unavailable": "आपका वर्तमान स्थान उपलब्ध नहीं है।",
    },
    "es": {
        "back": "Atrás",
        "traveler": "Viajero",
        "you_are_here": "Estás aquí",
        "coupons": "Cupones",
        "within_radius": "a menos de 5 km",
        "map_shows_nearest": "el mapa muestra los más cercanos",
        "no_coupons": "No hay cupones activos a menos de 5 km de tu ubicación actual.",
        "concierge": "Conserje",
        "coming_soon": "Próximamente",
        "chat_hint": "Pregúntame lo que quieras sobre estos cupones (próximamente).",
        "chat_placeholder": "Escribe un mensaje… (próximamente)",
        "send": "Enviar",
        "prev": "Anterior",
        "next": "Siguiente",
        "category": "Categoría",
        "subcategory": "Subcategoría",
        "all": "Todas",
        "loc_unavailable": "Tu ubicación actual no está disponible.",
    },
    "pt": {
        "back": "Voltar",
        "traveler": "Viajante",
        "you_are_here": "Você está aqui",
        "coupons": "Cupons",
        "within_radius": "a menos de 5 km",
        "map_shows_nearest": "o mapa mostra os mais próximos",
        "no_coupons": "Não há cupons ativos a menos de 5 km da sua localização atual.",
        "concierge": "Concierge",
        "coming_soon": "Em breve",
        "chat_hint": "Pergunte-me qualquer coisa sobre estes cupons (em breve).",
        "chat_placeholder": "Digite uma mensagem… (em breve)",
        "send": "Enviar",
        "prev": "Anterior",
        "next": "Próximo",
        "category": "Categoria",
        "subcategory": "Subcategoria",
        "all": "Todos",
        "loc_unavailable": "Sua localização atual não está disponível.",
    },
    "fr": {
        "back": "Retour",
        "traveler": "Voyageur",
        "you_are_here": "Vous êtes ici",
        "coupons": "Coupons",
        "within_radius": "à moins de 5 km",
        "map_shows_nearest": "la carte affiche les plus proches",
        "no_coupons": "Aucun coupon actif à moins de 5 km de votre position actuelle.",
        "concierge": "Conciergerie",
        "coming_soon": "Bientôt disponible",
        "chat_hint": "Posez-moi vos questions sur ces coupons (bientôt disponible).",
        "chat_placeholder": "Écrivez un message… (bientôt disponible)",
        "send": "Envoyer",
        "prev": "Précédent",
        "next": "Suivant",
        "category": "Catégorie",
        "subcategory": "Sous-catégorie",
        "all": "Toutes",
        "loc_unavailable": "Votre position actuelle n'est pas disponible.",
    },
    "de": {
        "back": "Zurück",
        "traveler": "Reisender",
        "you_are_here": "Sie sind hier",
        "coupons": "Gutscheine",
        "within_radius": "innerhalb von 5 km",
        "map_shows_nearest": "Karte zeigt die nächsten",
        "no_coupons": "Keine aktiven Gutscheine innerhalb von 5 km von Ihrem aktuellen Standort.",
        "concierge": "Concierge",
        "coming_soon": "Demnächst",
        "chat_hint": "Fragen Sie mich alles zu diesen Gutscheinen (demnächst).",
        "chat_placeholder": "Nachricht eingeben… (demnächst)",
        "send": "Senden",
        "prev": "Vorherige",
        "next": "Weiter",
        "category": "Kategorie",
        "subcategory": "Unterkategorie",
        "all": "Alle",
        "loc_unavailable": "Ihr aktueller Standort ist nicht verfügbar.",
    },
    "it": {
        "back": "Indietro",
        "traveler": "Viaggiatore",
        "you_are_here": "Sei qui",
        "coupons": "Coupon",
        "within_radius": "entro 5 km",
        "map_shows_nearest": "la mappa mostra i più vicini",
        "no_coupons": "Nessun coupon attivo entro 5 km dalla tua posizione attuale.",
        "concierge": "Concierge",
        "coming_soon": "Prossimamente",
        "chat_hint": "Chiedimi qualsiasi cosa su questi coupon (prossimamente).",
        "chat_placeholder": "Scrivi un messaggio… (prossimamente)",
        "send": "Invia",
        "prev": "Precedente",
        "next": "Successivo",
        "category": "Categoria",
        "subcategory": "Sottocategoria",
        "all": "Tutti",
        "loc_unavailable": "La tua posizione attuale non è disponibile.",
    },
    "nl": {
        "back": "Terug",
        "traveler": "Reiziger",
        "you_are_here": "U bent hier",
        "coupons": "Coupons",
        "within_radius": "binnen 5 km",
        "map_shows_nearest": "kaart toont dichtstbijzijnde",
        "no_coupons": "Geen actieve coupons binnen 5 km van uw huidige locatie.",
        "concierge": "Concierge",
        "coming_soon": "Binnenkort",
        "chat_hint": "Vraag me alles over deze coupons (binnenkort).",
        "chat_placeholder": "Typ een bericht… (binnenkort)",
        "send": "Verzenden",
        "prev": "Vorige",
        "next": "Volgende",
        "category": "Categorie",
        "subcategory": "Subcategorie",
        "all": "Alle",
        "loc_unavailable": "Uw huidige locatie is niet beschikbaar.",
    },
    "he": {
        "back": "חזרה",
        "traveler": "מטייל",
        "you_are_here": "אתה כאן",
        "coupons": "קופונים",
        "within_radius": "בטווח 5 ק\"מ",
        "map_shows_nearest": "המפה מציגה את הקרובים ביותר",
        "no_coupons": "אין קופונים פעילים בטווח 5 ק\"מ ממיקומך הנוכחי.",
        "concierge": "קונסיירז'",
        "coming_soon": "בקרוב",
        "chat_hint": "שאל אותי כל דבר על הקופונים האלה (בקרוב).",
        "chat_placeholder": "הקלד הודעה… (בקרוב)",
        "send": "שלח",
        "prev": "הקודם",
        "next": "הבא",
        "category": "קטגוריה",
        "subcategory": "תת-קטגוריה",
        "all": "הכול",
        "loc_unavailable": "המיקום הנוכחי שלך אינו זמין.",
    },
    "tr": {
        "back": "Geri",
        "traveler": "Gezgin",
        "you_are_here": "Buradasınız",
        "coupons": "Kuponlar",
        "within_radius": "5 km içinde",
        "map_shows_nearest": "harita en yakınları gösterir",
        "no_coupons": "Mevcut konumunuzun 5 km yakınında aktif kupon yok.",
        "concierge": "Konsiyerj",
        "coming_soon": "Yakında",
        "chat_hint": "Bu kuponlar hakkında bana her şeyi sorun (yakında).",
        "chat_placeholder": "Bir mesaj yazın… (yakında)",
        "send": "Gönder",
        "prev": "Önceki",
        "next": "Sonraki",
        "category": "Kategori",
        "subcategory": "Alt kategori",
        "all": "Tümü",
        "loc_unavailable": "Mevcut konumunuz kullanılamıyor.",
    },
}


# Singular "Coupon" (map legend) per language, and the word "Language" (only the
# English key is needed — ``translations`` back-fills the rest from English, and the
# language dropdown itself shows each language in its own name).
_COUPON_SINGULAR = {
    "en": "Coupon", "ko": "쿠폰", "zh-Hans": "优惠券", "zh-Hant": "優惠券",
    "th": "คูปอง", "vi": "Phiếu giảm giá", "fil": "Kupon", "hi": "कूपन",
    "es": "Cupón", "pt": "Cupom", "fr": "Coupon", "de": "Gutschein",
    "it": "Coupon", "nl": "Coupon", "he": "קופון", "tr": "Kupon",
}
for _lang, _word in _COUPON_SINGULAR.items():
    TRANSLATIONS.setdefault(_lang, {})["coupon"] = _word
TRANSLATIONS["en"]["language"] = "Language"

# Language dropdown: (code, endonym) in menu order. Codes must be TRANSLATIONS keys.
LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ("en", "English"), ("ko", "한국어"), ("zh-Hans", "简体中文"),
    ("zh-Hant", "繁體中文"), ("th", "ภาษาไทย"), ("vi", "Tiếng Việt"),
    ("fil", "Filipino"), ("hi", "हिन्दी"), ("es", "Español"), ("pt", "Português"),
    ("fr", "Français"), ("de", "Deutsch"), ("it", "Italiano"), ("nl", "Nederlands"),
    ("he", "עברית"), ("tr", "Türkçe"),
]
SUPPORTED = {code for code, _ in LANGUAGE_OPTIONS}


def lang_for_nationality(nationality: str) -> str:
    """UI language code for a traveler's nationality; English for unsupported ones."""
    return NATIONALITY_LANG.get(nationality, DEFAULT_LANG)


def resolve_lang(requested: str | None, default: str) -> str:
    """A user-requested language override if it's supported, else ``default``."""
    return requested if requested in SUPPORTED else default


def translations(lang: str) -> dict[str, str]:
    """The chrome-string map for ``lang``, English-filled for any missing key."""
    base = dict(TRANSLATIONS[DEFAULT_LANG])
    base.update(TRANSLATIONS.get(lang, {}))
    return base


def direction(lang: str) -> str:
    """'rtl' for right-to-left languages, otherwise 'ltr'."""
    return "rtl" if lang in RTL_LANGS else "ltr"
