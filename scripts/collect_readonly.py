#!/usr/bin/env python3
"""Owner-run TB331FC ADB inventory, stdlib only, Python >= 3.9.

Default: print the fixed plan; do not launch ADB or touch a device.
--collect: query one explicitly identified USB-connected TB331FC.
This is NOT a firmware backup, unlocker, USB sandbox, or installation approval.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid
from contextlib import contextmanager
from typing import Callable, Optional

VERSION = "1.0.0"
SERIAL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
OVERRIDE_ENV = (
    "ADB_SERVER_SOCKET", "ANDROID_ADB_SERVER_ADDRESS", "ANDROID_ADB_SERVER_PORT",
    "ADB_SERVER_PORT", "ADB_SERVER_HOST", "ANDROID_SERIAL", "ADB_VENDOR_KEYS", "ADB_TRACE",
)
PROPERTIES = (
    "ro.product.model", "ro.product.device", "ro.product.name", "ro.product.board",
    "ro.product.vendor.model", "ro.board.platform", "ro.soc.manufacturer", "ro.soc.model",
    "ro.product.cpu.abilist", "ro.build.fingerprint", "ro.build.display.id",
    "ro.build.version.incremental", "ro.build.version.release", "ro.build.version.sdk",
    "ro.build.version.security_patch", "ro.vendor.build.security_patch",
    "ro.boot.hardware", "ro.boot.hardware.sku", "ro.boot.bootloader",
    "ro.boot.verifiedbootstate", "ro.boot.flash.locked", "ro.boot.vbmeta.device_state",
    "ro.boot.veritymode", "ro.oem_unlock_supported", "ro.boot.slot_suffix",
    "ro.build.ab_update", "ro.boot.dynamic_partitions", "ro.boot.virtual_ab.enabled",
)
QUERIES = tuple(("prop:" + p, ("getprop", p)) for p in PROPERTIES) + (
    ("kernel", ("uname", "-srvm")),
    ("proc_version", ("cat", "/proc/version")),
    ("meminfo", ("cat", "/proc/meminfo")),
    ("partitions", ("cat", "/proc/partitions")),
    ("block_names", ("ls", "-l", "/dev/block/by-name")),
    ("dt_model", ("cat", "/sys/firmware/devicetree/base/model")),
    ("dt_compatible", ("cat", "/sys/firmware/devicetree/base/compatible")),
    ("shell_identity", ("id",)),
    ("selinux", ("getenforce",)),
    ("battery", ("dumpsys", "battery")),
)
ALLOWED_QUERIES = frozenset(q for _, q in QUERIES)
TRANSPORT_ERRORS = (
    "device offline", "no devices/emulators found", "device not found", "not found",
    "device unauthorized", "error: closed", "protocol fault", "connection reset",
    "cannot connect to daemon", "failed to get feature set", "cannot connect to server",
)

class InventoryError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_serial(serial: str) -> str:
    if not SERIAL_RE.fullmatch(serial) or serial.startswith("emulator-"):
        raise InventoryError("Serial must be an explicit USB device identifier, not a TCP endpoint or emulator.")
    return serial


def check_environment(env: dict) -> None:
    bad = [key for key in OVERRIDE_ENV if env.get(key)]
    if bad:
        raise InventoryError("Refusing ADB environment overrides: " + ", ".join(bad))


def parse_devices(text: str) -> list[dict]:
    devices = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices attached") or line.startswith("*"):
            continue
        tokens = line.split()
        if len(tokens) < 2:
            raise InventoryError("Unrecognized ADB device listing; stop for human review.")
        devices.append({"serial": tokens[0], "state": tokens[1], "details": tokens[2:]})
    return devices


def require_target(text: str, serial: str) -> dict:
    devices = parse_devices(text)
    if len(devices) != 1:
        raise InventoryError("Exactly one attached ADB device is required (including offline/unauthorized entries).")
    device = devices[0]
    if device["serial"] != serial:
        raise InventoryError("The attached device does not match the owner-specified serial.")
    if device["state"] != "device":
        raise InventoryError("Device is not authorized and online. Owner must inspect it; no automatic retry.")
    if not any(item.startswith("usb:") for item in device["details"]):
        raise InventoryError("No USB transport marker in ADB listing. Do not force; review transport manually.")
    return device


def model_is_target(model: str) -> bool:
    normal = re.sub(r"[\s_-]+", "", model.strip()).upper()
    return normal in ("TB331FC", "LENOVOTB331FC")


def adb_prefix(adb: str) -> list[str]:
    return [adb, "-H", "127.0.0.1", "-P", "5037"]


def query_argv(adb: str, serial: str, query: tuple[str, ...]) -> list[str]:
    validate_serial(serial)
    if query not in ALLOWED_QUERIES:
        raise InventoryError("Query not in the compiled-in read-only allowlist.")
    return adb_prefix(adb) + ["-s", serial, "shell", *query]


def execute(argv: list[str], timeout: int = 15) -> dict:
    started = utc_now()
    try:
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout, check=False,
                              text=True, errors="replace", shell=False)
    except subprocess.TimeoutExpired as exc:
        raise InventoryError("Command timed out; no retry; argv=" + json.dumps(argv)) from exc
    except OSError as exc:
        raise InventoryError("Could not execute the locally reviewed ADB binary.") from exc
    stdout, stderr = proc.stdout, proc.stderr
    if len(stdout) + len(stderr) > 2_000_000:
        raise InventoryError("Unexpectedly large output; collection stops.")
    return {"argv": argv, "started_utc": started, "returncode": proc.returncode,
            "stdout": stdout, "stderr": stderr}


def checked_record(record: dict, key: str) -> dict:
    record = dict(record)
    record["key"] = key
    if record["returncode"] == 0:
        record["status"] = "observed" if record["stdout"].strip("\x00\r\n ") else "unknown_empty"
    else:
        record["status"] = "unknown_error"
    # Do not classify missing sysfs files as a lost device. Transport errors from
    # ADB have the error prefix or explicit offline/authorization wording.
    error_text = (record["stderr"] + "\n" + record["stdout"]).lower()
    if record["returncode"] != 0 and (
        any(t in error_text for t in TRANSPORT_ERRORS if t != "not found")
        or ("error: device '" in error_text and "not found" in error_text)
    ):
        raise InventoryError("ADB transport/authorization changed; stop, no reconnect or retry.")
    return record


def collect_device(adb: str, serial: str, run: Callable = execute,
                   records: Optional[list] = None) -> list[dict]:
    validate_serial(serial)
    records = records if records is not None else []
    initial = run(adb_prefix(adb) + ["devices", "-l"])
    records.append(dict(initial, key="devices_before", status="private_transport_listing"))
    if initial["returncode"] != 0:
        raise InventoryError("ADB listing failed.")
    first = require_target(initial["stdout"], serial)
    identity = checked_record(run(query_argv(adb, serial, ("getprop", "ro.product.model"))), "identity_before")
    records.append(identity)
    if identity["returncode"] != 0 or not model_is_target(identity["stdout"]):
        raise InventoryError("Model is not an exact recognized TB331FC; stop without expanding queries.")
    for key, query in QUERIES:
        record = checked_record(run(query_argv(adb, serial, query)), key)
        records.append(record)
    last_identity = checked_record(run(query_argv(adb, serial, ("getprop", "ro.product.model"))), "identity_after")
    records.append(last_identity)
    if last_identity["returncode"] != 0 or last_identity["stdout"].strip() != identity["stdout"].strip():
        raise InventoryError("Device identity changed during collection.")
    final = run(adb_prefix(adb) + ["devices", "-l"])
    records.append(dict(final, key="devices_after", status="private_transport_listing"))
    if final["returncode"] != 0:
        raise InventoryError("Final ADB listing failed.")
    last = require_target(final["stdout"], serial)
    if first["details"] != last["details"]:
        raise InventoryError("USB/ADB transport metadata changed; inspect before accepting results.")
    return records


def secure_directory(path: Path) -> None:
    if path.is_symlink():
        raise InventoryError("Refusing a symlinked output/lock directory.")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise InventoryError("Output/lock location is not a directory.")
    os.chmod(path, 0o700)


@contextmanager
def session_lock(directory: Path):
    """Cooperative lock only; other processes can bypass it. Never unlink lock."""
    secure_directory(directory)
    filename = directory / "device-session.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(filename, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InventoryError("Another cooperative inventory session holds the device lock.") from exc
        os.ftruncate(fd, 0)
        os.write(fd, ("owner-inventory pid=" + str(os.getpid()) + "\n").encode())
        yield
    finally:
        os.close(fd)


def redact_text(text: str, serial: str, home: str) -> str:
    text = text.replace(serial, "<DEVICE_SERIAL>") if serial else text
    if home:
        text = text.replace(home, "<HOME>")
    text = re.sub(r"(?i)\b[0-9a-f]{64}\b", "<HEX64_REDACTED>", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<EMAIL>", text)
    text = re.sub(r"(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", "<MAC>", text)
    text = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<IPV4>", text)
    text = re.sub(r"/(?:Users|home)/[^/\s]+", "<HOME>", text)
    return text


def redacted_report(report: dict, serial: str, home: str) -> dict:
    public = copy.deepcopy(report)
    public.pop("device_serial", None)
    public["privacy"] = "AUTOMATICALLY_FILTERED_NOT_CLEARED_FOR_UPLOAD; owner review required"
    public["records"] = [r for r in public["records"] if r["key"] not in ("devices_before", "devices_after")]
    def walk(obj):
        if isinstance(obj, str):
            return redact_text(obj, serial, home)
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        return obj
    return walk(public)


def write_json_exclusive(path: Path, data: dict) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def plan() -> dict:
    return {"tool": "TB331FC owner inventory", "version": VERSION, "mode": "PLAN_ONLY",
            "device_access": False, "writes_to_tablet_requested": False,
            "queries": [{"key": key, "shell_argv": list(query)} for key, query in QUERIES],
            "notes": ["No ADB process is launched in plan mode.",
                      "Collection requires --collect and an explicit owner-selected USB serial.",
                      "No fastboot, reboot, root, setprop, install, EDL, partition dump or flash.",
                      "Android and ADB may write ordinary logs/authorization state: not forensic zero-write."]}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect", action="store_true", help="Owner-reviewed, fixed read-only ADB inventory.")
    parser.add_argument("--serial", help="Explicit USB serial. Omit to type privately in an interactive owner terminal.")
    parser.add_argument("--output-dir", type=Path,
                        default=Path.home() / ".local/share/tb331fc-owner-only")
    args = parser.parse_args(argv)
    if not args.collect:
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
        return 0
    try:
        check_environment(dict(os.environ))
        serial = args.serial
        if serial is None:
            if not sys.stdin.isatty():
                raise InventoryError("Collection needs --serial or an interactive owner terminal.")
            serial = getpass.getpass("Owner: type the TB331FC USB serial (hidden): ")
        validate_serial(serial)
        adb_found = shutil.which("adb")
        if not adb_found:
            raise InventoryError("ADB not found. Owner must install/review Android Platform Tools separately.")
        adb = str(Path(adb_found).resolve())
        output_root = args.output_dir.expanduser().absolute()
        secure_directory(output_root)
        run_dir = output_root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
        secure_directory(run_dir)
        report = {"schema_version": 1, "collector_version": VERSION, "started_utc": utc_now(),
                  "host": {"system": platform.system(), "machine": platform.machine(),
                           "macos_version": platform.mac_ver()[0], "python_version": platform.python_version()},
                  "adb_path": adb, "device_serial": serial, "status": "started",
                  "native_install_authorized": False, "records": [],
                  "privacy": "PRIVATE_OWNER_ONLY", "errors": []}
        try:
            with session_lock(Path.home() / ".local/state/tb331fc-omarchy"):
                # Hash the local executable; this is provenance, not a signature check.
                report["adb_sha256"] = hashlib.sha256(Path(adb).read_bytes()).hexdigest()
                version = execute([adb, "version"])
                report["adb_version"] = version["stdout"]
                if version["returncode"] != 0:
                    raise InventoryError("ADB version query failed.")
                collect_device(adb, serial, records=report["records"])
                report["status"] = "collection_completed"
        except (InventoryError, OSError) as exc:
            report["status"] = "aborted"
            report["errors"].append(str(exc))
        report["finished_utc"] = utc_now()
        write_json_exclusive(run_dir / "inventory.private.json", report)
        write_json_exclusive(run_dir / "inventory.redacted.json", redacted_report(report, serial, str(Path.home())))
        print("Status:", report["status"])
        print("Owner-only reports:", run_dir)
        print("Review the redacted file manually before sharing. This is not a backup or a flashing approval.")
        return 0 if report["status"] == "collection_completed" else 2
    except (InventoryError, OSError, EOFError) as exc:
        print("STOP:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
