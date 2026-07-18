"""English names for the shop taxonomy in docs/profiles/shops.md.

This is a **translation** of the taxonomy, and is deliberately separate from
`synthesize-shops/scripts/shop_names.py::SHOP_WORD`, which is a shop-*naming*
device, not a translation: SHOP_WORD renders 寿司・海鮮 as "Sushi" (good inside
「Sushi Sakura」) and 日用品・雑貨 as "Drug" (meaningless as a category label).

Subcategories are keyed by (category, subcategory) because 「日用品・雑貨」 appears
under both ドラッグストア and コンビニエンスストア.

Reusable beyond the dummy images: the XB eSIM app supports 20+ languages, so a
per-language taxonomy map is needed regardless. Promote this out of the skill
when a second consumer appears.
"""
from __future__ import annotations

CATEGORY_EN: dict[str, str] = {
    "レストラン": "Restaurant",
    "ファストフード": "Fast Food",
    "コーヒーショップ": "Coffee Shop",
    "スイーツショップ": "Sweets Shop",
    "バー": "Bar",
    "ドラッグストア": "Drugstore",
    "ディスカウントストア": "Discount Store",
    "美容院": "Hair Salon",
    "マッサージ店": "Massage",
    "家電量販店": "Electronics Store",
    "音楽・映像・ゲーム店": "Music, Video & Games",
    "書店": "Bookstore",
    "映画館": "Cinema",
    "カラオケボックス": "Karaoke",
    "スポーツジム・プール": "Gym & Pool",
    "レンタカー": "Car Rental",
    "スパ": "Spa",
    "衣料品店": "Clothing Store",
    "コンビニエンスストア": "Convenience Store",
    "荷物預かりサービス": "Luggage Storage",
}

