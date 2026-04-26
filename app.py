"""
Monthly Water Quality Report Dashboard
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import numpy as np
import config
from src.database import (
    get_connection,
    get_data_by_month,
    get_jar_test_by_month,
    get_available_months,
    get_database_summary
)
from src.data_processor import WaterQualityProcessor, JarTestProcessor


def main():
    # Page Configuration
    st.set_page_config(
        page_title="Water Quality Dashboard",
        page_icon="💧",
        layout=config.APP_LAYOUT,
        initial_sidebar_state="expanded"
    )

    st.title(config.APP_TITLE)
    st.markdown("---")

    # ============================================
    # SIDEBAR - Year/Month Selection & Thresholds
    # ============================================
    with st.sidebar:
        st.header("⚙️ การตั้งค่า")

        # Database Connection
        try:
            conn = get_connection()
            st.success("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
            st.stop()

        # Get available months
        available_months = get_available_months(conn)

        if not available_months:
            st.warning("⚠️ ไม่พบข้อมูลในฐานข้อมูล")
            st.stop()

        # Year/Month Selection
        st.subheader("📅 เลือกช่วงเวลา")

        # Extract unique years and months
        years = sorted(list(set([y for y, m in available_months])), reverse=True)

        selected_year = st.selectbox(
            "ปี (Year)",
            options=years,
            index=0
        )

        # Filter months for selected year
        months_for_year = sorted([m for y, m in available_months if y == selected_year])

        month_names = {
            1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
            5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
            9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"
        }

        selected_month = st.selectbox(
            "เดือน (Month)",
            options=months_for_year,
            format_func=lambda x: f"{x:02d} - {month_names.get(x, '')}",
            index=len(months_for_year) - 1
        )

        st.markdown("---")

        # Threshold Settings
        st.subheader("🎯 เกณฑ์มาตรฐาน")

        turbidity_threshold = st.number_input(
            "ความขุ่นน้ำประปาสูงสุด (NTU)",
            min_value=0.0,
            max_value=10.0,
            value=config.DEFAULT_THRESHOLDS["turbidity_tw_max"],
            step=0.01,
            help="ค่าความขุ่นที่ไม่ควรเกิน (มาตรฐาน: 1.00 NTU)"
        )

        cl2_threshold = st.number_input(
            "คลอรีนตกค้างต่ำสุด (mg/L)",
            min_value=0.0,
            max_value=5.0,
            value=config.DEFAULT_THRESHOLDS["cl2_min"],
            step=0.1,
            help="ค่าคลอรีนคงเหลือต่ำสุด (มาตรฐาน: 0.8 mg/L)"
        )

        ph_min = st.number_input(
            "ค่า pH ต่ำสุด",
            min_value=0.0,
            max_value=14.0,
            value=config.DEFAULT_THRESHOLDS["ph_min"],
            step=0.1
        )

        ph_max = st.number_input(
            "ค่า pH สูงสุด",
            min_value=0.0,
            max_value=14.0,
            value=config.DEFAULT_THRESHOLDS["ph_max"],
            step=0.1
        )

        rw_threshold = st.number_input(
            "ความขุ่นน้ำดิบสูงสุดสำหรับ @RW<100 (NTU)",
            min_value=0.0,
            max_value=1000.0,
            value=config.DEFAULT_THRESHOLDS["rw_turbidity_threshold"],
            step=10.0,
            help="เกณฑ์สำหรับกรองข้อมูลเมื่อน้ำดิบมีความขุ่นสูง"
        )

    # ============================================
    # MAIN CONTENT - Data Loading & Preview
    # ============================================

    st.header(f"📊 รายงานประจำเดือน {month_names[selected_month]} {selected_year}")

    # Load Data
    with st.spinner("กำลังโหลดข้อมูล..."):
        water_quality_df = get_data_by_month(conn, selected_year, selected_month)
        jar_test_df = get_jar_test_by_month(conn, selected_year, selected_month)

    # Display Database Summary
    with st.expander("📋 สรุปข้อมูลฐานข้อมูล", expanded=False):
        summary = get_database_summary(conn)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ระเบียน Water Quality", f"{summary.get('water_quality_count', 0):,}")
        with col2:
            st.metric("ระเบียน Jar Test", f"{summary.get('jar_test_count', 0):,}")
        with col3:
            date_range = summary.get('date_range', (None, None))
            if date_range[0] and date_range[1]:
                st.metric("ช่วงวันที่", f"{date_range[0]} ถึง {date_range[1]}")

        st.markdown("**Parameters ทั้งหมด:**")
        st.write(", ".join(summary.get('parameters', [])))

        st.markdown("**Sampling Points ทั้งหมด:**")
        all_points = summary.get('sampling_points', [])
        st.write(", ".join(all_points))

        # Check for CW, FW, TW specifically
        st.markdown("---")
        st.markdown("**ตรวจสอบ Sampling Points พิเศษ:**")
        special_points = ['CW', 'FW', 'TW', 'RW']
        for point in special_points:
            if point in all_points:
                st.success(f"✅ มี {point} ใน Database")
            else:
                st.error(f"❌ ไม่พบ {point} ใน Database")

    # Display Data Preview
    if not water_quality_df.empty:
        st.subheader("🔍 ตัวอย่างข้อมูล Water Quality")

        st.write(f"**จำนวนระเบียน:** {len(water_quality_df):,}")
        st.dataframe(
            water_quality_df.head(20),
            use_container_width=True,
            height=300
        )

        # Show statistics
        with st.expander("📈 สถิติข้อมูลเบื้องต้น"):
            st.write("**จำนวนระเบียนต่อ Parameter:**")
            param_counts = water_quality_df['parameter'].value_counts().reset_index()
            param_counts.columns = ['Parameter', 'Count']
            st.dataframe(param_counts, use_container_width=True)

            st.write("**จำนวนระเบียนต่อ Sampling Point:**")
            point_counts = water_quality_df['sampling_point'].value_counts().reset_index()
            point_counts.columns = ['Sampling Point', 'Count']
            st.dataframe(point_counts, use_container_width=True)

    else:
        st.warning(f"⚠️ ไม่พบข้อมูลสำหรับเดือน {month_names[selected_month]} {selected_year}")

    # Display Jar Test Data
    if not jar_test_df.empty:
        st.subheader("🧪 ตัวอย่างข้อมูล Jar Test")
        st.write(f"**จำนวนระเบียน:** {len(jar_test_df):,}")
        st.dataframe(
            jar_test_df.head(20),
            use_container_width=True,
            height=300
        )
    else:
        st.info("ℹ️ ไม่มีข้อมูล Jar Test ในช่วงเวลาที่เลือก")

    # ============================================
    # PHASE 2: DATA PROCESSING & ANALYSIS
    # ============================================
    st.markdown("---")
    st.header("📊 การวิเคราะห์ข้อมูล")

    if not water_quality_df.empty:
        # Initialize processor
        thresholds = {
            'turbidity_tw_max': turbidity_threshold,
            'cl2_min': cl2_threshold,
            'ph_min': ph_min,
            'ph_max': ph_max,
            'rw_turbidity_threshold': rw_threshold
        }

        processor = WaterQualityProcessor(water_quality_df, thresholds)

        # Table 1: Summary by Group and Parameter
        st.subheader("ตารางที่ 1: จำนวนตัวอย่างที่วิเคราะห์ในแต่ละกลุ่ม")

        sample_counts = processor.count_samples_by_group_and_parameter()

        # Thai parameter names mapping
        param_thai = {
            'Turbidity': 'ความขุ่น',
            'Alkalinity': 'ความเป็นด่าง',
            'pH': 'ความเป็นกรด-ด่าง',
            'Free Residual Cl2': 'คลอรีนตกค้างอิสระ',
            'Chemical Dosage': 'ปริมาณสารเคมีที่ใช้',
            '% Sludge': 'ปอนต์ขี้เลื่อย',
            'O2 Consume': 'ออกซิเจน คอนซูม',
            'Conductivity': 'ความนำไฟฟ้า',
            'DO': 'ออกซิเจนละลายน้ำ',
            'Color': 'สีปรากฏ',
            'SS': 'ของแข็งแขวนลอย',
            'NH3-N': 'แอมโมเนีย-ไนโตรเจน'
        }

        if not sample_counts.empty:
            # Filter out % Sludge from the table
            sample_counts = sample_counts[~sample_counts.index.isin(['% Sludge'])]

            sample_counts.index = sample_counts.index.map(lambda x: param_thai.get(x, x))
            sample_counts.columns = ['น้ำดิบ', 'น้ำตกตะกอน', 'น้ำกรอง', 'น้ำประปา']
            st.dataframe(sample_counts, use_container_width=True)

            # Debug info: Show which parameters have zero data in TW group
            with st.expander("🔍 ข้อมูลเพิ่มเติม - Parameters ที่ไม่มีข้อมูลน้ำประปา"):
                zero_tw_params = sample_counts[sample_counts['น้ำประปา'] == 0]
                if not zero_tw_params.empty:
                    st.write("**Parameters ที่ไม่มีข้อมูลที่จุดวัดน้ำประปา:**")
                    for param in zero_tw_params.index:
                        st.write(f"- {param}")

                    st.info("💡 หมายเหตุ: Parameters เหล่านี้อาจจะไม่ได้วัดที่จุดวัดน้ำประปา "  \
                           "หรือวัดเฉพาะช่วงเวลาที่ไม่ได้อยู่ในเดือนที่เลือก")
                else:
                    st.success("✅ ทุก Parameter มีข้อมูลที่จุดวัดน้ำประปาครบถ้วน")

            # Debug info: Show O2 Consume details
            with st.expander("🔍 ข้อมูลเพิ่มเติม - O2 Consume Sampling Points"):
                o2_data = water_quality_df[water_quality_df['parameter'] == 'O2 Consume']

                if not o2_data.empty:
                    st.write("**O2 Consume พบที่ Sampling Points ทั้งหมด (จริงใน Database):**")
                    o2_points = sorted(o2_data['sampling_point'].unique())
                    for point in o2_points:
                        count = len(o2_data[o2_data['sampling_point'] == point])
                        st.write(f"- **{point}**: {count} ระเบียน")

                    # Query specific date to see detailed records
                    st.write("---")
                    st.subheader("🔍 ตรวจสอบข้อมูลวันที่ 7 เม.ย. 2026")

                    query = """
                        SELECT date, time_period, time_label, sampling_point, value
                        FROM water_quality_data
                        WHERE parameter = 'O2 Consume'
                          AND date = '2026-04-07'
                        ORDER BY time_period, sampling_point
                    """

                    try:
                        o2_april7 = pd.read_sql_query(query, conn)
                        if not o2_april7.empty:
                            st.write("**O2 Consume วันที่ 7 เม.ย. 2026:**")
                            st.dataframe(o2_april7, use_container_width=True, hide_index=True)

                            # Summary by time period
                            st.write("**สรุปจำนวนครั้งตามช่วงเวลา:**")
                            time_summary = o2_april7.groupby(['time_period', 'time_label']).size().reset_index()
                            time_summary.columns = ['ช่วงเวลา', 'Label', 'จำนวนครั้ง']
                            st.dataframe(time_summary, use_container_width=True, hide_index=True)

                            # Summary by sampling point
                            st.write("**สรุปจำนวนครั้งตาม Sampling Point:**")
                            point_summary = o2_april7.groupby('sampling_point').size().reset_index()
                            point_summary.columns = ['Sampling Point', 'จำนวนครั้ง']
                            st.dataframe(point_summary, use_container_width=True, hide_index=True)

                            # Total records
                            st.metric("รวมทั้งหมด", f"{len(o2_april7)} ระเบียน")
                        else:
                            st.warning("ไม่พบข้อมูล O2 Consume วันที่ 7 เม.ย. 2026")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการ query: {e}")

                    st.info("💡 จากข้อมูลนี้จะเห็นว่าใน 1 วันมีการวัดที่ช่วงเวลาไหนบ้าง และ sampling point ไหนบ้าง")

                else:
                    st.warning("⚠️ ไม่พบข้อมูล O2 Consume ในเดือนที่เลือก")
        else:
            st.warning("ไม่พบข้อมูลสำหรับสรุปจำนวนตัวอย่าง")

        # Statistics for Turbidity
        st.subheader("สถิติความขุ่น (Turbidity)")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**น้ำกรอง (FW1, FW2)**")
            fw_stats = processor.calculate_statistics(
                'FW',  # Use group name instead of list
                'Turbidity',
                apply_filter=False
            )
            st.metric("ค่าเฉลี่ย", f"{fw_stats['mean']:.2f} NTU" if not np.isnan(fw_stats['mean']) else "N/A")
            st.metric("95th Percentile", f"{fw_stats['p95']:.2f} NTU" if not np.isnan(fw_stats['p95']) else "N/A")
            st.metric("100th Percentile", f"{fw_stats['p100']:.2f} NTU" if not np.isnan(fw_stats['p100']) else "N/A")

        with col2:
            st.markdown("**น้ำประปา (TW1, TW2, TW3, DPS1, DPS2)**")
            tw_stats = processor.calculate_statistics(
                'TW',  # Use group name instead of list
                'Turbidity',
                apply_filter=False
            )
            st.metric("ค่าเฉลี่ย", f"{tw_stats['mean']:.2f} NTU" if not np.isnan(tw_stats['mean']) else "N/A")
            st.metric("95th Percentile", f"{tw_stats['p95']:.2f} NTU" if not np.isnan(tw_stats['p95']) else "N/A")
            st.metric("100th Percentile", f"{tw_stats['p100']:.2f} NTU" if not np.isnan(tw_stats['p100']) else "N/A")

        # Statistics with @RW<100 filtering
        st.subheader("สถิติความขุ่น กรณี @RW<100")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**น้ำกรอง (FW1, FW2) @RW<100**")
            fw_stats_filtered = processor.calculate_statistics(
                'FW',  # Use group name instead of list
                'Turbidity',
                apply_filter=True
            )
            st.metric("ค่าเฉลี่ย", f"{fw_stats_filtered['mean']:.2f} NTU" if not np.isnan(fw_stats_filtered['mean']) else "N/A")
            st.metric("95th Percentile", f"{fw_stats_filtered['p95']:.2f} NTU" if not np.isnan(fw_stats_filtered['p95']) else "N/A")
            st.metric("100th Percentile", f"{fw_stats_filtered['p100']:.2f} NTU" if not np.isnan(fw_stats_filtered['p100']) else "N/A")

        with col2:
            st.markdown("**น้ำประปา (TW1, TW2, TW3, DPS1, DPS2) @RW<100**")
            tw_stats_filtered = processor.calculate_statistics(
                'TW',  # Use group name instead of list
                'Turbidity',
                apply_filter=True
            )
            st.metric("ค่าเฉลี่ย", f"{tw_stats_filtered['mean']:.2f} NTU" if not np.isnan(tw_stats_filtered['mean']) else "N/A")
            st.metric("95th Percentile", f"{tw_stats_filtered['p95']:.2f} NTU" if not np.isnan(tw_stats_filtered['p95']) else "N/A")
            st.metric("100th Percentile", f"{tw_stats_filtered['p100']:.2f} NTU" if not np.isnan(tw_stats_filtered['p100']) else "N/A")

        # NC Count for Treated Water
        st.subheader("จำนวนตัวอย่างที่ไม่ผ่านเกณฑ์ (NC)")

        col1, col2, col3 = st.columns(3)

        # Turbidity NC
        with col1:
            turb_nc, turb_total = processor.count_nc_samples(
                'TW',  # Use group name instead of list
                'Turbidity',
                lambda x: x > turbidity_threshold
            )
            st.metric("ความขุ่น (NC/Total)", f"{turb_nc}/{turb_total}")
            if turb_total > 0:
                turb_pct = ((turb_total - turb_nc) / turb_total) * 100
                st.metric("% ผ่านเกณฑ์", f"{turb_pct:.1f}%")

        # pH NC
        with col2:
            ph_nc, ph_total = processor.count_nc_samples(
                'TW',  # Use group name instead of list
                'pH',
                lambda x: x < ph_min or x > ph_max
            )
            st.metric("pH (NC/Total)", f"{ph_nc}/{ph_total}")
            if ph_total > 0:
                ph_pct = ((ph_total - ph_nc) / ph_total) * 100
                st.metric("% ผ่านเกณฑ์", f"{ph_pct:.1f}%")

        # Cl2 NC
        with col3:
            cl2_nc, cl2_total = processor.count_nc_samples(
                'TW',  # Use group name instead of list
                'Free Residual Cl2',
                lambda x: x < cl2_threshold
            )
            st.metric("คลอรีน (NC/Total)", f"{cl2_nc}/{cl2_total}")
            if cl2_total > 0:
                cl2_pct = ((cl2_total - cl2_nc) / cl2_total) * 100
                st.metric("% ผ่านเกณฑ์", f"{cl2_pct:.1f}%")

        # Jar Test Chemical Usage
        if not jar_test_df.empty:
            st.subheader("อัตราการใช้สารเคมี (Jar Test)")

            jar_processor = JarTestProcessor(jar_test_df)
            chemical_counts = jar_processor.count_chemical_usage_per_month()

            if not chemical_counts.empty:
                st.markdown("**จำนวนครั้ง/เดือน:**")
                for chemical, count in chemical_counts.items():
                    st.write(f"- **{chemical}**: {count} ครั้ง")
            else:
                st.info("ไม่มีข้อมูลการใช้สารเคมีในช่วงเวลาที่เลือก")

    # ============================================
    # PHASE 2 COMPLETE
    # ============================================
    st.markdown("---")
    st.success("✅ **Phase 2 สำเร็จ!** ระบบคำนวณ Business Logic และแสดงผลลัพธ์ครบถ้วนแล้ว")


if __name__ == "__main__":
    main()
