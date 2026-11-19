# -*- coding: utf-8 -*-
"""فاحص جودة بيانات الحدائق الافتراضية — Python 3.9+، دون مكتبات خارجية."""
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MUNICIPALITIES = ["جيزان", "أبو عريش", "صبيا", "صامطة", "بيش", "الدرب", "العارضة", "أحد المسارحة"]
CODES = {municipality: f"M{i:02d}" for i, municipality in enumerate(MUNICIPALITIES, 1)}
KINDS = {"حديقة حي", "حديقة عامة", "منتزه"}
STATUSES = {"نشطة", "تحت الصيانة", "مغلقة مؤقتًا"}
REQUIRED = ["معرّف الحديقة", "اسم الحديقة", "البلدية", "المساحة (م²)",
            "خط العرض", "خط الطول", "نوع الحديقة", "حالة التشغيل",
            "تاريخ آخر تحديث", "رمز البلدية"]
DIMS = ["الاكتمال", "التفرد", "صلاحية المساحة", "صحة الإحداثيات", "الاتساق المرجعي", "حداثة البيانات"]

def read_rows(filename):
    with (ROOT / filename).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def date_or_none(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None

def audit(rows):
    ids = Counter(r["معرّف الحديقة"] for r in rows)
    passed = [0] * len(DIMS)
    problems = []
    for idx, r in enumerate(rows, 1):
        area = number(r["المساحة (م²)"])
        lat = number(r["خط العرض"])
        lon = number(r["خط الطول"])
        updated = date_or_none(r["تاريخ آخر تحديث"])
        m = r["البلدية"]
        flags = [
            all(r.get(k, "").strip() != "" for k in REQUIRED),
            bool(r["معرّف الحديقة"].strip()) and ids[r["معرّف الحديقة"]] == 1,
            area is not None and area > 0,
            lat is not None and lon is not None and 16 <= lat <= 19 and 41 <= lon <= 44,
            m in CODES and r["رمز البلدية"] == CODES[m] and r["نوع الحديقة"] in KINDS and r["حالة التشغيل"] in STATUSES,
            updated is not None and date(2025, 11, 17) <= updated <= date(2026, 11, 17),
        ]
        for j, ok in enumerate(flags):
            passed[j] += int(ok)
            if not ok:
                problems.append({"رقم_الصف": idx, "معرّف_السجل": r["معرّف الحديقة"], "البعد": DIMS[j]})
    total = len(rows)
    rates = {dim: round(count * 100 / total, 4) if total else 0 for dim, count in zip(DIMS, passed)}
    overall = round(sum(rates.values()) / len(DIMS), 4)
    return {"عدد_السجلات": total, "عدد_الاختبارات": total * len(DIMS),
            "النجاحات_لكل_بعد": dict(zip(DIMS, passed)), "النسب_المئوية": rates,
            "المؤشر_الكلي_المئوي": overall, "عدد_الاختبارات_غير_المجتازة": len(problems),
            "تفاصيل_الاستثناءات": problems}

def main():
    before = audit(read_rows("البيانات_قبل_التحسين.csv"))
    after = audit(read_rows("البيانات_بعد_التحسين.csv"))
    report = {"تاريخ_القياس": "2026-11-17", "نوع_البيانات": "افتراضية بالكامل",
              "قبل_التحسين": before, "بعد_التحسين": after,
              "التحسن_بنقاط_مئوية": round(after["المؤشر_الكلي_المئوي"] - before["المؤشر_الكلي_المئوي"], 4)}
    path = ROOT / "تقرير_التحقق.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("تقرير جودة بيانات الحدائق (بيانات افتراضية)")
    print("البعد".ljust(25), "قبل".rjust(10), "بعد".rjust(10))
    for key in DIMS:
        print(key.ljust(25), f'{before["النسب_المئوية"][key]:.2f}%'.rjust(10),
              f'{after["النسب_المئوية"][key]:.2f}%'.rjust(10))
    print(f'\nالمؤشر العام: {before["المؤشر_الكلي_المئوي"]:.2f}% ← {after["المؤشر_الكلي_المئوي"]:.2f}%')
    print(f'التحسن: {report["التحسن_بنقاط_مئوية"]:.2f} نقطة مئوية')
    print(f"حُفظ التقرير في: {path.name}")

if __name__ == "__main__":
    main()
