# 素材检查与等比配准辅助

先用完整角色设计目标姿态，再交给可用的图像编辑工具补画。输入、逐字提示词和原始输出都保留。工具不自动猜缺失的肩膀、发丝或裙摆。

```sh
uv run --project engineering python engineering/tools/asset.py inspect characters/my-character/arm.png
```

检查画布、RGBA、alpha 范围、透明像素、边界接触及 hash。边界接触需要看图：可能是正常贴边，也可能被裁断。完全不透明图需要先完成语义抠图。

## 对齐生成图

在源编辑图与目标母版上选至少三个不共线的同名点，例如未改变的发饰中心、衣领角、花扣中心。点要分散，不能全部落在刚重画的眼睑或手指上。坐标均为图片原始像素，不是网页缩放后的屏幕坐标。

保存 points.json：

```json
{"source": [[12,20],[82,20],[12,90]], "target": [[30,40],[100,40],[30,110]]}
```

这是平移示例，实际使用自己的对应点：

```sh
uv run --project engineering python engineering/tools/asset.py register --source characters/my-character/edit.png --master characters/my-character/master.png --points characters/my-character/points.json --out scratch/registered-arm
```

结果含 `registered.png`、50% 叠图、深浅底图及 `registration.json`。解算只允许等比缩放、旋转、平移；默认最大点误差 2px，不能偷偷添加剪切或非等比拉伸。三点共线、错误配对和整片落到画布外会拒绝。源图 alpha 随同一矩阵变换。

原位抠出的同画布素材可显式用 `--identity` 代替 `--points`。它不会证明图层语义正确，只表示你确认坐标无需改变。输出必须是新的 scratch 目录，避免覆盖生产资产。

先看完整叠图的比例/方向，再放大接合处；将配准结果只接入其所属图层。平移对齐合格不能证明色差、补底、线条和动态遮挡合格。保留报告中的矩阵和 hash，后续不要凭肉眼重输一个近似值。
