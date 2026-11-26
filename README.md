# 鹿栖育苗 · 补光基准台

为温室更换不同批次的照度探头时建立可追溯的分位换算。基准段断档时保留现行系数，交接记录带上当时签发的系数版本。

## 谁在用

鹿栖育苗有东、西两个温室和六名轮班人员。东棚扦插台换上新批次 LX-26B 后，旧表和新表显示的补光水平不同。班长原来在 Excel 用一列比值换算，采样岗另用聊天附件传基准表。常遇到三种问题：同名附件来自不同架位，遮光和补光档混算，改过公式的表覆盖上一班历史记录。

上游是架位标签、基准表序列号和同秒采样。工作台负责安装登记、分段见证、经验分位拟合、签发和逐笔换算。下游育苗负责人从交接页面取当天版本化 CSV，沿用原有温室日报。

| 账号 | 角色 | 页面与典型动作 |
|---|---|---|
| yu | technician · 采样岗 | 登记亮暗段、申报拟合、抄录现场读数 |
| tang | supervisor · 校准班长 | 登记或暂停探头、签署或作废待见证段、签发换算、抄录读数 |
| lin | viewer · 育苗查阅 | 核对安装和见证、浏览系数、下载交接 CSV |

三个演示账号的密码都是 `SeedLight2026!`。部署到共享环境前更换 DB 和 JWT 凭据，并关闭演示 seed。

## 早班剧本

1. 11 月 24 日 05:50，班长打开「探头标本」，核对东二台 EQ-214，离台面 85 cm，基准表 REF-072。
2. 06:00，采样岗登记亮档附件 `east-1124-high-0600.csv` 的同秒读数，班长签字。
3. 06:10，提交附件 `east-1124-wrong-0610.csv` 时误录 REF-999，班长拒绝见证并作废。
4. 06:20，亮档末段通过见证。尝试拟合 06:00–06:30 时，后台列出 06:10 缺口。06:10 的暗档记录不可替代它。
5. 班长拒签失败候选，采样岗仍可用 Q-DEMO-EAST 记录 06:02 的 480 lx 测量。
6. 核对纸质记录后，采样岗以 `east-1124-high-recapture-0610.csv` 补录亮档中段，班长签证。
7. 采样岗重提原窗口。班长检查三段证据、留出误差和分位节点后签发，旧系数进入「已替换」。
8. 06:12，采样岗记录 480 lx。育苗人员下载 `light-shift-2026-11-24.csv`，在同一张交接单上看到新旧换算版本。

## 换算方法

每个窗口按探头、档位、基准日期隔离，至少连续三个已签字的十分钟段。每段最后一对读数作为留出点。训练原始和基准光照分别拟合 `QuantileTransformer(output_distribution="uniform")`，取最多 17 个经验分位节点。用原读数的经验概率在基准分位表逆插值，换算为 lx。版本存储训练与留出点数、留出原始及校准 MAE、Pearson 同秒趋势、输入 SHA256 及固定种子 77。样本范围不足 100 lx 或同秒 Pearson 小于 0.85 会拒绝拟合。交接时对时间和读数均禁止外推。

签证后的参考段禁止改动，但班长发现基准表与探头对时偏差时可撤回见证：原读数和签字留档复核，用到该段的待签候选退回「等待补采」，撤回时正在拟合的候选算完同样退回；已签发的现行曲线照常使用。补采段见证齐全后，等待中的候选自动在原记录下重新排队拟合，等待期间其他窗口照常拟合。每次拟合都登记所用采样段与输入摘要，新旧拟合均可复查，后台重试不会重复登记同一组采样的结果。

班长只能在相同日期、档位和时段替换现行版本。切换用安装点行锁、现行槽唯一约束和单事务，写入读数也锁同一安装点。旧读数凭证继续引用原换算。

## 运行

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
# 清理本项目演示数据
docker compose down -v --remove-orphans
```

浏览器打开 `http://127.0.0.1:18301/`，FastAPI 文档在 `http://127.0.0.1:19301/docs`。MySQL 映射 17801，Redis 只在容器网内可达。Nginx 将 `/api/` 代理到 FastAPI。

| 服务 | 技术 | 职责 |
|---|---|---|
| frontend | nginx 1.27、HTML/CSS/ES modules | 植物标本式安装标签、时段见证、分位表、交接凭证 |
| backend | Python 3.12、FastAPI、SQLAlchemy | JWT、事务写入、照度换算接口、审计 |
| worker | Python、scikit-learn、Redis 消息通知 | 后台拟合候选，从数据库持久化待处理任务恢复 |
| db | MySQL 8 | 安装、采样段、系数、读数、账号与审计 |
| redis | Redis 7 | 唤醒队列和 AOF |

本机开发可沿用 Compose 的数据库与 Redis，设置 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，在 backend 建立 Python 3.12 虚拟环境并安装 requirements，再运行 `uvicorn lab.app:app --reload` 和 `python -m lab.worker`。只调界面可直接修改静态文件后重建 frontend。

| 环境变量 | 默认用途 |
|---|---|
| FRONTEND_PORT / BACKEND_PORT / DB_PORT | 宿主机访问端口 |
| MYSQL_DATABASE / MYSQL_USER / MYSQL_PASSWORD / MYSQL_ROOT_PASSWORD | MySQL 库名及账号 |
| JWT_SECRET | JWT 签名 |
| SEED_DEMO | 启动后插入缺少的演示自然键；现有记录保留 |
| REDIS_URL / DATABASE_URL | 本地开发可覆盖内部连接 |

目录 `backend/lab` 按安装、见证、候选签发和读数组织。数据库初建由 ORM 模型生成。脚本和演示采样值在 `backend/scripts`。`frontend/src` 按 API、页面、状态和业务组件组织。档位和状态由后端 `lab/constants.py` 约束，分别用于 `segment_schema.py`、`segment_service.py`、`calibration_schema.py`、`calibration_service.py` 和 `readings.py`。前端映射位于 `src/constants.js`，由 `components/common.js`、`components/shell.js`、`pages/segments.js`、`pages/calibrations.js` 和 `pages/readings.js` 消费。

代码在本地批次内交付。当前仓库未指定单独的开源许可证。
