import streamlit as st
import pandas as pd
import os

# ======================
# ตั้งค่าหน้าเว็บ
# ======================

st.set_page_config(
    page_title="ERC 2568 Plant Database",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# โหลดข้อมูล
# ======================

@st.cache_data
def load_data():

    file_path = "ฐานข้อมูลต้นทุนและผลตอบแทน_ERC_2568.csv"

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ไม่พบไฟล์ข้อมูล: {file_path}")

    df = pd.read_csv(file_path, encoding="utf-8")

    numeric_cols = [
        "avg_cost_total",
        "avg_revenue_per_year",
        "avg_wta",
        "avg_proposed_price",
        "profit_est"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    if "account_type" in df.columns:
        df["account_type_desc"] = df["account_type"].map({
            "A": "บัญชี ก. (ต้นไม้ทั่วไป)",
            "B": "บัญชี ข. (พืชล้มลุกและพืชเกษตร)"
        })

    if (
        "profit_est" not in df.columns
        or df["profit_est"].isnull().all()
    ):
        df["profit_est"] = (
            df["avg_revenue_per_year"].fillna(0)
            - df["avg_cost_total"].fillna(0)
        )

    return df


try:
    df = load_data()

except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    st.stop()

# ======================
# Sidebar
# ======================

st.sidebar.header("🔍 ตัวกรองข้อมูล")

# ประเภทบัญชี

account_types = sorted(
    df["account_type_desc"].dropna().unique().tolist()
)

selected_accounts = st.sidebar.multiselect(
    "ประเภทบัญชี",
    options=account_types,
    default=account_types
)

# ภูมิภาค

region_options = ["CN", "N", "NE", "S"]

selected_regions = st.sidebar.multiselect(
    "ภูมิภาค",
    options=region_options,
    default=[]
)

# Active / Inactive

active_options = st.sidebar.multiselect(
    "สถานะข้อมูล",
    options=[1, 0],
    default=[1, 0],
    format_func=lambda x:
        "ใช้งานอยู่" if x == 1 else "ยกเลิกใช้งาน"
)

# Estimated

show_estimated = st.sidebar.checkbox(
    "รวมข้อมูลประมาณการ (estimated)",
    value=True
)

# ======================
# Filter
# ======================

filtered_df = df.copy()

# ประเภทบัญชี

filtered_df = filtered_df[
    filtered_df["account_type_desc"].isin(
        selected_accounts
    )
]

# Active

filtered_df = filtered_df[
    filtered_df["is_active"].isin(
        active_options
    )
]

# Estimated

if not show_estimated:
    filtered_df = filtered_df[
        filtered_df["regions"] != "estimated"
    ]

# Region

if selected_regions:

    filtered_df = filtered_df[
        filtered_df["regions"].fillna("").apply(
            lambda x: any(
                region in str(x).split(",")
                for region in selected_regions
            )
        )
    ]

# ======================
# Header
# ======================

st.title("🌱 ระบบสืบค้นข้อมูลต้นทุนและผลตอบแทนพืช (ERC 2568)")

st.success(
    f"พบข้อมูลจำนวน {len(filtered_df):,} รายการ"
)

# ======================
# Search
# ======================

search_query = st.text_input(
    "🔍 ค้นหาชื่อพืช",
    placeholder="เช่น มะม่วง ยางพารา ปาล์มน้ำมัน"
)

if search_query:

    display_df = filtered_df[
        filtered_df["plant_name"].str.contains(
            search_query,
            case=False,
            na=False
        )
    ]

else:

    display_df = filtered_df

# ======================
# Data Table
# ======================

st.markdown("### 🗃️ ฐานข้อมูลพืช")

available_cols = [
    "plant_id",
    "plant_name",
    "account_type_desc",
    "regions",
    "is_active",
    "avg_cost_total",
    "avg_revenue_per_year",
    "avg_wta",
    "avg_proposed_price"
]

cols_to_show = [
    c
    for c in available_cols
    if c in display_df.columns
]

st.dataframe(
    display_df[cols_to_show].reset_index(drop=True),
    use_container_width=True,
    hide_index=True
)

# ======================
# Download
# ======================

csv = display_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label=f"📥 ดาวน์โหลดข้อมูล ({len(display_df):,} รายการ)",
    data=csv,
    file_name="erc_plant_database.csv",
    mime="text/csv"
)
