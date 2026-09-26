from __future__ import annotations

import re

from .config import TextConfig


ASS_TAG_RE = re.compile(r"\{[^{}]*\}")
HTML_TAG_RE = re.compile(r"<[^>]+>")
KANA_RE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
SIMPLIFIED_CJK_RE = re.compile(
    "["
    "\u4eec\u8fd9\u4e3a\u4e2a\u65f6\u8bf4\u6ca1\u5bf9\u4ece\u8fd8"
    "\u8fc7\u540e\u53d1\u6837\u73b0\u5b9e\u5173\u6218\u573a\u673a"
    "\u672f\u6784\u89c9\u8ba9\u7ed9\u7ecf\u4e49\u6c14\u513f\u4e1c"
    "\u65e0\u590d\u542c\u89c1\u95f4\u95ee\u95e8\u8bdd\u8bed\u8bfb"
    "\u5199\u4e66\u7231\u5904\u957f\u52a1\u52a8\u52bf\u533b\u53d8"
    "\u8fb9\u8fbe\u8fdb\u8fdc\u9009\u96be\u79bb\u5f00\u4e48\u53ea"
    "]"
)

FULLWIDTH_ASCII_TABLE = str.maketrans(
    {
        **{chr(code): chr(code - 0xFEE0) for code in range(0xFF10, 0xFF1A)},
        **{chr(code): chr(code - 0xFEE0) for code in range(0xFF21, 0xFF3B)},
        **{chr(code): chr(code - 0xFEE0) for code in range(0xFF41, 0xFF5B)},
        "\u3000": " ",
    }
)

