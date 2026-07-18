"""English product descriptions for the synthetic product table.

Supplies the ``description_en`` column written by ``synthesize_products.py`` — a
short, traveler-facing blurb highlighting each product's appeal.

Design mirrors ``synthesize-shops/scripts/shop_i18n.py``: static data + pure
functions, so synthesis stays reproducible with no extra dependency. The other
three English columns product.tsv gains (``shop_name_en``, ``category_en``,
``subcategory_en``) are copied straight from shop.tsv and need nothing here.

A description is one ``DESC_TEMPLATE`` sentence for the (category, subcategory),
with ``{name}`` filled by the product's own English name (which already carries
the specific item + modifier, e.g. "Veggie-Loaded Shoyu Ramen"), followed by one
traveler perk drawn from the category's ``_PERKS`` group. So two products in the
same sub-category read differently because their names differ.
"""
from __future__ import annotations

# (category, subcategory) -> sentence with a {name} slot for the EN product name.
DESC_TEMPLATE: dict[tuple[str, str], str] = {
    ("レストラン", "寿司・海鮮"): "Our {name} features fresh fish and seafood prepared by skilled chefs.",
    ("レストラン", "ラーメン"): "Our {name} is a rich, steaming bowl of authentic Japanese ramen.",
    ("レストラン", "焼肉・ホルモン"): "Grill our {name} of premium beef right at your table.",
    ("レストラン", "天ぷら・とんかつ"): "Our {name} is fried crisp and golden and served with rice.",
    ("レストラン", "そば・うどん"): "Our {name} brings handmade noodles in a savory broth.",
    ("レストラン", "お好み焼き・もんじゃ焼き"): "Cook our {name} on the griddle right at your table.",
    ("レストラン", "イタリア料理"): "Our {name} offers Japanese-Italian flavors made fresh.",
    ("レストラン", "インド料理"): "Our {name} is full of aromatic Indian spices.",
    ("レストラン", "韓国料理"): "Our {name} delivers bold, spicy Korean flavors.",
    ("レストラン", "中華料理"): "Our {name} is a hearty Chinese favorite made to order.",

    ("ファストフード", "ハンバーガー"): "Our {name} is a juicy burger made fast for you.",
    ("ファストフード", "牛丼"): "Our {name} is a warm beef bowl served in minutes.",
    ("ファストフード", "カレー"): "Our {name} is comforting Japanese curry over rice.",
    ("ファストフード", "立ち食いそば"): "Our {name} is quick standing-counter soba, ready in a flash.",
    ("ファストフード", "フライドチキン"): "Our {name} is crispy fried chicken to grab and go.",
    ("ファストフード", "サンドイッチ・ベーカリー"): "Our {name} is freshly baked and ready to enjoy.",

    ("コーヒーショップ", "チェーンカフェ"): "Enjoy our {name} with free Wi-Fi and a comfy seat.",
    ("コーヒーショップ", "自家焙煎コーヒー"): "Our {name} is brewed from beans roasted in-house.",
    ("コーヒーショップ", "純喫茶"): "Our {name} carries the charm of an old-school Showa kissaten.",
    ("コーヒーショップ", "タピオカ・ドリンクスタンド"): "Our {name} is a refreshing drink made to order.",
    ("コーヒーショップ", "テーマカフェ（アニメ・動物）"): "Our {name} comes with fun, photo-worthy theme-cafe vibes.",

    ("スイーツショップ", "和菓子"): "Our {name} is a delicate traditional Japanese sweet, beautifully made.",
    ("スイーツショップ", "洋菓子・ケーキ"): "Our {name} is an elegant Western-style treat.",
    ("スイーツショップ", "クレープ・パンケーキ"): "Our {name} is fluffy, sweet, and freshly made.",
    ("スイーツショップ", "ソフトクリーム・アイス"): "Our {name} is creamy and comes in seasonal flavors.",
    ("スイーツショップ", "チョコレート専門店"): "Our {name} is crafted from fine artisan chocolate.",
    ("スイーツショップ", "たい焼き・どら焼き"): "Our {name} is a warm, filled Japanese sweet.",

    ("バー", "居酒屋"): "Our {name} pairs perfectly with a lively izakaya night.",
    ("バー", "立ち飲み屋"): "Our {name} is a casual standing-bar pick at a friendly price.",
    ("バー", "日本酒バー"): "Our {name} lets you savor regional sake from across Japan.",
    ("バー", "クラフトビール・ビアバー"): "Our {name} features local craft beer on tap.",
    ("バー", "ウイスキー・カクテルバー"): "Our {name} is expertly poured by our bartender.",
    ("バー", "ワインバー"): "Our {name} is a carefully selected pour to enjoy.",
    ("バー", "スポーツバー"): "Our {name} is the perfect companion while you watch the game.",

    ("ドラッグストア", "医薬品・常備薬"): "Our {name} covers everyday health and travel needs.",
    ("ドラッグストア", "化粧品・スキンケア"): "Our {name} is a popular Japanese beauty pick.",
    ("ドラッグストア", "ヘアケア・ボディケア"): "Our {name} keeps hair and skin fresh and cared for.",
    ("ドラッグストア", "サプリメント・健康食品"): "Our {name} supports your daily wellness.",
    ("ドラッグストア", "ベビー用品"): "Our {name} is a gentle, trusted baby-care essential.",
    ("ドラッグストア", "日用品・雑貨"): "Our {name} covers handy daily necessities.",

    ("ディスカウントストア", "総合ディスカウント"): "Our {name} bundles great value into one buy.",
    ("ディスカウントストア", "100円ショップ"): "Our {name} is handy and easy on the wallet.",
    ("ディスカウントストア", "免税専門店"): "Our {name} is offered tax-free for travelers.",
    ("ディスカウントストア", "アウトレット"): "Our {name} is a brand-name find at outlet prices.",
    ("ディスカウントストア", "生活雑貨"): "Our {name} adds affordable style to daily life.",

    ("美容院", "カット・カラー"): "Our {name} gives you a fresh style by skilled stylists.",
    ("美容院", "ヘッドスパ"): "Our {name} soothes your scalp and melts away stress.",
    ("美容院", "ネイルサロン"): "Our {name} finishes your nails with custom care.",
    ("美容院", "まつげエクステ"): "Our {name} gives you natural, fuller lashes.",
    ("美容院", "着付け・ヘアセット"): "Our {name} gets you dressed beautifully for a special day.",

    ("マッサージ店", "整体・カイロプラクティック"): "Our {name} realigns your body and eases tension.",
    ("マッサージ店", "リフレクソロジー（足つぼ）"): "Our {name} revives tired feet with expert pressure.",
    ("マッサージ店", "タイ古式マッサージ"): "Our {name} stretches and relaxes you from head to toe.",
    ("マッサージ店", "あん摩・指圧"): "Our {name} works pressure points to loosen tight muscles.",
    ("マッサージ店", "クイックマッサージ"): "Our {name} eases travel fatigue in no time.",
    ("マッサージ店", "ドライヘッドスパ"): "Our {name} guides you into deep, dry-spa relaxation.",

    ("家電量販店", "カメラ・レンズ"): "Our {name} captures your trip in stunning detail.",
    ("家電量販店", "オーディオ・イヤホン"): "Our {name} delivers rich, crisp sound.",
    ("家電量販店", "美容家電"): "Our {name} is a handy beauty gadget to take home.",
    ("家電量販店", "調理家電"): "Our {name} makes cooking quick and easy.",
    ("家電量販店", "PC・スマホ周辺機器"): "Our {name} keeps your devices powered and connected.",
    ("家電量販店", "ゲーム機・ソフト"): "Our {name} brings the fun of Japanese gaming home.",

    ("音楽・映像・ゲーム店", "CD・レコード"): "Our {name} is a great find for music lovers.",
    ("音楽・映像・ゲーム店", "楽器"): "Our {name} is ready to play right out of the box.",
    ("音楽・映像・ゲーム店", "中古ゲーム・レトロゲーム"): "Our {name} is a nostalgic pick for retro-game fans.",
    ("音楽・映像・ゲーム店", "アニメ・キャラクターグッズ"): "Our {name} is a must-have for anime fans.",
    ("音楽・映像・ゲーム店", "トレーディングカード"): "Our {name} could hold the rare card you want.",
    ("音楽・映像・ゲーム店", "フィギュア・ホビー"): "Our {name} is a collectible to treasure.",

    ("書店", "大型書店"): "Our {name} is a great read to pick up.",
    ("書店", "古書店"): "Our {name} is a rare secondhand treasure.",
    ("書店", "漫画・コミック"): "Our {name} is a must-read for manga fans.",
    ("書店", "洋書・多言語書籍"): "Our {name} is handy for readers in any language.",
    ("書店", "アート・写真集"): "Our {name} is a beautiful book to browse and keep.",

    ("映画館", "シネマコンプレックス"): "Our {name} gets you the latest releases on the big screen.",
    ("映画館", "ミニシアター・単館系"): "Our {name} brings you indie and art-house films.",
    ("映画館", "IMAX・4DX"): "Our {name} puts you inside the action with immersive screens.",
    ("映画館", "アニメ映画上映"): "Our {name} shows the latest anime on the big screen.",

    ("カラオケボックス", "一般カラオケボックス"): "Our {name} gives you a private room to sing your heart out.",
    ("カラオケボックス", "パーティールーム"): "Our {name} is built for group fun and celebrations.",
    ("カラオケボックス", "ひとりカラオケ"): "Our {name} is your own booth to sing solo in comfort.",
    ("カラオケボックス", "フリータイム・深夜パック"): "Our {name} lets you sing for hours at a great rate.",
    ("カラオケボックス", "コラボ・アニメルーム"): "Our {name} is an anime-themed room for fans.",

    ("スポーツジム・プール", "フィットネスジム"): "Our {name} gives you full access to the gym facilities.",
    ("スポーツジム・プール", "24時間ジム"): "Our {name} lets you work out any hour you like.",
    ("スポーツジム・プール", "プール・スイミング"): "Our {name} is your pass to lap pools and swimming.",
    ("スポーツジム・プール", "ヨガ・ピラティス"): "Our {name} helps you stretch, breathe, and unwind.",
    ("スポーツジム・プール", "ボルダリング"): "Our {name} gets you climbing at any skill level.",
    ("スポーツジム・プール", "ゴルフ練習場"): "Our {name} is your chance to practice your swing.",

    ("レンタカー", "コンパクトカー"): "Our {name} is an easy, economical way to explore.",
    ("レンタカー", "普通車"): "Our {name} is comfortable for city drives and road trips.",
    ("レンタカー", "ワンボックス（多人数）"): "Our {name} has room for the whole group.",
    ("レンタカー", "高級車・スポーツカー"): "Our {name} makes for a special drive to remember.",
    ("レンタカー", "EV"): "Our {name} is an eco-friendly way to get around.",
    ("レンタカー", "カーシェアリング"): "Our {name} is a quick ride you book from your phone.",

    ("スパ", "天然温泉"): "Our {name} lets you soak in relaxing hot-spring baths.",
    ("スパ", "スーパー銭湯"): "Our {name} opens up a bathhouse full of baths to enjoy.",
    ("スパ", "サウナ"): "Our {name} heats you up before a refreshing cold plunge.",
    ("スパ", "岩盤浴"): "Our {name} warms you on heated stone beds to detox.",
    ("スパ", "個室・貸切風呂"): "Our {name} gives you a private bath for a quiet soak.",
    ("スパ", "エステ"): "Our {name} pampers you with a relaxing treatment.",

    ("衣料品店", "ファストファッション"): "Our {name} is an on-trend piece at a friendly price.",
    ("衣料品店", "古着・ヴィンテージ"): "Our {name} is a one-of-a-kind vintage find.",
    ("衣料品店", "ストリートファッション"): "Our {name} brings bold Tokyo street style.",
    ("衣料品店", "和装・着物"): "Our {name} lets you wear traditional Japanese style.",
    ("衣料品店", "スポーツウェア"): "Our {name} keeps you moving in comfort.",
    ("衣料品店", "セレクトショップ"): "Our {name} is a hand-picked wardrobe staple.",
    ("衣料品店", "靴・スニーカー"): "Our {name} steps up any outfit.",

    ("コンビニエンスストア", "弁当・おにぎり"): "Our {name} is a tasty grab-and-go meal.",
    ("コンビニエンスストア", "スイーツ・アイス"): "Our {name} is a sweet convenience-store treat.",
    ("コンビニエンスストア", "ドリンク・酒類"): "Our {name} is a chilled pick for any time of day.",
    ("コンビニエンスストア", "日用品・雑貨"): "Our {name} covers the essentials in one stop.",
    ("コンビニエンスストア", "チケット・各種サービス"): "Our {name} makes a handy service quick and easy.",

    ("荷物預かりサービス", "コインロッカー"): "Our {name} keeps your bags safe while you explore.",
    ("荷物預かりサービス", "有人預かりカウンター"): "Our {name} stores your luggage with staff on hand.",
    ("荷物預かりサービス", "宿泊先への当日配送"): "Our {name} sends your bags straight to your hotel.",
    ("荷物預かりサービス", "空港への配送"): "Our {name} forwards your bags ahead to the airport.",
    ("荷物預かりサービス", "大型・特大荷物対応"): "Our {name} handles even oversized luggage with ease.",
}

