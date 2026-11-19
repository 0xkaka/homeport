#!/usr/bin/env python3
"""homeport 自检：三份模板能解析、策略名正确、规则一致。

用法：python3 scripts/check.py（需要 node；有 pyyaml 时额外做 YAML 解析）
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXIT, RELAY = "🏠住宅出口-勿选", "HP_Relay"
TYPES = {"DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "PROCESS-NAME"}
errors = []


def rule_ok(rule, where):
    parts = [p.strip() for p in rule.split(",")]
    if len(parts) < 3 or parts[0] not in TYPES:
        errors.append(f"{where}: 无法识别的规则 {rule}")
    elif parts[0] == "IP-CIDR6" and parts[2] != "REJECT":
        errors.append(f"{where}: IPv6 规则应为 REJECT：{rule}")
    elif parts[0] != "IP-CIDR6" and parts[2] != EXIT:
        errors.append(f"{where}: 策略应为 {EXIT}：{rule}")


def clash_rules():
    path = ROOT / "clash-party" / "override.yaml"
    text = path.read_text()
    try:
        import yaml
        doc = yaml.safe_load(text)
        leaf, group = doc["proxies+"][0], doc["proxy-groups+"][0]
        if leaf["name"] != EXIT or leaf.get("dialer-proxy") != RELAY:
            errors.append("clash: 住宅节点名或 dialer-proxy 不对")
        if group["name"] != RELAY:
            errors.append("clash: 中转组名不对")
        if "filter" in group:
            errors.append("clash: 跳板组不该再按名字筛选（filter），会让部分机场没有跳板")
        exc = re.compile(group["exclude-filter"].replace("(?i)", ""), re.I)
        if not exc.search(EXIT):
            errors.append("clash: exclude-filter 必须排除住宅出口自己，否则会死循环")
        rules = doc["+rules"]
    except ImportError:
        rules = re.findall(r"^  - ((?:IP|DOMAIN|PROCESS)-[^\n]+)$", text, re.M)
    for r in rules:
        rule_ok(r, "clash")
    return set(rules)


def flclash_rules():
    path = ROOT / "flclash" / "homeport.js"
    js = (
        path.read_text()
        + "\nconst c = main({});"
        + "\nconsole.log(JSON.stringify(c));"
    )
    try:
        out = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    except FileNotFoundError:
        # 没装 node：直接从源码里抠出数组拼规则
        src = path.read_text()
        arr = lambda n: re.findall(r'"([^"]+)"', re.search(rf"const {n} = \[(.*?)\];", src, re.S).group(1))
        rules = {f"DOMAIN-SUFFIX,{d},{EXIT}" for d in arr("SUFFIX")}
        rules |= {f"DOMAIN-KEYWORD,{k},{EXIT}" for k in arr("KEYWORD")}
        rules |= set(re.findall(r'"(IP-CIDR6,[^"]+)"', src))
        rules |= {f"IP-CIDR,160.79.104.0/21,{EXIT},no-resolve", f"IP-ASN,399358,{EXIT},no-resolve"}
        print("提示：未找到 node，flclash 只做静态检查", file=sys.stderr)
        return rules
    if out.returncode:
        errors.append(f"flclash: 脚本运行失败\n{out.stderr}")
        return set()
    cfg = json.loads(out.stdout)
    if cfg["proxies"][0]["name"] != EXIT or cfg["proxy-groups"][0]["name"] != RELAY:
        errors.append("flclash: 节点名或中转组名不对")
    for r in cfg["rules"]:
        rule_ok(r, "flclash")
    return {r for r in cfg["rules"] if not r.startswith("PROCESS-NAME")}


def shadowrocket_rules():
    lines = (ROOT / "shadowrocket" / "homeport.module").read_text().splitlines()
    if not lines[0].startswith("#!name=") or "[Rule]" not in lines:
        errors.append("shadowrocket: 缺少 #!name 或 [Rule]")
    rules = [l.strip() for l in lines[lines.index("[Rule]") + 1:] if l.strip() and not l.startswith("#")]
    for r in rules:
        rule_ok(r, "shadowrocket")
    return set(rules)


a, b, c = clash_rules(), flclash_rules(), shadowrocket_rules()
for name, s in (("flclash", b), ("shadowrocket", c)):
    if s != a:
        errors.append(f"{name} 与 clash 不一致：缺 {sorted(a - s)}，多 {sorted(s - a)}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"OK：三份模板一致，共 {len(a)} 条规则")
