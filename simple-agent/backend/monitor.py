import os
import time
from loguru import logger

from monitor.metrics import metrics_aggregator
from monitor.trace_store import trace_store
from monitor.report import report_generator
from monitor.diagnosis import shapley_diagnosis

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logger.add(
    os.path.join(LOG_DIR, "monitor_{time}.log"),
    rotation="1 hour",
    retention="7 days",
    encoding="utf-8",
)

POLL_INTERVAL = 5
_seen_tasks = set()
_diagnosed_tasks = set()


def monitor_loop():
    logger.info("monitor service started, poll interval = {}s", POLL_INTERVAL)
    while True:
        try:
            m = metrics_aggregator.get_global_metrics()
            logger.info(
                "GLOBAL | total={total} | success={success} | failed={failed} | "
                "running={running} | avg_duration_ms={avg_duration_ms} | "
                "avg_tokens={avg_tokens} | total_tool_calls={total_tool_calls}",
                **m,
            )

            for trace in trace_store.list_traces(limit=20):
                if trace.trace_id in _seen_tasks:
                    continue
                _seen_tasks.add(trace.trace_id)
                duration = (
                    (trace.end_time - trace.start_time) * 1000
                    if trace.end_time else 0
                )
                logger.info(
                    "TASK | id={} | status={} | duration_ms={:.0f} | tokens={} | "
                    "steps={} | content={}",
                    trace.trace_id[:8], trace.status, duration,
                    trace.total_tokens, trace.total_tool_calls,
                    (trace.task_content or "")[:80],
                )

            # 对存在问题（失败 / 失败 span / 命中异常）的任务输出根因诊断
            for trace in report_generator._collect_problem_traces(limit=20):
                if trace.trace_id in _diagnosed_tasks:
                    continue
                _diagnosed_tasks.add(trace.trace_id)
                diagnosis = shapley_diagnosis.get_root_cause(trace)
                logger.warning(
                    "DIAG | id={} | root_cause={}({}) | confidence={}% | anomalies={} | evidence={}",
                    trace.trace_id[:8],
                    diagnosis["root_cause_layer"],
                    diagnosis["root_cause_name"],
                    diagnosis["confidence"],
                    ",".join(a["rule_id"] for a in diagnosis["anomalies"]) or "-",
                    "; ".join(e["error"] for e in diagnosis["evidence"] if e["error"])[:160] or "-",
                )

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("monitor service stopped")
            break
        except Exception as e:
            logger.exception("monitor loop error: {}", e)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    monitor_loop()
