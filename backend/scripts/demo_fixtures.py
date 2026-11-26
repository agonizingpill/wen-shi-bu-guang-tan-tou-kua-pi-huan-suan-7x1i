from datetime import date

from lab.constants import Mode

REFERENCE_DAY = date(2026, 11, 23)
RELEASE_DAY = date(2026, 11, 24)
EAST_PROBE = "EQ-214"
ACCOUNTS = (
    ("yu", "余浣 · 值班采样", "technician"),
    ("tang", "唐栩 · 校准班长", "supervisor"),
    ("lin", "林禾 · 育苗查阅", "viewer"),
)
PROBES = (
    {"code": EAST_PROBE, "bay": "东棚 · 二号扦插台", "batch": "LX-26B",
     "reference_serial": "REF-072", "mount_cm": 85},
    {"code": "WH-093", "bay": "西棚 · 四号出苗架", "batch": "LX-25G",
     "reference_serial": "REF-191", "mount_cm": 110},
)


def daylight_points(start):
    block = (start - 360) // 10
    return [
        {"offset_seconds": i * 110, "raw_lux": 360 + 60 * i + block * 16,
         "reference_lux": 418 + 62 * i + block * 17}
        for i in range(6)
    ]


def shielded_points():
    return [
        {"offset_seconds": i * 110, "raw_lux": 50 + 22 * i,
         "reference_lux": 62 + 24 * i}
        for i in range(6)
    ]


def captures():
    return [
        (EAST_PROBE, mode, start, "REF-072", filename, status, values)
        for mode, start, filename, status, values in (
            (Mode.HIGH, 360, "east-1123-high-0600.csv", "witnessed", daylight_points(360)),
            (Mode.HIGH, 370, "east-1123-high-0610.csv", "witnessed", daylight_points(370)),
            (Mode.HIGH, 380, "east-1123-high-0620.csv", "witnessed", daylight_points(380)),
            (Mode.LOW, 300, "east-1123-low-0500.csv", "witnessed", shielded_points()),
        )
    ]
