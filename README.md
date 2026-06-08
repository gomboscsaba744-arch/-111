# 🌍 Global Order Pipeline (全球订单自动化流水线)

## 项目背景
这是一个全链路自动化系统，主要用于跨境电商订单的处理。
项目的前身是两个独立运作的 Python 脚本：
1. **CPF 自动查名脚本**：依靠 Telegram 机器人自动发送 CPF，进行数学验证码识别，并抓取客户姓名。
2. **DSers 自动改名脚本**：将含有姓名的 Excel 导入，利用 Playwright 控制浏览器，自动前往 DSers 平台给对应订单修改 Contact Name 并保存。

## 当前需求拓展 (4 大模式)
该项目整合了原有的两个脚本，并引入了“马帮 ERP 订单自动导出及格式清洗”功能，提供统一的终端菜单 (`main.py`)：

1. **模式 1 (完整全链路)**：输入天数 -> 从马帮ERP导出对应天数内的订单 -> 自动将马帮Excel清洗转换为标准模板 -> 去 Telegram 查CPF名字 -> 去 DSers 自动修改名字 -> 自动全选批量下单。
2. **模式 2 (仅修改 DSers 订单)**：跳过前面步骤，直接提供已查好名字的 Excel 表格，程序去 DSers 执行改名和批量下单。
3. **模式 3 (仅查询 CPF 名字)**：直接提供含有空白姓名和CPF的 Excel 表格，程序去 Telegram 查名字。
4. **模式 4 (仅导出及查询)**：输入天数 -> 马帮导出 -> Excel 格式化清洗 -> 去 Telegram 查CPF名字。

## 项目目录结构
- `main.py`: 项目的交互式主入口程序。
- `config.yaml`: 全局配置文件，包含各平台账号密码和 URL。
- `modules/`:
  - `telegram_cpf.py`: 封装的 CPF 查询模块（已完工）。
  - `dsers_automator.py`: 封装的 DSers 改名与下单模块（改名已完工，批量下单待新增）。
  - `mabang_scraper.py`: 负责登录马帮、筛选天数并下载导出 Excel 订单（待开发）。
  - `excel_processor.py`: 负责将马帮的生数据提取并映射为下游需要的模板格式（待开发）。
- `data/`: 存放运行中产生的文件（如 `raw_mabang/` 和 `processed_orders/`）。
- `sessions/`: 存放浏览器持久化上下文（免密登录）。

## 待办事项 (TODO)
- [ ] 开发 `mabang_scraper.py`，根据 `config.yaml` 提供的账号密码登录马帮 ERP 并自动化导出表格。
- [ ] 用户需提供从马帮导出的表头信息，以便开发 `excel_processor.py` 实现表格无缝衔接。
- [ ] 在 `dsers_automator.py` 中补充“批量下单”的自动化逻辑。