JAPANESE_VARIANT_TABLE = str.maketrans(
    {
        "\u4e1a": "\u696d",
        "\u4e1c": "\u6771",
        "\u4e24": "\u4e21",
        "\u4e25": "\u53b3",
        "\u4e3a": "\u70ba",
        "\u4e3d": "\u9e97",
        "\u4e49": "\u7fa9",
        "\u4e50": "\u697d",
        "\u4e60": "\u7fd2",
        "\u4e61": "\u90f7",
        "\u4e66": "\u66f8",
        "\u4e70": "\u8cb7",
        "\u4e9a": "\u4e9c",
        "\u4ea7": "\u7523",
        "\u4eb2": "\u89aa",
        "\u4ebf": "\u5104",
        "\u4ece": "\u5f93",
        "\u4ed3": "\u5009",
        "\u4eea": "\u5100",
        "\u4ef7": "\u4fa1",
        "\u4f17": "\u8846",
        "\u4f18": "\u512a",
        "\u4f20": "\u4f1d",
        "\u4f24": "\u50b7",
        "\u4f26": "\u502b",
        "\u4f2a": "\u507d",
        "\u4fa7": "\u5074",
        "\u503a": "\u50b5",
        "\u503e": "\u50be",
        "\u513f": "\u5150",
        "\u5170": "\u862d",
        "\u5173": "\u95a2",
        "\u5174": "\u8208",
        "\u517b": "\u990a",
        "\u517d": "\u7363",
        "\u518c": "\u518a",
        "\u519b": "\u8ecd",
        "\u519c": "\u8fb2",
        "\u51b3": "\u6c7a",
        "\u51b5": "\u6cc1",
        "\u51bb": "\u51cd",
        "\u51cf": "\u6e1b",
        "\u51fb": "\u6483",
        "\u5219": "\u5247",
        "\u521a": "\u525b",
        "\u521b": "\u5275",
        "\u522b": "\u5225",
        "\u5242": "\u5264",
        "\u5251": "\u5263",
        "\u5267": "\u5287",
        "\u529d": "\u52e7",
        "\u52a1": "\u52d9",
        "\u52a8": "\u52d5",
        "\u52b3": "\u52b4",
        "\u52bf": "\u52e2",
        "\u52cb": "\u52f2",
        "\u534f": "\u5354",
        "\u5355": "\u5358",
        "\u5356": "\u58f2",
        "\u536b": "\u885b",
        "\u5385": "\u5e81",
        "\u5386": "\u6b74",
        "\u538b": "\u5727",
        "\u53bf": "\u770c",
        "\u53d1": "\u767a",
        "\u53d8": "\u5909",
        "\u540e": "\u5f8c",
        "\u542f": "\u5553",
        "\u5458": "\u54e1",
        "\u54cd": "\u97ff",
        "\u5524": "\u559a",
        "\u56ed": "\u5712",
        "\u56f4": "\u56f2",
        "\u56fe": "\u56f3",
        "\u5706": "\u5186",
        "\u5723": "\u8056",
        "\u573a": "\u5834",
        "\u575a": "\u5805",
        "\u575b": "\u58c7",
        "\u5757": "\u584a",
        "\u5760": "\u589c",
        "\u5792": "\u5841",
        "\u57ab": "\u588a",
        "\u58f3": "\u6bbb",
        "\u5904": "\u51e6",
        "\u5907": "\u5099",
        "\u590d": "\u5fa9",
        "\u5934": "\u982d",
        "\u593a": "\u596a",
        "\u5987": "\u5a66",
        "\u5a31": "\u5a2f",
        "\u5b81": "\u5be7",
        "\u5b9e": "\u5b9f",
        "\u5ba1": "\u5be9",
        "\u5bab": "\u5bae",
        "\u5bbd": "\u5bdb",
        "\u5bf9": "\u5bfe",
        "\u5bfb": "\u5c0b",
        "\u5bfc": "\u5c0e",
        "\u5c1d": "\u5617",
        "\u5c42": "\u5c64",
        "\u5c81": "\u6b73",
        "\u5c9b": "\u5cf6",
        "\u5e01": "\u5e63",
        "\u5e08": "\u5e2b",
        "\u5e26": "\u5e2f",
        "\u5e7f": "\u5e83",
        "\u5e86": "\u6176",
        "\u5e93": "\u5eab",
        "\u5e94": "\u5fdc",
        "\u5e99": "\u5edf",
        "\u5e9f": "\u5ec3",
        "\u5f00": "\u958b",
        "\u5f02": "\u7570",
        "\u5f03": "\u68c4",
        "\u5f20": "\u5f35",
        "\u5f39": "\u5f3e",
        "\u5f3a": "\u5f37",
        "\u5f52": "\u5e30",
        "\u5f7b": "\u5fb9",
        "\u5fc6": "\u61b6",
        "\u5fe7": "\u6182",
        "\u6000": "\u61d0",
        "\u6001": "\u614b",
        "\u603b": "\u7dcf",
        "\u6076": "\u60aa",
        "\u607c": "\u60a9",
        "\u60ac": "\u61f8",
        "\u60ef": "\u6163",
        "\u6124": "\u61a4",
        "\u613f": "\u9858",
        "\u6218": "\u6226",
        "\u6237": "\u6238",
        "\u6267": "\u57f7",
        "\u6269": "\u62e1",
        "\u626b": "\u6383",
        "\u626c": "\u63da",
        "\u6270": "\u64fe",
        "\u629a": "\u64ab",
        "\u62a4": "\u8b77",
        "\u62a5": "\u5831",
        "\u62df": "\u64ec",
        "\u62e5": "\u64c1",
        "\u62e9": "\u629e",
        "\u6325": "\u63ee",
        "\u635f": "\u640d",
        "\u6362": "\u63db",
        "\u636e": "\u62e0",
        "\u6447": "\u63fa",
        "\u654c": "\u6575",
        "\u658b": "\u658e",
        "\u65a9": "\u65ac",
        "\u65e0": "\u7121",
        "\u65f6": "\u6642",
        "\u663e": "\u9865",
        "\u6653": "\u6681",
        "\u6682": "\u66ab",
        "\u672f": "\u8853",
        "\u6742": "\u96d1",
        "\u6743": "\u6a29",
        "\u6768": "\u694a",
        "\u6781": "\u6975",
        "\u6784": "\u69cb",
        "\u67ab": "\u6953",
        "\u6807": "\u6a19",
        "\u6808": "\u685f",
        "\u680b": "\u68df",
        "\u680f": "\u6b04",
        "\u6811": "\u6a39",
        "\u6837": "\u69d8",
        "\u6865": "\u6a4b",
        "\u68a6": "\u5922",
        "\u68c0": "\u691c",
        "\u6a31": "\u685c",
        "\u6b22": "\u6b53",
        "\u6bd5": "\u7562",
        "\u6c14": "\u6c17",
        "\u6c49": "\u6f22",
        "\u6c64": "\u6e6f",
        "\u6c9f": "\u6e9d",
        "\u6cf7": "\u6edd",
        "\u6cfd": "\u6ca2",
        "\u6d01": "\u6f54",
        "\u6d4b": "\u6e2c",
        "\u6d4e": "\u6e08",
        "\u6d53": "\u6fc3",
        "\u6da6": "\u6f64",
        "\u6da8": "\u6f32",
        "\u6e0a": "\u6df5",
        "\u6e10": "\u6f38",
        "\u6e14": "\u6f01",
        "\u6e83": "\u6f70",
        "\u6ee1": "\u6e80",
        "\u6ee4": "\u6ffe",
        "\u6ee5": "\u6feb",
        "\u6ee8": "\u6d5c",
        "\u6ee9": "\u7058",
        "\u6fd1": "\u702c",
        "\u706d": "\u6ec5",
        "\u7075": "\u970a",
        "\u707e": "\u707d",
        "\u70e7": "\u713c",
        "\u70ed": "\u71b1",
        "\u7231": "\u611b",
        "\u7237": "\u723a",
        "\u7275": "\u727d",
        "\u72b9": "\u7336",
        "\u72f1": "\u7344",
        "\u730e": "\u731f",
        "\u73af": "\u74b0",
        "\u73b0": "\u73fe",
        "\u7535": "\u96fb",
        "\u7545": "\u66a2",
        "\u7597": "\u7642",
        "\u75af": "\u760b",
        "\u76d1": "\u76e3",
        "\u76d8": "\u76e4",
        "\u77eb": "\u77ef",
        "\u77ff": "\u9271",
        "\u7801": "\u78bc",
        "\u7816": "\u78da",
        "\u786e": "\u78ba",
        "\u788d": "\u7919",
        "\u7978": "\u798d",
        "\u79bb": "\u96e2",
        "\u79ef": "\u7a4d",
        "\u7a33": "\u7a4f",
        "\u7a77": "\u7aae",
        "\u7ade": "\u7af6",
        "\u7b14": "\u7b46",
        "\u7b80": "\u7c21",
        "\u7c7b": "\u985e",
        "\u7cae": "\u7ce7",
        "\u7ea0": "\u7cfe",
        "\u7ea2": "\u7d05",
        "\u7ea6": "\u7d04",
        "\u7ea7": "\u7d1a",
        "\u7eaa": "\u7d00",
        "\u7eaf": "\u7d14",
        "\u7eb2": "\u7db1",
        "\u7eb3": "\u7d0d",
        "\u7eb5": "\u7e26",
        "\u7eb7": "\u7d1b",
        "\u7eb8": "\u7d19",
        "\u7ebf": "\u7dda",
        "\u7ec3": "\u7df4",
        "\u7ec4": "\u7d44",
        "\u7ec6": "\u7d30",
        "\u7ec7": "\u7e54",
        "\u7ec8": "\u7d42",
        "\u7ecd": "\u7d39",
        "\u7ecf": "\u7d4c",
        "\u7ed3": "\u7d50",
        "\u7ed8": "\u7d75",
        "\u7ed9": "\u7d66",
        "\u7edd": "\u7d76",
        "\u7edf": "\u7d71",
        "\u7ee7": "\u7d99",
        "\u7ee9": "\u7e3e",
        "\u7eed": "\u7d9a",
        "\u7ef4": "\u7dad",
        "\u7ef5": "\u7dbf",
        "\u7efc": "\u7dcf",
        "\u7eff": "\u7dd1",
        "\u7f13": "\u7de9",
        "\u7f16": "\u7de8",
        "\u7f18": "\u7e01",
        "\u7f29": "\u7e2e",
        "\u7f51": "\u7db2",
        "\u7f57": "\u7f85",
        "\u7f5a": "\u7f70",
        "\u8038": "\u8073",
        "\u803b": "\u6065",
        "\u804c": "\u8077",
        "\u8054": "\u806f",
        "\u806a": "\u8061",
        "\u8083": "\u7c9b",
        "\u80a0": "\u8178",
        "\u80a4": "\u819a",
        "\u80be": "\u814e",
        "\u80bf": "\u816b",
        "\u80c0": "\u8139",
        "\u80c1": "\u8107",
        "\u80dc": "\u52dd",
        "\u80f6": "\u81a0",
        "\u8109": "\u8108",
        "\u810f": "\u81d3",
        "\u8111": "\u8133",
        "\u817e": "\u9a30",
        "\u8230": "\u8266",
        "\u8270": "\u8271",
        "\u8273": "\u8276",
        "\u827a": "\u82b8",
        "\u82cf": "\u8607",
        "\u8350": "\u85a6",
        "\u836f": "\u85ac",
        "\u83b2": "\u84ee",
        "\u83b7": "\u7372",
        "\u8425": "\u55b6",
        "\u8427": "\u856d",
        "\u8428": "\u85a9",
        "\u84dd": "\u85cd",
        "\u8537": "\u8594",
        "\u867d": "\u96d6",
        "\u867e": "\u8766",
        "\u8680": "\u8755",
        "\u8681": "\u87fb",
        "\u8717": "\u8778",
        "\u8865": "\u88dc",
        "\u88ad": "\u8972",
        "\u89c1": "\u898b",
        "\u89c2": "\u89b3",
        "\u89c4": "\u898f",
        "\u89c6": "\u8996",
        "\u89c8": "\u89a7",
        "\u89c9": "\u899a",
        "\u8ba1": "\u8a08",
        "\u8ba4": "\u8a8d",
        "\u8ba8": "\u8a0e",
        "\u8ba9": "\u8b72",
        "\u8bad": "\u8a13",
        "\u8bae": "\u8b70",
        "\u8baf": "\u8a0a",
        "\u8bb0": "\u8a18",
        "\u8bb2": "\u8b1b",
        "\u8bb8": "\u8a31",
        "\u8bba": "\u8ad6",
        "\u8bbe": "\u8a2d",
        "\u8bbf": "\u8a2a",
        "\u8bc1": "\u8a3c",
        "\u8bc4": "\u8a55",
        "\u8bc6": "\u8b58",
        "\u8bc9": "\u8a34",
        "\u8bcd": "\u8a5e",
        "\u8bd1": "\u8a33",
        "\u8bd5": "\u8a66",
        "\u8bd7": "\u8a69",
        "\u8bda": "\u8aa0",
        "\u8bdd": "\u8a71",
        "\u8be5": "\u8a72",
        "\u8be6": "\u8a73",
        "\u8bed": "\u8a9e",
        "\u8bef": "\u8aa4",
        "\u8bf4": "\u8aac",
        "\u8bf7": "\u8acb",
        "\u8bf8": "\u8af8",
        "\u8bfa": "\u8afe",
        "\u8bfb": "\u8aad",
        "\u8bfe": "\u8ab2",
        "\u8c03": "\u8abf",
        "\u8c08": "\u8ac7",
        "\u8c22": "\u8b1d",
        "\u8c26": "\u8b19",
        "\u8c31": "\u8b5c",
        "\u8d1d": "\u8c9d",
        "\u8d1f": "\u8ca0",
        "\u8d22": "\u8ca1",
        "\u8d23": "\u8cac",
        "\u8d24": "\u8ce2",
        "\u8d25": "\u6557",
        "\u8d27": "\u8ca8",
        "\u8d28": "\u8cea",
        "\u8d29": "\u8ca9",
        "\u8d2a": "\u8caa",
        "\u8d2b": "\u8ca7",
        "\u8d2d": "\u8cfc",
        "\u8d2e": "\u8caf",
        "\u8d2f": "\u8cab",
        "\u8d34": "\u8cbc",
        "\u8d35": "\u8cb4",
        "\u8d37": "\u8cb8",
        "\u8d38": "\u8cbf",
        "\u8d39": "\u8cbb",
        "\u8d3a": "\u8cc0",
        "\u8d44": "\u8cc7",
        "\u8d4b": "\u8ce6",
        "\u8d4c": "\u8ced",
        "\u8d4f": "\u8cde",
        "\u8d54": "\u8ce0",
        "\u8d56": "\u983c",
        "\u8d5e": "\u8cdb",
        "\u8d60": "\u8d08",
        "\u8d75": "\u8d99",
        "\u8d8b": "\u8da8",
        "\u8dc3": "\u8e8d",
        "\u8f66": "\u8eca",
        "\u8f68": "\u8ecc",
        "\u8f6c": "\u8ee2",
        "\u8f6e": "\u8f2a",
        "\u8f6f": "\u8edf",
        "\u8f70": "\u8f5f",
        "\u8f74": "\u8ef8",
        "\u8f7b": "\u8efd",
        "\u8f7d": "\u8f09",
        "\u8f83": "\u8f03",
        "\u8f85": "\u8f14",
        "\u8f88": "\u8f29",
        "\u8f89": "\u8f1d",
        "\u8f91": "\u8f2f",
        "\u8f93": "\u8f38",
        "\u8f96": "\u8f44",
        "\u8f99": "\u8f4d",
        "\u8fb9": "\u8fba",
        "\u8fbe": "\u9054",
        "\u8fc1": "\u9077",
        "\u8fc7": "\u904e",
        "\u8fd0": "\u904b",
        "\u8fd8": "\u9084",
        "\u8fdb": "\u9032",
        "\u8fdc": "\u9060",
        "\u8fdd": "\u9055",
        "\u8fde": "\u9023",
        "\u8fdf": "\u9045",
        "\u8ff9": "\u8de1",
        "\u9002": "\u9069",
        "\u9009": "\u9078",
        "\u900a": "\u905c",
        "\u9012": "\u9013",
        "\u9057": "\u907a",
        "\u90bb": "\u96a3",
        "\u9171": "\u91a4",
        "\u917f": "\u91b8",
        "\u91ca": "\u91c8",
        "\u949f": "\u9418",
        "\u94a2": "\u92fc",
        "\u94c1": "\u9244",
        "\u94dc": "\u9285",
        "\u94ed": "\u9298",
        "\u94f6": "\u9280",
        "\u9510": "\u92ed",
        "\u9519": "\u932f",
        "\u9526": "\u9326",
        "\u952e": "\u9375",
        "\u9547": "\u93ae",
        "\u955c": "\u93e1",
        "\u957f": "\u9577",
        "\u95e8": "\u9580",
        "\u95ea": "\u9583",
        "\u95ed": "\u9589",
        "\u95ee": "\u554f",
        "\u95f4": "\u9593",
        "\u95fb": "\u805e",
        "\u9605": "\u95b2",
        "\u9601": "\u95a3",
        "\u961f": "\u968a",
        "\u9633": "\u967d",
        "\u9634": "\u9670",
        "\u9635": "\u9663",
        "\u9636": "\u968e",
        "\u9645": "\u969b",
        "\u9646": "\u9678",
        "\u9648": "\u9673",
        "\u9669": "\u967a",
        "\u9690": "\u96a0",
        "\u96be": "\u96e3",
        "\u96fe": "\u9727",
        "\u97f5": "\u97fb",
        "\u9875": "\u9801",
        "\u9876": "\u9802",
        "\u9879": "\u9805",
        "\u987a": "\u9806",
        "\u987b": "\u9808",
        "\u987e": "\u9867",
        "\u987f": "\u9813",
        "\u9886": "\u9818",
        "\u9891": "\u983b",
        "\u9898": "\u984c",
        "\u989c": "\u9854",
        "\u989d": "\u984d",
        "\u98ce": "\u98a8",
        "\u98de": "\u98db",
        "\u996d": "\u98ef",
        "\u996e": "\u98f2",
        "\u9970": "\u98fe",
        "\u9971": "\u98fd",
        "\u9972": "\u98fc",
        "\u9a6c": "\u99ac",
        "\u9a71": "\u99c6",
        "\u9a76": "\u99db",
        "\u9a7b": "\u99d0",
        "\u9a7e": "\u99d5",
        "\u9a7f": "\u99c5",
        "\u9a8c": "\u9a13",
        "\u9a91": "\u9a0e",
        "\u9a97": "\u9a19",
        "\u9a9a": "\u9a12",
        "\u9c7c": "\u9b5a",
        "\u9c9c": "\u9bae",
        "\u9cb8": "\u9be8",
        "\u9cde": "\u9c57",
        "\u9e1f": "\u9ce5",
        "\u9e21": "\u9d8f",
        "\u9e23": "\u9cf4",
        "\u9e2d": "\u9d28",
        "\u9e45": "\u9d5e",
        "\u9e64": "\u9db4",
        "\u9e70": "\u9df9",
        "\u9f50": "\u6589",
        "\u9f7f": "\u6b6f",
        "\u9f84": "\u9f62",
        "\u9f99": "\u7adc",
    }
)


