"""
00_prepare_data.py
把 BGLR 的 wheat 数据集（R 的 .RData 格式）转成 CSV 表格，供后面的 Python 脚本使用。

运行方式（在 D:\GS\gs-eval 目录下）：
    .venv\\Scripts\\python.exe scripts\\00_prepare_data.py

输入：data/raw/BGLR_1.1.4.tar.gz   （从 CRAN 下载的 BGLR 源码包）
输出：data/wheat_X.csv   基因型矩阵，599 行（品系） x 1279 列（DArT 标记），取值 0/1
      data/wheat_Y.csv   表型矩阵，599 行（品系） x 4 列（4 个环境）
      data/wheat_A.csv   亲缘关系矩阵（加性关系矩阵），599 x 599
      data/wheat_sets.csv 每个品系属于哪个环境，599 行
"""

import io
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import rdata

# Windows 终端默认用 GBK 编码，中文和特殊符号会乱码，这两行强制成 UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- 路径设置
# __file__ 是"当前这个脚本自己的路径"。.resolve() 拿到绝对路径，
# .parents[1] 往上退两级：scripts/00_prepare_data.py -> scripts -> gs-eval
ROOT = Path(__file__).resolve().parents[1]
RAW_TAR = ROOT / "data" / "raw" / "BGLR_1.1.4.tar.gz"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("项目根目录:", ROOT)
print("压缩包路径:", RAW_TAR)

# ------------------------------------------------- 第 1 步：从 tar.gz 里取出 wheat.RData
# tarfile 是 Python 自带的库，能读写 .tar.gz 压缩包（就是"一坨文件的压缩集合"）
with tarfile.open(RAW_TAR, "r:gz") as tar:
    member = tar.getmember("BGLR/data/wheat.RData")
    rdata_bytes = tar.extractfile(member).read()
print(f"从压缩包中读出 wheat.RData: {len(rdata_bytes)} 字节")

# ------------------------------------------- 第 2 步：把 R 的二进制文件解析成 Python 对象
# rdata 这个库专门干这件事：读 R 保存的 .RData / .rda 文件
parsed = rdata.parser.parse_file(io.BytesIO(rdata_bytes))
objects = rdata.conversion.convert(parsed)
print("解析出的对象名:", list(objects.keys()))

# 小坑记录: wheat.X / wheat.Y / wheat.A 被 rdata 转成了 xarray 对象(要用 .values 取值)，
# 但 wheat.sets 直接就是 numpy 数组。用 np.asarray() 把两种都统一成 numpy 数组。
X_da = np.asarray(objects["wheat.X"].values)   # 基因型
Y_da = np.asarray(objects["wheat.Y"].values)   # 表型
A_da = np.asarray(objects["wheat.A"].values)   # 亲缘关系矩阵
sets_da = np.asarray(objects["wheat.sets"])    # 环境编号 (本来就是 numpy 数组)

# ------------------------------------------- 第 3 步：转成 pandas 表格（DataFrame）
# .values 把 xarray 的包装撕掉，露出里面的 numpy 数组
X = pd.DataFrame(X_da, dtype=np.int8)
Y = pd.DataFrame(Y_da, dtype=float)
A = pd.DataFrame(A_da, dtype=float)
sets = pd.Series(sets_da.ravel(), name="env")

# 给行列起名字，方便人看
X.columns = [f"m{i + 1}" for i in range(X.shape[1])]
X.index = [f"line{i + 1}" for i in range(X.shape[0])]
Y.columns = [f"env{i + 1}" for i in range(Y.shape[1])]
Y.index = X.index
A.columns = X.index
A.index = X.index
sets.index = X.index

# ---------------------------------------------------------------- 第 4 步：打印体检报告
print()
print("=" * 50)
print("数据体检")
print("=" * 50)
print(f"基因型矩阵 X : {X.shape}   <- (品系数, 标记数)")
print(f"表型矩阵   Y : {Y.shape}   <- (品系数, 环境数)")
print(f"亲缘矩阵   A : {A.shape}")
print()
print("X 的取值种类:", np.unique(X_da))
print("X 中 1 的比例: %.3f" % X_da.mean())
print()
print("Y 前 3 行:")
print(Y.head(3).to_string())
print()
print("Y 各环境缺失值个数:")
print(Y.isna().sum().to_string())
print()
print("Y 各环境的均值 / 标准差:")
print(pd.DataFrame({"mean": Y.mean(), "std": Y.std()}).to_string())
print()
print("环境编号分布 (wheat.sets):")
print(sets.value_counts().sort_index().to_string())
print()
print("A 矩阵对角线前 5 个:", np.round(A.values.diagonal()[:5], 4))
print("A 矩阵取值范围: %.3f ~ %.3f" % (A.values.min(), A.values.max()))

# ---------------------------------------------------------------- 第 5 步：存成 CSV
X.to_csv(DATA_DIR / "wheat_X.csv")
Y.to_csv(DATA_DIR / "wheat_Y.csv")
A.to_csv(DATA_DIR / "wheat_A.csv")
sets.to_csv(DATA_DIR / "wheat_sets.csv", index=False)
print()
print("已写出 4 个 CSV 到", DATA_DIR)
