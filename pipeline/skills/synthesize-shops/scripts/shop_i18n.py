"""English translations for the synthetic shop table.

Holds the parallel-English side of the four localised columns written by
``synthesize_shops.py``:

  * ``category_en``    -- ``CATEGORY_EN``   (one per category)
  * ``subcategory_en`` -- ``SUBCATEGORY_EN`` (keyed by (category, subcategory),
                          because 「日用品・雑貨」 / 「スイーツ・アイス」 recur)
  * ``address_en``     -- ``romanise_address`` + the ``CHO_EN`` 町丁 romaji table
  * ``description_en`` -- ``make_description`` (feature blurb + traveller perk)

Everything here is static data plus pure functions, so the synthesis stays
reproducible and needs no romanisation library at runtime. The 町丁 romaji were
generated once with pykakasi and then hand-corrected — many central-Tokyo place
names have irregular readings a converter gets wrong (三ノ輪=Minowa not "Sannowa",
千駄ケ谷=Sendagaya, 白金=Shirokane, 本町=Honmachi, 神田神保町=Kanda-Jimbocho).
"""
from __future__ import annotations

import re

# --- category -------------------------------------------------------------
CATEGORY_EN: dict[str, str] = {
    "レストラン": "Restaurant",
    "ファストフード": "Fast Food",
    "コーヒーショップ": "Coffee Shop",
    "スイーツショップ": "Sweets Shop",
    "バー": "Bar",
    "ドラッグストア": "Drugstore",
    "ディスカウントストア": "Discount Store",
    "美容院": "Beauty Salon",
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

# --- (category, subcategory) -> English label ------------------------------
SUBCATEGORY_EN: dict[tuple[str, str], str] = {
    ("レストラン", "寿司・海鮮"): "Sushi & Seafood",
    ("レストラン", "ラーメン"): "Ramen",
    ("レストラン", "焼肉・ホルモン"): "Yakiniku & Horumon",
    ("レストラン", "天ぷら・とんかつ"): "Tempura & Tonkatsu",
    ("レストラン", "そば・うどん"): "Soba & Udon",
    ("レストラン", "お好み焼き・もんじゃ焼き"): "Okonomiyaki & Monjayaki",
    ("レストラン", "イタリア料理"): "Italian Cuisine",
    ("レストラン", "インド料理"): "Indian Cuisine",
    ("レストラン", "韓国料理"): "Korean Cuisine",
    ("レストラン", "中華料理"): "Chinese Cuisine",

    ("ファストフード", "ハンバーガー"): "Hamburgers",
    ("ファストフード", "牛丼"): "Gyudon (Beef Bowl)",
    ("ファストフード", "カレー"): "Curry",
    ("ファストフード", "立ち食いそば"): "Standing Soba",
    ("ファストフード", "フライドチキン"): "Fried Chicken",
    ("ファストフード", "サンドイッチ・ベーカリー"): "Sandwiches & Bakery",

    ("コーヒーショップ", "チェーンカフェ"): "Chain Cafe",
    ("コーヒーショップ", "自家焙煎コーヒー"): "House-Roasted Coffee",
    ("コーヒーショップ", "純喫茶"): "Retro Kissaten",
    ("コーヒーショップ", "タピオカ・ドリンクスタンド"): "Bubble Tea & Drink Stand",
    ("コーヒーショップ", "テーマカフェ（アニメ・動物）"): "Theme Cafe (Anime & Animals)",

    ("スイーツショップ", "和菓子"): "Wagashi (Japanese Sweets)",
    ("スイーツショップ", "洋菓子・ケーキ"): "Cakes & Pastries",
    ("スイーツショップ", "クレープ・パンケーキ"): "Crepes & Pancakes",
    ("スイーツショップ", "ソフトクリーム・アイス"): "Soft Serve & Ice Cream",
    ("スイーツショップ", "チョコレート専門店"): "Chocolate Specialist",
    ("スイーツショップ", "たい焼き・どら焼き"): "Taiyaki & Dorayaki",

    ("バー", "居酒屋"): "Izakaya",
    ("バー", "立ち飲み屋"): "Standing Bar",
    ("バー", "日本酒バー"): "Sake Bar",
    ("バー", "クラフトビール・ビアバー"): "Craft Beer & Beer Bar",
    ("バー", "ウイスキー・カクテルバー"): "Whisky & Cocktail Bar",
    ("バー", "ワインバー"): "Wine Bar",
    ("バー", "スポーツバー"): "Sports Bar",

    ("ドラッグストア", "医薬品・常備薬"): "Medicine & Remedies",
    ("ドラッグストア", "化粧品・スキンケア"): "Cosmetics & Skincare",
    ("ドラッグストア", "ヘアケア・ボディケア"): "Hair & Body Care",
    ("ドラッグストア", "サプリメント・健康食品"): "Supplements & Health Foods",
    ("ドラッグストア", "ベビー用品"): "Baby Products",
    ("ドラッグストア", "日用品・雑貨"): "Daily Goods & Sundries",

    ("ディスカウントストア", "総合ディスカウント"): "General Discount",
    ("ディスカウントストア", "100円ショップ"): "100-Yen Shop",
    ("ディスカウントストア", "免税専門店"): "Duty-Free Store",
    ("ディスカウントストア", "アウトレット"): "Outlet",
    ("ディスカウントストア", "生活雑貨"): "Household Goods",

    ("美容院", "カット・カラー"): "Cut & Color",
    ("美容院", "ヘッドスパ"): "Head Spa",
    ("美容院", "ネイルサロン"): "Nail Salon",
    ("美容院", "まつげエクステ"): "Eyelash Extensions",
    ("美容院", "着付け・ヘアセット"): "Kimono Dressing & Hair Styling",

    ("マッサージ店", "整体・カイロプラクティック"): "Seitai & Chiropractic",
    ("マッサージ店", "リフレクソロジー（足つぼ）"): "Reflexology (Foot Massage)",
    ("マッサージ店", "タイ古式マッサージ"): "Thai Massage",
    ("マッサージ店", "あん摩・指圧"): "Anma & Shiatsu",
    ("マッサージ店", "クイックマッサージ"): "Quick Massage",
    ("マッサージ店", "ドライヘッドスパ"): "Dry Head Spa",

    ("家電量販店", "カメラ・レンズ"): "Cameras & Lenses",
    ("家電量販店", "オーディオ・イヤホン"): "Audio & Earphones",
    ("家電量販店", "美容家電"): "Beauty Appliances",
    ("家電量販店", "調理家電"): "Kitchen Appliances",
    ("家電量販店", "PC・スマホ周辺機器"): "PC & Phone Accessories",
    ("家電量販店", "ゲーム機・ソフト"): "Game Consoles & Software",

    ("音楽・映像・ゲーム店", "CD・レコード"): "CDs & Records",
    ("音楽・映像・ゲーム店", "楽器"): "Musical Instruments",
    ("音楽・映像・ゲーム店", "中古ゲーム・レトロゲーム"): "Used & Retro Games",
    ("音楽・映像・ゲーム店", "アニメ・キャラクターグッズ"): "Anime & Character Goods",
    ("音楽・映像・ゲーム店", "トレーディングカード"): "Trading Cards",
    ("音楽・映像・ゲーム店", "フィギュア・ホビー"): "Figures & Hobby",

    ("書店", "大型書店"): "Large Bookstore",
    ("書店", "古書店"): "Antiquarian Books",
    ("書店", "漫画・コミック"): "Manga & Comics",
    ("書店", "洋書・多言語書籍"): "Foreign & Multilingual Books",
    ("書店", "アート・写真集"): "Art & Photography Books",

    ("映画館", "シネマコンプレックス"): "Multiplex Cinema",
    ("映画館", "ミニシアター・単館系"): "Art-House Cinema",
    ("映画館", "IMAX・4DX"): "IMAX & 4DX",
    ("映画館", "アニメ映画上映"): "Anime Screenings",

    ("カラオケボックス", "一般カラオケボックス"): "Standard Karaoke Box",
    ("カラオケボックス", "パーティールーム"): "Party Room",
    ("カラオケボックス", "ひとりカラオケ"): "Solo Karaoke",
    ("カラオケボックス", "フリータイム・深夜パック"): "Free-Time & Late-Night Pack",
    ("カラオケボックス", "コラボ・アニメルーム"): "Collab & Anime Room",

    ("スポーツジム・プール", "フィットネスジム"): "Fitness Gym",
    ("スポーツジム・プール", "24時間ジム"): "24-Hour Gym",
    ("スポーツジム・プール", "プール・スイミング"): "Pool & Swimming",
    ("スポーツジム・プール", "ヨガ・ピラティス"): "Yoga & Pilates",
    ("スポーツジム・プール", "ボルダリング"): "Bouldering",
    ("スポーツジム・プール", "ゴルフ練習場"): "Golf Range",

    ("レンタカー", "コンパクトカー"): "Compact Car",
    ("レンタカー", "普通車"): "Standard Car",
    ("レンタカー", "ワンボックス（多人数）"): "Minivan (Large Group)",
    ("レンタカー", "高級車・スポーツカー"): "Luxury & Sports Car",
    ("レンタカー", "EV"): "Electric Vehicle",
    ("レンタカー", "カーシェアリング"): "Car Sharing",

    ("スパ", "天然温泉"): "Natural Hot Spring",
    ("スパ", "スーパー銭湯"): "Super Sento Bathhouse",
    ("スパ", "サウナ"): "Sauna",
    ("スパ", "岩盤浴"): "Ganbanyoku (Stone Sauna)",
    ("スパ", "個室・貸切風呂"): "Private Bath",
    ("スパ", "エステ"): "Esthetic Spa",

    ("衣料品店", "ファストファッション"): "Fast Fashion",
    ("衣料品店", "古着・ヴィンテージ"): "Vintage & Secondhand",
    ("衣料品店", "ストリートファッション"): "Streetwear",
    ("衣料品店", "和装・着物"): "Kimono & Traditional Wear",
    ("衣料品店", "スポーツウェア"): "Sportswear",
    ("衣料品店", "セレクトショップ"): "Select Shop",
    ("衣料品店", "靴・スニーカー"): "Shoes & Sneakers",

    ("コンビニエンスストア", "弁当・おにぎり"): "Bento & Onigiri",
    ("コンビニエンスストア", "スイーツ・アイス"): "Sweets & Ice Cream",
    ("コンビニエンスストア", "ドリンク・酒類"): "Drinks & Alcohol",
    ("コンビニエンスストア", "日用品・雑貨"): "Daily Goods & Sundries",
    ("コンビニエンスストア", "チケット・各種サービス"): "Tickets & Services",

    ("荷物預かりサービス", "コインロッカー"): "Coin Lockers",
    ("荷物預かりサービス", "有人預かりカウンター"): "Staffed Luggage Counter",
    ("荷物預かりサービス", "宿泊先への当日配送"): "Same-Day Hotel Delivery",
    ("荷物預かりサービス", "空港への配送"): "Airport Delivery",
    ("荷物預かりサービス", "大型・特大荷物対応"): "Oversized Luggage",
}

# --- 町丁 (chome-stripped S_NAME) -> map-style romaji ----------------------
# Hyphens follow common English/Google-Maps style (Nihombashi-Kayabacho,
# Kanda-Jimbocho, Azabu-Juban); long vowels are written short.
CHO_EN: dict[str, str] = {
    "一ツ橋": "Hitotsubashi", "一番町": "Ichibancho", "三ノ輪": "Minowa",
    "三崎町": "Misakicho", "三田": "Mita", "三番町": "Sanbancho", "三筋": "Misuji",
    "上原": "Uehara", "上落合": "Kami-Ochiai", "上野": "Ueno",
    "上野公園": "Ueno-Koen", "上野桜木": "Ueno-Sakuragi",
    "下宮比町": "Shimomiyabicho", "下落合": "Shimo-Ochiai", "下谷": "Shitaya",
    "中井": "Nakai", "中町": "Nakamachi", "中落合": "Naka-Ochiai",
    "中里町": "Nakazatocho", "丸の内": "Marunouchi", "九段北": "Kudan-Kita",
    "九段南": "Kudan-Minami", "二十騎町": "Nijikkimachi", "二番町": "Nibancho",
    "五番町": "Gobancho", "京橋": "Kyobashi", "今戸": "Imado", "代々木": "Yoyogi",
    "代々木神園町": "Yoyogi-Kamizonocho", "代官山町": "Daikanyamacho",
    "佃": "Tsukuda", "住吉町": "Sumiyoshicho", "余丁町": "Yochomachi",
    "信濃町": "Shinanomachi", "元代々木町": "Moto-Yoyogicho",
    "元浅草": "Moto-Asakusa", "元赤坂": "Moto-Akasaka", "元麻布": "Moto-Azabu",
    "入船": "Irifune", "入谷": "Iriya", "八丁堀": "Hatchobori", "八重洲": "Yaesu",
    "六本木": "Roppongi", "六番町": "Rokubancho", "内幸町": "Uchisaiwaicho",
    "内神田": "Uchi-Kanda", "内藤町": "Naitomachi", "円山町": "Maruyamacho",
    "初台": "Hatsudai", "勝どき": "Kachidoki", "北の丸公園": "Kitanomaru-Koen",
    "北上野": "Kita-Ueno", "北山伏町": "Kita-Yamabushicho",
    "北新宿": "Kita-Shinjuku", "北町": "Kitamachi", "北青山": "Kita-Aoyama",
    "千代田": "Chiyoda", "千束": "Senzoku", "千駄ケ谷": "Sendagaya",
    "南元町": "Minami-Motomachi", "南山伏町": "Minami-Yamabushicho",
    "南平台町": "Nampeidaicho", "南榎町": "Minami-Enokicho", "南町": "Minamimachi",
    "南青山": "Minami-Aoyama", "南麻布": "Minami-Azabu", "原町": "Haramachi",
    "台場": "Daiba", "台東": "Taito", "喜久井町": "Kikuicho",
    "四番町": "Yonbancho", "四谷": "Yotsuya", "四谷三栄町": "Yotsuya-San'eicho",
    "四谷坂町": "Yotsuya-Sakamachi", "四谷本塩町": "Yotsuya-Honshiocho",
    "外神田": "Soto-Kanda", "大久保": "Okubo", "大京町": "Daikyocho",
    "大山町": "Oyamacho", "大手町": "Otemachi", "天神町": "Tenjincho",
    "宇田川町": "Udagawacho", "富ケ谷": "Tomigaya", "富久町": "Tomihisacho",
    "富士見": "Fujimi", "寿": "Kotobuki", "小島": "Kojima", "山吹町": "Yamabukicho",
    "岩戸町": "Iwatocho", "岩本町": "Iwamotocho", "左門町": "Samoncho",
    "市谷仲之町": "Ichigaya-Nakanocho", "市谷八幡町": "Ichigaya-Hachimancho",
    "市谷加賀町": "Ichigaya-Kagacho", "市谷台町": "Ichigaya-Daimachi",
    "市谷山伏町": "Ichigaya-Yamabushicho", "市谷左内町": "Ichigaya-Sanaicho",
    "市谷本村町": "Ichigaya-Hommuracho", "市谷柳町": "Ichigaya-Yanagicho",
    "市谷田町": "Ichigaya-Tamachi", "市谷甲良町": "Ichigaya-Koracho",
    "市谷砂土原町": "Ichigaya-Sadoharacho", "市谷船河原町": "Ichigaya-Funagawaracho",
    "市谷薬王寺町": "Ichigaya-Yakuojicho", "市谷長延寺町": "Ichigaya-Choenjicho",
    "市谷鷹匠町": "Ichigaya-Takajomachi", "幡ケ谷": "Hatagaya",
    "平河町": "Hirakawacho", "広尾": "Hiroo", "弁天町": "Bentencho",
    "恵比寿": "Ebisu", "恵比寿南": "Ebisu-Minami", "恵比寿西": "Ebisu-Nishi",
    "愛住町": "Aizumicho", "愛宕": "Atago", "戸塚町": "Totsukamachi",
    "戸山": "Toyama", "払方町": "Haraikatamachi", "揚場町": "Agebacho",
    "改代町": "Kaitaicho", "新宿": "Shinjuku", "新富": "Shintomi",
    "新小川町": "Shin-Ogawamachi", "新川": "Shinkawa", "新橋": "Shimbashi",
    "日本堤": "Nihonzutsumi", "日本橋": "Nihombashi",
    "日本橋中洲": "Nihombashi-Nakasu", "日本橋久松町": "Nihombashi-Hisamatsucho",
    "日本橋人形町": "Nihombashi-Ningyocho", "日本橋兜町": "Nihombashi-Kabutocho",
    "日本橋堀留町": "Nihombashi-Horidomecho", "日本橋大伝馬町": "Nihombashi-Odenmacho",
    "日本橋室町": "Nihombashi-Muromachi", "日本橋富沢町": "Nihombashi-Tomizawacho",
    "日本橋小伝馬町": "Nihombashi-Kodenmacho", "日本橋小網町": "Nihombashi-Koamicho",
    "日本橋小舟町": "Nihombashi-Kobunacho", "日本橋本町": "Nihombashi-Honcho",
    "日本橋本石町": "Nihombashi-Hongokucho", "日本橋横山町": "Nihombashi-Yokoyamacho",
    "日本橋浜町": "Nihombashi-Hamacho", "日本橋箱崎町": "Nihombashi-Hakozakicho",
    "日本橋茅場町": "Nihombashi-Kayabacho", "日本橋蛎殻町": "Nihombashi-Kakigaracho",
    "日本橋馬喰町": "Nihombashi-Bakurocho", "日比谷公園": "Hibiya-Koen",
    "早稲田南町": "Waseda-Minamicho", "早稲田町": "Wasedamachi",
    "早稲田鶴巻町": "Waseda-Tsurumakicho", "明石町": "Akashicho", "晴海": "Harumi",
    "月島": "Tsukishima", "有楽町": "Yurakucho", "本町": "Honmachi", "東": "Higashi",
    "東上野": "Higashi-Ueno", "東五軒町": "Higashi-Gokencho",
    "東新橋": "Higashi-Shimbashi", "東日本橋": "Higashi-Nihombashi",
    "東榎町": "Higashi-Enokicho", "東浅草": "Higashi-Asakusa",
    "東神田": "Higashi-Kanda", "東麻布": "Higashi-Azabu", "松が谷": "Matsugaya",
    "松涛": "Shoto", "柳橋": "Yanagibashi", "根岸": "Negishi",
    "桜丘町": "Sakuragaokacho", "榎町": "Enokicho", "横寺町": "Yokoteramachi",
    "橋場": "Hashiba", "歌舞伎町": "Kabukicho", "水道町": "Suidocho",
    "永田町": "Nagatacho", "池之端": "Ikenohata", "河田町": "Kawadacho",
    "津久戸町": "Tsukudocho", "浅草": "Asakusa", "浅草橋": "Asakusabashi",
    "浜松町": "Hamamatsucho", "浜離宮庭園": "Hamarikyu-Teien", "海岸": "Kaigan",
    "清川": "Kiyokawa", "渋谷": "Shibuya", "港南": "Konan", "湊": "Minato",
    "片町": "Katamachi", "猿楽町": "Sarugakucho", "白金": "Shirokane",
    "白金台": "Shirokanedai", "白銀町": "Hakugincho", "百人町": "Hyakunincho",
    "皇居外苑": "Kokyo-Gaien", "矢来町": "Yaraicho", "神南": "Jinnan",
    "神宮前": "Jingumae", "神山町": "Kamiyamacho", "神楽坂": "Kagurazaka",
    "神楽河岸": "Kagura-Gashi", "神泉町": "Shinsencho",
    "神田佐久間河岸": "Kanda-Sakumagashi", "神田佐久間町": "Kanda-Sakumacho",
    "神田北乗物町": "Kanda-Kitanorimonocho", "神田司町": "Kanda-Tsukasacho",
    "神田和泉町": "Kanda-Izumicho", "神田多町": "Kanda-Tacho",
    "神田富山町": "Kanda-Tomiyamacho", "神田小川町": "Kanda-Ogawamachi",
    "神田岩本町": "Kanda-Iwamotocho", "神田平河町": "Kanda-Hirakawacho",
    "神田東松下町": "Kanda-Higashimatsushitacho", "神田東紺屋町": "Kanda-Higashikonyacho",
    "神田松永町": "Kanda-Matsunagacho", "神田淡路町": "Kanda-Awajicho",
    "神田相生町": "Kanda-Aioicho", "神田神保町": "Kanda-Jimbocho",
    "神田紺屋町": "Kanda-Konyacho", "神田練塀町": "Kanda-Neribeicho",
    "神田美倉町": "Kanda-Mikuracho", "神田美土代町": "Kanda-Mitoshirocho",
    "神田花岡町": "Kanda-Hanaokacho", "神田西福田町": "Kanda-Nishifukudacho",
    "神田錦町": "Kanda-Nishikicho", "神田鍛冶町": "Kanda-Kajicho",
    "神田須田町": "Kanda-Sudacho", "神田駿河台": "Kanda-Surugadai",
    "秋葉原": "Akihabara", "竜泉": "Ryusen", "笹塚": "Sasazuka",
    "筑土八幡町": "Tsukudo-Hachimancho", "箪笥町": "Tansumachi", "築地": "Tsukiji",
    "築地町": "Tsukijimachi", "紀尾井町": "Kioicho", "納戸町": "Nandomachi",
    "細工町": "Saikumachi", "舟町": "Funamachi", "芝": "Shiba",
    "芝公園": "Shiba-Koen", "芝大門": "Shiba-Daimon", "芝浦": "Shibaura",
    "花川戸": "Hanakawado", "若宮町": "Wakamiyacho", "若松町": "Wakamatsucho",
    "若葉": "Wakaba", "荒木町": "Arakicho", "蔵前": "Kuramae",
    "虎ノ門": "Toranomon", "袋町": "Fukuromachi", "西五軒町": "Nishi-Gokencho",
    "西原": "Nishihara", "西新宿": "Nishi-Shinjuku", "西新橋": "Nishi-Shimbashi",
    "西早稲田": "Nishi-Waseda", "西浅草": "Nishi-Asakusa", "西神田": "Nishi-Kanda",
    "西落合": "Nishi-Ochiai", "西麻布": "Nishi-Azabu", "谷中": "Yanaka",
    "豊海町": "Toyomicho", "赤坂": "Akasaka", "赤城下町": "Akagishitamachi",
    "赤城元町": "Akagimotomachi", "道玄坂": "Dogenzaka", "鉢山町": "Hachiyamacho",
    "銀座": "Ginza", "鍛冶町": "Kajicho", "隼町": "Hayabusacho",
    "雷門": "Kaminarimon", "霞が関": "Kasumigaseki", "霞ヶ丘町": "Kasumigaokamachi",
    "須賀町": "Sugacho", "飯田橋": "Iidabashi", "馬場下町": "Babashitacho",
    "駒形": "Komagata", "高田馬場": "Takadanobaba", "高輪": "Takanawa",
    "鳥越": "Torigoe", "鴬谷町": "Uguisudanicho", "麹町": "Kojimachi",
    "麻布十番": "Azabu-Juban", "麻布台": "Azabudai", "麻布永坂町": "Azabu-Nagasakacho",
    "麻布狸穴町": "Azabu-Mamianacho",
}

# --- address romanisation -------------------------------------------------
_WARD_EN = {
    "千代田区": "Chiyoda", "中央区": "Chuo", "新宿区": "Shinjuku",
    "台東区": "Taito", "港区": "Minato", "渋谷区": "Shibuya",
}
_KANJI_DIGIT = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                "六": 6, "七": 7, "八": 8, "九": 9}
_CHOME_RE = re.compile(r"([一二三四五六七八九十]+)丁目$")


