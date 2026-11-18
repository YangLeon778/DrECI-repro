"""解析工具：把模型自由文本解析成 Yes / No / 解析失败。

原仓库 core.py 的解析存在明显缺陷（只匹配 `{"Answer":"No"}`），因此这里实现
分层解析，并显式区分「解析失败」，便于单独计数。
"""

import json
import re

_ESC = lambda s: s.replace('\\"', '"').replace("\\n", "\n")


def _norm(text):
    t = _ESC(text or "")
    # 原仓库提示词中的 JSON 花括号经 f-string 转义后变成 {{ }}，模型会原样模仿；
    # 先折叠重复花括号，避免解析器漏判
    t = re.sub(r"\{(?=\s*[{])", "", t)
    t = re.sub(r"\}(?=\s*[}])", "", t)
    return t


_NOT_MET = {"no", "none", "false", "n/a", "null", "不满足"}


def _rule_met(val):
    """规则值是否表示「该规则成立」。'No'/{"No"}/None 均视为不成立。"""
    s = str(val).strip().strip("{").strip("}").strip().strip('"').strip()
    return s.lower() not in _NOT_MET and s != ""


def parse_answer(text):
    """把一段回复解析为 (label, method)。

    label: 'Yes' / 'No' / None（解析失败）
    method: 命中的解析层级，便于审计
    """
    if not text:
        return None, "empty"
    t = _norm(text)
    flat = re.sub(r"\s+", " ", t)  # 折叠换行，让跨行 JSON 可被整体识别

    # 1) 显式 {"Answer": "Yes"/"No"}，取最后一次出现
    hits = re.findall(r'\{\s*"Answer"\s*:\s*"(Yes|No)"\s*\}', flat, flags=re.IGNORECASE)
    if hits:
        return hits[-1].capitalize(), "answer_json"

    # 2) 逐个解析 JSON 对象（取最后一个可解析的）
    blocks = re.findall(r"\{[^{}]*\}", flat)
    for block in reversed(blocks):
        try:
            obj = json.loads(block)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        if "Answer" in obj:
            v = str(obj["Answer"]).strip().capitalize()
            if v in ("Yes", "No"):
                return v, "answer_json"
        rule_keys = [k for k in obj if re.fullmatch(r"Rule\s*\d+", str(k).strip())]
        if rule_keys:
            met = [k for k in rule_keys if _rule_met(obj[k])]
            return ("Yes" if met else "No"), "rule_json"
        # 形如 {"No"}（非法 JSON，但可能是键名为 No 的对象）
        if len(obj) == 1 and list(obj)[0].strip().lower() in _NOT_MET:
            return "No", "no_json"

    # 3) 规则值兜底（应对 {"Rule 2": {"No"}} 这类嵌套写法）
    pairs = re.findall(r'"Rule\s*\d+"\s*:\s*(\{[^{}]*\}|"[^"]*")', flat)
    if pairs:
        met = [p for p in pairs if _rule_met(p)]
        return ("Yes" if met else "No"), "rule_regex"

    # 4) 全部回答 {"No"}
    if re.search(r'\{\s*"No"\s*\}', flat, flags=re.IGNORECASE):
        return "No", "no_json"

    # 5) <Answer>Yes</Answer>
    hits = re.findall(r"<Answer>\s*(Yes|No)\s*</Answer>", flat, flags=re.IGNORECASE)
    if hits:
        return hits[-1].capitalize(), "answer_tag"

    # 6) 兜底：句中 "answer is Yes/No"
    m = re.findall(
        r"(?:final answer|answer)\s*(?:is|:)?\s*(?:\*\*)?\s*(Yes|No)\b",
        flat,
        flags=re.IGNORECASE,
    )
    if m:
        return m[-1].capitalize(), "answer_phrase"

    return None, "parse_fail"


def count_yes(text):
    """Causal Explorer 单条回复是否判 Yes（q 计数用）。"""
    label, _ = parse_answer(text)
    return 1 if label == "Yes" else 0


def extract_subq4(text):
    """从 Mediator Detector 回复中抽取 'Answer to subquestion 4:' 之后的一行。

    与原仓库 agent3/get_mediator.py 逻辑一致，但额外做大小写/空白容错。
    返回 (z_value, ok)
    """
    if not text:
        return "None", False
    t = _norm(text)
    idx = t.lower().find("answer to subquestion 4")
    if idx == -1:
        return "None", False
    start = idx + len("answer to subquestion 4")
    rest = t[start:]
    rest = re.sub(r"^[:\s*]*", "", rest)
    line = rest.split("\n")[0].strip().strip("*").strip()
    if not line:
        return "None", False
    return line, True
