"""Paired Japanese / English vocabulary for synthetic shop names.

The English name is a *parallel* name, not a transliteration of the Japanese one:
every vocabulary entry carries both forms, so no romanisation library is needed
and the two names always describe the same shop.

Keyed by (category, subcategory) because 「日用品・雑貨」 appears under both
ドラッグストア and コンビニエンスストア.
"""
from __future__ import annotations

# (category, subcategory) -> (Japanese shop word, English shop word)
SHOP_WORD: dict[tuple[str, str], tuple[str, str]] = {
    ("レストラン", "寿司・海鮮"): ("鮨", "Sushi"),
    ("レストラン", "ラーメン"): ("ラーメン", "Ramen"),
    ("レストラン", "焼肉・ホルモン"): ("焼肉", "Yakiniku"),
    ("レストラン", "天ぷら・とんかつ"): ("天ぷら", "Tempura"),
    ("レストラン", "そば・うどん"): ("そば", "Soba"),
    ("レストラン", "お好み焼き・もんじゃ焼き"): ("お好み焼き", "Okonomiyaki"),
    ("レストラン", "イタリア料理"): ("イタリアン", "Italian"),
    ("レストラン", "インド料理"): ("インド料理", "Indian"),
    ("レストラン", "韓国料理"): ("韓国料理", "Korean"),
    ("レストラン", "中華料理"): ("中華", "Chinese"),

    ("ファストフード", "ハンバーガー"): ("バーガー", "Burger"),
    ("ファストフード", "牛丼"): ("牛丼", "Gyudon"),
    ("ファストフード", "カレー"): ("カレー", "Curry"),
    ("ファストフード", "立ち食いそば"): ("立ち食いそば", "Standing Soba"),
    ("ファストフード", "フライドチキン"): ("チキン", "Chicken"),
    ("ファストフード", "サンドイッチ・ベーカリー"): ("ベーカリー", "Bakery"),

    ("コーヒーショップ", "チェーンカフェ"): ("カフェ", "Cafe"),
    ("コーヒーショップ", "自家焙煎コーヒー"): ("焙煎所", "Roastery"),
    ("コーヒーショップ", "純喫茶"): ("喫茶", "Kissa"),
    ("コーヒーショップ", "タピオカ・ドリンクスタンド"): ("タピオカ", "Tapioca"),
    ("コーヒーショップ", "テーマカフェ（アニメ・動物）"): ("テーマカフェ", "Theme Cafe"),

    ("スイーツショップ", "和菓子"): ("和菓子", "Wagashi"),
    ("スイーツショップ", "洋菓子・ケーキ"): ("洋菓子", "Patisserie"),
    ("スイーツショップ", "クレープ・パンケーキ"): ("クレープ", "Crepe"),
    ("スイーツショップ", "ソフトクリーム・アイス"): ("アイス", "Ice Cream"),
    ("スイーツショップ", "チョコレート専門店"): ("ショコラ", "Chocolat"),
    ("スイーツショップ", "たい焼き・どら焼き"): ("たい焼き", "Taiyaki"),

    ("バー", "居酒屋"): ("居酒屋", "Izakaya"),
    ("バー", "立ち飲み屋"): ("立ち飲み", "Standing Bar"),
    ("バー", "日本酒バー"): ("酒処", "Sake Bar"),
    ("バー", "クラフトビール・ビアバー"): ("ビア", "Beer"),
    ("バー", "ウイスキー・カクテルバー"): ("バー", "Bar"),
    ("バー", "ワインバー"): ("ワイン", "Wine"),
    ("バー", "スポーツバー"): ("スポーツバー", "Sports Bar"),

    ("ドラッグストア", "医薬品・常備薬"): ("薬局", "Pharmacy"),
    ("ドラッグストア", "化粧品・スキンケア"): ("コスメ", "Cosme"),
    ("ドラッグストア", "ヘアケア・ボディケア"): ("ヘアケア", "Hair Care"),
    ("ドラッグストア", "サプリメント・健康食品"): ("サプリ", "Supplement"),
    ("ドラッグストア", "ベビー用品"): ("ベビー", "Baby"),
    ("ドラッグストア", "日用品・雑貨"): ("ドラッグ", "Drug"),

    ("ディスカウントストア", "総合ディスカウント"): ("ディスカウント", "Discount"),
    ("ディスカウントストア", "100円ショップ"): ("100円ショップ", "100 Yen Shop"),
    ("ディスカウントストア", "免税専門店"): ("免税店", "Duty Free"),
    ("ディスカウントストア", "アウトレット"): ("アウトレット", "Outlet"),
    ("ディスカウントストア", "生活雑貨"): ("雑貨", "Zakka"),

    ("美容院", "カット・カラー"): ("ヘアサロン", "Hair Salon"),
    ("美容院", "ヘッドスパ"): ("ヘッドスパ", "Head Spa"),
    ("美容院", "ネイルサロン"): ("ネイル", "Nail"),
    ("美容院", "まつげエクステ"): ("アイラッシュ", "Eyelash"),
    ("美容院", "着付け・ヘアセット"): ("着付け", "Kimono Dressing"),

    ("マッサージ店", "整体・カイロプラクティック"): ("整体", "Seitai"),
    ("マッサージ店", "リフレクソロジー（足つぼ）"): ("足つぼ", "Reflexology"),
    ("マッサージ店", "タイ古式マッサージ"): ("タイ古式", "Thai Massage"),
    ("マッサージ店", "あん摩・指圧"): ("指圧", "Shiatsu"),
    ("マッサージ店", "クイックマッサージ"): ("クイックマッサージ", "Quick Massage"),
    ("マッサージ店", "ドライヘッドスパ"): ("ドライヘッドスパ", "Dry Head Spa"),

    ("家電量販店", "カメラ・レンズ"): ("カメラ", "Camera"),
    ("家電量販店", "オーディオ・イヤホン"): ("オーディオ", "Audio"),
    ("家電量販店", "美容家電"): ("美容家電", "Beauty Appliance"),
    ("家電量販店", "調理家電"): ("調理家電", "Kitchen Appliance"),
    ("家電量販店", "PC・スマホ周辺機器"): ("PC", "PC"),
    ("家電量販店", "ゲーム機・ソフト"): ("ゲーム", "Game"),

    ("音楽・映像・ゲーム店", "CD・レコード"): ("レコード", "Records"),
    ("音楽・映像・ゲーム店", "楽器"): ("楽器", "Instruments"),
    ("音楽・映像・ゲーム店", "中古ゲーム・レトロゲーム"): ("レトロゲーム", "Retro Game"),
    ("音楽・映像・ゲーム店", "アニメ・キャラクターグッズ"): ("アニメ", "Anime"),
    ("音楽・映像・ゲーム店", "トレーディングカード"): ("トレカ", "Trading Card"),
    ("音楽・映像・ゲーム店", "フィギュア・ホビー"): ("ホビー", "Hobby"),

    ("書店", "大型書店"): ("書店", "Books"),
    ("書店", "古書店"): ("古書", "Antiquarian"),
    ("書店", "漫画・コミック"): ("コミック", "Comics"),
    ("書店", "洋書・多言語書籍"): ("洋書", "Foreign Books"),
    ("書店", "アート・写真集"): ("アートブック", "Art Books"),

    ("映画館", "シネマコンプレックス"): ("シネマ", "Cinema"),
    ("映画館", "ミニシアター・単館系"): ("ミニシアター", "Mini Theater"),
    ("映画館", "IMAX・4DX"): ("IMAX", "IMAX"),
    ("映画館", "アニメ映画上映"): ("アニメシアター", "Anime Theater"),

    ("カラオケボックス", "一般カラオケボックス"): ("カラオケ", "Karaoke"),
    ("カラオケボックス", "パーティールーム"): ("パーティールーム", "Party Room"),
    ("カラオケボックス", "ひとりカラオケ"): ("ひとりカラオケ", "Solo Karaoke"),
    ("カラオケボックス", "フリータイム・深夜パック"): ("カラオケ", "Karaoke"),
    ("カラオケボックス", "コラボ・アニメルーム"): ("アニメカラオケ", "Anime Karaoke"),

    ("スポーツジム・プール", "フィットネスジム"): ("フィットネス", "Fitness"),
    ("スポーツジム・プール", "24時間ジム"): ("24時間ジム", "24H Gym"),
    ("スポーツジム・プール", "プール・スイミング"): ("スイミング", "Swimming"),
    ("スポーツジム・プール", "ヨガ・ピラティス"): ("ヨガ", "Yoga"),
    ("スポーツジム・プール", "ボルダリング"): ("ボルダリング", "Bouldering"),
    ("スポーツジム・プール", "ゴルフ練習場"): ("ゴルフ", "Golf"),

    ("レンタカー", "コンパクトカー"): ("レンタカー", "Rent-a-Car"),
    ("レンタカー", "普通車"): ("レンタカー", "Rent-a-Car"),
    ("レンタカー", "ワンボックス（多人数）"): ("レンタカー", "Rent-a-Car"),
    ("レンタカー", "高級車・スポーツカー"): ("プレミアムレンタカー", "Premium Rent-a-Car"),
    ("レンタカー", "EV"): ("EVレンタカー", "EV Rent-a-Car"),
    ("レンタカー", "カーシェアリング"): ("カーシェア", "Car Share"),

    ("スパ", "天然温泉"): ("温泉", "Onsen"),
    ("スパ", "スーパー銭湯"): ("銭湯", "Sento"),
    ("スパ", "サウナ"): ("サウナ", "Sauna"),
    ("スパ", "岩盤浴"): ("岩盤浴", "Ganbanyoku"),
    ("スパ", "個室・貸切風呂"): ("貸切風呂", "Private Bath"),
    ("スパ", "エステ"): ("エステ", "Esthetic"),

    ("衣料品店", "ファストファッション"): ("ファッション", "Fashion"),
    ("衣料品店", "古着・ヴィンテージ"): ("古着", "Vintage"),
    ("衣料品店", "ストリートファッション"): ("ストリート", "Street"),
    ("衣料品店", "和装・着物"): ("呉服", "Kimono"),
    ("衣料品店", "スポーツウェア"): ("スポーツ", "Sports"),
    ("衣料品店", "セレクトショップ"): ("セレクト", "Select"),
    ("衣料品店", "靴・スニーカー"): ("シューズ", "Shoes"),

    ("コンビニエンスストア", "弁当・おにぎり"): ("コンビニ", "Convenience"),
    ("コンビニエンスストア", "スイーツ・アイス"): ("コンビニ", "Convenience"),
    ("コンビニエンスストア", "ドリンク・酒類"): ("コンビニ", "Convenience"),
    ("コンビニエンスストア", "日用品・雑貨"): ("コンビニ", "Convenience"),
    ("コンビニエンスストア", "チケット・各種サービス"): ("コンビニ", "Convenience"),

    ("荷物預かりサービス", "コインロッカー"): ("コインロッカー", "Coin Locker"),
    ("荷物預かりサービス", "有人預かりカウンター"): ("手荷物預かり", "Luggage Storage"),
    ("荷物預かりサービス", "宿泊先への当日配送"): ("荷物配送", "Luggage Delivery"),
    ("荷物預かりサービス", "空港への配送"): ("空港配送", "Airport Delivery"),
    ("荷物預かりサービス", "大型・特大荷物対応"): ("大型荷物預かり", "Large Luggage"),
}

