# 跨境吴老师 Amazon 类目销量趋势 Skill

基于用户本地配置的卖家精灵（SellerSprite）MCP，为指定商品和 Amazon 站点定位高度相关的类目，并生成近 24 个自然月的完整类目销量趋势离线 HTML 看板。MCP 能验证叶子时自动使用已验证叶子类目；不能验证时，必须先由用户确认最细匹配类目。

## 一、适用场景

- 需要观察某商品所属 Amazon 已验证叶子类目，或用户确认最细匹配类目的月度销量趋势。
- 需要比较前 12 个月与近 12 个月的完整类目销量。
- 需要获得可离线打开、可交付的单文件 HTML 看板。

不用于关键词趋势、ASIN 销量趋势，且不会使用 Top 100 商品样本替代完整类目销量。

## 二、从公共仓库安装

本仓库为公共 GitHub 仓库。安装无需提交 GitHub 用户名、接受邀请、申请访问权限或提供 GitHub 令牌。

在 Codex 中新建一个对话，输入：

```text
请从以下 GitHub 仓库安装跨境吴老师 Amazon 类目销量趋势 Skill：
https://github.com/defway888-design/kuajing-wulaoshi-amazon-category-sales-trend-skill
```

Codex 会下载并安装到当前用户自己的 `$CODEX_HOME/skills/kuajing-wulaoshi-amazon-category-sales-trend`；未设置 `CODEX_HOME` 时，默认安装到 `~/.codex/skills/kuajing-wulaoshi-amazon-category-sales-trend`。无需手动创建固定路径。

安装完成后，该 Skill 会在下一个 Codex 对话中可用；如当前客户端尚未刷新 Skill 列表，再重启 Codex。

安装完成后，关闭并重新打开 Codex，使 Skill 生效。

## 三、启动方式

安装后，可在 Codex 输入以下任一短语：

```text
运行跨境吴老师 Amazon 类目近24个月销量趋势分析
```

```text
分析商品所在 Amazon 类目近24个月销量趋势
```

Skill 会先要求提供：

1. 商品名称
2. Amazon 站点代码：`US`、`UK`、`AU`、`CA`、`JP`、`DE`、`FR`、`IT`、`ES`、`MX`、`BR`、`IN`、`AE`

示例：`商品名称：示例商品；站点：US`

执行时会按真实进度显示跨境吴老师品牌提示，例如“跨境吴老师正在检查卖家精灵 MCP 连接…”、“跨境吴老师正在获取近24个月完整类目销量数据…”和“跨境吴老师正在生成类目销量趋势看板…”。遇到需要选择连接、确认类目或任务阻塞时，也会以跨境吴老师前缀说明下一步或事实原因。

## 四、执行后会发生什么

1. Skill 在当前运行环境中发现并绑定用户自己的卖家精灵 MCP；不会固定使用特定 MCP 服务名、地址或账号。
2. 根据商品语义定位候选类目；MCP 可验证叶子时自动继续，无法验证时展示类目路径与 `nodeIdPath`，等待用户确认后再继续。
3. 以完整类目月度 `totalUnits` 为销量主指标，采集截至上一个自然月的 24 个自然月窗口。
4. 生成单文件离线 HTML 看板，包含类目路径、月度趋势、两个 12 个月周期对比、关键洞察与月度明细。

若某些月份不可用，页面会保留这 24 个日历月份，缺失月显示“—（缺失）”。已确认月份仍可统计；但当前后两个 12 个月周期任一方覆盖不完整时，变化量与增长率均显示“—”。

## 五、使用注意

- 请先在自己的 Codex 环境配置可用的卖家精灵 MCP。
- 有多个可用卖家精灵 MCP 连接时，Skill 会请你选择本次任务使用的连接。
- SellerSprite MCP 未提供叶子验证时，Skill 不会将路径最末级、商品数或空结果当作叶子证明；只有用户确认具体候选路径后才会采集销量。看板会明确显示“用户确认的最细匹配类目（SellerSprite MCP 未提供叶子验证）”。
- 任务内会复用相同请求的已确认结果并串行调用；仅遵循运行时工具明确给出的限流或重试提示，不虚构官方调用额度。
- Skill 的模板通过自身相对路径加载；输出写入当前任务环境可写的交付目录，不依赖作者电脑的盘符、用户目录、缓存、临时目录、工作区或 MCP 配置位置。
- 不会将商品名、类目路径、节点 ID、销量、MCP 地址、密钥或调用日志写入本 Skill 仓库。
- 本 Skill 为跨境吴老师专用模板，未经授权不得移除、替换或弱化 Skill 名称、执行提示和页面标题中的跨境吴老师标识。

## 六、仓库文件说明

| 文件或目录 | 作用 |
| --- | --- |
| `SKILL.md` | Skill 的工作流、数据口径与输出规则。 |
| `agents/openai.yaml` | Codex 中显示名称、简介与默认启动提示。 |
| `references/data-contract.md` | MCP 能力绑定、字段判定、缺失月份与调用控制规则。 |
| `assets/category-sales-trend-template.html` | 固定紫粉视觉的离线 HTML 看板模板。 |
| `scripts/build_dashboard.py` | 校验月度数据并向模板安全注入数据的本地构建脚本。 |

## 七、版本记录

**后续每次发布功能更新，均在下表新增一行。GitHub 提交记录只记录该功能变更对应的主要提交；仅补充或修订说明文档时，不新增功能版本，也不新增版本记录行。**

| 版本 | 日期 | 功能变更 | 主要提交 |
| --- | --- | --- | --- |
| v1.0.0 | 2026-08-07 | 首次发布：动态绑定卖家精灵 MCP，基于完整类目 `totalUnits` 生成近 24 个月离线销量趋势看板，并支持缺失月份的部分覆盖展示。 | [`4701a41`](https://github.com/defway888-design/kuajing-wulaoshi-amazon-category-sales-trend-skill/commit/4701a41724952ff356f6225e9c8ca9589c4902b8) |
| v1.1.0 | 2026-08-07 | 新增类目双轨确认：MCP 可验证叶子时自动继续；缺少叶子验证能力时必须取得用户对具体路径的确认，并在看板中透明标注未验证状态。 | [`19a8a50`](https://github.com/defway888-design/kuajing-wulaoshi-amazon-category-sales-trend-skill/commit/19a8a50ef279264db1259928fdd06e610a33a3db) |
| v1.2.0 | 2026-08-07 | 新增跨境吴老师品牌化执行提示：覆盖模板准备、MCP 连接、类目确认、数据采集、看板生成、阻塞与完成路径。 | [`d75f302`](https://github.com/defway888-design/kuajing-wulaoshi-amazon-category-sales-trend-skill/commit/d75f3024152e7389e9353be355f93f50acd0aab1) |
| v1.3.0 | 2026-09-01 | 新增公共仓库与运行时可移植性规则：安装到每位用户自己的 Codex 目录，动态使用本机 MCP 与可写交付目录，不依赖开发机路径、账号或配置。 | [`3ce777a`](https://github.com/defway888-design/kuajing-wulaoshi-amazon-category-sales-trend-skill/commit/3ce777a114221db33330abe548016e13713e802d) |
