import uuid

TRACE_ID_HEADER = "X-Trace-Id"


def new_trace_id() -> str:
    return uuid.uuid4().hex
