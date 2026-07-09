import threading

# Single lock to handle serialization of all side effects and eliminate deadlocks.
_lifecycle_lock = threading.Lock()


def _send_email(kind: str, booking) -> None:
    pass


def _write_audit(kind: str, booking) -> None:
    pass


def notify_created(booking) -> None:
    with _lifecycle_lock:
        _send_email("created", booking)
        _write_audit("created", booking)


def notify_cancelled(booking) -> None:
    with _lifecycle_lock:
        _write_audit("cancelled", booking)
        _send_email("cancelled", booking)
