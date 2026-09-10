import threading
import time
import asyncio
import traceback
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime

class TaskInfo:
    def __init__(self, task_id: str, name: str, category: str = "General"):
        self.task_id = task_id
        self.name = name
        self.category = category
        self.status = "PENDING"  # PENDING, RUNNING, PAUSED, SUCCESS, FAILED, CANCELLED
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.logs: List[str] = []
        self.error: Optional[str] = None
        self.action_required: Optional[str] = None
        self.result: Any = None
        self.current_progress: int = 0
        self.total_progress: int = 0
        self.progress_text: str = ""
        self.progress_percent: Optional[float] = None
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._is_paused = False
        self._accumulated_seconds: float = 0.0
        self._last_resume_time: Optional[datetime] = None
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_task: Optional[asyncio.Task] = None
        self._active_contexts: List[Any] = []

    def register_context(self, context):
        """注册关联的 Playwright BrowserContext，以便在终止任务时立即关闭"""
        with self._lock:
            if context not in self._active_contexts:
                self._active_contexts.append(context)

    def set_action_required(self, text: str):
        with self._lock:
            self.action_required = text

    def _extract_action_required_from_log(self, msg: str):
        import re
        if not msg or self.action_required:
            return
        # 1. 匹配“需配置选项: ...” / “需选择选项: ...” / “需处理选项: ...”
        m1 = re.search(r'(?:需配置选项|需选择选项|需处理选项|需要选项|阻断拦截|阻断提示|拦截原因)[：:\s]+([^\n，。]+)', msg)
        if m1:
            self.action_required = m1.group(1).strip()
            return
        # 2. 匹配“提示【请选择...】” / “店小秘提示: 请选择...”
        m2 = re.search(r'(?:提示|报错|拦截)[：:【\[]\s*(请选择[^\n，。】\]]+|请填写[^\n，。】\]]+|未选择[^\n，。】\]]+|缺少[^\n，。】\]]+)', msg)
        if m2:
            self.action_required = m2.group(1).strip()
            return
        # 3. 匹配常见特定短语 “请选择物流属性” / “请选择运费模板” / “请选择服务模板” / “请选择发货期” 等
        m3 = re.search(r'(请选择(?:物流属性|运费模板|服务模板|发货期|包装|类目|品牌|属性|国家|仓库|SKU|商品|选项)[^\n，。】\]]*)', msg)
        if m3:
            self.action_required = m3.group(1).strip()
            return
        # 4. 任意带有告警/错误标志的“请选择...”
        if any(k in msg for k in ["⚠️", "❌", "提示", "错误", "拦截", "弹窗"]):
            m4 = re.search(r'(请选择[^\s，。！？【】\[\]]+)', msg)
            if m4:
                self.action_required = m4.group(1).strip()
                return

    def _extract_progress_from_log(self, msg: str):
        import re
        # 0. 过滤掉流程控制类 [步骤 X/Y]，防止把步骤序号误匹配为商品数量
        cleaned_msg = re.sub(r'\[?步骤\s*\d+\s*[/／]\s*\d+\]?', '', msg)

        # 1. 匹配 X/Y (例如: 15/120 条, 30/50 件, 现在是 15/120)
        m = re.search(r'(\d+)\s*[/／]\s*(\d+)', cleaned_msg)
        if m and any(k in msg for k in ["进度", "处理", "更新", "修改", "条", "件", "单", "现在是", "重试", "回填"]):
            curr, total = int(m.group(1)), int(m.group(2))
            if total > 0 and curr <= total:
                self.current_progress, self.total_progress = curr, total
                unit = "件" if ("件" in msg or "商品" in msg or "库存" in self.name) else "条"
                prefix = "重试 " if "重试" in msg else ""
                self.progress_text = f"{prefix}{curr}/{total} {unit}"
                return

        # 2. 匹配店小秘弹窗进度文本: 已成功修改 7 个产品 / 失败了 0 个
        m_dxm = re.search(r'(?:已成功修改|成功修改|成功)\s*(\d+)\s*个', cleaned_msg)
        if m_dxm:
            succ = int(m_dxm.group(1))
            fail = 0
            m_fail = re.search(r'(?:失败了|失败)\s*(\d+)\s*个', cleaned_msg)
            if m_fail:
                fail = int(m_fail.group(1))
            curr = succ + fail
            self.current_progress = curr
            unit = "件" if ("件" in msg or "商品" in msg or "库存" in self.name) else "条"
            if self.total_progress > 0:
                self.progress_text = f"{curr}/{self.total_progress} {unit}"
            else:
                self.progress_text = f"{curr} {unit}"
            return

        # 3. 匹配单条总量 (例如: 共 120 条, 共需修改 50 件)
        m_tot = re.search(r'共\s*(?:需修改\s*)?(\d+)\s*(?:条|件)', cleaned_msg)
        if m_tot:
            n = int(m_tot.group(1))
            if self.total_progress == 0:
                self.total_progress = n
            if not self.progress_text or "/" not in self.progress_text:
                unit = "件" if ("件" in msg or "库存" in self.name) else "条"
                self.progress_text = f"共 {n} {unit}"
            return

        # 4. 完成
        if any(k in msg for k in ["所有任务执行完毕", "圆满完成", "全部完成", "已更新完成", "全部步骤执行完毕", "批量修改已成功全部完成"]):
            if self.total_progress > 0:
                self.current_progress = self.total_progress
                unit = "件" if "库存" in self.name else "条"
                self.progress_text = f"{self.total_progress}/{self.total_progress} {unit}"
            else:
                self.progress_text = "已完成"

    def set_progress(self, current: int, total: int, prefix: str = "", unit: str = "条"):
        with self._lock:
            self.current_progress = current
            self.total_progress = total
            if total > 0:
                self.progress_percent = min(100.0, max(0.0, round(current / total * 100, 1)))
                pfx = f"{prefix} " if prefix else ""
                self.progress_text = f"{pfx}{current}/{total} {unit}"
            else:
                self.progress_text = f"{current} {unit}"

    def append_log(self, msg: str):
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{ts}] {msg}"
            self.logs.append(log_line)
            if len(self.logs) > 500:
                self.logs.pop(0)
            try:
                self._extract_progress_from_log(msg)
                self._extract_action_required_from_log(msg)
            except Exception:
                pass

    def get_logs(self) -> List[str]:
        with self._lock:
            return list(self.logs)

    def get_duration_seconds(self) -> int:
        with self._lock:
            secs = self._accumulated_seconds
            if self.status == "RUNNING" and self._last_resume_time:
                secs += (datetime.now() - self._last_resume_time).total_seconds()
            return int(max(0, secs))

    def get_duration_str(self) -> str:
        seconds = self.get_duration_seconds()
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def request_cancel(self):
        with self._lock:
            if self._last_resume_time:
                self._accumulated_seconds += (datetime.now() - self._last_resume_time).total_seconds()
                self._last_resume_time = None
            self._cancel_requested = True
            self._is_paused = False
            self.status = "CANCELLED"
            self.end_time = datetime.now()
        self.append_log("⚠️ 收到用户终止任务请求，正在强行终止运行并关闭浏览器...")
        
        # 1. 立即给原生协程发信号中断 (打破 await 等阻塞)
        if self._async_loop and self._async_task and not self._async_task.done():
            try:
                self._async_loop.call_soon_threadsafe(self._async_task.cancel)
            except Exception:
                pass

        # 2. 强行关闭已注册的 Playwright context
        for ctx in list(self._active_contexts):
            try:
                if self._async_loop and self._async_loop.is_running():
                    self._async_loop.call_soon_threadsafe(lambda c=ctx: asyncio.create_task(c.close()))
            except Exception:
                pass

    def run_async(self, coro):
        """
        供外部同步线程执行协程，并将事件循环句柄挂载到 TaskInfo 上，以便随时可以被 cancel 终止
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._async_loop = loop
        
        async def _async_runner():
            self._async_task = asyncio.create_task(coro)
            try:
                return await self._async_task
            except asyncio.CancelledError:
                raise RuntimeError("TASK_CANCELLED_BY_USER")
        try:
            return loop.run_until_complete(_async_runner())
        finally:
            self._async_loop = None
            self._async_task = None
            try:
                loop.close()
            except Exception:
                pass

    def pause(self):
        with self._lock:
            if self.status == "RUNNING":
                if self._last_resume_time:
                    self._accumulated_seconds += (datetime.now() - self._last_resume_time).total_seconds()
                    self._last_resume_time = None
                self._is_paused = True
                self.status = "PAUSED"
        self.append_log("⏸ 任务已由用户在看板中临时暂停...")

    def resume(self):
        with self._lock:
            if self.status == "PAUSED":
                self._last_resume_time = datetime.now()
                self._is_paused = False
                self.status = "RUNNING"
        self.append_log("▶ 任务已恢复继续执行...")

    def check_pause(self):
        """流水线执行过程中轮询调用，支持随时挂起等待"""
        while self._is_paused and not self._cancel_requested:
            time.sleep(0.3)
        if self._cancel_requested:
            raise RuntimeError("TASK_CANCELLED_BY_USER")

    async def async_check_pause(self):
        """异步协程执行过程中挂起等待与取消检查"""
        while self._is_paused and not self._cancel_requested:
            await asyncio.sleep(0.3)
        if self._cancel_requested:
            raise RuntimeError("TASK_CANCELLED_BY_USER")

    @property
    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    @property
    def is_paused(self) -> bool:
        return self._is_paused


class TaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance._tasks: Dict[str, TaskInfo] = {}
                cls._instance._threads: Dict[str, threading.Thread] = {}
        return cls._instance

    def submit_task(
        self,
        task_id: str,
        name: str,
        target_fn: Callable,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        category: str = "General",
        on_progress: Optional[Callable[[str], None]] = None
    ) -> TaskInfo:
        kwargs = kwargs or {}
        
        # 如果已经存在运行中或暂停的相同 task_id，先检查状态
        if task_id in self._tasks:
            existing = self._tasks[task_id]
            if existing.status in ("RUNNING", "PAUSED"):
                return existing

        task_info = TaskInfo(task_id, name, category)
        self._tasks[task_id] = task_info

        def _runner():
            with task_info._lock:
                task_info.status = "RUNNING"
                task_info.start_time = datetime.now()
                task_info._last_resume_time = datetime.now()
                task_info._accumulated_seconds = 0.0
            task_info.append_log(f"🚀 任务【{name}】已在后台独立线程中启动...")
            
            def _progress_callback(msg: str):
                task_info.append_log(msg)
                task_info.check_pause()
                if on_progress:
                    try:
                        on_progress(msg)
                    except Exception:
                        pass

            try:
                # 检查 target_fn 是否为异步协程函数
                if asyncio.iscoroutinefunction(target_fn):
                    if 'progress_callback' in target_fn.__code__.co_varnames:
                        kwargs['progress_callback'] = _progress_callback
                    if 'task_info' in target_fn.__code__.co_varnames:
                        kwargs['task_info'] = task_info
                    res = task_info.run_async(target_fn(*args, **kwargs))
                else:
                    if 'progress_callback' in target_fn.__code__.co_varnames:
                        kwargs['progress_callback'] = _progress_callback
                    if 'task_info' in target_fn.__code__.co_varnames:
                        kwargs['task_info'] = task_info
                    res = target_fn(*args, **kwargs)

                if task_info.status != "CANCELLED":
                    with task_info._lock:
                        if task_info._last_resume_time:
                            task_info._accumulated_seconds += (datetime.now() - task_info._last_resume_time).total_seconds()
                            task_info._last_resume_time = None
                        task_info.result = res
                        task_info.status = "SUCCESS"
                        task_info.end_time = datetime.now()
                        if task_info.total_progress > 0:
                            task_info.current_progress = task_info.total_progress
                            task_info.progress_percent = 100.0
                            unit = "件" if "库存" in task_info.name else "条"
                            task_info.progress_text = f"{task_info.total_progress}/{task_info.total_progress} {unit}"
                    task_info.append_log(f"✅ 任务【{name}】圆满完成，耗时 {task_info.get_duration_str()}。")
            except Exception as e:
                with task_info._lock:
                    if task_info._last_resume_time:
                        task_info._accumulated_seconds += (datetime.now() - task_info._last_resume_time).total_seconds()
                        task_info._last_resume_time = None
                    if task_info._cancel_requested:
                        task_info.status = "CANCELLED"
                        task_info.end_time = datetime.now()
                        task_info.append_log(f"⚠️ 任务【{name}】已成功取消终止。")
                    else:
                        task_info.status = "FAILED"
                        task_info.end_time = datetime.now()
                        task_info.error = str(e)
                        task_info._extract_action_required_from_log(str(e))
                        tb = traceback.format_exc()
                        task_info.append_log(f"❌ 任务【{name}】发生异常: {e}\n{tb}")
                        if task_info.action_required:
                            task_info.append_log(f"🔔 看板提示：该任务需要配置选项【{task_info.action_required}】")

        t = threading.Thread(target=_runner, daemon=True, name=f"TaskWorker-{task_id}")
        self._threads[task_id] = t
        t.start()
        return task_info

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskInfo]:
        return list(self._tasks.values())

    def get_active_tasks(self) -> List[TaskInfo]:
        return [t for t in self._tasks.values() if t.status in ("RUNNING", "PAUSED")]

    def cancel_task(self, task_id: str):
        task = self.get_task(task_id)
        if task and task.status in ("RUNNING", "PAUSED"):
            task.request_cancel()
            task.status = "CANCELLED"
            task.end_time = datetime.now()

    def pause_task(self, task_id: str):
        task = self.get_task(task_id)
        if task and task.status == "RUNNING":
            task.pause()

    def resume_task(self, task_id: str):
        task = self.get_task(task_id)
        if task and task.status == "PAUSED":
            task.resume()


# 全局单例
global_task_manager = TaskManager()