SUBCATEGORY_EN: dict[tuple[str, str], str] = {
    ("レストラン", "寿司・海鮮"): "Sushi & Seafood",
    ("レストラン", "ラーメン"): "Ramen",
    ("レストラン", "焼肉・ホルモン"): "Yakiniku & Offal",
    ("レストラン", "天ぷら・とんかつ"): "Tempura & Tonkatsu",
    ("レストラン", "そば・うどん"): "Soba & Udon",
    ("レストラン", "お好み焼き・もんじゃ焼き"): "Okonomiyaki & Monjayaki",
    ("レストラン", "イタリア料理"): "Italian",
    ("レストラン", "インド料理"): "Indian",
    ("レストラン", "韓国料理"): "Korean",
    ("レストラン", "中華料理"): "Chinese",

    ("ファストフード", "ハンバーガー"): "Hamburger",
    ("ファストフード", "牛丼"): "Gyudon Beef Bowl",
    ("ファストフード", "カレー"): "Curry",
    ("ファストフード", "立ち食いそば"): "Standing Soba",
    ("ファストフード", "フライドチキン"): "Fried Chicken",
    ("ファストフード", "サンドイッチ・ベーカリー"): "Sandwich & Bakery",

    ("コーヒーショップ", "チェーンカフェ"): "Chain Cafe",
    ("コーヒーショップ", "自家焙煎コーヒー"): "Specialty Roastery",
    ("コーヒーショップ", "純喫茶"): "Retro Kissaten",
    ("コーヒーショップ", "タピオカ・ドリンクスタンド"): "Bubble Tea Stand",
    ("コーヒーショップ", "テーマカフェ（アニメ・動物）"): "Theme Cafe (Anime & Animals)",

    ("スイーツショップ", "和菓子"): "Wagashi",
    ("スイーツショップ", "洋菓子・ケーキ"): "Patisserie & Cake",
    ("スイーツショップ", "クレープ・パンケーキ"): "Crepe & Pancake",
    ("スイーツショップ", "ソフトクリーム・アイス"): "Soft Serve & Ice Cream",
    ("スイーツショップ", "チョコレート専門店"): "Chocolate Specialist",
    ("スイーツショップ", "たい焼き・どら焼き"): "Taiyaki & Dorayaki",

    ("バー", "居酒屋"): "Izakaya",
    ("バー", "立ち飲み屋"): "Standing Bar",
    ("バー", "日本酒バー"): "Sake Bar",
    ("バー", "クラフトビール・ビアバー"): "Craft Beer Bar",
    ("バー", "ウイスキー・カクテルバー"): "Whisky & Cocktail Bar",
    ("バー", "ワインバー"): "Wine Bar",
    ("バー", "スポーツバー"): "Sports Bar",

    ("ドラッグストア", "医薬品・常備薬"): "Medicine",
    ("ドラッグストア", "化粧品・スキンケア"): "Cosmetics & Skincare",
    ("ドラッグストア", "ヘアケア・ボディケア"): "Hair & Body Care",
    ("ドラッグストア", "サプリメント・健康食品"): "Supplements",
    ("ドラッグストア", "ベビー用品"): "Baby Products",
    ("ドラッグストア", "日用品・雑貨"): "Daily Goods",

    ("ディスカウントストア", "総合ディスカウント"): "General Discount",
    ("ディスカウントストア", "100円ショップ"): "100-Yen Shop",
    ("ディスカウントストア", "免税専門店"): "Duty-Free Store",
    ("ディスカウントストア", "アウトレット"): "Outlet",
    ("ディスカウントストア", "生活雑貨"): "Household Goods",

    ("美容院", "カット・カラー"): "Cut & Color",
    ("美容院", "ヘッドスパ"): "Head Spa",
    ("美容院", "ネイルサロン"): "Nail Salon",
    ("美容院", "まつげエクステ"): "Eyelash Extensions",
    ("美容院", "着付け・ヘアセット"): "Kimono Dressing & Hair",

    ("マッサージ店", "整体・カイロプラクティック"): "Seitai & Chiropractic",
    ("マッサージ店", "リフレクソロジー（足つぼ）"): "Reflexology (Foot)",
    ("マッサージ店", "タイ古式マッサージ"): "Thai Massage",
    ("マッサージ店", "あん摩・指圧"): "Anma & Shiatsu",
    ("マッサージ店", "クイックマッサージ"): "Quick Massage",
    ("マッサージ店", "ドライヘッドスパ"): "Dry Head Spa",

    ("家電量販店", "カメラ・レンズ"): "Cameras & Lenses",
    ("家電量販店", "オーディオ・イヤホン"): "Audio & Earphones",
    ("家電量販店", "美容家電"): "Beauty Appliances",
    ("家電量販店", "調理家電"): "Kitchen Appliances",
    ("家電量販店", "PC・スマホ周辺機器"): "PC & Phone Accessories",
    ("家電量販店", "ゲーム機・ソフト"): "Consoles & Games",

    ("音楽・映像・ゲーム店", "CD・レコード"): "CDs & Vinyl",
    ("音楽・映像・ゲーム店", "楽器"): "Musical Instruments",
    ("音楽・映像・ゲーム店", "中古ゲーム・レトロゲーム"): "Used & Retro Games",
    ("音楽・映像・ゲーム店", "アニメ・キャラクターグッズ"): "Anime & Character Goods",
    ("音楽・映像・ゲーム店", "トレーディングカード"): "Trading Cards",
    ("音楽・映像・ゲーム店", "フィギュア・ホビー"): "Figures & Hobby",

    ("書店", "大型書店"): "Large Bookstore",
    ("書店", "古書店"): "Antiquarian Books",
    ("書店", "漫画・コミック"): "Manga & Comics",
    ("書店", "洋書・多言語書籍"): "Foreign & Multilingual Books",
    ("書店", "アート・写真集"): "Art & Photo Books",

    ("映画館", "シネマコンプレックス"): "Cinema Complex",
    ("映画館", "ミニシアター・単館系"): "Independent Cinema",
    ("映画館", "IMAX・4DX"): "IMAX & 4DX",
    ("映画館", "アニメ映画上映"): "Anime Film Screening",

    ("カラオケボックス", "一般カラオケボックス"): "Standard Karaoke Box",
    ("カラオケボックス", "パーティールーム"): "Party Room",
    ("カラオケボックス", "ひとりカラオケ"): "Solo Karaoke",
    ("カラオケボックス", "フリータイム・深夜パック"): "Free Time & Late-Night Pack",
    ("カラオケボックス", "コラボ・アニメルーム"): "Collab & Anime Room",

    ("スポーツジム・プール", "フィットネスジム"): "Fitness Gym",
    ("スポーツジム・プール", "24時間ジム"): "24-Hour Gym",
    ("スポーツジム・プール", "プール・スイミング"): "Pool & Swimming",
    ("スポーツジム・プール", "ヨガ・ピラティス"): "Yoga & Pilates",
    ("スポーツジム・プール", "ボルダリング"): "Bouldering",
    ("スポーツジム・プール", "ゴルフ練習場"): "Golf Driving Range",

    ("レンタカー", "コンパクトカー"): "Compact Car",
    ("レンタカー", "普通車"): "Standard Car",
    ("レンタカー", "ワンボックス（多人数）"): "Minivan (Group)",
    ("レンタカー", "高級車・スポーツカー"): "Luxury & Sports Car",
    ("レンタカー", "EV"): "Electric Vehicle",
    ("レンタカー", "カーシェアリング"): "Car Sharing",

    ("スパ", "天然温泉"): "Natural Hot Spring",
    ("スパ", "スーパー銭湯"): "Super Sento",
    ("スパ", "サウナ"): "Sauna",
    ("スパ", "岩盤浴"): "Ganbanyoku Stone Sauna",
    ("スパ", "個室・貸切風呂"): "Private Bath",
    ("スパ", "エステ"): "Esthetic Salon",

    ("衣料品店", "ファストファッション"): "Fast Fashion",
    ("衣料品店", "古着・ヴィンテージ"): "Vintage & Used Clothing",
    ("衣料品店", "ストリートファッション"): "Street Fashion",
    ("衣料品店", "和装・着物"): "Kimono & Traditional Wear",
    ("衣料品店", "スポーツウェア"): "Sportswear",
    ("衣料品店", "セレクトショップ"): "Select Shop",
    ("衣料品店", "靴・スニーカー"): "Shoes & Sneakers",

    ("コンビニエンスストア", "弁当・おにぎり"): "Bento & Onigiri",
    ("コンビニエンスストア", "スイーツ・アイス"): "Sweets & Ice Cream",
    ("コンビニエンスストア", "ドリンク・酒類"): "Drinks & Alcohol",
    ("コンビニエンスストア", "日用品・雑貨"): "Daily Goods",
    ("コンビニエンスストア", "チケット・各種サービス"): "Tickets & Services",

    ("荷物預かりサービス", "コインロッカー"): "Coin Locker",
    ("荷物預かりサービス", "有人預かりカウンター"): "Staffed Luggage Counter",
    ("荷物預かりサービス", "宿泊先への当日配送"): "Same-Day Hotel Delivery",
    ("荷物預かりサービス", "空港への配送"): "Airport Delivery",
    ("荷物預かりサービス", "大型・特大荷物対応"): "Large & Oversized Luggage",
}
