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
            # Define the order of parameters to display (only these 10)
            param_order = [
                'Turbidity',
                'Alkalinity',
                'pH',
                'Free Residual Cl2',
                'Conductivity',
                'O2 Consume',
                'DO',
                'SS',
                'Color',
                'NH3-N'
            ]

            # Filter and reorder according to the specified order
            sample_counts = sample_counts[sample_counts.index.isin(param_order)]
            # Reindex to maintain the specified order (only keep existing parameters)
            sample_counts = sample_counts.reindex([p for p in param_order if p in sample_counts.index])

            sample_counts.index = sample_counts.index.map(lambda x: param_thai.get(x, x))
            sample_counts.columns = ['น้ำดิบ', 'น้ำตกตะกอน', 'น้ำกรอง', 'น้ำประปา']
            st.dataframe(sample_counts, use_container_width=True)

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

        # Recycle Water Analysis
        if not water_quality_df.empty:
            st.subheader("การวิเคราะห์ตัวอย่างจากระบบกำจัดตะกอน")

            recycle_stats = processor.get_recycle_water_stats()

            if recycle_stats:
                col1, col2 = st.columns(2)

                with col1:
                    if 'Turbidity' in recycle_stats:
                        st.markdown("**ความขุ่นน้ำนำกลับ**")
                        turb_count = recycle_stats['Turbidity']['count']
                        st.metric("จำนวนตัวอย่าง", f"{turb_count} ครั้ง")

                with col2:
                    if 'Conductivity' in recycle_stats:
                        st.markdown("**ความนำไฟฟ้าน้ำนำกลับ**")
                        cond_count = recycle_stats['Conductivity']['count']
                        st.metric("จำนวนตัวอย่าง", f"{cond_count} ครั้ง")
            else:
                st.info("ไม่มีข้อมูลน้ำนำกลับในช่วงเวลาที่เลือก")

        # Performance Evaluation Table
        if not water_quality_df.empty:
            st.subheader("สรุปเกณฑ์ประเมินผลงาน")

            # Calculate all required metrics
            turb_tw_nc, turb_tw_total = processor.count_nc_samples(
                'TW', 'Turbidity', lambda x: x > turbidity_threshold
            )
            ph_nc, ph_total = processor.count_nc_samples(
                'TW', 'pH', lambda x: x < ph_min or x > ph_max
            )
            cl2_nc, cl2_total = processor.count_nc_samples(
                'TW', 'Free Residual Cl2', lambda x: x < cl2_threshold
            )

            # Get statistics with count
            fw_stats_with_count = processor.get_statistics_with_count('FW', 'Turbidity', apply_filter=False)
            tw_stats_with_count = processor.get_statistics_with_count('TW', 'Turbidity', apply_filter=False)
            fw_stats_filtered_with_count = processor.get_statistics_with_count('FW', 'Turbidity', apply_filter=True)
            tw_stats_filtered_with_count = processor.get_statistics_with_count('TW', 'Turbidity', apply_filter=True)

            # Build performance table data
            perf_data = {
                'เกณฑ์วัดการดำเนินงาน': [
                    'จำนวนตัวอย่างได้มาตรฐาน ด้านกายภาพ (ความขุ่น)',
                    'จำนวนตัวอย่างค่าความเป็นกรด-ด่าง (pH)',
                    'จำนวนตัวอย่างได้มาตรฐาน ด้านเคมี (คลอรีน)',
                    'ค่าความขุ่นน้ำหลังกรองเฉลี่ย',
                    'ค่าความขุ่นน้ำหลังกรอง (95percentile)',
                    'ค่าความขุ่นน้ำประปาเฉลี่ย',
                    'ค่าความขุ่นน้ำประปา (95percentile)',
                    'ค่าความขุ่นน้ำประปา (100percentile)',
                    'ค่าความขุ่นน้ำหลังกรองเฉลี่ย@ที่ RW<100',
                    'ค่าความขุ่นน้ำหลังกรอง (95percentile)@ที่ RW<100',
                    'ค่าความขุ่นน้ำหลังกรอง (100percentile)@ที่ RW<100',
                    'ค่าความขุ่นน้ำประปาเฉลี่ย@ที่ RW<100',
                    'ค่าความขุ่นน้ำประปา (95percentile)@ที่ RW<100',
                    'ค่าความขุ่นน้ำประปา (100percentile)@ที่ RW<100'
                ],
                'หน่วยวัด': [
                    'ร้อยละ', 'ร้อยละ', 'ร้อยละ',
                    'NTU', 'NTU', 'NTU', 'NTU', 'NTU',
                    'NTU', 'NTU', 'NTU',
                    'NTU', 'NTU', 'NTU'
                ],
                'จำนวน NC': [
                    turb_tw_nc, ph_nc, cl2_nc,
                    '', '', '', '', '', '', '', '', '', '', ''
                ],
                'จำนวนตัวอย่าง': [
                    turb_tw_total, ph_total, cl2_total,
                    fw_stats_with_count['total_count'], fw_stats_with_count['total_count'],
                    tw_stats_with_count['total_count'], tw_stats_with_count['total_count'], tw_stats_with_count['total_count'],
                    fw_stats_filtered_with_count['total_count'], fw_stats_filtered_with_count['total_count'], fw_stats_filtered_with_count['total_count'],
                    tw_stats_filtered_with_count['total_count'], tw_stats_filtered_with_count['total_count'], tw_stats_filtered_with_count['total_count']
                ],
                'ผลงาน': [
                    f"{((turb_tw_total - turb_tw_nc) / turb_tw_total * 100):.1f}%" if turb_tw_total > 0 else "N/A",
                    f"{((ph_total - ph_nc) / ph_total * 100):.1f}%" if ph_total > 0 else "N/A",
                    f"{((cl2_total - cl2_nc) / cl2_total * 100):.1f}%" if cl2_total > 0 else "N/A",
                    f"{fw_stats_with_count['mean']:.2f}" if not np.isnan(fw_stats_with_count['mean']) else "N/A",
                    f"{fw_stats_with_count['p95']:.2f}" if not np.isnan(fw_stats_with_count['p95']) else "N/A",
                    f"{tw_stats_with_count['mean']:.2f}" if not np.isnan(tw_stats_with_count['mean']) else "N/A",
                    f"{tw_stats_with_count['p95']:.2f}" if not np.isnan(tw_stats_with_count['p95']) else "N/A",
                    f"{tw_stats_with_count['p100']:.2f}" if not np.isnan(tw_stats_with_count['p100']) else "N/A",
                    f"{fw_stats_filtered_with_count['mean']:.2f}" if not np.isnan(fw_stats_filtered_with_count['mean']) else "N/A",
                    f"{fw_stats_filtered_with_count['p95']:.2f}" if not np.isnan(fw_stats_filtered_with_count['p95']) else "N/A",
                    f"{fw_stats_filtered_with_count['p100']:.2f}" if not np.isnan(fw_stats_filtered_with_count['p100']) else "N/A",
                    f"{tw_stats_filtered_with_count['mean']:.2f}" if not np.isnan(tw_stats_filtered_with_count['mean']) else "N/A",
                    f"{tw_stats_filtered_with_count['p95']:.2f}" if not np.isnan(tw_stats_filtered_with_count['p95']) else "N/A",
                    f"{tw_stats_filtered_with_count['p100']:.2f}" if not np.isnan(tw_stats_filtered_with_count['p100']) else "N/A"
                ]
            }

            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
