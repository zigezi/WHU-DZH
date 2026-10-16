# P5a.35 落地证据：值分类法 + 首案相关缺口修复

**依据**：P5a.35 §二/§三。首案（用户盲审 ①T ②F ③T ④U → 仲裁改判 ②T，IV 类补遗）。

## 1. 值分类法落到 lint（`deident.classify_lint`）
- **I 实例标识符**（RES_/USR_/PAY_/FLT_/ORD_/ITEM_/PROD_/EMAIL_/ADDR_ 伪真值）；
- **II 数值/日期/金额**（`date`/`expression`/`$x.yy`）；
- **III 人名**（NAME_）；
- **IV 领域词表/枚举**（origin/destination=IATA 形状、cabin/status/source/flight_type/insurance、reason）= **允许裸值**。
- ④「无原始真值」= 机器判（`lint_no_residual`），移出人工 rubric（a35 §三）。

## 2. 抽检 ⑤ 逼出的**新缺口**（已修）
`classify_lint` 的 unclassified 检查发现生成器漏了若干类，已逐个封死：

| 缺口 | 类 | 修法 |
|---|---|---|
| `item_ids`/`new_item_ids`/`item_id`/`product_id` | I | 键映射 ITEM/PROD |
| 地址族 address1/2/city/state/zip/country | I | 键映射 ADDR |
| 自由文本里的 10 位 item id / `$金额` | I/II | scrub `\b\d{10}\b`、金额 ×1.37 |
| `paypal_后加号` 支付 id（原正则漏 paypal） | I | 正则补 `paypal` |
| email | I | `_RE_EMAIL` → EMAIL_ 伪真值 |
| 自由文本里的人名（III） | III | **DB 用户名册**词表抹除 → NAME_ |
| origin/destination 误报为裸值 | IV | IATA 形状 `^[A-Z]{3}$` 判 IV |

- 复跑：`all_pass=True`（I-III 无残余/JSON/db 非成员），distinct 443。

## 3. 仅剩的开放问题（交仲裁）
自由文本 `summary/thought`（90+17）里仍含**商品名/地名**（如 "desk lamp"、"Charlotte"）——**开集但源自封闭目录/地址库**。
- 按 a35 先例（机场码=IV 豁免，因不决定 GT 且由接收任务驱动），建议判 **IV 豁免**；
- 或按 III 收紧（需商品/地名词表抹除）。
**opencode 不擅自定**：当前 classify 把它们记为 unclassified（不 fail 库），等裁决后一行开关。

## 4. 首案结论（与仲裁一致）
①T（I-III 全伪真值）②T（共指=同实体同假值；PHL/EWR 是不同实体）③T（日期平移保序）④机器通过 ⑤IV 合规 → **通过**。
