# homeport

**一句话：让 Claude、Google、Stripe 这些网站，在你所有设备上都看到同一个“住宅 IP”。**

很多人用机场节点访问 Claude / Google，节点一会儿日本一会儿美国，IP 来回跳，再加上机场 IP 是机房 IP，很容易触发风控：注册要验证、付款失败、身份认证不过、甚至封号。

homeport 做的事情很简单：把这些“敏感网站”单独挑出来，统一走一条固定的**住宅代理**；其他网站照旧走你的机场，速度不受影响。

---

## 目录

1. [原理（看不懂可以跳过）](#1-原理看不懂可以跳过)
2. [开始前要准备什么](#2-开始前要准备什么)
3. [Mac：Clash Party](#3-macclash-party)
4. [安卓：FlClash](#4-安卓flclash)
5. [iPhone / iPad：Shadowrocket（小火箭）](#5-iphone--ipadshadowrocket小火箭)
6. [检查是否成功](#6-检查是否成功)
7. [Claude Code、终端、Chrome 的额外设置](#7-claude-code终端chrome-的额外设置)
8. [常见问题](#8-常见问题)
9. [哪些网站会走住宅出口](#9-哪些网站会走住宅出口)
10. [给维护者：修改规则](#10-给维护者修改规则)

---

## 1. 原理（看不懂可以跳过）

```
            ┌──────────────── 敏感网站（Claude / Google / Stripe …）────────────────┐
你的设备 ──►│  HP_Relay（机场里的台/日/新/美/韩节点，自动选最快）──► HP_Home（住宅代理）──► 网站 │
            └───────────────────────────────────────────────────────────────────────┘
            其他网站 ──► 照常走你的机场
```

- **HP_Home**：你买的住宅代理。网站最终看到的就是它的 IP。所有设备填同一个，IP 就一致了。
- **HP_Relay**：跳板。国内直连住宅代理，握手内容是明文，容易被干扰断线；先经过一个机场节点再连过去就稳了。跳板换来换去**不影响**最终 IP。
- 另外，Claude 的 IPv6 地址走住宅代理会报错（502），这套规则直接把它拦掉，让设备自动改用 IPv4，你不用管。

---

## 2. 开始前要准备什么

### ① 一个机场订阅（你现在翻墙用的那个）

已经能正常翻墙就行。注意节点名字里最好带“台湾 / 日本 / 新加坡 / 美国 / 韩国”或 `TW / JP / SG / US / KR` 这类字样，程序靠名字自动挑跳板。

### ② 一条静态住宅 HTTP 代理

去住宅代理服务商购买，选的时候注意三点：
如果不会 请看教程：https://x.com/0xjackkk/status/2117862295397335283

| 要求 | 说明 |
| --- | --- |
| **静态（Static）** | IP 固定不变。别买“动态/轮换（Rotating）”的。 |
| **住宅（Residential / ISP）** | 不要买“机房（Datacenter）”的。 |
| **HTTP 协议，带用户名密码** | 大部分服务商默认就是。 |

买好后，后台能看到这样四项信息，**抄下来**，后面每台设备都要填同样的：

| 项目 | 举例（假的，别照抄） |
| --- | --- |
| 地址 / Host | `198.51.100.23` |
| 端口 / Port | `6123` |
| 用户名 / Username | `abcd1234` |
| 密码 / Password | `xyz789` |

> 💡 有的服务商给的是一整串，比如 `198.51.100.23:6123:abcd1234:xyz789`，按冒号拆开就是 地址:端口:用户名:密码。

### ③ 对应的客户端

| 设备 | 客户端 | 怎么装 |
| --- | --- | --- |
| Mac | Clash Party | 去官方 GitHub Releases 下载 `.dmg` |
| 安卓 | FlClash（版本 ≥ 0.8.85） | 去官方 GitHub Releases 下载 `.apk` |
| iPhone / iPad | Shadowrocket | 美区 App Store 购买 |

先确认客户端里**机场订阅已经导入、能正常翻墙**，再继续下面的步骤。

---

## 3. Mac：Clash Party

### 第 1 步：导入覆写

1. 打开 Clash Party，点左侧菜单 **「覆写」**。
2. 点右上角 **＋（新建）**，选择 **从 URL / 链接导入**。
3. 粘贴这个链接，确定：

   ```
   https://raw.githubusercontent.com/0xkaka/homeport/main/clash-party/override.yaml
   ```

   > 导入失败？说明当前网络打不开 GitHub。先把 Clash Party 打开、连上机场再导入。

### 第 2 步：填住宅代理

1. 在覆写列表里找到刚导入的这一项，点 **编辑**（铅笔图标或右键 → 编辑）。
2. 找到最上面这一段：

   ```yaml
   proxies+:
     - name: HP_Home
       type: http
       server: "<HOST>"
       port: 0
       username: "<USERNAME>"
       password: "<PASSWORD>"
   ```

3. 把它改成你自己的，例如：

   ```yaml
       server: "198.51.100.23"
       port: 6123
       username: "abcd1234"
       password: "xyz789"
   ```

   ⚠️ 注意：
   - 引号 `"` 要保留，**尖括号 `< >` 要删掉**。
   - `port` 后面直接写数字，**不加引号**，也**不能是 0**。
   - 每行开头的空格不要动，YAML 对缩进很敏感。
4. 保存。

### 第 3 步：启用并重启

1. 左侧点 **「订阅」/「配置」**，在你的机场订阅上点编辑（或右键），找到 **覆写** 一栏，勾选刚才那份覆写，保存。
2. 左侧点 **「内核设置」**，点那个 **旋转箭头（重启内核）** 按钮。
3. 确认首页的代理模式是 **规则（Rule）**，不是「全局」或「直连」。

### ⚠️ 以后别点“更新”这份覆写

更新会重新下载链接里的模板，你填的地址密码会被冲回 `<HOST>` 这些占位符。规则有更新时，要么重新导入后再填一遍，要么手动改。

---

## 4. 安卓：FlClash

> FlClash 用的是一段 **JavaScript 脚本**，和 Mac 那份 YAML 不通用，别贴错。

### 第 1 步：导入脚本

1. 打开 FlClash，底部点 **「工具」** → **「进阶配置」** → **「脚本」**。
2. 点 **＋（添加）**，选 **通过 URL 导入**，粘贴：

   ```
   https://raw.githubusercontent.com/0xkaka/homeport/main/flclash/homeport.js
   ```

### 第 2 步：填住宅代理

1. 点开刚导入的脚本进入编辑。
2. 文件开头有这一段：

   ```js
   const HOME = {
     server: "<HOST>",
     port: 0,
     username: "<USERNAME>",
     password: "<PASSWORD>",
   };
   ```

3. 改成你自己的，例如：

   ```js
   const HOME = {
     server: "198.51.100.23",
     port: 6123,
     username: "abcd1234",
     password: "xyz789",
   };
   ```

   ⚠️ 引号和逗号都要保留，尖括号删掉；`port` 写数字，不加引号，不能是 0。
4. 保存。**以后不要再“从 URL 重新导入”**，否则会被冲回占位符。

### 第 3 步：让脚本生效（这一步最容易漏）

1. 底部点 **「配置」**，在你的机场订阅上点右侧的 **⋮ / 配置按钮**。
2. 进入 **「覆写」** → **「脚本」** → 选中刚才那份脚本。
3. 回到 **「仪表盘」**，关掉再打开连接（或点重启）。

> 只导入脚本、没在订阅里选中，等于没装。

---

## 5. iPhone / iPad：Shadowrocket（小火箭）

小火箭分两部分：**节点**里填账号密码，**模块**里放规则。

### 第 1 步：添加住宅节点

1. 首页右上角点 **＋**。
2. **类型** 选 **HTTP**。
3. 按下面填：

   | 栏位 | 填什么 |
   | --- | --- |
   | 地址 | 住宅代理地址，如 `198.51.100.23` |
   | 端口 | 如 `6123` |
   | 用户 | 如 `abcd1234` |
   | 密码 | 如 `xyz789` |
   | **备注** | **`HP_Home`**（必须一字不差，大小写也一样） |

4. 右上角 **完成**。

> 备注填错，规则就找不到这个节点，所有敏感网站都会连不上。

### 第 2 步：设置跳板（代理通过）

1. 在首页节点列表里找到 `HP_Home`，点它右边的 **ⓘ**。
2. 找到 **「代理通过」**，选一个你机场里的 **台湾 / 日本 / 新加坡 / 美国 / 韩国** 节点（挑一个稳定的）。
3. 保存。

> 不设也能用，但就是手机直连住宅代理，容易断。跳板节点挂了，回来这里换一个就行。

### 第 3 步：添加模块

1. 底部点 **「配置」** → **「模块」**。
2. 右上角 **＋**，粘贴：

   ```
   https://raw.githubusercontent.com/0xkaka/homeport/main/shadowrocket/homeport.module
   ```

3. 点 **下载**，确认模块列表里出现 `homeport` 且开关是打开的。

### 第 4 步：切到“配置”模式

1. 回到首页，**全局路由** 选 **「配置」**。
   - 选「代理」= 所有流量走当前选中节点，规则不生效。
   - 选「直连」= 全部不翻墙。
2. 首页顶部开关打开，连接。

> 模块优先级比订阅配置高，以后更新机场订阅不会把规则冲掉；小火箭的模块也可以放心点更新，因为账号密码在节点里，不在模块里。

---

## 6. 检查是否成功

**目标：所有设备看到的 IP 一模一样，而且就是你住宅代理的 IP。**

### 手机 / 平板

打开浏览器访问：

```
https://ipv4.webshare.io/
```

页面上只有一行 IP。和住宅代理后台显示的 IP 对一下。

### Mac

打开「终端」，粘贴回车：

```bash
curl -x http://127.0.0.1:7890 https://ipv4.webshare.io/
```

输出的 IP 应该和手机上一样。

> `7890` 是 Clash Party 默认端口。如果你改过，到 Clash Party 首页 / 设置里看“混合端口（Mixed Port）”是多少，替换掉。

### 不一样怎么办？

看 [8. 常见问题](#8-常见问题)。

---

## 7. Claude Code、终端、Chrome 的额外设置

### Chrome：关闭 QUIC

Chrome 会用 QUIC（基于 UDP）偷偷绕过代理，导致 IP 不一致。

1. 地址栏输入 `chrome://flags/#enable-quic`，回车。
2. 把 **Experimental QUIC protocol** 改成 **Disabled**。
3. 点右下角 **Relaunch** 重启 Chrome。

### 终端 / Claude Code：手动指定代理

终端里的程序（包括 Claude Code、git、npm）**不会自动走系统代理**。

1. 终端里运行 `open ~/.zshrc`（没有这个文件就先运行 `touch ~/.zshrc`）。
2. 在文件末尾加上这三行，保存：

   ```zsh
   export http_proxy=http://127.0.0.1:7890
   export https_proxy=http://127.0.0.1:7890
   export all_proxy=socks5://127.0.0.1:7890
   ```

3. 关掉终端重新打开（或运行 `source ~/.zshrc`）。
4. 验证：运行 `curl https://ipv4.webshare.io/`，应显示住宅 IP。

---

## 8. 常见问题

**Q：Claude / Google 全打不开了。**
A：基本是住宅代理没填对。逐项检查：
- 地址、端口、用户名、密码有没有抄错，尖括号删了没；
- `port` 是不是还是 0；
- 小火箭的节点备注是不是正好 `HP_Home`；
- 住宅代理有没有到期 / 流量用完（去服务商后台看）。

**Q：Clash Party / FlClash 报错，配置加载失败。**
A：
- 改 YAML 时缩进被弄乱了，或者引号少了一个。最稳的办法：删掉这份覆写，重新导入，只改那四个值。
- 机场节点名里没有任何地区字样，跳板组 `HP_Relay` 是空的。见下一条。

**Q：我的机场节点名字没有“日本 / 美国”这些字，怎么办？**
A：打开覆写（或脚本），找到 `filter:`（FlClash 里是 `RELAY_FILTER`），把你节点名里的关键字加进括号里，用 `|` 隔开。例如节点叫 `Tokyo-01`、`LA-02`，就在最后加上 `|Tokyo|LA`。

**Q：页面能打开，但时不时断线 / 很慢。**
A：多半是跳板节点质量差。
- Mac / 安卓：`HP_Relay` 每 5 分钟会自动测速换最快的，一般会自己恢复。也可以在 `exclude-filter` 里加关键字，排除某些烂节点。
- iPhone：回到 `HP_Home` 的 ⓘ →「代理通过」换一个节点。

**Q：所有跳板都挂了，想先凑合用。**
A：
- Mac：覆写里把 `dialer-proxy: HP_Relay` 改成 `dialer-proxy: DIRECT`，并删掉 `proxy-groups+:` 那一整段。
- 安卓：脚本里把 `"dialer-proxy": RELAY` 改成 `"dialer-proxy": "DIRECT"`。
- iPhone：「代理通过」改成不选。

代价是直连住宅代理，可能会被干扰断线。

**Q：手机和电脑的 IP 不一样。**
A：
- 三台设备填的是不是同一条住宅代理；
- 小火箭全局路由是不是「配置」，Clash 是不是「规则」模式；
- Mac 上 Chrome 的 QUIC 关了没。

**Q：规则更新了，我要怎么更新？**
A：
- iPhone：「配置」→「模块」→ 左滑 homeport → 更新。账号在节点里，不受影响。
- Mac / 安卓：更新会冲掉你填的账号。先把四个值记好，更新（或重新导入）后再填一遍。

---

## 9. 哪些网站会走住宅出口

| 类别 | 域名 / 规则 |
| --- | --- |
| Claude / Anthropic | `claude.ai` `claude.com` `clau.de` `anthropic.com` `claudeusercontent.com` `claudemcpcontent.com` `modelcontextprotocol.io`，含关键词 `anthropic` `claude`，以及 Anthropic 的 IP 段和 ASN |
| 监控 / 风控 | `sentry.io` `datadoghq.com`（含 `browser-intake`）`growthbook.io` `usefathom.com` `segment.io` `siftscience.com` `intercom.io` `intercomcdn.com` |
| 人机验证 | `hcaptcha.com` `challenges.cloudflare.com` `recaptcha.net` |
| 支付 / 身份认证 | `stripe.com` `stripe.network` `stripecdn.com` `withpersona.com` |
| Google | `google.com` `googleapis.com` `gstatic.com` `googleusercontent.com` `gmail.com` |
| 安卓 App（仅 FlClash） | Claude App、Google Play、Google Wallet |
| IP 检测 | `webshare.io` `ipinfo.io` |
| 拦截 | Anthropic IPv6 `2607:6bc0::/48` `2607:6bc0:11::/48` |

不在表里的网站，照常走你的机场。

---

## 10. 给维护者：修改规则

三份文件要**同步修改**：

| 文件 | 改哪里 |
| --- | --- |
| `clash-party/override.yaml` | `+rules:` 下面加一行 `- DOMAIN-SUFFIX,example.com,HP_Home` |
| `flclash/homeport.js` | `SUFFIX` 数组里加 `"example.com",` |
| `shadowrocket/homeport.module` | `[Rule]` 下面加一行 `DOMAIN-SUFFIX,example.com,HP_Home` |

改完运行自检，确认三份一致：

```bash
python3 scripts/check.py
```

推送到 GitHub 后，Actions 也会自动跑一遍。
