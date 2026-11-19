#!/usr/bin/env python3
"""homeport 自检：模板能运行、策略名正确、跳板选对、规则一致。

用法：python3 scripts/check.py（需要 node；没有 node 时只做静态检查）

Clash Party / Clash Verge Rev / FlClash 共用 flclash/homeport.js，
小火箭用 shadowrocket/homeport.module，两边规则必须一致（安卓 App 规则除外）。
"""

import json
import re
import shutil
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


# 用几种常见订阅结构跑脚本，检查跳板选得对不对
CASES = {
    # 普通机场：MATCH 指向主选择组
    "match": ({"proxies": [{"name": "🇯🇵 东京"}], "proxy-groups": [
        {"name": "♻️ 自动选择", "type": "url-test", "proxies": ["🇯🇵 东京"]},
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "🇯🇵 东京"]}],
        "rules": ["GEOIP,CN,DIRECT", "MATCH,🚀 节点选择"]}, "🚀 节点选择"),
    # 没有 MATCH：用第一个 select 组
    "select": ({"proxies": [{"name": "A"}], "proxy-groups": [
        {"name": "auto", "type": "url-test", "proxies": ["A"]},
        {"name": "PROXY", "type": "select", "proxies": ["auto", "A"]}], "rules": []}, "PROXY"),
    # 什么组都没有：退回 HP_Relay
    "none": ({"proxies": [{"name": "A"}], "proxy-groups": [], "rules": ["MATCH,DIRECT"]}, RELAY),
}


def flclash_rules():
    path = ROOT / "flclash" / "homeport.js"
    src = path.read_text()
    if not shutil.which("node"):
        arr = lambda n: re.findall(r'"([^"]+)"', re.search(rf"const {n} = \[(.*?)\];", src, re.S).group(1))
        rules = {f"DOMAIN-SUFFIX,{d},{EXIT}" for d in arr("SUFFIX")}
        rules |= {f"DOMAIN-KEYWORD,{k},{EXIT}" for k in arr("KEYWORD")}
        rules |= set(re.findall(r'"(IP-CIDR6,[^"]+)"', src))
        rules |= {f"IP-CIDR,160.79.104.0/21,{EXIT},no-resolve", f"IP-ASN,399358,{EXIT},no-resolve"}
        print("提示：未找到 node，脚本只做静态检查", file=sys.stderr)
        return rules
    # Clash Verge Rev / Clash Party 用的写法
    desktop = src.replace("const main = (config) => {", "function main(config, profileName) {").rstrip()
    desktop = re.sub(r"\n};$", "\n}", desktop)
    rules = set()
    for variant, code in (("flclash", src), ("desktop", desktop)):
        for case, (cfg, want) in CASES.items():
            js = code + f"\nconsole.log(JSON.stringify(main({json.dumps(cfg, ensure_ascii=False)})));"
            out = subprocess.run(["node", "-e", js], capture_output=True, text=True)
            if out.returncode:
                errors.append(f"{variant}/{case}: 脚本运行失败\n{out.stderr}")
                continue
            c = json.loads(out.stdout)
            leaf = next((p for p in c["proxies"] if p["name"] == EXIT), None)
            if not leaf:
                errors.append(f"{variant}/{case}: 没有住宅出口节点")
                continue
            if leaf.get("dialer-proxy") != want:
                errors.append(f"{variant}/{case}: 跳板应为 {want}，实际 {leaf.get('dialer-proxy')}")
            names = {p["name"] for p in c["proxies"]} | {g["name"] for g in c["proxy-groups"]} | {"DIRECT"}
            if leaf.get("dialer-proxy") not in names:
                errors.append(f"{variant}/{case}: 跳板 {leaf.get('dialer-proxy')} 不存在")
            for r in c["rules"]:
                if EXIT in r or "REJECT" in r:
                    rule_ok(r, f"{variant}/{case}")
            rules = {r for r in c["rules"] if (EXIT in r or r.startswith("IP-CIDR6")) and not r.startswith("PROCESS-NAME")}
    return rules


def shadowrocket_rules():
    lines = (ROOT / "shadowrocket" / "homeport.module").read_text().splitlines()
    if not lines[0].startswith("#!name=") or "[Rule]" not in lines:
        errors.append("shadowrocket: 缺少 #!name 或 [Rule]")
    rules = [l.strip() for l in lines[lines.index("[Rule]") + 1:] if l.strip() and not l.startswith("#")]
    for r in rules:
        rule_ok(r, "shadowrocket")
    return set(rules)


a, b = flclash_rules(), shadowrocket_rules()
if a != b:
    errors.append(f"shadowrocket 与脚本不一致：缺 {sorted(a - b)}，多 {sorted(b - a)}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"OK：脚本和小火箭模块一致，共 {len(a)} 条规则")
