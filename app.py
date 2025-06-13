import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# --- Konfigurasi ---
st.set_page_config(page_title="Amazon Top Bestselling Books", layout="wide")
def set_background_color():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f5e6ca;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_color()
# --- Autentikasi Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

if os.path.exists("creds.json"):
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
else:
    creds_dict = json.loads(st.secrets["creds_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
sheet = client.open("bestselling books").worksheet("Books")
try:
    with st.spinner("🔄 Mengambil data dari Google Sheets..."):
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
    st.success("✅ Data berhasil diambil.")
except Exception as e:
    st.error(f"❌ Gagal ambil data: {e}")
    st.stop()

# --- Sidebar filter ---
st.sidebar.header("🎯 Filter Buku")
year = st.sidebar.selectbox("Pilih Tahun", sorted(df["year"].unique(), reverse=True))
genre = st.sidebar.multiselect("Pilih Genre", options=df["genre"].unique(), default=list(df["genre"].unique()))
rating_min = st.sidebar.slider("Rating Minimum", 0.0, 5.0, 3.5, step=0.1)

df_filtered = df[(df["year"] == year) & 
                 (df["genre"].isin(genre)) & 
                 (df["user_rating"] >= rating_min)]

# --- Header ---
st.title("📚 Amazon Top Bestselling Books Dashboard")
st.markdown("Menampilkan data buku terlaris Amazon tahun 2009–2019 dengan visualisasi interaktif dan kemampuan edit data langsung.")

# --- Data Table ---
st.subheader("📋 Data Buku yang Difilter")
st.dataframe(df_filtered, use_container_width=True)

# --- VISUAL 1: Top Rating Books ---
st.subheader("⭐ Top 10 Buku Berdasarkan Rating")
top_books = df_filtered.sort_values("user_rating", ascending=False).head(10)
fig1 = px.bar(top_books, x="name", y="user_rating", color="author", title="Top 10 Buku Rating Tertinggi")
st.plotly_chart(fig1, use_container_width=True)

# --- VISUAL 2: Histogram Harga ---
st.subheader("💰 Distribusi Harga Buku")
fig2 = px.histogram(df, x="price", nbins=30, color="genre", title="Distribusi Harga Buku")
st.plotly_chart(fig2, use_container_width=True)

# --- VISUAL 3: Tren Buku per Tahun ---
st.subheader("📈 Jumlah Buku Terbit per Tahun")
trend = df.groupby("year").size().reset_index(name="jumlah_buku")
fig3 = px.line(trend, x="year", y="jumlah_buku", markers=True, title="Tren Buku per Tahun")
st.plotly_chart(fig3, use_container_width=True)

# --- VISUAL 4: Proporsi Genre ---
st.subheader("📊 Proporsi Genre Buku")
genre_count = df["genre"].value_counts().reset_index()
genre_count.columns = ["genre", "count"]
fig4 = px.pie(genre_count, values="count", names="genre", title="Distribusi Genre Buku")
st.plotly_chart(fig4, use_container_width=True)

# --- VISUAL 5: Top Penulis Terbanyak ---
st.subheader("🧑‍💼 Penulis dengan Jumlah Buku Terbanyak")
author_count = df["author"].value_counts().nlargest(10).reset_index()
author_count.columns = ["author", "jumlah_buku"]
fig5 = px.bar(author_count, x="jumlah_buku", y="author", orientation="h", title="Top 10 Penulis")
st.plotly_chart(fig5, use_container_width=True)

# --- VISUAL 6: Rating vs Price ---
st.subheader("🔍 Korelasi Rating dan Harga")
fig6 = px.scatter(df, x="price", y="user_rating", color="genre", hover_data=["name", "author"], title="Rating vs Harga Buku")
st.plotly_chart(fig6, use_container_width=True)

# --- EDIT DATA SECTION ---
st.subheader("✏️ Edit Data Buku")
row = st.number_input("Baris data (1–{})".format(len(df)), min_value=1, max_value=len(df))
new_price = st.number_input("Harga baru", value=float(df.loc[row-1, "price"]))
new_rating = st.slider("Rating baru", 0.0, 5.0, float(df.loc[row-1, "user_rating"]), 0.1)

if st.button("Simpan Perubahan"):
    sheet.update_cell(row + 1, df.columns.get_loc("price") + 1, new_price)
    sheet.update_cell(row + 1, df.columns.get_loc("user_rating") + 1, new_rating)
    st.success("✅ Data berhasil diubah. Refresh halaman untuk lihat hasil.")
