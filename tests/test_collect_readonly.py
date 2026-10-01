"""Mock-based tests: no ADB server, tablet, firmware, or USB access is used."""
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collect_readonly as c

SERIAL = "TEST331FC"
LISTING = "List of devices attached\nTEST331FC device usb:001 product:fake model:TB331FC device:fake transport_id:1\n"


def result(argv, stdout="", stderr="", returncode=0):
    return {"argv": argv, "stdout": stdout, "stderr": stderr,
            "returncode": returncode, "started_utc": "TEST"}


class FakeADB:
    def __init__(self, model="TB331FC", listing=LISTING):
        self.calls = []
        self.model = model
        self.listing = listing

    def __call__(self, argv):
        self.calls.append(argv)
        if argv[-2:] == ["devices", "-l"]:
            return result(argv, self.listing)
        if argv[-2:] == ["getprop", "ro.product.model"]:
            return result(argv, self.model + "\n")
        if argv[-2:] == ["ls", "-l"]:
            raise AssertionError("unexpected argv")
        if argv[-1] == "/dev/block/by-name":
            return result(argv, stderr="ls: permission denied\n", returncode=1)
        return result(argv, "test-value\n")


class InventoryTests(unittest.TestCase):
    def test_01_default_does_not_execute(self):
        with patch.object(c, "execute", side_effect=AssertionError("execution prohibited")), patch.object(c.shutil, "which", side_effect=AssertionError("tool lookup prohibited")), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(c.main([]), 0)
        self.assertFalse(json.loads(out.getvalue())["device_access"])

    def test_02_plan_has_no_mutation_command(self):
        forbidden = {"reboot", "root", "su", "push", "install", "setprop", "flash", "erase", "dd", "sh", "bash"}
        for _, query in c.QUERIES:
            self.assertTrue(forbidden.isdisjoint(query))

    def test_03_no_unique_boot_serial_properties(self):
        self.assertNotIn("ro.boot.bootload_sn", c.PROPERTIES)
        self.assertNotIn("ro.serialno", c.PROPERTIES)
        self.assertNotIn("ro.boot.serialno", c.PROPERTIES)

    def test_04_valid_serial(self):
        self.assertEqual(c.validate_serial(SERIAL), SERIAL)

    def test_05_bad_serials(self):
        for value in ("", "-s", "x;reboot", "x y", "192.168.1.2:5555", "emulator-5554", "x\n", "x" * 129):
            with self.subTest(value=value), self.assertRaises(c.InventoryError):
                c.validate_serial(value)

    def test_06_environment_override_denied(self):
        for key in c.OVERRIDE_ENV:
            with self.subTest(key=key), self.assertRaises(c.InventoryError):
                c.check_environment({key: "unexpected"})

    def test_07_plain_environment_allowed(self):
        c.check_environment({"PATH": "/usr/bin", "HOME": "/tmp", "ANDROID_SERIAL": ""})

    def test_08_one_usb_allowed(self):
        self.assertEqual(c.require_target(LISTING, SERIAL)["serial"], SERIAL)

    def test_09_zero_devices_denied(self):
        with self.assertRaises(c.InventoryError):
            c.require_target("List of devices attached\n", SERIAL)

    def test_10_multiple_devices_denied(self):
        with self.assertRaises(c.InventoryError):
            c.require_target(LISTING + "SECOND unauthorized usb:002\n", SERIAL)

    def test_11_unauthorized_or_offline_denied(self):
        for state in ("unauthorized", "offline", "recovery", "sideload"):
            with self.subTest(state=state), self.assertRaises(c.InventoryError):
                c.require_target(LISTING.replace(" device usb:", " " + state + " usb:"), SERIAL)

    def test_12_wrong_serial_denied(self):
        with self.assertRaises(c.InventoryError):
            c.require_target(LISTING, "OTHER")

    def test_13_missing_usb_denied(self):
        with self.assertRaises(c.InventoryError):
            c.require_target(LISTING.replace("usb:001 ", ""), SERIAL)

    def test_14_exact_model_only(self):
        for model in ("TB331FC", "Lenovo TB331FC", "Lenovo_TB331FC"):
            self.assertTrue(c.model_is_target(model))
        for model in ("TB331FU", "TB335FC", "TB331FC-Pro", "unknown"):
            self.assertFalse(c.model_is_target(model))

    def test_15_wrong_model_stops_early(self):
        fake = FakeADB(model="TB335FC")
        with self.assertRaises(c.InventoryError):
            c.collect_device("/fake/adb", SERIAL, run=fake)
        self.assertEqual(len(fake.calls), 2)

    def test_16_full_success_with_unknown_permission(self):
        fake = FakeADB()
        records = c.collect_device("/fake/adb", SERIAL, run=fake)
        record = next(r for r in records if r["key"] == "block_names")
        self.assertEqual(record["status"], "unknown_error")
        self.assertEqual(len(fake.calls), len(c.QUERIES) + 4)

    def test_17_all_shell_calls_target_exact_serial(self):
        fake = FakeADB()
        c.collect_device("/fake/adb", SERIAL, run=fake)
        for argv in fake.calls:
            self.assertEqual(argv[1:5], ["-H", "127.0.0.1", "-P", "5037"])
            if "shell" in argv:
                self.assertEqual(argv[5:8], ["-s", SERIAL, "shell"])
                self.assertIn(tuple(argv[8:]), c.ALLOWED_QUERIES)

    def test_18_arbitrary_query_denied(self):
        for query in (("getprop",), ("getprop", "ro.boot.bootload_sn"), ("reboot",), ("sh", "-c", "id")):
            with self.subTest(query=query), self.assertRaises(c.InventoryError):
                c.query_argv("/fake/adb", SERIAL, query)

    def test_19_timeout_no_retry(self):
        with patch.object(c.subprocess, "run", side_effect=subprocess.TimeoutExpired(["adb"], 15)) as run:
            with self.assertRaises(c.InventoryError):
                c.execute(["/fake/adb", "version"])
        self.assertEqual(run.call_count, 1)

    def test_20_execute_uses_no_host_shell(self):
        fake = subprocess.CompletedProcess(["adb"], 0, "ok", "")
        with patch.object(c.subprocess, "run", return_value=fake) as run:
            c.execute(["/fake/adb", "version"])
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_21_missing_property_is_unknown(self):
        self.assertEqual(c.checked_record(result([], "\n"), "x")["status"], "unknown_empty")

    def test_22_transport_failure_stops(self):
        with self.assertRaises(c.InventoryError):
            c.checked_record(result([], stderr="error: device 'TEST331FC' not found", returncode=1), "x")

    def test_23_regular_missing_file_not_transport_failure(self):
        self.assertEqual(c.checked_record(result([], stderr="cat: /sys/missing: No such file or directory", returncode=1), "x")["status"], "unknown_error")

    def test_24_redaction(self):
        text = SERIAL + " " + "a" * 64 + " user@example.com AA:BB:CC:DD:EE:FF 192.168.1.2 /Users/alice/file"
        output = c.redact_text(text, SERIAL, "/Users/alice")
        for sensitive in (SERIAL, "a" * 64, "user@example.com", "AA:BB:CC:DD:EE:FF", "192.168.1.2", "/Users/alice"):
            self.assertNotIn(sensitive, output)

    def test_25_public_report_excludes_listing_and_serial(self):
        raw = {"device_serial": SERIAL, "records": [{"key": "devices_before", "stdout": SERIAL}, {"key": "kernel", "stdout": "ok"}], "native_install_authorized": False}
        filtered = c.redacted_report(raw, SERIAL, "/Users/owner")
        self.assertNotIn("device_serial", filtered)
        self.assertEqual(len(filtered["records"]), 1)
        self.assertIn("NOT_CLEARED_FOR_UPLOAD", filtered["privacy"])
        self.assertFalse(filtered["native_install_authorized"])
        self.assertIn("device_serial", raw)  # original is unchanged

    def test_26_private_permissions_and_exclusive_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "private"
            c.secure_directory(directory)
            path = directory / "test.json"
            c.write_json_exclusive(path, {"test": True})
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                c.write_json_exclusive(path, {})

    def test_27_symlink_directory_denied(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real").mkdir()
            (root / "link").symlink_to(root / "real", target_is_directory=True)
            with self.assertRaises(c.InventoryError):
                c.secure_directory(root / "link")

    def test_28_lock_exclusive_and_reusable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with c.session_lock(root):
                with self.assertRaises(c.InventoryError):
                    with c.session_lock(root):
                        pass
            with c.session_lock(root):
                self.assertTrue((root / "device-session.lock").is_file())

    def test_29_end_identity_mismatch_aborts(self):
        fake = FakeADB()
        model_count = 0
        def runner(argv):
            nonlocal model_count
            if argv[-2:] == ["getprop", "ro.product.model"]:
                model_count += 1
                if model_count == 3:
                    return result(argv, "TB335FC")
            return fake(argv)
        with self.assertRaises(c.InventoryError):
            c.collect_device("/fake/adb", SERIAL, run=runner)

    def test_30_noninteractive_missing_serial_stops(self):
        with patch.object(c.sys.stdin, "isatty", return_value=False), patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()), patch.object(c, "execute", side_effect=AssertionError("must not execute")):
            self.assertEqual(c.main(["--collect"]), 2)

    def test_31_unexpected_large_output(self):
        fake = subprocess.CompletedProcess(["adb"], 0, "x" * 2_000_001, "")
        with patch.object(c.subprocess, "run", return_value=fake), self.assertRaises(c.InventoryError):
            c.execute(["/fake/adb", "version"])

    def test_32_transport_changed_aborts(self):
        fake = FakeADB()
        listings = 0
        def runner(argv):
            nonlocal listings
            if argv[-2:] == ["devices", "-l"]:
                listings += 1
                if listings == 2:
                    return result(argv, LISTING.replace("usb:001", "usb:002"))
            return fake(argv)
        with self.assertRaises(c.InventoryError):
            c.collect_device("/fake/adb", SERIAL, run=runner)

if __name__ == "__main__":
    unittest.main()
