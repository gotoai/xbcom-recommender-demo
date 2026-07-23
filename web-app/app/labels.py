"""Localised labels for coupon **taxonomy** — category and subcategory names — in
the user-mode reco screen's display language.

These are keyed by the canonical **English** label (``category_en`` /
``subcategory_en`` from the primary TSVs), which is what the rest of the app filters
on. The English string is also the fallback: ``label(lang, en)`` returns the
translation when present, otherwise the English label unchanged — so a language with
no (or partial) coverage degrades gracefully to English rather than breaking.

Filtering always uses the English canonical value; only the *displayed* text is
translated (see ``main._coupon_list_ctx``).

NOTE: machine-authored translations — have a native speaker review before production.
"""
from __future__ import annotations

# category_en -> {lang: native label}. English is the fallback (not stored here).
CATEGORY_LABELS: dict[str, dict[str, str]] = {
    "ko": {
        "Bar": "바", "Karaoke": "노래방", "Convenience Store": "편의점",
        "Music, Video & Games": "음악·영상·게임", "Car Rental": "렌터카",
        "Clothing Store": "의류점", "Sweets Shop": "디저트 가게",
        "Coffee Shop": "커피숍", "Beauty Salon": "미용실", "Restaurant": "레스토랑",
        "Discount Store": "할인점", "Massage": "마사지", "Luggage Storage": "짐 보관",
        "Gym & Pool": "헬스장·수영장", "Bookstore": "서점", "Drugstore": "드러그스토어",
        "Fast Food": "패스트푸드", "Spa": "스파", "Electronics Store": "전자제품점",
        "Cinema": "영화관",
    },
    "zh-Hans": {
        "Bar": "酒吧", "Karaoke": "卡拉OK", "Convenience Store": "便利店",
        "Music, Video & Games": "音乐·影像·游戏", "Car Rental": "租车",
        "Clothing Store": "服装店", "Sweets Shop": "甜品店", "Coffee Shop": "咖啡店",
        "Beauty Salon": "美容院", "Restaurant": "餐厅", "Discount Store": "折扣店",
        "Massage": "按摩", "Luggage Storage": "行李寄存", "Gym & Pool": "健身房·泳池",
        "Bookstore": "书店", "Drugstore": "药妆店", "Fast Food": "快餐", "Spa": "水疗",
        "Electronics Store": "电器店", "Cinema": "电影院",
    },
    "zh-Hant": {
        "Bar": "酒吧", "Karaoke": "卡拉OK", "Convenience Store": "便利商店",
        "Music, Video & Games": "音樂·影像·遊戲", "Car Rental": "租車",
        "Clothing Store": "服飾店", "Sweets Shop": "甜點店", "Coffee Shop": "咖啡店",
        "Beauty Salon": "美容院", "Restaurant": "餐廳", "Discount Store": "折扣店",
        "Massage": "按摩", "Luggage Storage": "行李寄放", "Gym & Pool": "健身房·泳池",
        "Bookstore": "書店", "Drugstore": "藥妝店", "Fast Food": "速食", "Spa": "水療",
        "Electronics Store": "電器行", "Cinema": "電影院",
    },
    "th": {
        "Bar": "บาร์", "Karaoke": "คาราโอเกะ", "Convenience Store": "ร้านสะดวกซื้อ",
        "Music, Video & Games": "เพลง วิดีโอ และเกม", "Car Rental": "เช่ารถ",
        "Clothing Store": "ร้านเสื้อผ้า", "Sweets Shop": "ร้านขนมหวาน",
        "Coffee Shop": "ร้านกาแฟ", "Beauty Salon": "ร้านเสริมสวย",
        "Restaurant": "ร้านอาหาร", "Discount Store": "ร้านลดราคา", "Massage": "นวด",
        "Luggage Storage": "รับฝากสัมภาระ", "Gym & Pool": "ฟิตเนสและสระว่ายน้ำ",
        "Bookstore": "ร้านหนังสือ", "Drugstore": "ร้านขายยาและเครื่องสำอาง",
        "Fast Food": "ฟาสต์ฟู้ด", "Spa": "สปา",
        "Electronics Store": "ร้านเครื่องใช้ไฟฟ้า", "Cinema": "โรงภาพยนตร์",
    },
    "vi": {
        "Bar": "Quán bar", "Karaoke": "Karaoke", "Convenience Store": "Cửa hàng tiện lợi",
        "Music, Video & Games": "Nhạc, video & trò chơi", "Car Rental": "Thuê xe",
        "Clothing Store": "Cửa hàng quần áo", "Sweets Shop": "Tiệm đồ ngọt",
        "Coffee Shop": "Quán cà phê", "Beauty Salon": "Thẩm mỹ viện",
        "Restaurant": "Nhà hàng", "Discount Store": "Cửa hàng giảm giá",
        "Massage": "Mát-xa", "Luggage Storage": "Giữ hành lý",
        "Gym & Pool": "Phòng gym & hồ bơi", "Bookstore": "Nhà sách",
        "Drugstore": "Hiệu thuốc", "Fast Food": "Đồ ăn nhanh", "Spa": "Spa",
        "Electronics Store": "Cửa hàng điện tử", "Cinema": "Rạp chiếu phim",
    },
    "fil": {
        "Bar": "Bar", "Karaoke": "Karaoke", "Convenience Store": "Convenience Store",
        "Music, Video & Games": "Musika, Video at Laro",
        "Car Rental": "Rentahan ng Sasakyan", "Clothing Store": "Tindahan ng Damit",
        "Sweets Shop": "Tindahan ng Matamis", "Coffee Shop": "Coffee Shop",
        "Beauty Salon": "Beauty Salon", "Restaurant": "Restawran",
        "Discount Store": "Discount Store", "Massage": "Masahe",
        "Luggage Storage": "Imbakan ng Bagahe", "Gym & Pool": "Gym at Pool",
        "Bookstore": "Tindahan ng Libro", "Drugstore": "Botika",
        "Fast Food": "Fast Food", "Spa": "Spa",
        "Electronics Store": "Tindahan ng Electronics", "Cinema": "Sinehan",
    },
    "hi": {
        "Bar": "बार", "Karaoke": "कराओके", "Convenience Store": "सुविधा स्टोर",
        "Music, Video & Games": "संगीत, वीडियो और गेम", "Car Rental": "कार किराया",
        "Clothing Store": "कपड़ों की दुकान", "Sweets Shop": "मिठाई की दुकान",
        "Coffee Shop": "कॉफ़ी शॉप", "Beauty Salon": "ब्यूटी सैलून",
        "Restaurant": "रेस्तराँ", "Discount Store": "डिस्काउंट स्टोर", "Massage": "मालिश",
        "Luggage Storage": "सामान रखने की सेवा", "Gym & Pool": "जिम और पूल",
        "Bookstore": "किताबों की दुकान", "Drugstore": "दवा की दुकान",
        "Fast Food": "फ़ास्ट फ़ूड", "Spa": "स्पा",
        "Electronics Store": "इलेक्ट्रॉनिक्स स्टोर", "Cinema": "सिनेमा",
    },
    "es": {
        "Bar": "Bar", "Karaoke": "Karaoke", "Convenience Store": "Tienda de conveniencia",
        "Music, Video & Games": "Música, vídeo y juegos",
        "Car Rental": "Alquiler de coches", "Clothing Store": "Tienda de ropa",
        "Sweets Shop": "Dulcería", "Coffee Shop": "Cafetería",
        "Beauty Salon": "Salón de belleza", "Restaurant": "Restaurante",
        "Discount Store": "Tienda de descuentos", "Massage": "Masaje",
        "Luggage Storage": "Consigna de equipaje", "Gym & Pool": "Gimnasio y piscina",
        "Bookstore": "Librería", "Drugstore": "Farmacia y droguería",
        "Fast Food": "Comida rápida", "Spa": "Spa",
        "Electronics Store": "Tienda de electrónica", "Cinema": "Cine",
    },
    "pt": {
        "Bar": "Bar", "Karaoke": "Karaokê", "Convenience Store": "Loja de conveniência",
        "Music, Video & Games": "Música, vídeo e jogos",
        "Car Rental": "Aluguel de carros", "Clothing Store": "Loja de roupas",
        "Sweets Shop": "Doceria", "Coffee Shop": "Cafeteria",
        "Beauty Salon": "Salão de beleza", "Restaurant": "Restaurante",
        "Discount Store": "Loja de descontos", "Massage": "Massagem",
        "Luggage Storage": "Guarda-volumes", "Gym & Pool": "Academia e piscina",
        "Bookstore": "Livraria", "Drugstore": "Farmácia e drogaria",
        "Fast Food": "Fast food", "Spa": "Spa",
        "Electronics Store": "Loja de eletrônicos", "Cinema": "Cinema",
    },
    "fr": {
        "Bar": "Bar", "Karaoke": "Karaoké", "Convenience Store": "Supérette",
        "Music, Video & Games": "Musique, vidéo et jeux",
        "Car Rental": "Location de voitures", "Clothing Store": "Magasin de vêtements",
        "Sweets Shop": "Confiserie", "Coffee Shop": "Café",
        "Beauty Salon": "Salon de beauté", "Restaurant": "Restaurant",
        "Discount Store": "Magasin discount", "Massage": "Massage",
        "Luggage Storage": "Consigne à bagages", "Gym & Pool": "Salle de sport et piscine",
        "Bookstore": "Librairie", "Drugstore": "Pharmacie et parapharmacie",
        "Fast Food": "Restauration rapide", "Spa": "Spa",
        "Electronics Store": "Magasin d'électronique", "Cinema": "Cinéma",
    },
    "de": {
        "Bar": "Bar", "Karaoke": "Karaoke", "Convenience Store": "Convenience-Store",
        "Music, Video & Games": "Musik, Video & Games", "Car Rental": "Autovermietung",
        "Clothing Store": "Bekleidungsgeschäft", "Sweets Shop": "Süßwarenladen",
        "Coffee Shop": "Café", "Beauty Salon": "Schönheitssalon",
        "Restaurant": "Restaurant", "Discount Store": "Discounter", "Massage": "Massage",
        "Luggage Storage": "Gepäckaufbewahrung", "Gym & Pool": "Fitnessstudio & Pool",
        "Bookstore": "Buchhandlung", "Drugstore": "Drogerie", "Fast Food": "Fast Food",
        "Spa": "Spa", "Electronics Store": "Elektronikmarkt", "Cinema": "Kino",
    },
    "it": {
        "Bar": "Bar", "Karaoke": "Karaoke", "Convenience Store": "Minimarket",
        "Music, Video & Games": "Musica, video e giochi", "Car Rental": "Autonoleggio",
        "Clothing Store": "Negozio di abbigliamento", "Sweets Shop": "Pasticceria",
        "Coffee Shop": "Caffetteria", "Beauty Salon": "Salone di bellezza",
        "Restaurant": "Ristorante", "Discount Store": "Discount", "Massage": "Massaggi",
        "Luggage Storage": "Deposito bagagli", "Gym & Pool": "Palestra e piscina",
        "Bookstore": "Libreria", "Drugstore": "Farmacia e drogheria",
        "Fast Food": "Fast food", "Spa": "Spa",
        "Electronics Store": "Negozio di elettronica", "Cinema": "Cinema",
    },
    "nl": {
        "Bar": "Bar", "Karaoke": "Karaoke", "Convenience Store": "Buurtwinkel",
        "Music, Video & Games": "Muziek, video & games", "Car Rental": "Autoverhuur",
        "Clothing Store": "Kledingwinkel", "Sweets Shop": "Snoepwinkel",
        "Coffee Shop": "Koffiebar", "Beauty Salon": "Schoonheidssalon",
        "Restaurant": "Restaurant", "Discount Store": "Discountwinkel",
        "Massage": "Massage", "Luggage Storage": "Bagageopslag",
        "Gym & Pool": "Sportschool & zwembad", "Bookstore": "Boekhandel",
        "Drugstore": "Drogisterij", "Fast Food": "Fastfood", "Spa": "Spa",
        "Electronics Store": "Elektronicawinkel", "Cinema": "Bioscoop",
    },
    "he": {
        "Bar": "בר", "Karaoke": "קריוקי", "Convenience Store": "חנות נוחות",
        "Music, Video & Games": "מוזיקה, וידאו ומשחקים", "Car Rental": "השכרת רכב",
        "Clothing Store": "חנות בגדים", "Sweets Shop": "חנות ממתקים",
        "Coffee Shop": "בית קפה", "Beauty Salon": "מכון יופי", "Restaurant": "מסעדה",
        "Discount Store": "חנות זול", "Massage": "עיסוי", "Luggage Storage": "שמירת מזוודות",
        "Gym & Pool": "חדר כושר ובריכה", "Bookstore": "חנות ספרים",
        "Drugstore": "בית מרקחת", "Fast Food": "מזון מהיר", "Spa": "ספא",
        "Electronics Store": "חנות אלקטרוניקה", "Cinema": "קולנוע",
    },
    "tr": {
        "Bar": "Bar", "Karaoke": "Karaoke", "Convenience Store": "Market",
        "Music, Video & Games": "Müzik, Video ve Oyun", "Car Rental": "Araç Kiralama",
        "Clothing Store": "Giyim Mağazası", "Sweets Shop": "Tatlıcı",
        "Coffee Shop": "Kahve Dükkânı", "Beauty Salon": "Güzellik Salonu",
        "Restaurant": "Restoran", "Discount Store": "İndirim Mağazası", "Massage": "Masaj",
        "Luggage Storage": "Emanet Bagaj", "Gym & Pool": "Spor Salonu ve Havuz",
        "Bookstore": "Kitapçı", "Drugstore": "Eczane ve Kozmetik", "Fast Food": "Fast Food",
        "Spa": "Spa", "Electronics Store": "Elektronik Mağazası", "Cinema": "Sinema",
    },
}

# subcategory_en -> {lang: native label}, fully populated across all 16 supported
# languages (English is the fallback). The large table lives in its own module.
from .labels_subcategory import SUBCATEGORY_LABELS  # noqa: E402


def category_label(lang: str, category_en: str) -> str:
    """Translated category name for ``lang``; the English label if untranslated."""
    return CATEGORY_LABELS.get(lang, {}).get(category_en, category_en)


def subcategory_label(lang: str, subcategory_en: str) -> str:
    """Translated subcategory name for ``lang``; the English label if untranslated."""
    return SUBCATEGORY_LABELS.get(lang, {}).get(subcategory_en, subcategory_en)
