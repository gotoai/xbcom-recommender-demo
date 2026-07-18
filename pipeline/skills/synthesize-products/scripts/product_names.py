"""Paired Japanese / English vocabulary and price bands for synthetic products.

Same design as `synthesize-shops/scripts/shop_names.py`: every entry carries both
language forms, so the English name is a parallel name rather than a
transliteration and no romanisation library is needed.

Names are **compositional** — `{modifier}{item}` — which is what gives 6,000 shops
distinguishable products out of 117 sub-categories:

    醤油ラーメン  +  野菜たっぷり  ->  野菜たっぷり醤油ラーメン / Veggie-Loaded Shoyu Ramen
                     魚介          ->  魚介醤油ラーメン       / Seafood Shoyu Ramen

Encoding
    item / modifier : "ja|en"  or  "ja|en|price_multiplier"  (multiplier defaults 1.0)
    PRODUCTS[(category, subcategory)] = (items, mod_pool_key | None, (price_lo, price_hi))

Modifiers are chosen to work as an adjectival **prefix in both languages**, so the
two names stay structurally parallel. Their price multiplier keeps the name and the
price honest with each other: a 特上 item costs more than an あっさり one.

Keyed by (category, subcategory) because 「日用品・雑貨」 appears under both
ドラッグストア and コンビニエンスストア.
"""
from __future__ import annotations

# --- modifier pools -----------------------------------------------------------
MOD_POOLS: dict[str, list[str]] = {
    "ramen": [
        "野菜たっぷり|Veggie-Loaded|1.1", "魚介|Seafood|1.1", "特製|Special|1.3",
        "濃厚|Rich|1.1", "あっさり|Light", "炙りチャーシュー|Roasted Chashu|1.4",
        "全部のせ|Fully Loaded|1.5", "激辛|Extra-Spicy|1.05", "大盛|Large|1.2",
        "煮干し|Niboshi|1.1", "background|x",  # placeholder removed below
    ],
    "sushi": [
        "特上|Premium|1.6", "上|Prime|1.3", "おまかせ|Chef's Choice|1.5",
        "旬の|Seasonal|1.2", "本日の|Today's", "産直|Farm-Direct|1.3",
        "極上|Deluxe|1.8",
    ],
    "washoku": [
        "特製|Special|1.3", "名物|Signature|1.2", "旬の|Seasonal|1.2",
        "大盛|Large|1.2", "本日の|Today's", "極上|Deluxe|1.5", "自家製|Homemade|1.1",
    ],
    "yakiniku": [
        "特選|Premium Selection|1.5", "和牛|Wagyu|1.8", "厚切り|Thick-Cut|1.3",
        "塩だれ|Salt-Tare", "味噌だれ|Miso-Tare", "上|Prime|1.3", "炙り|Seared|1.2",
    ],
    "western": [
        "本日の|Today's", "シェフおすすめ|Chef's Recommendation|1.3", "季節の|Seasonal|1.2",
        "特製|Special|1.3", "自家製|Homemade|1.1", "熟成|Aged|1.4",
    ],
    "asian": [
        "本格|Authentic|1.2", "特製|Special|1.3", "辛口|Spicy", "マイルド|Mild",
        "名物|Signature|1.2", "食べ放題|All-You-Can-Eat|1.6",
    ],
    "fastfood": [
        "期間限定|Limited-Time|1.1", "特製|Special|1.2", "大盛|Large|1.3",
        "ダブル|Double|1.5", "スパイシー|Spicy", "チーズ|Cheese|1.15",
    ],
    "cafe": [
        "本日の|Today's", "季節限定|Seasonal|1.15", "自家製|Homemade|1.1",
        "特製|Special|1.2", "デカフェ|Decaf", "アイス|Iced", "ホット|Hot",
    ],
    "sweets": [
        "季節限定|Seasonal|1.2", "自家製|Homemade|1.1", "特製|Special|1.2",
        "苺の|Strawberry|1.25", "抹茶|Matcha|1.15", "期間限定|Limited-Time|1.1",
        "栗の|Chestnut|1.25",
    ],
    "bar": [
        "厳選|Hand-Picked|1.3", "季節の|Seasonal|1.15", "特選|Premium|1.4",
        "店主おすすめ|Owner's Pick|1.2", "数量限定|Limited Stock|1.3", "樽生|Draft",
    ],
    "retail": [
        "人気の|Popular", "限定|Limited Edition|1.3", "新作|New Arrival|1.2",
        "定番|Classic", "売れ筋|Best-Selling|1.1", "日本限定|Japan-Exclusive|1.4",
    ],
    "beauty": [
        "人気|Popular", "指名|With Stylist|1.3", "初回|First-Visit|0.8",
        "平日限定|Weekday-Only|0.85", "トリートメント付き|With Treatment|1.4",
    ],
    "relax": [
        "人気|Popular", "平日限定|Weekday-Only|0.85", "強め|Firm-Pressure",
        "リラックス|Relaxing", "オイル付き|With Oil|1.3",
    ],
    "ticket": [
        "平日|Weekday|0.9", "土日|Weekend|1.1", "レイトショー|Late-Show|0.8",
        "早割|Early-Bird|0.85",
    ],
    "gym": [
        "平日限定|Weekday-Only|0.85", "初回体験|First-Time Trial|0.6",
        "早朝|Early-Morning|0.9", "レンタル付き|With Rental|1.2",
    ],
    "rental": [
        "平日|Weekday|0.9", "週末|Weekend|1.2", "早割|Early-Bird|0.85",
        "免責補償付き|With Insurance|1.15", "ETC付き|With ETC|1.05",
    ],
    "luggage": [
        "当日|Same-Day", "早朝受付|Early Drop-Off|1.1", "事前予約|Advance-Booking|0.9",
    ],
    "spa": [
        "平日限定|Weekday-Only|0.85", "深夜|Late-Night|1.2", "朝風呂|Morning-Bath|0.9",
        "タオル付き|With Towel|1.15", "館内着付き|With Loungewear|1.2",
    ],
    "conv": [
        "期間限定|Limited-Time|1.1", "新発売|New Release|1.05", "増量|Extra-Portion|1.2",
        "人気|Popular",
    ],
}
MOD_POOLS["ramen"] = [m for m in MOD_POOLS["ramen"] if not m.startswith("background")]