JAPANESE_CONTEXT_REPLACEMENTS = {
    "\u673a\u95a2": "\u6a5f\u95a2",
    "\u673a\u4f1a": "\u6a5f\u4f1a",
    "\u673a\u68b0": "\u6a5f\u68b0",
    "\u673a\u80fd": "\u6a5f\u80fd",
    "\u673a\u69cb": "\u6a5f\u69cb",
    "\u5371\u673a": "\u5371\u6a5f",
    "\u5951\u673a": "\u5951\u6a5f",
}
def collapse_progressive_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        line = line.strip()
        key = _dedupe_key(line)
        if line and key and key not in seen:
            seen.add(key)
            unique.append(line)

    if len(unique) < 3:
        return unique

    keys = [_dedupe_key(line) for line in unique]
    result: list[str] = []
    for index, line in enumerate(unique):
        key = keys[index]
        is_progressive_fragment = any(
            other_index != index
            and key
            and key in other_key
            and len(other_key) > len(key)
            for other_index, other_key in enumerate(keys)
        )
        if not is_progressive_fragment:
            result.append(line)
    return result


def _dedupe_key(value: str) -> str:
    return re.sub(r"\s+", "", value)


def clean_subtitle(text: str | None) -> str:
    if not text:
        return ""

    cleaned = str(text)
    cleaned = cleaned.replace("\\N", "\n").replace("\\n", "\n")
    cleaned = ASS_TAG_RE.sub("", cleaned)
    cleaned = HTML_TAG_RE.sub("", cleaned)
    cleaned = cleaned.replace("\u200b", "").replace("\ufeff", "")

    lines = []
    for line in cleaned.splitlines():
        stripped = re.sub(r"\s+", " ", line).strip()
        if stripped:
            lines.append(stripped)

    return "\n".join(collapse_progressive_lines(_dedupe_adjacent(lines)))


