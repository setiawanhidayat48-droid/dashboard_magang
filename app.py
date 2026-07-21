import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Dashboard Pekerjaan Magang", page_icon="📊", layout="wide")
st.title("📊 Dashboard Laporan Pekerjaan (BOQ)")
st.markdown("---")

# 2. Memuat Data Excel
# Tambahkan ttl=60 agar dashboard mengecek data baru ke Google Sheets setiap 60 detik
@st.cache_data(ttl=60) 
def load_data():
    sheet_id = "1UIWChBdk8Ny-QXBHnWccHFdkDP5P0Ss_jIeu9H_0CK0" 
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Membaca data langsung dari internet
    df = pd.read_csv(url)
    
    # --- SISTEM PEMBERSIH DATA (AUTO-CLEANING) ---
    # 1. Ubah paksa jadi teks, lalu hapus semua karakter selain angka (seperti titik, koma, spasi, atau huruf Rp)
    df["Nilai BOQ"] = df["Nilai BOQ"].astype(str).str.replace(r'\D', '', regex=True)
    # 2. Kembalikan tipe datanya menjadi angka murni (numeric)
    df["Nilai BOQ"] = pd.to_numeric(df["Nilai BOQ"], errors='coerce')
    
    # Buang baris yang Nilai BOQ-nya kosong
    df = df.dropna(subset=['Nilai BOQ'])
    return df

df = load_data()

# 3. Sidebar Filter
st.sidebar.header("Filter Data")
departemen = st.sidebar.multiselect("Pilih Departemen:", options=df["Departemen"].dropna().unique(), default=df["Departemen"].dropna().unique())
mitra = st.sidebar.multiselect("Pilih Mitra:", options=df["Mitra"].dropna().unique(), default=df["Mitra"].dropna().unique())

df_selection = df.query("Departemen == @departemen & Mitra == @mitra")

if df_selection.empty:
    st.warning("⚠️ Data tidak tersedia berdasarkan filter yang dipilih!")
    st.stop()

# 4. Membuat Sistem Tab (Menu Navigasi)
tab1, tab2 = st.tabs(["📋 Executive Summary", "🔍 Detail & Analisis Lanjutan"])

# --- ISI TAB 1: SUMMARY ---
with tab1:
    st.subheader("Ringkasan Eksekutif")
    
    # Kalkulasi Metrik
    total_boq = int(df_selection["Nilai BOQ"].sum())
    total_project = len(df_selection)
    po_released = len(df_selection[df_selection["PO"] == "Relaesed"])
    done_projects = len(df_selection[df_selection["Status Kerjaan"] == "Done"])

    # Menampilkan 4 Kolom Angka Ringkasan
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nilai BOQ", f"Rp {total_boq:,}")
    col2.metric("Total Proyek", total_project)
    col3.metric("PO Released", po_released)
    col4.metric("Proyek Selesai (Done)", done_projects)
    st.markdown("---")
    
    # Grafik Ringkasan
    kiri, kanan = st.columns(2)
    with kiri:
        boq_by_dept = df_selection.groupby("Departemen")["Nilai BOQ"].sum().reset_index()
        fig_dept = px.bar(boq_by_dept, x="Departemen", y="Nilai BOQ", title="Total Nilai BOQ per Departemen", color="Departemen", template="plotly_white")
        st.plotly_chart(fig_dept, use_container_width=True)
    with kanan:
        status_counts = df_selection["Status Kerjaan"].value_counts().reset_index()
        status_counts.columns = ['Status Kerjaan', 'Jumlah']
        fig_status = px.pie(status_counts, names="Status Kerjaan", values="Jumlah", title="Distribusi Status Pekerjaan", hole=0.4)
        st.plotly_chart(fig_status, use_container_width=True)

# --- ISI TAB 2: DETAIL ---
with tab2:
    st.subheader("Analisis Mitra & Kategori")
    
    # Grafik Detail Tambahan
    kiri2, kanan2 = st.columns(2)
    with kiri2:
        boq_by_mitra = df_selection.groupby("Mitra")["Nilai BOQ"].sum().reset_index()
        fig_mitra = px.bar(boq_by_mitra, x="Mitra", y="Nilai BOQ", title="Nilai BOQ berdasarkan Mitra", color="Mitra", template="plotly_white")
        st.plotly_chart(fig_mitra, use_container_width=True)
    with kanan2:
        kategori_counts = df_selection["Kategory"].value_counts().reset_index()
        kategori_counts.columns = ['Kategori', 'Jumlah']
        fig_kategori = px.bar(kategori_counts, x="Kategori", y="Jumlah", title="Jumlah Proyek per Kategori", template="plotly_white")
        st.plotly_chart(fig_kategori, use_container_width=True)

    st.markdown("---")
    
    # --- GRAFIK BARU: SITE ID vs NILAI BOQ ---
    st.subheader("Analisis Detail per Site ID")
    
    # Menghapus baris yang tidak memiliki Site ID agar grafik bersih
    df_site = df_selection.dropna(subset=["Site ID"])
    
    # Melakukan agregasi (SUM) Nilai BOQ berdasarkan Site ID
    boq_by_site = df_site.groupby("Site ID")["Nilai BOQ"].sum().reset_index()
    
    # Mengurutkan dari nilai terbesar ke terkecil agar grafik lebih mudah dibaca
    boq_by_site = boq_by_site.sort_values(by="Nilai BOQ", ascending=False)
    
    fig_site = px.bar(
        boq_by_site, 
        x="Site ID", 
        y="Nilai BOQ", 
        title="Total Nilai BOQ berdasarkan Site ID", 
        template="plotly_white",
        text_auto='.2s' # Menambahkan angka singkatan otomatis di atas batang grafik (misal: 25M)
    )
    # Menyesuaikan kemiringan teks sumbu X agar nama Site ID tidak bertabrakan
    fig_site.update_layout(xaxis_tickangle=-45)
    
    st.plotly_chart(fig_site, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Tabel Data Lengkap")
    # Tabel interaktif penuh
    st.dataframe(df_selection, use_container_width=True)