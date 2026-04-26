# Project: Monthly Water Quality Report Dashboard (Streamlit)

## 0. Project Knowledge Base (MUST READ)
Before starting any task, you must read and internalize the business logic and structure from these files:
- `DATABASE_SCHEMA.md`: Technical details of the database tables, relations, and data types.
- `Parameter ทั้งหมด.md`: Definitions of calculations like @RW<100 and Jar Test logic.
- `ชื่อเรียกกลุ่มของ Sampling Point.md`: Mapping of sampling points (RW, CW, FW, TW).
- `รายการ Parameters ทั้งหมดใน Database.md`: List of all 12 parameters in the schema.
- `รูปแบบ Dashboard ที่ต้องการ.md`: UI layout, thresholds, and reporting requirements.

## 1. System Directives & Communication
- **Communication:** You MUST interact with the user in THAI.
- **Implementation:** All code, SQL queries, and technical documentation must be in ENGLISH.
- **Workflow:** Divide the work into phases. Complete one phase, verify with the user, then move to the next. Use agentic reasoning to ensure complex logic (like @RW<100) is executed accurately.

## 2. Project Context & Data Source
- **Database Location:** The SQLite database file is located in the `data/` directory.
- **Sampling Groups:**
    - **Raw Water (RW):** RW, RW 1, RW2
    - **Settled Water (CW):** C1-C24, CW1, CW2
    - **Filtered Water (FW):** FW1, FW2
    - **Tap Water (TW):** TW1, TW2, TW3, DPS1, DPS2

## 3. Development Phases

### Phase 1: Environment & Database Setup
- Initialize a Streamlit app.
- Create a sidebar for Year/Month selection and dynamic thresholds.
- Implement a robust SQLite connection utility targeting the file within the `data/` folder.
- **Task:** Cross-check the actual database against `DATABASE_SCHEMA.md` and show a data preview.

### Phase 2: Data Engineering & Logic Implementation
Use Pandas to implement logic from the Reference Materials:
- **Grouping:** Apply sampling point mappings.
- **Filtering (@RW<100):** Implement the temporal filter (exclude FW/TW data if RW Turbidity > 100 at the same timestamp).
- **Aggregations:** Calculate Counts, Means, 95th, and 100th Percentiles.
- **Chemical Usage:** Implement the "1 count per shift" logic for Jar Tests.

### Phase 3: Dashboard UI Construction
Build the UI according to `รูปแบบ Dashboard ที่ต้องการ.md`:
- **Summary Table:** Analysis counts per parameter and group.
- **Chemical & Sludge Sections:** Specialized metrics.
- **Performance Evaluation Table:** Final report with NC Counts and results (%, NTU, etc.).

## 4. Technical Stack
- **Frontend:** Streamlit
- **Data Engine:** Python (Pandas, SQLAlchemy/sqlite3)
- **Database:** SQLite (Stored in `data/` folder)

---
**Initial Instruction:** "Confirm in THAI that you have read all 5 reference files, including DATABASE_SCHEMA.md. Verify that you know the database is located in the 'data' folder, then summarize the '@RW<100' and 'Jar Test' logic to ensure accuracy before starting Phase 1."