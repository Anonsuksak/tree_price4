import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. ตั้งค่าหน้าตารูปแบบเว็บ Dashboard
st.set_page_config(
    page_title="ERC 2568 Crop Cost & Return Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันโหลดและล้างข้อมูล
@st.cache_data
def load_data():
    file_path = "ฐานข้อมูลต้นทุนและผลตอบแทน_ERC_2568.csv"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ข้อมูล: {file_path}")

    df = pd.read_csv(file_path, encoding='utf-8')
    
    # แปลงคอลัมน์ตัวเลขให้ถูกต้องและปลอดภัยจากสัญลักษณ์คอมมา (,)
    numeric_cols = ['avg_cost_total', 'avg_revenue_per_year', 'avg_wta', 'avg_proposed_price', 'profit_est']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # แปลงรูปแบบประเภทบัญชีกลาง กกพ.
    if 'account_type' in df.columns:
        df['account_type_desc'] = df['account_type'].map({'A': 'บัญชี ก. (ต้นไม้ทั่วไป)', 'B': 'บัญชี ข. (ต้นไม้ล้มลุก)'})
    else:
        df['account_type_desc'] = 'ไม่ระบุประเภทบัญชี'
    df['account_type_desc'] = df['account_type_desc'].fillna('ไม่ระบุประเภทบัญชี')

    # คำนวณกำไรประเมินสุทธิ (รายได้ - ต้นทุน)
    if 'profit_est' not in df.columns or df['profit_est'].isnull().all():
        df['profit_est'] = df['avg_revenue_per_year'].fillna(0) - df['avg_cost_total'].fillna(0)
        
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    st.stop()

# 3. ส่วนควบคุมด้านข้าง (Sidebar Filters)
st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")

account_types = df['account_type_desc'].unique().tolist()
selected_accounts = st.sidebar.multiselect(
    "เลือกประเภทบัญชีพืช:", 
    options=account_types, 
    default=account_types
)

# การกรองข้อมูล 1 แถวคือ 1 ชนิดพืช
filtered_df = df[
    (df['account_type_desc'].isin(selected_accounts)) &
    (df['is_active'] == 1) # กรองเฉพาะพืชที่ยังใช้งานอยู่จริง
].copy()

# 4. ส่วนหัวของหน้า Dashboard
st.title("🌱 แดชบอร์ดวิเคราะห์ต้นทุนและผลตอบแทนพืช (ERC 2568)")
st.markdown("### 📊 การวิเคราะห์เชิงเปรียบเทียบ")

# 5. ส่วนแสดงกราฟ

st.markdown("### 📊 การวิเคราะห์เชิงเปรียบเทียบ")

# 6. ส่วนสร้างกราฟ (Visualizations)
tab1, tab2 = st.tabs(["🔝 10 อันดับพืช", "⚖️ ความสัมพันธ์ ต้นทุน vs รายได้"])

with tab1:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        metric_to_plot = st.selectbox("เลือกตัวชี้วัดที่ต้องการดูสถิติสูงสุด:", ["avg_cost_total", "avg_revenue_per_year", "avg_proposed_price"])
        metric_labels = {
            "avg_cost_total": "ต้นทุนรวมเฉลี่ย (บาท)",
            "avg_revenue_per_year": "รายได้เฉลี่ยต่อปี (บาท)",
            "avg_proposed_price": "ราคาเสนออ้างอิง (บาท)"
        }
        
        if not filtered_df.empty:
            top_10 = filtered_df.dropna(subset=[metric_to_plot]).nlargest(10, metric_to_plot)
            fig_bar = px.bar(
                top_10,
                x=metric_to_plot,
                y='plant_name' if 'plant_name' in top_10.columns else top_10.index,
                orientation='h',
                title=f"🥇 10 อันดับพืชที่มี{metric_labels[metric_to_plot]}สูงสุด",
                labels={metric_to_plot: metric_labels[metric_to_plot], 'plant_name': 'ชื่อพืช'},
                color=metric_to_plot,
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูลสำหรับสร้างกราฟแท่ง")
        
    with col_chart2:
        if not filtered_df.empty:
            fig_pie = px.pie(
                filtered_df, 
                names='account_type_desc', 
                title="สัดส่วนพืชตามประเภทบัญชีกลาง",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูลสำหรับสร้างกราฟวงกลม")

with tab2:
    st.markdown("#### กราฟกระจายตัวเปรียบเทียบต้นทุนรวมและรายได้ต่อปีแยกตามพืช")
    if not filtered_df.empty:
        fig_scatter = px.scatter(
            filtered_df,
            x="avg_cost_total",
            y="avg_revenue_per_year",
            color="account_type_desc",
            hover_name="plant_name" if "plant_name" in filtered_df.columns else None,
            labels={
                "avg_cost_total": "ต้นทุนรวมเฉลี่ย (บาท)",
                "avg_revenue_per_year": "รายได้รวมเฉลี่ยต่อปี (บาท)"
            },
            title="Cost vs Revenue Analysis"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("⚠️ ไม่มีข้อมูลสำหรับการพล็อตจุดกราฟ")

# 7. ส่วนแสดงและดาวน์โหลดตารางข้อมูลดิบ
st.markdown("---")
st.markdown("### 🗃️ ตารางค้นหาข้อมูลและดาวน์โหลด (Data Explorer)")

search_query = st.text_input("🔍 พิมพ์ชื่อพืชที่ต้องการค้นหา (แบบหน้าร้าน Real-time):")
if search_query and 'plant_name' in filtered_df.columns:
    display_df = filtered_df[filtered_df['plant_name'].str.contains(search_query, na=False)]
else:
    display_df = filtered_df

available_cols = ['plant_id', 'plant_name', 'account_type_desc', 'avg_cost_total', 'avg_revenue_per_year', 'avg_wta', 'avg_proposed_price']
cols_to_show = [c for c in available_cols if c in display_df.columns]

st.dataframe(display_df[cols_to_show], use_container_width=True)

# ปุ่มดาวน์โหลด
csv = display_df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label=f"📥 ดาวน์โหลดข้อมูลที่เลือกทั้งหมด ({len(display_df)} รายการ) เป็นไฟล์ CSV",
    data=csv,
    file_name='filtered_erc_data_2568.csv',
    mime='text/csv',
)
