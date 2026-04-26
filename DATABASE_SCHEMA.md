# Database Schema - ExtoDATA Water Quality System

## Overview
**Database File**: `water_quality.db` (SQLite)
**Last Updated**: 2026-04-24
**Total Records**: 7,244 รายการ

---

## Tables

### 1. 📊 water_quality_data (ตารางข้อมูลหลัก)

ตารางหลักสำหรับเก็บข้อมูลคุณภาพน้ำทุกประเภทจากกระบวนการผลิตน้ำประปา

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `date` | TEXT | NOT NULL | วันที่ตรวจวัด (Format: YYYY-MM-DD) |
| `time_period` | TEXT | NOT NULL | ช่วงเวลา (00.00-08.00, 08.00-16.00, 16.00-24.00) |
| `time_label` | TEXT | | Label เวลา (00 น., 08 น., 16 น.) |
| `shift_team` | INTEGER | | ทีมผลัดที่รับผิดชอบ (1, 2, 3, 4) |
| `sampling_point` | TEXT | NOT NULL | จุดวัด (RW, TW, C1-C24, CW1, CW2, FW1, FW2, DPS1, DPS2) |
| `parameter` | TEXT | NOT NULL | ชื่อพารามิเตอร์ (ดูรายการด้านล่าง) |
| `value` | REAL | | ค่าที่วัดได้ |
| `analyst_name` | TEXT | | ชื่อผู้วิเคราะห์ |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | เวลาบันทึกข้อมูล |

**จำนวนระเบียน**: 5,744 รายการ

---

### 2. 🧪 jar_test_results (ตารางทดสอบ Jar Test)

ตารางสำหรับเก็บข้อมูลการทดสอบ Jar Test เพื่อตรวจสอบประสิทธิภาพของสารเคมี

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `date` | TEXT | NOT NULL | วันที่ทดสอบ |
| `time_period` | TEXT | NOT NULL | ช่วงเวลา |
| `time_label` | TEXT | | Label เวลา |
| `shift_team` | INTEGER | | ทีมผลัด |
| `jar_number` | TEXT | NOT NULL | เลขที่ Jar (1-6) |
| `chemical` | TEXT | | ชื่อสารเคมีที่ทดสอบ |
| `dose` | REAL | | ปริมาณสารเคมี (mg/L) |
| `turbidity` | REAL | | ค่า Turbidity หลังการทดสอบ |
| `alkalinity` | REAL | | ค่า Alkalinity หลังการทดสอบ |
| `ph` | REAL | | ค่า pH หลังการทดสอบ |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | เวลาบันทึกข้อมูล |

**จำนวนระเบียน**: 1,498 รายการ

---

### 3. 📋 sqlite_sequence (ตารางระบบ)

ตารางระบบสำหรับ track auto-increment values

**จำนวนระเบียน**: 2 รายการ

---

## Parameters (พารามิเตอร์)

### Main Parameters (พื้นฐาน) - 3 ตัว

| Parameter | จำนวนรายการ | หน่วย | คำอธิบาย |
|-----------|--------------|------|-----------|
| **Turbidity** | 978 | NTU | ความขุ่น |
| **Alkalinity** | 972 | mg/L as CaCO₃ | ค่าความเป็นด่าง |
| **pH** | 972 | - | ค่าความเป็นกรด-ด่าง |

### Special Parameters (พิเศษ) - 7 ตัว

| Parameter | จำนวนรายการ | หน่วย | คำอธิบาย |
|-----------|--------------|------|-----------|
| **Free Residual Cl2** | 660 | mg/L | คลอรีนคงเหลือ |
| **Chemical Dosage** | 1,027 | mg/L | ปริมาณสารเคมีที่ใช้ในการผลิต |
| **% Sludge** | 972 | % | ปอนต์ขี้เลื่อย |
| **O2 Consume** | 60 | mg/L | ค่าออกซิเจนที่ใช้ |
| **Conductivity** | 66 | µS/cm | ค่านำไฟฟ้าง |
| **DO** | 15 | mg/L | ค่าออกซิเจนละลายในน้ำ |
| **Color** | 9 | Pt-Co | สีน้ำ |
| **SS** | 7 | mg/L | ตะกอนแขวน |
| **NH3-N** | 6 | mg/L | ไนโตรเจน |

**หมายเหตุ**:
- Color, SS, NH3-N: ตรวจวัดเฉพาะบางวัน (ส่วนใหญ่วันอาทิตย์ล่ะครั้ง)
- ส่วนใหญ่ตรวจวัดเวลา 08:00 น.
- **O2 Consume**: วัดที่ 4 sampling points (RW, CW, FW, TW) - เหมือนกับ Conductivity

---

## Sampling Points (จุดวัด)

### Main Sampling Points
- **RW** (Raw Water) - น้ำดิบ
- **TW** (Treated Water) - น้ำผลิต

### Clarifier Sampling Points
- **C1 - C24**: Clarifier 1-24
- **CW1, CW2**: Clarifier Water
- **FW1, FW2**: Filter Water

### Other Sampling Points
- **RW1, RW2**: Raw Water points
- **TW1, TW2, TW3**: Treated Water points
- **DPS1, DPS2**: Distribution Points

---

## Time Periods (ช่วงเวลา)

| time_period | time_label | ช่วงเวลา |
|-------------|------------|-----------|
| 00.00-08.00 | 00 น. | เวลา 00:00 - 08:00 น. |
| 08.00-16.00 | 08 น. | เวลา 08:00 - 16:00 น. |
| 16.00-24.00 | 16 น. | เวลา 16:00 - 24:00 น. |

