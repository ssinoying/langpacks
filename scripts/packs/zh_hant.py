"""HSK1 lesson packs for Traditional Chinese: the zh_hans lessons respelled in Taiwan standard forms.

Pinyin and Vietnamese stay the same; every string is converted with the explicit maps below (words first, then characters).
Adding a simplified character to zh_hans.py means adding it here too; the self-check at the bottom fails otherwise.
"""
import re

from packs import zh_hans

# One simplified form, several traditional ones: convert by word.
WORDS = {"老板": "老闆", "面条": "麵條", "周末": "週末"}

CHARS = dict(zip(
    "东两个么习书买亲们会儿内别剧务医厕号吗员园国场块妈学对岁师张时机条来样楼欢气汉没点热爱爷猫现电着礼红纪网脑节见视试话语请读课谢货贵车边还这进远钟钱问间题风飞饭饿后几干里听离痴",
    "東兩個麼習書買親們會兒內別劇務醫廁號嗎員園國場塊媽學對歲師張時機條來樣樓歡氣漢沒點熱愛爺貓現電著禮紅紀網腦節見視試話語請讀課謝貨貴車邊還這進遠鐘錢問間題風飛飯餓後幾幹裡聽離癡"))


def to_trad(text):
    for s, t in WORDS.items():
        text = text.replace(s, t)
    return "".join(CHARS.get(c, c) for c in text)


def convert(x):
    if isinstance(x, str):
        return to_trad(x)
    if isinstance(x, (list, tuple)):
        return type(x)(convert(v) for v in x)
    if isinstance(x, dict):
        return {k: convert(v) for k, v in x.items()}
    return x


PACKS = [{**convert(spec), "id": spec["id"].replace("zh-hans-", "zh-hant-")} for spec in zh_hans.PACKS]

# Simplified characters that are not map keys would slip through silently; these appear in the source but are fine as is.
_SAME = set("一七三上下不中九也了二五京人什今他以件住作你便候做元八公六再冬冷出分到剁加北十午半去友口只叫可右吃同吧呢和哥哪唱商啊喂喜喝四在坐"
            "夏外多夜大天太女奶她好妹姐姨子季孩宅宜客家小少就工左常年床店弟影往很忙怎您想我房所手打拜教新旁日早明星春昨是晚最月有朋服期"
            "末本李杯板林果校桌歌死每比水河油洗渣渴溜火父爸牛王玩班球生男百的直看真秋站等米美老考茶菜行衣西要走起跟路迎追那阿院雨霸非面首周")
_unknown = {c for c in re.findall(r"[㐀-鿿]", repr(zh_hans.PACKS)) if c not in CHARS and c not in _SAME}
assert not _unknown, f"add to CHARS or _SAME in zh_hant.py: {''.join(sorted(_unknown))}"
_left = {c for c in re.findall(r"[㐀-鿿]", repr(PACKS)) if c in CHARS}
assert not _left, f"simplified left in zh_hant: {''.join(sorted(_left))}"