def normalize_japanese_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = str(text).translate(FULLWIDTH_ASCII_TABLE)
    normalized = normalized.translate(JAPANESE_VARIANT_TABLE)
    for source, target in JAPANESE_CONTEXT_REPLACEMENTS.items():
        normalized = normalized.replace(source, target)
    return re.sub(r"[ \t]+", " ", normalized).strip()


def split_bilingual(
    primary: str | None,
    secondary: str | None = None,
    config: TextConfig | None = None,
) -> tuple[str, str]:
    cfg = config or TextConfig()
    primary_clean = clean_subtitle(primary)
    secondary_clean = clean_subtitle(secondary)
    lines = [line for line in primary_clean.splitlines() if line.strip()]
    explicit_split_modes = {
        "first_japanese",
        "japanese_first",
        "first_chinese",
        "chinese_first",
    }

    if secondary_clean and secondary_clean != primary_clean:
        language_split = None
        if len(lines) > 1 and cfg.split_mode in explicit_split_modes:
            primary_has_japanese = any(_line_language(line) == "japanese" for line in lines)
            if primary_has_japanese:
                language_split = _split_lines_by_language(lines)
        if language_split:
            return language_split

        if cfg.primary_subtitle_language.lower() in {"chinese", "zh", "cn"}:
            return secondary_clean, primary_clean
        return primary_clean, secondary_clean

    if len(lines) > 1 and cfg.split_mode in explicit_split_modes:
        language_split = _split_lines_by_language(lines)
        if language_split:
            return language_split
        if cfg.split_mode in {"first_japanese", "japanese_first"}:
            return lines[0], "\n".join(lines[1:])
        return "\n".join(lines[1:]), lines[0]

    if not lines:
        return "", ""
    if len(lines) == 1:
        return lines[0], ""

    language_split = _split_lines_by_language(lines)
    if language_split:
        return language_split

    if cfg.japanese_first:
        return lines[0], "\n".join(lines[1:])

    return "\n".join(lines[1:]), lines[0]


