"""Windows process lifetime ownership shared by commands and source fetches.

Assign the trusted, gated child before letting it launch a command or use the
network. The controller keeps the only job handle, so its death also stops work.
This is lifecycle management within the current user, not an OS security sandbox.
"""

import ctypes
import os
import time


class _Limits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", ctypes.c_uint32), ("minimum", ctypes.c_size_t),
                ("maximum", ctypes.c_size_t), ("active_limit", ctypes.c_uint32),
                ("affinity", ctypes.c_size_t), ("priority", ctypes.c_uint32),
                ("scheduling", ctypes.c_uint32)]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", _Limits), ("io", ctypes.c_uint64 * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [("user_time", ctypes.c_int64), ("kernel_time", ctypes.c_int64),
                ("period_user_time", ctypes.c_int64), ("period_kernel_time", ctypes.c_int64),
                ("faults", ctypes.c_uint32), ("total", ctypes.c_uint32),
                ("active", ctypes.c_uint32), ("terminated", ctypes.c_uint32)]


class Job:
    def __init__(self):
        if os.name != "nt":
            raise OSError("Windows Job Objects require Windows")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        handle, dword, boolean = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32
        signatures = {
            "CreateJobObjectW": ([handle, ctypes.c_wchar_p], handle),
            "SetInformationJobObject": ([handle, ctypes.c_int, handle, dword], boolean),
            "QueryInformationJobObject": ([handle, ctypes.c_int, handle, dword, handle], boolean),
            "OpenProcess": ([dword, boolean, dword], handle),
            "AssignProcessToJobObject": ([handle, handle], boolean),
            "TerminateJobObject": ([handle, ctypes.c_uint], boolean),
            "CloseHandle": ([handle], boolean),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = arguments, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.api.CloseHandle(self.handle)
            raise error

    def assign(self, pid: int):
        process = self.api.OpenProcess(0x0100 | 0x0001, False, pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.api.AssignProcessToJobObject(self.handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(process)

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        try:
            if not self.api.TerminateJobObject(self.handle, 1):
                raise ctypes.WinError(ctypes.get_last_error())
            deadline = time.monotonic() + 10
            while True:
                accounting = _Accounting()
                if not self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(accounting),
                                                          ctypes.sizeof(accounting), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                if not accounting.active:
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError("Windows job cleanup did not reach an empty process set")
                time.sleep(.01)
        finally:
            self.api.CloseHandle(self.handle)