def _kanji_to_int(s: str) -> int:
    """Small 1–99 kanji-numeral parser — enough for any 丁目 number."""
    if "十" not in s:
        return _KANJI_DIGIT[s]
    tens, _, ones = s.partition("十")
    return (_KANJI_DIGIT[tens] if tens else 1) * 10 + (_KANJI_DIGIT[ones] if ones else 0)


def split_chome(s_name: str) -> tuple[str, int | None]:
    """(町丁 without 丁目, chome number or None) from a shapefile S_NAME."""
    if m := _CHOME_RE.search(s_name):
        return s_name[:m.start()], _kanji_to_int(m.group(1))
    return s_name, None


def romanise_address(ward: str, s_name: str, banchi: int, go: int) -> str:
    """English postal form, e.g. ``1-15-16 Hatchobori, Chuo-ku, Tokyo``.

    Mirrors the Japanese ``東京都<区><S_NAME><banchi>番<go>号``: the block number
    is ``chome-banchi-go`` (chome dropped where the 町丁 has none).
    """
    cho, chome = split_chome(s_name)
    cho_en = CHO_EN[cho]
    block = f"{chome}-{banchi}-{go}" if chome is not None else f"{banchi}-{go}"
    return f"{block} {cho_en}, {_WARD_EN[ward]}-ku, Tokyo"


