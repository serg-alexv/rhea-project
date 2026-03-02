# LICENSE MATRIX（草案）

## 1）制品与许可证映射
- 核心源代码：`Apache-2.0`。
- 指定工具模块：`MIT`（仅在明确标注时）。
- 文档：`CC BY 4.0`（受限材料可用 `CC BY-NC 4.0`）。
- 研究数据/内容：按数据卡单独声明。
- 品牌/Logo/名称：受商标政策约束，不属于开源代码许可。

## 2）第三方许可白名单（默认）
- `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `MPL-2.0`。

## 3）受限或需复核
- `GPL-*`, `AGPL-*`, `LGPL-*`, `SSPL-*`，以及非商业/自定义许可证。
- 无明确 SPDX 标识的依赖。

## 4）合规控制
- CI 自动 SPDX 扫描。
- 发布前必须更新 `NOTICE` 与归属信息。
- 策略检查失败即阻止 merge/release。

## 5）例外
许可证例外需 maintainer + steward 书面批准，并留下决策记录。
