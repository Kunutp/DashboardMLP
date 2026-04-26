### 💧 Water Quality Monthly Report Dashboard

A Streamlit-powered dashboard for monitoring and reporting water quality in water treatment plants. Track parameters from Raw Water to Treated Water with advanced analytics and filtering capabilities.

---

### ✨ **Features**

- **Monthly Reporting**: Select year/month and customize quality thresholds
  - Turbidity < 1.00 NTU
  - Free Residual Cl2 > 0.8 mg/L
  - pH range: 6.5 - 8.5

- **Sample Count Summary**: Track analysis counts by parameter and sampling point (RW, CW, FW, TW)

- **Jar Test Analysis**: Calculate chemical usage rates (Alum, PACl, Polymer, Lime) per shift

- **Recycle Water Analysis**: Monitor turbidity and conductivity

- **Performance Evaluation**:
  - NC (Non-Compliance) counts with compliance percentages
  - Statistics: Mean, 95th percentile, 100th percentile
  - Special **@RW<100 filtering** (excludes data when raw water turbidity exceeds 100 NTU)

---

### 🛠️ **Tech Stack**

- **Framework**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Database**: SQLite
- **Language**: Python 3.8+

---

### 🚀 **Installation**

```bash
# Clone repository
git clone https://github.com/Kunutp/DashboardMLP.git
cd DashboardMLP

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

---

### 📖 **Usage**

1. Select **Year** and **Month** for the report
2. Adjust **Quality Thresholds** if needed
3. View **Summary Tables** and **Charts**
4. Export monthly performance reports

---

### 🎯 **Key Business Logic**

- **@RW<100 Filtering**: Excludes FW/TW data when raw water turbidity > 100 NTU at same timestamp
- **Jar Test Counting**: Counts once per shift (08.00-16.00 or 16.00-24.00) when chemical testing occurs
- **NC Counts**: Tracks instances where values exceed quality standards

---

### 📂 **Project Structure**

```
DashboardMLP/
├── app.py                      # Main Streamlit app
├── config.py                   # Configuration settings
├── requirements.txt            # Dependencies
├── src/
│   ├── database.py            # Database utilities
│   └── data_processor.py      # Business logic
└── data/
    └── water_quality.db       # SQLite database
```

---

### 📄 **License**

For internal use only.

---

**Note**: Developed for water quality monitoring and monthly reporting compliance.