# --- (category, subcategory) -> (items, mod pool, (price_lo, price_hi)) --------
PRODUCTS: dict[tuple[str, str], tuple[list[str], str | None, tuple[int, int]]] = {
    ("レストラン", "寿司・海鮮"): (
        ["握り寿司セット|Nigiri Sushi Set", "海鮮丼|Seafood Rice Bowl",
         "寿司盛り合わせ|Sushi Platter", "刺身盛り合わせ|Sashimi Platter",
         "ちらし寿司|Chirashi Sushi"], "sushi", (2000, 8000)),
    ("レストラン", "ラーメン"): (
        ["醤油ラーメン|Shoyu Ramen", "味噌ラーメン|Miso Ramen",
         "豚骨ラーメン|Tonkotsu Ramen", "つけ麺|Tsukemen", "塩ラーメン|Shio Ramen",
         "担々麺|Tantanmen"], "ramen", (800, 1600)),
    ("レストラン", "焼肉・ホルモン"): (
        ["焼肉セット|Yakiniku Set", "カルビ|Karubi", "ホルモン盛り合わせ|Assorted Horumon",
         "牛タン|Beef Tongue", "焼肉コース|Yakiniku Course"], "yakiniku", (3000, 12000)),
    ("レストラン", "天ぷら・とんかつ"): (
        ["天ぷら定食|Tempura Set Meal", "ロースかつ定食|Tonkatsu Set Meal",
         "天丼|Tendon", "ヒレかつ定食|Hirekatsu Set Meal"], "washoku", (1200, 3500)),
    ("レストラン", "そば・うどん"): (
        ["ざるそば|Zaru Soba", "天ぷらそば|Tempura Soba", "きつねうどん|Kitsune Udon",
         "鴨南蛮|Kamo Nanban", "カレーうどん|Curry Udon"], "washoku", (700, 1800)),
    ("レストラン", "お好み焼き・もんじゃ焼き"): (
        ["お好み焼き|Okonomiyaki", "もんじゃ焼き|Monjayaki", "豚玉|Butatama",
         "ミックス焼き|Mixed Okonomiyaki"], "washoku", (900, 2200)),
    ("レストラン", "イタリア料理"): (
        ["パスタランチ|Pasta Lunch", "マルゲリータ|Margherita Pizza",
         "コースディナー|Course Dinner", "リゾット|Risotto",
         "ボロネーゼ|Bolognese"], "western", (1200, 6000)),
    ("レストラン", "インド料理"): (
        ["カレーセット|Curry Set", "ナンカレーセット|Naan Curry Set",
         "タンドリーチキン|Tandoori Chicken", "ビリヤニ|Biryani"], "asian", (1000, 3000)),
    ("レストラン", "韓国料理"): (
        ["サムギョプサル|Samgyeopsal", "ビビンバ|Bibimbap", "韓国鍋セット|Korean Hotpot Set",
         "チヂミ|Jeon", "参鶏湯|Samgyetang"], "asian", (1200, 4000)),
    ("レストラン", "中華料理"): (
        ["麻婆豆腐定食|Mapo Tofu Set", "小籠包|Xiaolongbao", "中華コース|Chinese Course",
         "餃子セット|Gyoza Set", "青椒肉絲定食|Chinjao Rosu Set"], "asian", (900, 5000)),

    ("ファストフード", "ハンバーガー"): (
        ["チーズバーガーセット|Cheeseburger Set", "ベーコンバーガー|Bacon Burger",
         "照り焼きバーガー|Teriyaki Burger", "アボカドバーガー|Avocado Burger"],
        "fastfood", (500, 1200)),
    ("ファストフード", "牛丼"): (
        ["牛丼|Gyudon", "牛丼セット|Gyudon Set", "ねぎ玉牛丼|Negitama Gyudon",
         "チーズ牛丼|Cheese Gyudon"], "fastfood", (400, 900)),
    ("ファストフード", "カレー"): (
        ["カツカレー|Katsu Curry", "ビーフカレー|Beef Curry",
         "野菜カレー|Vegetable Curry", "チキンカレー|Chicken Curry"],
        "fastfood", (500, 1200)),
    ("ファストフード", "立ち食いそば"): (
        ["かけそば|Kake Soba", "天ぷらそば|Tempura Soba", "月見そば|Tsukimi Soba",
         "コロッケそば|Korokke Soba"], "fastfood", (350, 700)),
    ("ファストフード", "フライドチキン"): (
        ["チキンセット|Chicken Set", "フライドチキン5ピース|5-Piece Fried Chicken",
         "チキンバーガー|Chicken Burger", "手羽先|Chicken Wings"], "fastfood", (600, 1600)),
    ("ファストフード", "サンドイッチ・ベーカリー"): (
        ["サンドイッチセット|Sandwich Set", "クロワッサン|Croissant",
         "惣菜パンセット|Savory Bread Set", "カツサンド|Katsu Sando"],
        "fastfood", (300, 1000)),

    ("コーヒーショップ", "チェーンカフェ"): (
        ["ブレンドコーヒー|Blended Coffee", "カフェラテ|Cafe Latte",
         "コーヒー＆ケーキセット|Coffee & Cake Set", "カプチーノ|Cappuccino"],
        "cafe", (350, 900)),
    ("コーヒーショップ", "自家焙煎コーヒー"): (
        ["シングルオリジン|Single Origin Coffee", "ハンドドリップ|Hand Drip Coffee",
         "焙煎豆200g|Roasted Beans 200g", "エスプレッソ|Espresso"], "cafe", (500, 2500)),
    ("コーヒーショップ", "純喫茶"): (
        ["ブレンドとトーストセット|Blend & Toast Set", "クリームソーダ|Cream Soda",
         "ナポリタン|Napolitan", "プリンアラモード|Pudding a la Mode"],
        "cafe", (600, 1500)),
    ("コーヒーショップ", "タピオカ・ドリンクスタンド"): (
        ["タピオカミルクティー|Bubble Milk Tea", "黒糖タピオカ|Brown Sugar Boba",
         "フルーツティー|Fruit Tea", "タロミルク|Taro Milk"], "cafe", (450, 900)),
    ("コーヒーショップ", "テーマカフェ（アニメ・動物）"): (
        ["コラボドリンク|Collab Drink", "猫カフェ1時間|Cat Cafe 1 Hour",
         "テーマプレート|Theme Plate", "コラボデザート|Collab Dessert"],
        "cafe", (900, 3000)),

    ("スイーツショップ", "和菓子"): (
        ["上生菓子詰合せ|Assorted Wagashi", "どら焼き5個入|5 Dorayaki",
         "最中詰合せ|Assorted Monaka", "羊羹|Yokan"], "sweets", (700, 3500)),
    ("スイーツショップ", "洋菓子・ケーキ"): (
        ["ショートケーキ|Strawberry Shortcake", "ホールケーキ|Whole Cake",
         "焼菓子詰合せ|Assorted Baked Sweets", "モンブラン|Mont Blanc"],
        "sweets", (500, 5000)),
    ("スイーツショップ", "クレープ・パンケーキ"): (
        ["クレープ|Crepe", "パンケーキセット|Pancake Set",
         "チョコバナナクレープ|Choco Banana Crepe", "スフレパンケーキ|Souffle Pancake"],
        "sweets", (600, 1800)),
    ("スイーツショップ", "ソフトクリーム・アイス"): (
        ["ソフトクリーム|Soft Serve", "アイス2種盛り|Two-Scoop Ice Cream",
         "パフェ|Parfait", "ジェラート|Gelato"], "sweets", (350, 900)),
    ("スイーツショップ", "チョコレート専門店"): (
        ["ボンボンショコラ6粒|6 Bonbon Chocolats", "板チョコ詰合せ|Assorted Chocolate Bars",
         "ガトーショコラ|Gateau Chocolat", "トリュフ詰合せ|Assorted Truffles"],
        "sweets", (1000, 5000)),
    ("スイーツショップ", "たい焼き・どら焼き"): (
        ["たい焼き3個|3 Taiyaki", "どら焼き詰合せ|Assorted Dorayaki",
         "クリームたい焼き|Cream Taiyaki", "あんこたい焼き|Anko Taiyaki"],
        "sweets", (400, 1500)),

    ("バー", "居酒屋"): (
        ["飲み放題2時間|2-Hour All-You-Can-Drink", "宴会コース|Banquet Course",
         "おつまみ盛り合わせ|Assorted Snacks", "串焼き盛り合わせ|Assorted Skewers"],
        "bar", (2500, 6000)),
    ("バー", "立ち飲み屋"): (
        ["生ビール＋おつまみ|Draft Beer & Snack", "ハイボールセット|Highball Set",
         "せんべろセット|1000-Yen Drink Set", "角打ちセット|Kakuuchi Set"],
        "bar", (800, 2000)),
    ("バー", "日本酒バー"): (
        ["日本酒3種飲み比べ|Sake Tasting Flight", "純米大吟醸1合|Junmai Daiginjo 1 Go",
         "酒肴セット|Sake & Appetizer Set", "冷酒セット|Chilled Sake Set"],
        "bar", (1200, 4000)),
    ("バー", "クラフトビール・ビアバー"): (
        ["クラフトビール3種|3 Craft Beers", "パイント1杯|1 Pint",
         "ビール＆ソーセージ|Beer & Sausage", "テイスティングセット|Tasting Set"],
        "bar", (900, 3500)),
    ("バー", "ウイスキー・カクテルバー"): (
        ["シングルモルト|Single Malt", "カクテル2杯セット|2 Cocktails",
         "ウイスキー飲み比べ|Whisky Flight", "ハイボール3杯|3 Highballs"],
        "bar", (1200, 5000)),
    ("バー", "ワインバー"): (
        ["グラスワイン2杯|2 Glasses of Wine", "ボトルワイン|Bottle of Wine",
         "ワイン＆チーズ|Wine & Cheese", "ワインフライト|Wine Flight"],
        "bar", (1500, 8000)),
    ("バー", "スポーツバー"): (
        ["観戦セット|Match Viewing Set", "ビール＆ピザ|Beer & Pizza",
         "ドリンク2杯セット|2-Drink Set", "貸切観戦プラン|Private Viewing Plan"],
        "bar", (1500, 4000)),

    ("ドラッグストア", "医薬品・常備薬"): (
        ["総合感冒薬|Cold Medicine", "胃腸薬|Stomach Medicine",
         "解熱鎮痛薬|Painkiller", "目薬|Eye Drops"], "retail", (700, 2500)),
    ("ドラッグストア", "化粧品・スキンケア"): (
        ["化粧水|Face Lotion", "美容液|Serum", "シートマスク30枚|30 Sheet Masks",
         "日焼け止め|Sunscreen"], "retail", (800, 6000)),
    ("ドラッグストア", "ヘアケア・ボディケア"): (
        ["シャンプーセット|Shampoo Set", "トリートメント|Hair Treatment",
         "ボディソープ|Body Wash", "ヘアオイル|Hair Oil"], "retail", (600, 3000)),
    ("ドラッグストア", "サプリメント・健康食品"): (
        ["マルチビタミン|Multivitamin", "コラーゲンサプリ|Collagen Supplement",
         "青汁30包|30 Aojiru Packets", "乳酸菌サプリ|Probiotic Supplement"],
        "retail", (900, 4500)),
    ("ドラッグストア", "ベビー用品"): (
        ["おむつパック|Diaper Pack", "ベビーローション|Baby Lotion",
         "粉ミルク|Baby Formula", "おしりふき|Baby Wipes"], "retail", (800, 3500)),
    ("ドラッグストア", "日用品・雑貨"): (
        ["日用品セット|Daily Goods Set", "マスク50枚|50 Face Masks",
         "洗剤詰替パック|Detergent Refill", "歯ブラシセット|Toothbrush Set"],
        "retail", (400, 2000)),

    ("ディスカウントストア", "総合ディスカウント"): (
        ["お土産まとめ買いセット|Souvenir Bulk Set", "日用品バラエティセット|Variety Goods Set",
         "お菓子詰合せ|Assorted Snacks", "コスメ福袋|Cosmetics Lucky Bag"],
        "retail", (1000, 5000)),
    ("ディスカウントストア", "100円ショップ"): (
        ["雑貨5点セット|5-Item Zakka Set", "キッチン用品セット|Kitchen Goods Set",
         "文具セット|Stationery Set", "トラベル用品セット|Travel Goods Set"],
        "retail", (100, 500)),
    ("ディスカウントストア", "免税専門店"): (
        ["免税お菓子セット|Duty-Free Snack Set", "免税化粧品セット|Duty-Free Cosmetics Set",
         "免税お土産セット|Duty-Free Souvenir Set", "免税酒類セット|Duty-Free Liquor Set"],
        "retail", (2000, 15000)),
    ("ディスカウントストア", "アウトレット"): (
        ["アウトレット衣料品|Outlet Apparel", "アウトレットバッグ|Outlet Bag",
         "アウトレットシューズ|Outlet Shoes", "アウトレット雑貨|Outlet Goods"],
        "retail", (2000, 12000)),
    ("ディスカウントストア", "生活雑貨"): (
        ["インテリア雑貨|Interior Goods", "キッチン雑貨|Kitchen Zakka",
         "収納用品|Storage Goods", "バス用品|Bath Goods"], "retail", (600, 3500)),

    ("美容院", "カット・カラー"): (
        ["カット|Haircut", "カット＆カラー|Cut & Color", "カラーリング|Hair Coloring",
         "パーマ|Perm"], "beauty", (4000, 15000)),
    ("美容院", "ヘッドスパ"): (
        ["ヘッドスパ30分|30-Min Head Spa", "ヘッドスパ60分|60-Min Head Spa",
         "スパ＆カット|Spa & Cut", "炭酸スパ|Carbonated Spa"], "beauty", (3000, 10000)),
    ("美容院", "ネイルサロン"): (
        ["ジェルネイル|Gel Nails", "ネイルアート|Nail Art",
         "ケアコース|Nail Care Course", "フットネイル|Foot Nails"],
        "beauty", (3500, 12000)),
    ("美容院", "まつげエクステ"): (
        ["まつげエクステ100本|100 Eyelash Extensions", "まつげパーマ|Lash Lift",
         "エクステ付け放題|Unlimited Extensions", "まつげカール|Lash Curl"],
        "beauty", (4000, 12000)),
    ("美容院", "着付け・ヘアセット"): (
        ["着物レンタル＆着付け|Kimono Rental & Dressing", "ヘアセット|Hair Styling",
         "浴衣プラン|Yukata Plan", "振袖着付け|Furisode Dressing"],
        "beauty", (3000, 12000)),

    ("マッサージ店", "整体・カイロプラクティック"): (
        ["整体60分|60-Min Seitai", "骨盤矯正|Pelvic Correction",
         "全身整体90分|90-Min Full Body Seitai", "整体30分|30-Min Seitai"],
        "relax", (3500, 10000)),
    ("マッサージ店", "リフレクソロジー（足つぼ）"): (
        ["足つぼ30分|30-Min Foot Reflexology", "足つぼ60分|60-Min Foot Reflexology",
         "足＆肩セット|Foot & Shoulder Set", "足つぼ45分|45-Min Foot Reflexology"],
        "relax", (2500, 7000)),
    ("マッサージ店", "タイ古式マッサージ"): (
        ["タイ古式60分|60-Min Thai Massage", "タイ古式90分|90-Min Thai Massage",
         "タイ古式120分|120-Min Thai Massage", "タイ古式＆足つぼ|Thai Massage & Foot"],
        "relax", (4000, 12000)),
    ("マッサージ店", "あん摩・指圧"): (
        ["指圧40分|40-Min Shiatsu", "全身指圧60分|60-Min Full Body Shiatsu",
         "肩こりコース|Shoulder Relief Course", "あん摩30分|30-Min Anma"],
        "relax", (3000, 8000)),
    ("マッサージ店", "クイックマッサージ"): (
        ["クイック15分|15-Min Quick Massage", "クイック30分|30-Min Quick Massage",
         "肩・首10分|10-Min Neck & Shoulder", "クイック20分|20-Min Quick Massage"],
        "relax", (1000, 3500)),
    ("マッサージ店", "ドライヘッドスパ"): (
        ["ドライヘッドスパ30分|30-Min Dry Head Spa",
         "ドライヘッドスパ60分|60-Min Dry Head Spa", "快眠コース|Deep Sleep Course",
         "ドライヘッドスパ45分|45-Min Dry Head Spa"], "relax", (3000, 9000)),

    ("家電量販店", "カメラ・レンズ"): (
        ["ミラーレスカメラ|Mirrorless Camera", "標準ズームレンズ|Standard Zoom Lens",
         "コンパクトカメラ|Compact Camera", "単焦点レンズ|Prime Lens"],
        "retail", (30000, 250000)),
    ("家電量販店", "オーディオ・イヤホン"): (
        ["ワイヤレスイヤホン|Wireless Earbuds", "ヘッドホン|Headphones",
         "ポータブルスピーカー|Portable Speaker", "有線イヤホン|Wired Earphones"],
        "retail", (5000, 60000)),
    ("家電量販店", "美容家電"): (
        ["ヘアドライヤー|Hair Dryer", "ヘアアイロン|Hair Straightener",
         "美顔器|Facial Device", "電動シェーバー|Electric Shaver"],
        "retail", (6000, 60000)),
    ("家電量販店", "調理家電"): (
        ["電気ケトル|Electric Kettle", "炊飯器|Rice Cooker",
         "ホットプレート|Hot Plate", "電子レンジ|Microwave Oven"],
        "retail", (4000, 80000)),
    ("家電量販店", "PC・スマホ周辺機器"): (
        ["モバイルバッテリー|Power Bank", "スマホケース|Phone Case",
         "USB-Cハブ|USB-C Hub", "ワイヤレス充電器|Wireless Charger"],
        "retail", (1500, 20000)),
    ("家電量販店", "ゲーム機・ソフト"): (
        ["携帯ゲーム機|Handheld Console", "ゲームソフト|Game Software",
         "コントローラー|Controller", "据置ゲーム機|Home Console"],
        "retail", (5000, 50000)),

    ("音楽・映像・ゲーム店", "CD・レコード"): (
        ["中古レコード|Used Vinyl Record", "新譜CD|New Release CD",
         "レコード3枚セット|3-Record Set", "アナログ盤|Analog Record"],
        "retail", (1000, 8000)),
    ("音楽・映像・ゲーム店", "楽器"): (
        ["エフェクター|Guitar Effects Pedal", "ウクレレ|Ukulele",
         "楽器アクセサリー|Instrument Accessories", "電子ピアノ|Digital Piano"],
        "retail", (3000, 60000)),
    ("音楽・映像・ゲーム店", "中古ゲーム・レトロゲーム"): (
        ["レトロゲームソフト|Retro Game Cartridge", "中古ゲーム機|Used Console",
         "ゲーム3本セット|3-Game Bundle", "レトロ携帯機|Retro Handheld"],
        "retail", (1500, 30000)),
    ("音楽・映像・ゲーム店", "アニメ・キャラクターグッズ"): (
        ["キャラクターグッズセット|Character Goods Set", "アクリルスタンド|Acrylic Stand",
         "ぬいぐるみ|Plush Toy", "缶バッジセット|Can Badge Set"],
        "retail", (800, 8000)),
    ("音楽・映像・ゲーム店", "トレーディングカード"): (
        ["トレカBOX|Trading Card Box", "レアカード|Rare Card",
         "スターターデッキ|Starter Deck", "パック10袋|10 Card Packs"],
        "retail", (500, 20000)),
    ("音楽・映像・ゲーム店", "フィギュア・ホビー"): (
        ["スケールフィギュア|Scale Figure", "プラモデル|Plastic Model Kit",
         "ねんどろいど|Nendoroid", "ソフビフィギュア|Sofubi Figure"],
        "retail", (2000, 25000)),

    ("書店", "大型書店"): (
        ["話題の新刊|New Release Book", "雑誌セット|Magazine Set",
         "ベストセラー|Bestseller", "文庫本3冊|3 Paperbacks"], "retail", (700, 3500)),
    ("書店", "古書店"): (
        ["古書1冊|Antiquarian Book", "古地図|Antique Map",
         "古書3冊セット|3 Used Books", "浮世絵復刻版|Ukiyo-e Reprint"],
        "retail", (500, 12000)),
    ("書店", "漫画・コミック"): (
        ["コミック全巻セット|Complete Manga Set", "新刊コミック|New Manga Volume",
         "コミック5冊セット|5-Volume Manga Set", "画集付きコミック|Manga with Art Book"],
        "retail", (500, 12000)),
    ("書店", "洋書・多言語書籍"): (
        ["洋書1冊|Foreign Language Book", "日本ガイドブック|Japan Guidebook",
         "多言語辞書|Multilingual Dictionary", "日本語学習書|Japanese Textbook"],
        "retail", (1000, 5000)),
    ("書店", "アート・写真集"): (
        ["写真集|Photo Book", "アートブック|Art Book",
         "画集|Illustration Collection", "建築書|Architecture Book"],
        "retail", (2000, 9000)),

    ("映画館", "シネマコンプレックス"): (
        ["一般1名|1 Adult Ticket", "ペアチケット|Pair Ticket",
         "ポップコーンセット|Ticket & Popcorn Set"], "ticket", (1500, 3500)),
    ("映画館", "ミニシアター・単館系"): (
        ["一般1名|1 Adult Ticket", "会員料金|Member Ticket",
         "特集上映券|Special Screening Ticket"], "ticket", (1300, 2200)),
    ("映画館", "IMAX・4DX"): (
        ["IMAX一般1名|1 IMAX Ticket", "4DX一般1名|1 4DX Ticket",
         "IMAXペア|IMAX Pair Ticket"], "ticket", (2000, 4500)),
    ("映画館", "アニメ映画上映"): (
        ["一般1名|1 Adult Ticket", "特典付きチケット|Ticket with Bonus",
         "ペアチケット|Pair Ticket"], "ticket", (1500, 3000)),

    ("カラオケボックス", "一般カラオケボックス"): (
        ["1時間1名|1 Hour per Person", "3時間パック|3-Hour Pack",
         "ドリンクバー付き2時間|2 Hours with Drink Bar"], "ticket", (500, 3000)),
    ("カラオケボックス", "パーティールーム"): (
        ["パーティープラン|Party Plan", "貸切2時間|2-Hour Private Room",
         "飲み放題付き3時間|3 Hours with Free Drinks"], "ticket", (2000, 8000)),
    ("カラオケボックス", "ひとりカラオケ"): (
        ["ひとりカラオケ1時間|1-Hour Solo Karaoke", "ひとり3時間パック|3-Hour Solo Pack",
         "ひとり2時間パック|2-Hour Solo Pack"], "ticket", (500, 2500)),
    ("カラオケボックス", "フリータイム・深夜パック"): (
        ["フリータイム|Free Time Plan", "深夜パック|Late-Night Pack",
         "朝うたパック|Morning Pack"], "ticket", (1000, 3500)),
    ("カラオケボックス", "コラボ・アニメルーム"): (
        ["コラボルーム2時間|2-Hour Collab Room", "特典付きプラン|Plan with Bonus",
         "アニメルーム貸切|Private Anime Room"], "ticket", (1500, 5000)),

    ("スポーツジム・プール", "フィットネスジム"): (
        ["ビジター1回|1 Visitor Pass", "1日利用券|1-Day Pass",
         "回数券5回|5-Visit Pass"], "gym", (1500, 12000)),
    ("スポーツジム・プール", "24時間ジム"): (
        ["ビジター1回|1 Visitor Pass", "1週間パス|1-Week Pass",
         "1日利用券|1-Day Pass"], "gym", (1500, 8000)),
    ("スポーツジム・プール", "プール・スイミング"): (
        ["プール1回|1 Pool Visit", "1日券|1-Day Pass", "回数券5回|5-Visit Pass"],
        "gym", (800, 6000)),
    ("スポーツジム・プール", "ヨガ・ピラティス"): (
        ["体験レッスン|Trial Lesson", "レッスン1回|1 Lesson",
         "4回チケット|4-Lesson Ticket"], "gym", (1500, 12000)),
    ("スポーツジム・プール", "ボルダリング"): (
        ["1日利用|1-Day Pass", "ビジター1回|1 Visitor Pass",
         "体験コース|Trial Course"], "gym", (1800, 4500)),
    ("スポーツジム・プール", "ゴルフ練習場"): (
        ["1時間打ち放題|1-Hour Unlimited Balls", "ボール100球|100 Balls",
         "レッスン1回|1 Lesson"], "gym", (1000, 6000)),

    ("レンタカー", "コンパクトカー"): (
        ["6時間レンタル|6-Hour Rental", "24時間レンタル|24-Hour Rental",
         "12時間レンタル|12-Hour Rental"], "rental", (5000, 12000)),
    ("レンタカー", "普通車"): (
        ["6時間レンタル|6-Hour Rental", "24時間レンタル|24-Hour Rental",
         "12時間レンタル|12-Hour Rental"], "rental", (7000, 18000)),
    ("レンタカー", "ワンボックス（多人数）"): (
        ["24時間レンタル|24-Hour Rental", "12時間レンタル|12-Hour Rental",
         "週末プラン|Weekend Plan"], "rental", (12000, 30000)),
    ("レンタカー", "高級車・スポーツカー"): (
        ["6時間レンタル|6-Hour Rental", "24時間レンタル|24-Hour Rental",
         "ドライブプラン|Drive Plan"], "rental", (20000, 80000)),
    ("レンタカー", "EV"): (
        ["24時間レンタル|24-Hour Rental", "12時間レンタル|12-Hour Rental",
         "充電込みプラン|Plan with Charging"], "rental", (8000, 20000)),
    ("レンタカー", "カーシェアリング"): (
        ["15分利用|15-Min Use", "6時間パック|6-Hour Pack", "3時間パック|3-Hour Pack"],
        "rental", (300, 6000)),

    ("スパ", "天然温泉"): (
        ["入浴1名|1 Bath Entry", "入浴＆岩盤浴|Bath & Ganbanyoku",
         "貸切風呂|Private Bath"], "spa", (800, 3500)),
    ("スパ", "スーパー銭湯"): (
        ["入浴1名|1 Bath Entry", "入浴＆食事セット|Bath & Meal Set",
         "回数券5回|5-Visit Pass"], "spa", (600, 4500)),
    ("スパ", "サウナ"): (
        ["サウナ1回|1 Sauna Visit", "サウナ＆水風呂|Sauna & Cold Plunge",
         "3時間コース|3-Hour Course"], "spa", (1000, 4000)),
    ("スパ", "岩盤浴"): (
        ["岩盤浴60分|60-Min Ganbanyoku", "岩盤浴＆入浴|Ganbanyoku & Bath",
         "90分コース|90-Min Course"], "spa", (1200, 4000)),
    ("スパ", "個室・貸切風呂"): (
        ["貸切風呂60分|60-Min Private Bath", "貸切風呂90分|90-Min Private Bath",
         "個室プラン|Private Room Plan"], "spa", (3000, 12000)),
    ("スパ", "エステ"): (
        ["フェイシャル60分|60-Min Facial", "ボディエステ90分|90-Min Body Treatment",
         "体験コース|Trial Course"], "spa", (5000, 20000)),

    ("衣料品店", "ファストファッション"): (
        ["Tシャツ|T-Shirt", "デニムパンツ|Denim Jeans", "アウター|Outerwear",
         "ワンピース|Dress"], "retail", (1500, 8000)),
    ("衣料品店", "古着・ヴィンテージ"): (
        ["ヴィンテージシャツ|Vintage Shirt", "古着デニム|Used Denim",
         "ヴィンテージアウター|Vintage Outerwear", "古着スウェット|Used Sweatshirt"],
        "retail", (2500, 25000)),
    ("衣料品店", "ストリートファッション"): (
        ["グラフィックTシャツ|Graphic T-Shirt", "パーカー|Hoodie", "キャップ|Cap",
         "スケートデッキ|Skate Deck"], "retail", (3000, 18000)),
    ("衣料品店", "和装・着物"): (
        ["浴衣セット|Yukata Set", "帯|Obi", "着物一式|Full Kimono Set",
         "羽織|Haori"], "retail", (8000, 80000)),
    ("衣料品店", "スポーツウェア"): (
        ["トレーニングウェア|Training Wear", "ランニングシューズ|Running Shoes",
         "スポーツTシャツ|Sports T-Shirt", "ジャージ|Track Suit"],
        "retail", (3000, 20000)),
    ("衣料品店", "セレクトショップ"): (
        ["セレクトシャツ|Select Shirt", "ニット|Knitwear", "ジャケット|Jacket",
         "コート|Coat"], "retail", (6000, 40000)),
    ("衣料品店", "靴・スニーカー"): (
        ["スニーカー|Sneakers", "レザーシューズ|Leather Shoes", "サンダル|Sandals",
         "ブーツ|Boots"], "retail", (4000, 30000)),

    ("コンビニエンスストア", "弁当・おにぎり"): (
        ["幕の内弁当|Makunouchi Bento", "おにぎり3個セット|3 Onigiri Set",
         "から揚げ弁当|Karaage Bento", "サンドイッチ|Sandwich"], "conv", (350, 900)),
    ("コンビニエンスストア", "スイーツ・アイス"): (
        ["コンビニスイーツ|Convenience Store Sweets", "アイスクリーム|Ice Cream",
         "プリン|Pudding", "シュークリーム|Cream Puff"], "conv", (150, 600)),
    ("コンビニエンスストア", "ドリンク・酒類"): (
        ["缶ビール6本|6 Cans of Beer", "ペットボトル飲料|Bottled Drink",
         "缶チューハイ3本|3 Chuhai Cans", "日本酒カップ|Sake Cup"], "conv", (150, 1500)),
    ("コンビニエンスストア", "日用品・雑貨"): (
        ["日用品セット|Daily Goods Set", "文具セット|Stationery Set",
         "トラベルセット|Travel Kit", "モバイル充電器|Mobile Charger"],
        "conv", (300, 1500)),
    ("コンビニエンスストア", "チケット・各種サービス"): (
        ["チケット発券|Ticket Issue", "宅配便発送|Parcel Shipping",
         "コピーサービス|Copy Service", "プリントサービス|Print Service"],
        "conv", (200, 2000)),

    ("荷物預かりサービス", "コインロッカー"): (
        ["小サイズ1日|Small Locker 1 Day", "中サイズ1日|Medium Locker 1 Day",
         "大サイズ1日|Large Locker 1 Day"], "luggage", (400, 1000)),
    ("荷物預かりサービス", "有人預かりカウンター"): (
        ["1個1日|1 Bag per Day", "2個1日|2 Bags per Day",
         "大型1個1日|1 Large Bag per Day"], "luggage", (500, 1500)),
    ("荷物預かりサービス", "宿泊先への当日配送"): (
        ["1個配送|1 Bag Delivery", "2個配送|2 Bags Delivery",
         "大型1個配送|1 Large Bag Delivery"], "luggage", (1500, 4000)),
    ("荷物預かりサービス", "空港への配送"): (
        ["羽田空港配送|Haneda Airport Delivery", "成田空港配送|Narita Airport Delivery",
         "1個配送|1 Bag Delivery"], "luggage", (2000, 5000)),
    ("荷物預かりサービス", "大型・特大荷物対応"): (
        ["大型1個1日|1 Large Bag per Day", "特大1個1日|1 Oversized Bag per Day",
         "スキー・ゴルフバッグ|Ski/Golf Bag"], "luggage", (800, 2500)),
}