# Each category maps to one perk group; perks are short traveler-facing tags.
_PERK_GROUP: dict[str, str] = {
    "レストラン": "food", "ファストフード": "food", "コーヒーショップ": "food",
    "スイーツショップ": "food", "バー": "food", "コンビニエンスストア": "food",
    "ドラッグストア": "retail", "ディスカウントストア": "retail",
    "家電量販店": "retail", "音楽・映像・ゲーム店": "retail", "書店": "retail",
    "衣料品店": "retail",
    "美容院": "wellness", "マッサージ店": "wellness", "スパ": "wellness",
    "スポーツジム・プール": "wellness",
    "映画館": "leisure", "カラオケボックス": "leisure",
    "レンタカー": "service", "荷物預かりサービス": "service",
}
_PERKS: dict[str, list[str]] = {
    "food": [
        "English menu available.", "Cash and cards accepted.",
        "Show your XB coupon for a special price.", "Freshly made to order.",
    ],
    "retail": [
        "Tax-free with your passport.", "A great souvenir to take home.",
        "Show your XB coupon to save.", "Popular with overseas visitors.",
    ],
    "wellness": [
        "Reservations recommended; English OK.", "Book with your XB coupon.",
        "A relaxing break from sightseeing.", "First-timers from abroad welcome.",
    ],
    "leisure": [
        "English guidance available.", "Show your XB coupon for a discount.",
        "Great for groups of travelers.", "Reserve your spot with ease.",
    ],
    "service": [
        "Simple booking for visitors.", "English support available.",
        "Show your XB coupon to save.", "Handy for your Tokyo trip.",
    ],
}


def make_description(rng, category: str, subcategory: str, name_en: str) -> str:
    """Short EN blurb: the subcategory template filled with the product's English
    name, plus one traveler perk from the category's group.

    Uses its own ``rng`` (a ``random.Random``) so callers can keep it separate
    from the product-name/price stream and leave those columns unchanged.
    """
    sentence = DESC_TEMPLATE[(category, subcategory)].format(name=name_en)
    perk = rng.choice(_PERKS[_PERK_GROUP[category]])
    return f"{sentence} {perk}"
