"""Host-level telemetry."""
import psutil, time

def snapshot():
    vm = psutil.virtual_memory()
    io = psutil.disk_io_counters()
    net = psutil.net_io_counters()
    return {
        "ts": time.time(),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_used_bytes": vm.used,
        "memory_percent": vm.percent,
        "disk_read_bytes": io.read_bytes if io else None,
        "disk_write_bytes": io.write_bytes if io else None,
        "net_sent_bytes": net.bytes_sent if net else None,
        "net_recv_bytes": net.bytes_recv if net else None,
    }