# 屋号 (trade name) pool -- (Japanese, English).
YAGO: list[tuple[str, str]] = [
    ("さくら", "Sakura"), ("ふじ", "Fuji"), ("大和", "Yamato"), ("松", "Matsu"),
    ("竹", "Take"), ("梅", "Ume"), ("葵", "Aoi"), ("椿", "Tsubaki"),
    ("すみれ", "Sumire"), ("もみじ", "Momiji"), ("光", "Hikari"), ("陽", "Hinata"),
    ("星", "Hoshi"), ("月", "Tsuki"), ("川", "Kawa"), ("山", "Yama"),
    ("海", "Umi"), ("空", "Sora"), ("森", "Mori"), ("太郎", "Taro"),
    ("花子", "Hanako"), ("源", "Minamoto"), ("武蔵", "Musashi"), ("江戸", "Edo"),
    ("雅", "Miyabi"), ("粋", "Iki"), ("福", "Fuku"), ("吉", "Kichi"),
    ("寿", "Kotobuki"), ("千代", "Chiyo"), ("八千代", "Yachiyo"), ("朝日", "Asahi"),
    ("夕日", "Yuhi"), ("白樺", "Shirakaba"), ("欅", "Keyaki"), ("楓", "Kaede"),
    ("菊", "Kiku"), ("蓮", "Hasu"), ("鶴", "Tsuru"), ("亀", "Kame"),
    ("龍", "Ryu"), ("虎", "Tora"), ("鳳", "Ho"), ("七福", "Shichifuku"),
    ("宝", "Takara"), ("絆", "Kizuna"), ("和", "Nagomi"), ("雫", "Shizuku"),
    ("茜", "Akane"), ("結", "Yui"),
]

# Ward -> English, for the branch-suffix pattern.
WARD_EN = {
    "千代田区": "Chiyoda", "中央区": "Chuo", "新宿区": "Shinjuku",
    "台東区": "Taito", "港区": "Minato", "渋谷区": "Shibuya",
}

# (Japanese pattern, English pattern). Same index is used for both so the two
# names stay structurally parallel.
PATTERNS: list[tuple[str, str]] = [
    ("{w}{y}", "{Y} {W}"),
    ("{y}{w}", "{Y} {W}"),
    ("{w} {y}", "{W} {Y}"),
    ("{y}{w} {ward}店", "{Y} {W} {Ward}"),
    ("{w} {y} {ward}店", "{W} {Y} {Ward}"),
]


def make_name(rng, category: str, subcategory: str, ward: str) -> tuple[str, str]:
    """Return (japanese_name, english_name) for one shop."""
    w, w_en = SHOP_WORD[(category, subcategory)]
    y, y_en = rng.choice(YAGO)
    ja_pat, en_pat = rng.choice(PATTERNS)
    ja = ja_pat.format(w=w, y=y, ward=ward.removesuffix("区"))
    en = en_pat.format(W=w_en, Y=y_en, Ward=WARD_EN[ward])
    return ja, en
