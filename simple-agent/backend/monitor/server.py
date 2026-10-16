from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .report import report_generator
from .trace_store import trace_store
from .metrics import metrics_aggregator
from .diagnosis import shapley_diagnosis
from .anomaly import anomaly_detector

app = FastAPI(title="Monitor Agent", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def index():
    return {"service": "monitor-agent", "status": "running"}


@app.get("/report")
def get_full_report():
    """获取完整监控诊断报告（含 Shapley 根因分析）"""
    return report_generator.generate_full_report()


@app.get("/metrics")
def get_metrics():
    return metrics_aggregator.get_global_metrics()


@app.get("/metrics/layer")
def get_layer_metrics():
    return metrics_aggregator.get_layer_metrics()


@app.get("/metrics/tool")
def get_tool_metrics():
    return metrics_aggregator.get_tool_metrics()


@app.get("/traces")
def list_traces(limit: int = 20, status: str = None):
    traces = trace_store.list_traces(limit=limit, status=status)
    return [t.dict() for t in traces]


@app.get("/anomalies")
def list_anomalies(limit: int = 50):
    """列出所有命中异常规则的 trace 及其实时检测结果"""
    result = []
    for trace in trace_store.list_traces(limit=limit):
        anomalies = anomaly_detector.detect(trace)
        if anomalies:
            result.append({
                "trace_id": trace.trace_id,
                "task_content": (trace.task_content or "")[:80],
                "status": trace.status,
                "anomalies": anomalies,
            })
    return result


@app.get("/trace/{trace_id}")
def get_trace(trace_id: str):
    trace = trace_store.get_trace(trace_id)
    if not trace:
        return {"error": "Trace not found"}
    diagnosis = shapley_diagnosis.get_root_cause(trace)
    return {"trace": trace.dict(), "diagnosis": diagnosis}
