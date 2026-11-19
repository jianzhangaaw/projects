# 验证记录

不是「在我机器上能跑」，而是每一项都复制到 `%TEMP%\pf-verify` 这类干净目录、按 README 的命令从零执行，贴的是实际退出码与产物。

**环境**：Windows 11、Python 3.14.0、JDK 17.0.14、Node 24.18、Docker 29.6（MySQL 8.0.46 容器）

| 项目 | 执行的命令 | 结果 |
| --- | --- | --- |
| 01 MNIST | `python src/mnist_dim_reduction.py` | exit 0，55 秒，5 种算法指标全部输出，11 张图重生成；t-SNE trustworthiness 0.9895 |
| 02 关联规则 | `python run_all.py` | exit 0，29.5 秒，正确性校验 → 实验一~五 → 11 张图，全部重跑成功 |
| 03 Titanic | `python src/analyze.py` | exit 0，输出 6 张图 + `results.json`（93 个键），控制台报告完整 |
| 04 Spaceship | `python src/run_experiment.py --models logreg --seeds 42` | exit 0，5 折 0.4 秒，acc=0.7921 auc=0.8623，`out/cv_summary.json` 落盘 |
| 05 智聘通 | `docker compose up -d` → `mvnw -s settings.xml -DskipTests package` → `java -jar ...` → `npm run dev` | 容器 healthy；jar 构建 exit 0；登录接口返回 200 + JWT；前端 5173 返回 200；学生端四个页面截图正常，种子数据正确渲染 |
| 06 小程序 | `node tools/check-miniprogram.js .` | 49 项通过、0 失败（页面完整性 / JSON / JS 语法 / WXML 配对 / 188 条词库 / 记忆算法 17 项断言） |
| 07 Java Swing | `javac -encoding UTF-8 -d build src/*.java` → `java -cp build Shot docs` | 编译 exit 0，10 个 class；窗口渲染出登录页与主界面，6 条学生数据正确显示 |
| 08 网页 | 用 Chrome 打开 `index.html` 截图 | 3 张截图，无失败请求；26 张照片引用全部命中磁盘 |

## 这一轮修掉的问题

都是「原目录能跑、换地方就不行」或「根本跑不通」的：

1. **01**：`data/` 里的 14 MB npz 不进仓库，README 里写清了首次运行的两个数据获取脚本。
2. **03**：脚本里 6 个 `↔`（U+2194）和 2 个 `²`（U+00B2）在 GBK 控制台上抛 `UnicodeEncodeError`，原样跑必崩。已换成 ASCII，并在文件头加了 stdout UTF-8 兜底。
3. **04**：`raw/` 里原本有 4 份逐字节相同的镜像数据（A/B/HF1/HF2），只保留了一份；TabPFN 改为可选，不装也能跑其余四类模型。
4. **05**：
   - `application.yml` 里有明文的远程 MySQL 密码和阿里云 OSS AccessKey，全部改为环境变量、默认值指向本地 compose；
   - `student_skill` / `student_experience` 实体有 `fileId` 字段但建表语句没有这一列，`/api/student/skills/by-student` 直接 500——补列；
   - `company_draft` 表整个缺失，但 `CompanyController` 和 `AdminReviewController` 都在用——补建表；
   - `schema.sql` 在容器里初始化时没声明字符集，CHECK 约束里的中文被当成 latin1，导致任何中文取值都通不过——文件头加 `SET NAMES utf8mb4`；
   - 删掉 59 MB 的 vite 错误日志和 `node_modules` / `target`。
5. **06**：本机装不了微信开发者工具（安装器需要 UAC 提权，无人值守装不上），改为静态校验 + 核心算法单测；README 里如实写明运行需要开发者工具。
6. **07**：补了 `run.bat`；截图脚本改成直接渲染窗口到 PNG，绕开 DPI 缩放导致的屏幕拷贝错位。
7. **08**：
   - 图片路径全是 `C:\Users\...\Desktop\源代码\photos\...` 绝对路径，换机器必裂——全部改相对路径；
   - 5 张图指向 `picsum.photos`，该站本机不可达——换成本地文件（实景照片裁剪 + 生成的字母头像）；
   - 26 张 PNG 共 19.3 MB，转 JPEG 后 4.8 MB。

## 没做到的事

- **06 的模拟器截图**：微信开发者工具需要 UAC 提权安装，这台机器上无人值守装不了。静态校验能证明代码结构自洽、算法正确，但「界面长什么样」需要自己在开发者工具里看一眼。
- **05 的企业端 / 管理端**：接口与页面都在，但截图只做了学生端。企业端登录（`company01`）我没有逐页点过，只验证了登录与岗位列表接口。
- **04 的 TabPFN 全量**：只验证了 `logreg` 单模型单种子的流程可跑，没有重跑 5 折 × 3 种子（约 70 分钟）和 TabPFN（约 68 分钟）。
