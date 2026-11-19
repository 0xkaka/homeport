// homeport · FlClash 覆写脚本（FlClash ≥ 0.8.85）
//
// 作用：Claude、Google、支付和风控相关域名统一走住宅出口 🏠住宅出口-勿选。
// 链路：本机 → 你在机场里选的节点（跳板）→ 🏠住宅出口-勿选（住宅代理）→ 目标站点。
//
// 使用前把下面 HOME 里的 server / port / username / password 换成自己的住宅代理。
// 改完以后别再从 URL 重新导入，否则会被占位符覆盖。
//
// 跳板跟随机场的“主选择组”（你平时点节点的那个组）：你选哪个节点，住宅代理就经过哪个节点。
// 主选择组 = 订阅里最后一条 MATCH 规则指向的组；找不到就用第一个 select 组；
// 再找不到才退回 HP_Relay（机场全部节点自动测速）。
// 想固定直连住宅代理：把 FORCE_RELAY 改成 "DIRECT"。
//
// Clash Verge Rev / Clash Party 也用这份脚本，只要把下面 main 那一行改成
// function main(config, profileName) {，最后一行 }; 改成 }。

const HOME = {
  server: "<HOST>",
  port: 0,
  username: "<USERNAME>",
  password: "<PASSWORD>",
};

const EXIT = "🏠住宅出口-勿选";
const RELAY = "HP_Relay";
const FORCE_RELAY = ""; // 留空 = 跟随主选择组；填 "DIRECT" 或某个组名 / 节点名 = 固定用它
const RELAY_EXCLUDE = "(?i)住宅出口|到期|过期|剩余|官网|网址|失联|故障|重置|套餐|Expire|Traffic|Reset|^(DIRECT|REJECT|COMPATIBLE|PASS)$";

const SUFFIX = [
  // Claude / Anthropic
  "claude.ai", "claude.com", "clau.de", "anthropic.com",
  "claudeusercontent.com", "claudemcpcontent.com", "modelcontextprotocol.io",
  // 监控 / 风控 / 验证 / 支付
  "sentry.io", "datadoghq.com", "growthbook.io", "usefathom.com", "segment.io",
  "siftscience.com", "hcaptcha.com", "challenges.cloudflare.com",
  "intercom.io", "intercomcdn.com",
  "stripe.com", "stripe.network", "stripecdn.com", "withpersona.com",
  // Google（含 Gmail、Google Pay）
  "google.com", "googleapis.com", "gstatic.com", "googleusercontent.com",
  "gmail.com", "recaptcha.net",
  // 出口 IP 检测
  "webshare.io", "ipinfo.io",
];

const KEYWORD = ["anthropic", "claude", "browser-intake"];

const PROCESS = [
  "com.anthropic.claude",                 // Claude 安卓 App
  "com.android.vending",                  // Google Play
  "com.google.android.apps.walletnfcrel", // Google Wallet
];

// 找机场的主选择组：最后一条 MATCH 规则指向的组 → 第一个 select 组
function mainGroup(config) {
  const groups = config["proxy-groups"] || [];
  const names = new Set(groups.map((g) => g.name));
  const rules = config.rules || [];
  for (let i = rules.length - 1; i >= 0; i--) {
    const p = String(rules[i]).split(",").map((x) => x.trim());
    if (/^(MATCH|FINAL)$/i.test(p[0]) && names.has(p[1])) return p[1];
  }
  const sel = groups.find((g) => g.type === "select");
  return sel ? sel.name : "";
}

const main = (config) => {
  config.proxies = config.proxies || [];
  config["proxy-groups"] = config["proxy-groups"] || [];
  const groups = config["proxy-groups"];

  // 机场里用 include-all 自动收节点的组，把住宅出口排除掉，防止被选中后死循环
  for (const g of groups) {
    if (g["include-all"] || g["include-all-proxies"]) {
      g["exclude-filter"] = g["exclude-filter"] ? g["exclude-filter"] + "|住宅出口" : "住宅出口";
    }
  }

  // 跳板：跟随主选择组；找不到才建一个自动测速组
  let relay = FORCE_RELAY || mainGroup(config);
  if (!relay) {
    groups.push({
      name: RELAY,
      type: "url-test",
      hidden: true,
      url: "https://www.gstatic.com/generate_204",
      interval: 300,
      tolerance: 50,
      lazy: false,
      "include-all": true,
      "exclude-filter": RELAY_EXCLUDE,
    });
    relay = RELAY;
  }

  config.proxies.push({
    name: EXIT,
    type: "http",
    ...HOME,
    "dialer-proxy": relay,
  });

  const rules = [
    // Anthropic IPv6 段经住宅代理会 502，先拒掉，客户端会自动回落 IPv4
    "IP-CIDR6,2607:6bc0::/48,REJECT,no-resolve",
    "IP-CIDR6,2607:6bc0:11::/48,REJECT,no-resolve",
    ...SUFFIX.map((d) => `DOMAIN-SUFFIX,${d},${EXIT}`),
    ...KEYWORD.map((k) => `DOMAIN-KEYWORD,${k},${EXIT}`),
    `IP-CIDR,160.79.104.0/21,${EXIT},no-resolve`,
    `IP-ASN,399358,${EXIT},no-resolve`,
    ...PROCESS.map((p) => `PROCESS-NAME,${p},${EXIT}`),
  ];
  config.rules = rules.concat(config.rules || []);
  return config;
};
