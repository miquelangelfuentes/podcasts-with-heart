"""
Hardware Compatibility and System Diagnostic Module for Podcasts with Heart.
Inspects local hardware (disk storage, RAM, CPU logical cores, GPU/ONNX Runtime acceleration, and network)
to assess readiness for 100% offline neural voice synthesis (Kokoro-82M & Piper TTS).
"""

import os
import sys
import shutil
import platform
from typing import Dict, Any, List

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False


class SystemChecker:
    """Hardware compatibility and offline synthesis diagnostic tool."""

    @staticmethod
    def check_disk(target_path: str = ".") -> Dict[str, Any]:
        """Checks free disk storage on the application drive."""
        try:
            abs_path = os.path.abspath(target_path)
            while not os.path.exists(abs_path) and os.path.dirname(abs_path) != abs_path:
                abs_path = os.path.dirname(abs_path)

            usage = shutil.disk_usage(abs_path)
            free_gb = round(usage.free / (1024 ** 3), 2)
            total_gb = round(usage.total / (1024 ** 3), 2)

            # Requirements: Kokoro-82M (~115 MB) + Piper models (~250 MB) total ~365 MB
            if free_gb >= 2.0:
                status = "ok"
                msg = f"{free_gb} GB free of {total_gb} GB (More than enough for all offline models)"
            elif free_gb >= 1.0:
                status = "ok"
                msg = f"{free_gb} GB free of {total_gb} GB (Sufficient for Kokoro-82M and Piper offline synthesis)"
            elif free_gb >= 0.5:
                status = "warning"
                msg = f"{free_gb} GB free of {total_gb} GB (Tight storage for offline models; freeing space recommended)"
            else:
                status = "error"
                msg = f"{free_gb} GB free of {total_gb} GB (Very low disk space, minimum 500 MB required)"

            return {
                "name": "Disk Storage",
                "status": status,
                "value": f"{free_gb} GB free",
                "details": msg,
                "free_gb": free_gb
            }
        except Exception as e:
            return {
                "name": "Disk Storage",
                "status": "warning",
                "value": "Unknown",
                "details": f"Could not determine disk storage: {e}",
                "free_gb": 0.0
            }

    @staticmethod
    def check_ram() -> Dict[str, Any]:
        """Measures total and available physical RAM via Windows API, /proc/meminfo, or psutil."""
        total_gb = 0.0
        avail_gb = 0.0

        if sys.platform == "win32":
            try:
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
                    avail_gb = round(stat.ullAvailPhys / (1024 ** 3), 2)
            except Exception:
                pass
        elif os.path.exists("/proc/meminfo"):
            try:
                meminfo = {}
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            meminfo[parts[0].strip()] = parts[1].strip()
                if "MemTotal" in meminfo:
                    kb_total = float(meminfo["MemTotal"].split()[0])
                    total_gb = round(kb_total / (1024 ** 2), 2)
                if "MemAvailable" in meminfo:
                    kb_avail = float(meminfo["MemAvailable"].split()[0])
                    avail_gb = round(kb_avail / (1024 ** 2), 2)
            except Exception:
                pass

        if total_gb == 0.0:
            try:
                import psutil
                mem = psutil.virtual_memory()
                total_gb = round(mem.total / (1024 ** 3), 2)
                avail_gb = round(mem.available / (1024 ** 3), 2)
            except Exception:
                pass

        if total_gb > 0:
            if total_gb >= 7.5 and avail_gb >= 1.5:
                status = "ok"
                msg = f"{total_gb} GB total ({avail_gb} GB available). Excellent for neural voice inference in memory."
            elif total_gb >= 3.5 and avail_gb >= 0.8:
                status = "ok"
                msg = f"{total_gb} GB total ({avail_gb} GB available). Well suited for CPU-based neural synthesis."
            elif avail_gb >= 0.4:
                status = "warning"
                msg = f"{total_gb} GB total ({avail_gb} GB available). Low memory headroom; closing other apps recommended."
            else:
                status = "error"
                msg = f"{total_gb} GB total ({avail_gb} GB available). Very low available RAM for neural model execution."
            val_str = f"{total_gb} GB ({avail_gb} GB free)"
        else:
            status = "ok"
            val_str = "Undetermined"
            msg = "Could not directly query physical memory; application will proceed normally."

        return {
            "name": "Physical RAM",
            "status": status,
            "value": val_str,
            "details": msg,
            "total_gb": total_gb,
            "avail_gb": avail_gb
        }

    @staticmethod
    def check_cpu() -> Dict[str, Any]:
        """Checks processor cores and architecture."""
        cores = os.cpu_count() or 2
        arch = platform.machine()
        proc_name = platform.processor() or "Compatible Processor"

        if len(proc_name) > 40:
            proc_name = proc_name[:37] + "..."

        if cores >= 4:
            status = "ok"
            msg = f"{cores} logical cores ({arch}). Fast multi-threaded neural synthesis."
        elif cores >= 2:
            status = "ok"
            msg = f"{cores} logical cores ({arch}). Adequate speed for generating podcasts."
        else:
            status = "warning"
            msg = f"{cores} single core. Synthesis may take longer."

        return {
            "name": "Processor (CPU)",
            "status": status,
            "value": f"{cores} cores ({arch})",
            "details": f"{proc_name} — {msg}",
            "cores": cores
        }

    @staticmethod
    def check_gpu() -> Dict[str, Any]:
        """Detects whether dedicated GPU hardware acceleration is available via ONNX Runtime."""
        gpu_name = "CPU Inference (Fast & Universal)"
        has_accel = False
        providers = []

        if HAS_ONNX:
            try:
                avail = ort.get_available_providers()
                if "CUDAExecutionProvider" in avail:
                    gpu_name = "NVIDIA CUDA (Maximum GPU Acceleration)"
                    has_accel = True
                elif "DmlExecutionProvider" in avail:
                    gpu_name = "DirectML (Windows Hardware Acceleration)"
                    has_accel = True
                providers = avail
            except Exception:
                pass

        return {
            "name": "Graphics Acceleration (GPU)",
            "status": "ok",
            "value": "GPU Active" if has_accel else "Standard CPU",
            "details": f"{gpu_name}. Both Kokoro-82M and Piper ONNX are optimized for modern CPUs as well as GPUs.",
            "has_acceleration": has_accel,
            "providers": providers
        }

    @staticmethod
    def check_internet() -> Dict[str, Any]:
        """Checks connection to Hugging Face for initial model downloads."""
        if not HAS_REQUESTS:
            return {
                "name": "Connection (Hugging Face)",
                "status": "warning",
                "value": "Not checked",
                "details": "Network request module not loaded.",
                "online": False
            }

        try:
            try:
                resp = requests.head("https://huggingface.co", timeout=2.5, verify=True)
            except requests.exceptions.SSLError:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                resp = requests.head("https://huggingface.co", timeout=2.5, verify=False)
            if resp.status_code < 400:
                return {
                    "name": "Hugging Face Connection",
                    "status": "ok",
                    "value": "Online & Reachable",
                    "details": "You can download or reinstall official models with a single click.",
                    "online": True
                }
            else:
                return {
                    "name": "Hugging Face Connection",
                    "status": "warning",
                    "value": f"HTTP {resp.status_code}",
                    "details": "Server responded with caution. If models are installed, you can work 100% offline.",
                    "online": False
                }
        except Exception:
            return {
                "name": "Hugging Face Connection",
                "status": "warning",
                "value": "Offline",
                "details": "No internet connection detected. If models are already downloaded, works 100% autonomously.",
                "online": False
            }

    @classmethod
    def run_full_diagnostic(cls, target_path: str = ".") -> Dict[str, Any]:
        """Runs complete system hardware diagnostic and outputs consolidated verdict."""
        disk = cls.check_disk(target_path)
        ram = cls.check_ram()
        cpu = cls.check_cpu()
        gpu = cls.check_gpu()
        net = cls.check_internet()

        checks = [disk, ram, cpu, gpu, net]

        has_error = any(c["status"] == "error" for c in checks)
        has_warning = any(c["status"] == "warning" for c in checks)

        if has_error:
            overall = "error"
            title = "⚠️ System has limitations that may impact performance"
            summary = "Check available disk space or free up RAM before synthesizing long podcast episodes."
        elif has_warning:
            overall = "warning"
            title = "👍 System is ready for local neural voice synthesis"
            summary = "Your computer can synthesize English podcasts autonomously with good performance."
        else:
            overall = "ok"
            title = "✨ Excellent hardware compatibility detected"
            summary = "Optimal environment for 100% offline, high-fidelity neural voice synthesis."

        return {
            "overall_status": overall,
            "overall_title": title,
            "overall_summary": summary,
            "checks": checks
        }