# --- description ----------------------------------------------------------
# One traveller-facing feature blurb per (category, subcategory). Each ends with
# a period; ``make_description`` appends one perk from the category's group pool.
_DESC: dict[tuple[str, str], str] = {
    ("レストラン", "寿司・海鮮"): "Fresh sushi and seasonal seafood prepared at the counter.",
    ("レストラン", "ラーメン"): "Rich, steaming bowls of authentic Japanese ramen.",
    ("レストラン", "焼肉・ホルモン"): "Grill premium wagyu and beef right at your table.",
    ("レストラン", "天ぷら・とんかつ"): "Crispy tempura and golden tonkatsu fried to order.",
    ("レストラン", "そば・うどん"): "Handmade soba and udon noodles in savory broth.",
    ("レストラン", "お好み焼き・もんじゃ焼き"): "Cook savory okonomiyaki and monja on your own griddle.",
    ("レストラン", "イタリア料理"): "Pasta and pizza with a Japanese-Italian twist.",
    ("レストラン", "インド料理"): "Aromatic curries and fresh-baked naan.",
    ("レストラン", "韓国料理"): "Sizzling Korean BBQ and spicy classics.",
    ("レストラン", "中華料理"): "Hearty Chinese favorites from dim sum to noodles.",

    ("ファストフード", "ハンバーガー"): "Juicy burgers made fast, perfect on the go.",
    ("ファストフード", "牛丼"): "Warm beef bowls served in minutes for a cheap bite.",
    ("ファストフード", "カレー"): "Comforting Japanese curry over rice, ready fast.",
    ("ファストフード", "立ち食いそば"): "Quick standing-counter soba for a speedy meal.",
    ("ファストフード", "フライドチキン"): "Crispy fried chicken to grab and go.",
    ("ファストフード", "サンドイッチ・ベーカリー"): "Freshly baked breads and sandwiches all day.",

    ("コーヒーショップ", "チェーンカフェ"): "A reliable spot for coffee and free Wi-Fi.",
    ("コーヒーショップ", "自家焙煎コーヒー"): "Small-batch beans roasted in-house.",
    ("コーヒーショップ", "純喫茶"): "Old-school Showa-era charm and hand-drip coffee.",
    ("コーヒーショップ", "タピオカ・ドリンクスタンド"): "Bubble tea and fruit drinks made to order.",
    ("コーヒーショップ", "テーマカフェ（アニメ・動物）"): "A themed cafe full of anime and animal fun.",

    ("スイーツショップ", "和菓子"): "Delicate traditional Japanese sweets, beautifully crafted.",
    ("スイーツショップ", "洋菓子・ケーキ"): "Elegant cakes and Western-style pastries.",
    ("スイーツショップ", "クレープ・パンケーキ"): "Fluffy pancakes and stuffed crepes.",
    ("スイーツショップ", "ソフトクリーム・アイス"): "Creamy soft serve and gelato in seasonal flavors.",
    ("スイーツショップ", "チョコレート専門店"): "Artisan chocolates and handmade bonbons.",
    ("スイーツショップ", "たい焼き・どら焼き"): "Warm taiyaki and dorayaki filled with sweet bean paste.",

    ("バー", "居酒屋"): "A lively izakaya for drinks and small plates.",
    ("バー", "立ち飲み屋"): "A casual standing bar with cheap drinks and snacks.",
    ("バー", "日本酒バー"): "Sample regional sake flights from across Japan.",
    ("バー", "クラフトビール・ビアバー"): "Local craft beers on tap.",
    ("バー", "ウイスキー・カクテルバー"): "Japanese whisky and expertly mixed cocktails.",
    ("バー", "ワインバー"): "A cozy wine bar with curated pours.",
    ("バー", "スポーツバー"): "Catch the game with drinks and a big screen.",

    ("ドラッグストア", "医薬品・常備薬"): "Everyday medicines and travel health essentials.",
    ("ドラッグストア", "化粧品・スキンケア"): "Popular Japanese cosmetics and skincare.",
    ("ドラッグストア", "ヘアケア・ボディケア"): "Shampoos, lotions and body-care staples.",
    ("ドラッグストア", "サプリメント・健康食品"): "Vitamins, supplements and health foods.",
    ("ドラッグストア", "ベビー用品"): "Diapers, formula and baby-care basics.",
    ("ドラッグストア", "日用品・雑貨"): "Daily necessities and household sundries.",

    ("ディスカウントストア", "総合ディスカウント"): "Aisles of bargains from snacks to electronics.",
    ("ディスカウントストア", "100円ショップ"): "Handy goods and souvenirs, mostly 100 yen.",
    ("ディスカウントストア", "免税専門店"): "Tax-free deals on brands and souvenirs.",
    ("ディスカウントストア", "アウトレット"): "Brand-name goods at outlet prices.",
    ("ディスカウントストア", "生活雑貨"): "Affordable homeware and lifestyle goods.",

    ("美容院", "カット・カラー"): "Stylish cuts and color by skilled stylists.",
    ("美容院", "ヘッドスパ"): "A soothing head spa to refresh and relax.",
    ("美容院", "ネイルサロン"): "Custom nail art and gentle care.",
    ("美容院", "まつげエクステ"): "Natural-looking eyelash extensions.",
    ("美容院", "着付け・ヘアセット"): "Kimono dressing and hair styling for special days.",

    ("マッサージ店", "整体・カイロプラクティック"): "Body alignment and chiropractic relief.",
    ("マッサージ店", "リフレクソロジー（足つぼ）"): "Foot reflexology to revive tired feet.",
    ("マッサージ店", "タイ古式マッサージ"): "Traditional Thai stretching massage.",
    ("マッサージ店", "あん摩・指圧"): "Traditional anma and shiatsu pressure-point therapy.",
    ("マッサージ店", "クイックマッサージ"): "A quick massage to ease travel fatigue.",
    ("マッサージ店", "ドライヘッドスパ"): "A dry head spa for deep relaxation.",

    ("家電量販店", "カメラ・レンズ"): "Cameras, lenses and gear for every level.",
    ("家電量販店", "オーディオ・イヤホン"): "Headphones, earbuds and audio gear.",
    ("家電量販店", "美容家電"): "Hair dryers and beauty gadgets.",
    ("家電量販店", "調理家電"): "Rice cookers and handy kitchen appliances.",
    ("家電量販店", "PC・スマホ周辺機器"): "PC and smartphone accessories galore.",
    ("家電量販店", "ゲーム機・ソフト"): "Game consoles and the latest titles.",

    ("音楽・映像・ゲーム店", "CD・レコード"): "Crates of CDs and vinyl records to dig through.",
    ("音楽・映像・ゲーム店", "楽器"): "Guitars, keyboards and musical gear.",
    ("音楽・映像・ゲーム店", "中古ゲーム・レトロゲーム"): "Retro consoles and rare used games.",
    ("音楽・映像・ゲーム店", "アニメ・キャラクターグッズ"): "Anime merch and character goods.",
    ("音楽・映像・ゲーム店", "トレーディングカード"): "Trading cards, singles and booster packs.",
    ("音楽・映像・ゲーム店", "フィギュア・ホビー"): "Collectible figures and hobby kits.",

    ("書店", "大型書店"): "Floors of books across every genre.",
    ("書店", "古書店"): "Rare and secondhand books to browse.",
    ("書店", "漫画・コミック"): "Shelves of manga and comics.",
    ("書店", "洋書・多言語書籍"): "Foreign-language books and magazines.",
    ("書店", "アート・写真集"): "Art books and photography collections.",

    ("映画館", "シネマコンプレックス"): "A modern multiplex with the latest releases.",
    ("映画館", "ミニシアター・単館系"): "Indie and art-house films in an intimate theater.",
    ("映画館", "IMAX・4DX"): "Big-screen IMAX and motion 4DX experiences.",
    ("映画館", "アニメ映画上映"): "Anime films on the big screen.",

    ("カラオケボックス", "一般カラオケボックス"): "Private rooms to sing your heart out.",
    ("カラオケボックス", "パーティールーム"): "Spacious rooms built for group parties.",
    ("カラオケボックス", "ひとりカラオケ"): "Solo booths for singing alone in comfort.",
    ("カラオケボックス", "フリータイム・深夜パック"): "Free-time and late-night singing packages.",
    ("カラオケボックス", "コラボ・アニメルーム"): "Anime-themed collab rooms for fans.",

    ("スポーツジム・プール", "フィットネスジム"): "A full gym with machines and free weights.",
    ("スポーツジム・プール", "24時間ジム"): "Work out any hour, day or night.",
    ("スポーツジム・プール", "プール・スイミング"): "Lap pools and swimming for all levels.",
    ("スポーツジム・プール", "ヨガ・ピラティス"): "Yoga and pilates to stretch and unwind.",
    ("スポーツジム・プール", "ボルダリング"): "Climbing walls for every skill level.",
    ("スポーツジム・プール", "ゴルフ練習場"): "A driving range to practice your swing.",

    ("レンタカー", "コンパクトカー"): "Easy, economical compact cars to rent.",
    ("レンタカー", "普通車"): "Comfortable standard cars for city drives and road trips.",
    ("レンタカー", "ワンボックス（多人数）"): "Roomy minivans for groups and families.",
    ("レンタカー", "高級車・スポーツカー"): "Luxury and sports cars for a special drive.",
    ("レンタカー", "EV"): "Eco-friendly electric cars to rent.",
    ("レンタカー", "カーシェアリング"): "By-the-hour car sharing, booked from your phone.",

    ("スパ", "天然温泉"): "Soak in natural hot-spring baths.",
    ("スパ", "スーパー銭湯"): "A large public bathhouse with many baths.",
    ("スパ", "サウナ"): "Finnish-style sauna and cold plunge.",
    ("スパ", "岩盤浴"): "Warm stone-bed bathing to detox and relax.",
    ("スパ", "個室・貸切風呂"): "Private reserved baths for a quiet soak.",
    ("スパ", "エステ"): "Facials and body treatments to pamper yourself.",

    ("衣料品店", "ファストファッション"): "On-trend styles at friendly prices.",
    ("衣料品店", "古着・ヴィンテージ"): "Curated vintage and secondhand finds.",
    ("衣料品店", "ストリートファッション"): "Bold Tokyo streetwear and sneakers.",
    ("衣料品店", "和装・着物"): "Kimono and traditional Japanese wear.",
    ("衣料品店", "スポーツウェア"): "Activewear and sports gear.",
    ("衣料品店", "セレクトショップ"): "A hand-picked mix of fashion labels.",
    ("衣料品店", "靴・スニーカー"): "Sneakers and shoes for every style.",

    ("コンビニエンスストア", "弁当・おにぎり"): "Grab-and-go bento, onigiri and hot snacks.",
    ("コンビニエンスストア", "スイーツ・アイス"): "Convenience-store sweets and ice cream.",
    ("コンビニエンスストア", "ドリンク・酒類"): "Cold drinks, beer and spirits around the clock.",
    ("コンビニエンスストア", "日用品・雑貨"): "Everyday essentials, open 24 hours.",
    ("コンビニエンスストア", "チケット・各種サービス"): "Tickets, ATM and handy services in one stop.",

    ("荷物預かりサービス", "コインロッカー"): "Self-service lockers for your bags.",
    ("荷物預かりサービス", "有人預かりカウンター"): "A staffed counter to store luggage safely.",
    ("荷物預かりサービス", "宿泊先への当日配送"): "Same-day luggage delivery to your hotel.",
    ("荷物預かりサービス", "空港への配送"): "Send your bags ahead to the airport.",
    ("荷物預かりサービス", "大型・特大荷物対応"): "Storage for oversized and bulky luggage.",
}

# Each category belongs to one perk group; perks are short traveller-facing tags.
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
        "Show your XB coupon for a special deal.", "A short walk from the station.",
    ],
    "retail": [
        "Tax-free shopping with your passport.", "English-speaking staff on hand.",
        "Show your XB coupon to save.", "Popular with overseas visitors.",
    ],
    "wellness": [
        "Walk-ins welcome; English OK.", "Book easily with your XB coupon.",
        "A relaxing break from sightseeing.", "First-timers from abroad welcome.",
    ],
    "leisure": [
        "English guidance available.", "Show your XB coupon for a discount.",
        "Great for groups of travelers.", "Open late for night owls.",
    ],
    "service": [
        "Simple booking for visitors.", "English support available.",
        "Show your XB coupon to save.", "Handy for your Tokyo trip.",
    ],
}


def make_description(rng, category: str, subcategory: str) -> str:
    """A short EN blurb: subcategory feature sentence + one traveller perk.

    Uses its own ``rng`` (a ``random.Random``) so callers can keep it separate
    from the geography/name stream and leave those columns unchanged.
    """
    perk = rng.choice(_PERKS[_PERK_GROUP[category]])
    return f"{_DESC[(category, subcategory)]} {perk}"
