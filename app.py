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


@st.dialog("📊 กราฟจำนวนครั้งตรวจวัดรายวัน")
def show_daily_count_chart(
    processor: WaterQualityProcessor,
    parameter: str,
    group: str,
    year: int,
    month: int,
    param_thai_name: str,
    group_thai_name: str
):
    """
    Show daily count chart in modal dialog

    Args:
        processor: WaterQualityProcessor instance
        parameter: Internal parameter name (e.g., 'Turbidity')
        group: Internal group name (e.g., 'TW')
        year: Selected year
        month: Selected month
        param_thai_name: Thai parameter name for display
        group_thai_name: Thai group name for display
    """
    st.markdown(f"### {param_thai_name} - {group_thai_name}")

    # Get daily counts
    daily_counts = processor.get_daily_counts_for_parameter_group(
        parameter, group, year, month
    )

    if daily_counts.empty:
        st.warning("ไม่มีข้อมูลในช่วงเวลาที่เลือก")
        return

    # Summary metrics
    total_count = daily_counts['count'].sum()
    avg_count = daily_counts['count'].mean()
    max_day = daily_counts.loc[daily_counts['count'].idxmax(), 'day']
    max_count = daily_counts['count'].max()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("จำนวนครั้งทั้งหมด", f"{total_count} ครั้ง")
    with col2:
        st.metric("เฉลี่ยต่อวัน", f"{avg_count:.1f} ครั้ง")
    with col3:
        st.metric("วันที่มีการตรวจวัดมากที่สุด", f"วันที่ {max_day}")

    st.markdown("---")

    # Bar chart
    chart_data = daily_counts.set_index('day')['count']
    st.bar_chart(chart_data)


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

            # Convert to long format for interactive table
            sample_counts_reset = sample_counts.reset_index()
            sample_counts_reset.columns = ['พารามิเตอร์'] + list(sample_counts_reset.columns[1:])

            # Map parameter names to Thai
            sample_counts_reset['พารามิเตอร์'] = sample_counts_reset['พารามิเตอร์'].map(param_thai)

            # Rename columns to Thai before melting
            column_thai_map = {
                'RW': 'น้ำดิบ',
                'CW': 'น้ำตกตะกอน',
                'FW': 'น้ำกรอง',
                'TW': 'น้ำประปา'
            }
            sample_counts_reset.columns = ['พารามิเตอร์'] + [column_thai_map.get(col, col) for col in sample_counts.columns]

            # Melt to long format
            long_format = sample_counts_reset.melt(
                id_vars=['พารามิเตอร์'],
                var_name='กลุ่ม',
                value_name='จำนวน'
            )

            # Map Thai group names back to English for internal use
            group_reverse_map = {
                'น้ำดิบ': 'RW',
                'น้ำตกตะกอน': 'CW',
                'น้ำกรอง': 'FW',
                'น้ำประปา': 'TW'
            }

            # Create internal parameter name column (hidden)
            reverse_param_thai = {v: k for k, v in param_thai.items()}
            long_format['param_internal'] = long_format['พารามิเตอร์'].map(reverse_param_thai)
            long_format['group_internal'] = long_format['กลุ่ม'].map(group_reverse_map)

            # Create pivot view for display (keep original format for reference)
            sample_counts_copy = sample_counts.copy()
            sample_counts_copy.index = sample_counts_copy.index.map(lambda x: param_thai.get(x, x))
            sample_counts_copy.columns = ['น้ำดิบ', 'น้ำตกตะกอน', 'น้ำกรอง', 'น้ำประปา']

            # Create tabs
            tab1, tab2 = st.tabs(["📊 ตารางสรุป (Pivot)", "📈 ดูกราฟรายวัน"])

            with tab1:
                st.dataframe(sample_counts_copy, use_container_width=True)

            with tab2:
                st.markdown("### ตารางสรุปจำนวนตัวอย่างที่วิเคราะห์")
                st.markdown("👆 **คลิกที่แถวในตารางด้านล่าง** เพื่อดูกราฟจำนวนครั้งตรวจวัดรายวัน")

                # Display interactive table with row selection
                selection = st.dataframe(
                    long_format[['พารามิเตอร์', 'กลุ่ม', 'จำนวน']],
                    on_select="rerun",
                    use_container_width=True,
                    hide_index=True
                )

                # Handle selection
                if selection.selection['rows']:
                    # Get first selected row
                    selected_idx = selection.selection['rows'][0]
                    selected_row = long_format.iloc[selected_idx]

                    # Store in session state
                    st.session_state.selected_param_internal = selected_row['param_internal']
                    st.session_state.selected_group_internal = selected_row['group_internal']
                    st.session_state.selected_param_thai = selected_row['พารามิเตอร์']
                    st.session_state.selected_group_thai = selected_row['กลุ่ม']

        # Show dialog if selection exists
        if all(key in st.session_state for key in ['selected_param_internal', 'selected_group_internal',
                                                     'selected_param_thai', 'selected_group_thai']):
            show_daily_count_chart(
                processor,
                st.session_state.selected_param_internal,
                st.session_state.selected_group_internal,
                selected_year,
                selected_month,
                st.session_state.selected_param_thai,
                st.session_state.selected_group_thai
            )

            # Clear session state after showing dialog
            for key in ['selected_param_internal', 'selected_group_internal',
                       'selected_param_thai', 'selected_group_thai']:
                if key in st.session_state:
                    del st.session_state[key]

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

            # Recycle Water Daily Counts (Interactive)
            if recycle_stats:
                st.markdown("---")
                st.markdown("### กราฟจำนวนครั้งตรวจวัดรายวันของน้ำนำกลับ")
                st.markdown("👆 **คลิกที่แถวในตารางด้านล่าง** เพื่อดูกราฟจำนวนครั้งตรวจวัดรายวัน")

                # Prepare data for recycle water table
                recycle_data = []
                for param_name, param_thai_name in [('Turbidity', 'ความขุ่นน้ำนำกลับ'), ('Conductivity', 'ความนำไฟฟ้าน้ำนำกลับ')]:
                    if param_name in recycle_stats:
                        recycle_data.append({
                            'พารามิเตอร์': param_thai_name,
                            'จำนวนตัวอย่าง': recycle_stats[param_name]['count'],
                            'param_internal': param_name,
                            'group_internal': 'recycle_water'
                        })

                if recycle_data:
                    recycle_df = pd.DataFrame(recycle_data)

                    # Display recycle water table with selection
                    recycle_selection = st.dataframe(
                        recycle_df,
                        column_config={
                            'พารามิเตอร์': st.column_config.TextColumn('พารามิเตอร์'),
                            'จำนวนตัวอย่าง': st.column_config.NumberColumn('จำนวนตัวอย่าง')
                        },
                        on_select="rerun",
                        use_container_width=True,
                        hide_index=True
                    )

                    # Handle recycle water selection
                    if recycle_selection.selection['rows']:
                        # Get first selected row
                        selected_idx = recycle_selection.selection['rows'][0]
                        selected_row = recycle_df.iloc[selected_idx]

                        # Store in session state (override with recycle water selection)
                        st.session_state.selected_param_internal = selected_row['param_internal']
                        st.session_state.selected_group_internal = 'recycle_water'
                        st.session_state.selected_param_thai = selected_row['พารามิเตอร์']
                        st.session_state.selected_group_thai = 'น้ำนำกลับ'

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
                    None, None, None, None, None, None, None, None, None, None, None
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

        # Extreme Values Analysis (Outlier Detection)
        if not water_quality_df.empty:
            st.markdown("---")
            st.subheader("ตรวจสอบความถูกต้อง: ค่าความขุ่นที่สูงผิดปกติ")
            st.markdown("แสดงค่าความขุ่นที่อยู่เหนือ 95th percentile และค่าสูงสุด (100th percentile) ของน้ำหลังกรองและน้ำประปา")

            # Get extreme values for FW and TW (normal case)
            fw_extremes = processor.get_extreme_values('Turbidity', 'FW', percentile_threshold=95.0)
            tw_extremes = processor.get_extreme_values('Turbidity', 'TW', percentile_threshold=95.0)

            # Get extreme values for FW and TW (@RW<100 case)
            fw_extremes_rw = processor.get_extreme_values_rw_filtered('Turbidity', 'FW', percentile_threshold=95.0, rw_threshold=rw_threshold)
            tw_extremes_rw = processor.get_extreme_values_rw_filtered('Turbidity', 'TW', percentile_threshold=95.0, rw_threshold=rw_threshold)

            # Combine all
            all_extremes_list = []

            for extremes, group_name, is_rw_filtered in [
                (fw_extremes, 'น้ำกรอง (FW)', False),
                (tw_extremes, 'น้ำประปา (TW)', False),
                (fw_extremes_rw, 'น้ำกรอง (FW)', True),
                (tw_extremes_rw, 'น้ำประปา (TW)', True)
            ]:
                if not extremes.empty:
                    extremes = extremes.copy()
                    extremes['กลุ่ม'] = group_name
                    extremes['@RW<100'] = 'ใช่' if is_rw_filtered else 'ไม่ใช่'
                    all_extremes_list.append(extremes)

            if all_extremes_list:
                # Combine
                all_extremes = pd.concat(all_extremes_list, ignore_index=True)

                # Sort by value descending
                all_extremes = all_extremes.sort_values('value', ascending=False)

                # Reorder columns
                all_extremes = all_extremes[['date', 'time_period', 'กลุ่ม', 'value', 'percentile_type', '@RW<100']]

                # Rename columns to Thai
                all_extremes.columns = ['วันที่', 'ช่วงเวลา', 'กลุ่ม', 'ความขุ่น (NTU)', 'ประเภท', 'สถานะ @RW<100']

                # Translate percentile_type to Thai
                percentile_thai = {
                    '95th': '95th percentile',
                    '100th': '100th percentile'
                }
                all_extremes['ประเภท'] = all_extremes['ประเภท'].map(percentile_thai)

                st.dataframe(all_extremes, use_container_width=True, hide_index=True)
            else:
                st.info("ไม่พบค่าความขุ่นที่สูงผิดปกติในช่วงเวลาที่เลือก")


if __name__ == "__main__":
    main()