def _split_lines_by_language(lines: list[str]) -> tuple[str, str] | None:
    languages = [_line_language(line) for line in lines]
    japanese_lines = [line for line, language in zip(lines, languages) if language == "japanese"]
    chinese_lines = [line for line, language in zip(lines, languages) if language == "chinese"]
    unknown_lines = [line for line, language in zip(lines, languages) if language is None]

    if japanese_lines and chinese_lines:
        return _join_lines(japanese_lines), _join_lines(chinese_lines)

    if japanese_lines and unknown_lines and all(_looks_cjk(line) for line in unknown_lines):
        return _join_lines(japanese_lines), _join_lines(unknown_lines)

    if len(lines) == 2 and len(unknown_lines) == 1:
        if japanese_lines:
            return _join_lines(japanese_lines), unknown_lines[0]
        if chinese_lines:
            return unknown_lines[0], _join_lines(chinese_lines)

    return None


def _join_lines(lines: list[str]) -> str:
    return "\n".join(collapse_progressive_lines(lines))


def _line_language(line: str) -> str | None:
    if _looks_japanese(line):
        return "japanese"
    if _looks_chinese(line):
        return "chinese"
    return None


def _looks_japanese(line: str) -> bool:
    return bool(KANA_RE.search(line))


def _looks_chinese(line: str) -> bool:
    return bool(SIMPLIFIED_CJK_RE.search(line))


def _looks_cjk(line: str) -> bool:
    return bool(CJK_RE.search(line))


def _dedupe_adjacent(lines: list[str]) -> list[str]:
    deduped: list[str] = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return deduped