# --- hard price ceilings (tax-exclusive JPY) ----------------------------------
# A modifier's multiplier is normally allowed to carry a price past its band's
# upper bound — a 全部のせ ramen *should* cost more than the ordinary range. These
# sub-categories are the exception: the ceiling is part of what the shop IS, so
# the final price is clamped instead.
PRICE_CAP: dict[tuple[str, str], int] = {
    ("ディスカウントストア", "100円ショップ"): 500,
}


def _split(entry: str) -> tuple[str, str, float]:
    parts = entry.split("|")
    return parts[0], parts[1], float(parts[2]) if len(parts) > 2 else 1.0


def make_product(rng, category: str, subcategory: str, mod_probability: float = 0.75):
    """Return (japanese_name, english_name, price_multiplier)."""
    items, pool, _band = PRODUCTS[(category, subcategory)]
    ja, en, mult = _split(rng.choice(items))
    if pool and rng.random() < mod_probability:
        m_ja, m_en, m_mult = _split(rng.choice(MOD_POOLS[pool]))
        ja, en, mult = f"{m_ja}{ja}", f"{m_en} {en}", mult * m_mult
    return ja, en, mult


def price_band(category: str, subcategory: str) -> tuple[int, int]:
    return PRODUCTS[(category, subcategory)][2]


def price_cap(category: str, subcategory: str) -> int | None:
    """Hard tax-exclusive ceiling for this (category, subcategory), if any."""
    return PRICE_CAP.get((category, subcategory))


def variant_count(category: str, subcategory: str) -> int:
    """Distinct names this (category, subcategory) can produce."""
    items, pool, _ = PRODUCTS[(category, subcategory)]
    return len(items) * (1 + (len(MOD_POOLS[pool]) if pool else 0))