---

## Shift Teams (ทีมผลัด)

| Shift Team | คำอธิบาย |
|------------|-----------|
| 1 | ทีมผลัดที่ 1 |
| 2 | ทีมผลัดที่ 2 |
| 3 | ทีมผลัดที่ 3 |
| 4 | ทีมผลัดที่ 4 |

---

## ตัวอย่าง Query พื้นฐาน

### 1. ดึงข้อมูลทั้งหมดสำหรับวันที่หนึ่ง

```sql
SELECT *
FROM water_quality_data
WHERE date = '2025-08-07'
ORDER BY time_period, parameter, sampling_point;
```

### 2. ดึงข้อมูลตาม parameter เฉพาะ

```sql
SELECT date, time_period, sampling_point, value
FROM water_quality_data
WHERE parameter = 'Turbidity'
  AND date = '2025-08-07'
ORDER BY time_period, sampling_point;
```

### 3. ดึงข้อมูลตาม sampling point เฉพาะ

```sql
SELECT date, time_period, parameter, value
FROM water_quality_data
WHERE sampling_point = 'RW'
  AND date = '2025-08-07'
ORDER BY time_period, parameter;
```

### 4. สรุปข้อมูลรายวัน

```sql
SELECT 
    date,
    COUNT(*) as total_records,
    COUNT(DISTINCT parameter) as num_parameters,
    COUNT(DISTINCT sampling_point) as num_sampling_points
FROM water_quality_data
GROUP BY date
ORDER BY date DESC;
```

### 5. ดึงข้อมูล Jar Test

```sql
SELECT *
FROM jar_test_results
WHERE date = '2025-08-07'
  AND jar_number = '1'
ORDER BY time_period;
```

### 6. เปรียบเทียบค่า RW กับ TW

```sql
SELECT 
    parameter,
    AVG(CASE WHEN sampling_point = 'RW' THEN value END) as avg_rw,
    AVG(CASE WHEN sampling_point = 'TW' THEN value END) as avg_tw
FROM water_quality_data
WHERE date = '2025-08-07'
  AND sampling_point IN ('RW', 'TW')
GROUP BY parameter;
```

### 7. ตรวจสอบข้อมูลที่ขาดหาย

```sql
-- หา time_period ที่ไม่มีข้อมูล
SELECT DISTINCT date, time_period
FROM water_quality_data
WHERE date = '2025-08-07'
ORDER BY time_period;

-- หา parameter ที่ไม่มีข้อมูลในวันหนึ่ง
SELECT 
    p.parameter_name,
    COUNT(wq.parameter) as record_count
FROM (SELECT DISTINCT parameter as parameter_name FROM water_quality_data) p
LEFT JOIN water_quality_data wq 
  ON p.parameter_name = wq.parameter AND wq.date = '2025-08-07'
GROUP BY p.parameter_name
HAVING record_count = 0;
```

---

## การเชื่อมต่อกับ Python

### การเชื่อมต่อพื้นฐาน

```python
import sqlite3
import pandas as pd

# เชื่อมต่อ database
conn = sqlite3.connect('water_quality.db')

# อ่านข้อมูลเป็น DataFrame
df = pd.read_sql_query("""
    SELECT * FROM water_quality_data
    WHERE date = '2025-08-07'
""", conn)

conn.close()
```

### การบันทึกข้อมูลใหม่

```python
import sqlite3

conn = sqlite3.connect('water_quality.db')
cursor = conn.cursor()

# บันทึกข้อมูล
cursor.execute("""
    INSERT INTO water_quality_data 
    (date, time_period, time_label, shift_team, sampling_point, parameter, value)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", ('2025-08-07', '00.00-08.00', '00 น.', 2, 'RW', 'pH', 7.2))

conn.commit()
conn.close()
```

---

## หมายเหตุ

1. **Date Format**: เก็บเป็น TEXT ในรูปแบบ YYYY-MM-DD เพื่อให้ง่ายต่อการ query และ sorting

2. **Value ที่เป็น NULL**: แสดงว่าไม่ได้ตรวจวัดในช่วงเวลานั้น

3. **Multiple Time Periods**: แต่ละวันมี 3 time periods (00.00-08.00, 08.00-16.00, 16.00-24.00)

4. **Sampling Points**: แต่ละ parameter อาจไม่ได้วัดทุก sampling points

5. **Unit Conversion**: ค่าที่เก็บใน database เป็นค่าวัดจริง ไม่ได้แปลงหน่วย

---

## การติดตั้งและใช้งาน

### การใช้งานร่วมกับ Python

```python
# ตัวอย่างการ query ข้อมูล
import sqlite3
import pandas as pd

conn = sqlite3.connect('water_quality.db')

# 1. ดึงข้อมูลทั้งหมด
df = pd.read_sql("SELECT * FROM water_quality_data", conn)

# 2. Filter ตามวันที่
df_today = df[df['date'] == '2025-08-07']

# 3. Group by parameter
param_stats = df.groupby('parameter')['value'].agg(['mean', 'min', 'max'])

conn.close()
```

### การ Export ข้อมูล

```python
# Export เป็น CSV
df.to_csv('water_quality_export.csv', index=False)

# Export เป็น Excel
df.to_excel('water_quality_export.xlsx', index=False)
```

---

## เอกสารอ้างอิง

- Excel Importer: `src/excel_importer.py`
- Block Extraction: `src/phase2_block_extraction.py`
- Database Operations: `src/phase4_database.py`

---

**สร้างเมื่อ**: 2026-04-24
**เวอร์ชั่น**: 1.0
