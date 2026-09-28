"""
数据准备：把 BGLR 的 wheat 数据集转成 CSV。

用法: python scripts/00_prepare_data.py
输入: data/raw/BGLR_1.1.4.tar.gz
输出: data/wheat_X.csv, wheat_Y.csv, wheat_A.csv, wheat_sets.csv
"""

import io
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import rdata

# Windows 终端默认 GBK，中文输出会乱码
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RAW_TAR = ROOT / "data" / "raw" / "BGLR_1.1.4.tar.gz"
DATA_DIR = ROOT / "data"

if not RAW_TAR.exists():
    raise SystemExit(
        f"缺少 {RAW_TAR}\n"
        "先下载: Invoke-WebRequest -Uri "
        "\"https://mirrors.tuna.tsinghua.edu.cn/CRAN/src/contrib/BGLR_1.1.4.tar.gz\" "
        f"-OutFile \"{RAW_TAR}\""
    )

# 取出 wheat.RData。CRAN 的源码包里 data/ 下就是原始数据集，不需要装 R
with tarfile.open(RAW_TAR, "r:gz") as tar:
    rdata_bytes = tar.extractfile(tar.getmember("BGLR/data/wheat.RData")).read()

# rdata 负责解析 R 的二进制格式
objects = rdata.conversion.convert(rdata.parser.parse_file(io.BytesIO(rdata_bytes)))

# wheat.X/Y/A 被转成 xarray 对象，wheat.sets 直接是 ndarray，统一成 numpy
X = pd.DataFrame(np.asarray(objects["wheat.X"].values), dtype=np.int8)
Y = pd.DataFrame(np.asarray(objects["wheat.Y"].values), dtype=float)
A = pd.DataFrame(np.asarray(objects["wheat.A"].values), dtype=float)
sets = pd.Series(np.asarray(objects["wheat.sets"]).ravel(), name="env")

X.index = [f"line{i + 1}" for i in range(X.shape[0])]
X.columns = [f"m{i + 1}" for i in range(X.shape[1])]
Y.index = X.index
Y.columns = [f"env{i + 1}" for i in range(Y.shape[1])]
A.index = X.index
A.columns = X.index
sets.index = X.index

print(f"基因型 X: {X.shape}  取值 {np.unique(X.values).tolist()}  1 的比例 {X.values.mean():.3f}")
print(f"表型   Y: {Y.shape}  每个环境均值 {np.round(Y.mean().values, 6).tolist()}")
print(f"亲缘   A: {A.shape}  对角均值 {np.diag(A.values).mean():.3f}")
print(f"环境分组: {sorted(int(s) for s in sets.unique())}  每组样本数 {np.bincount(sets.values)[1:].tolist()}")

X.to_csv(DATA_DIR / "wheat_X.csv")
Y.to_csv(DATA_DIR / "wheat_Y.csv")
A.to_csv(DATA_DIR / "wheat_A.csv")
sets.to_csv(DATA_DIR / "wheat_sets.csv", index=False)
print(f"已写出 4 个 CSV -> {DATA_DIR}")
