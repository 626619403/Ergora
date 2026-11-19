"""Bounded Windows contract reads for dedicated native processes."""

from __future__ import annotations

import os
from pathlib import Path


def _read_windows_contract(path, limit=1_048_576):
    """Keep the frozen compiler's bounded, no-follow read boundary on Windows."""
    import ctypes
    import msvcrt
    import stat
    from dev_platform.contracts import need

    path = Path(path).absolute()
    need(not any(p.lstat().st_file_attributes & 0x400 for p in (path, *path.parents)),
         "Symlinked or reparsed contract path is forbidden")
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = ctypes.c_void_p
    api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                               handle, ctypes.c_uint32, ctypes.c_uint32, handle]
    api.CreateFileW.restype = handle
    api.GetFileInformationByHandleEx.argtypes = [handle, ctypes.c_int, handle, ctypes.c_uint32]
    api.GetFileInformationByHandleEx.restype = ctypes.c_int
    api.CloseHandle.argtypes = [handle]
    api.CloseHandle.restype = ctypes.c_int
    # Open the final reparse point itself; sharing only reads prevents concurrent edits.
    native = api.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
    if native == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attributes = (ctypes.c_uint32 * 2)()
        if not api.GetFileInformationByHandleEx(native, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
        need(not attributes[0] & 0x400, "Symlinked or reparsed contract path is forbidden")
        fd = msvcrt.open_osfhandle(native, os.O_RDONLY | os.O_BINARY)
        native = None  # The CRT stream now owns the handle.
        with os.fdopen(fd, "rb") as stream:
            need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Contract must be a regular file")
            raw = stream.read(limit + 1)
        need(len(raw) <= limit, "Contract exceeds size limit")
        return raw
    finally:
        if native is not None:
            api.CloseHandle(native)
