# 门店履约分析

`01_fulfillment_pandas.ipynb` 读取 SQLite 汇总查询，完成字段检查、门店与整体指标计算、两张图表、分析结论和 CSV 导出。

在项目根目录启动：

```bash
bash scripts/start_notebook.sh
```

在浏览器访问启动日志中的本地地址，使用已配置的 Jupyter 身份验证。服务绑定 127.0.0.1。

无交互运行并保存输出：

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/01_fulfillment_pandas.ipynb
```

依赖见根目录 `requirements-notebook.txt`。WSL 中文图表使用 `/mnt/c/Windows/Fonts/msyh.ttc`。CSV 和 PNG 保存于 `reports/`，检查结果见 `checks/notebook_validation.json`。
