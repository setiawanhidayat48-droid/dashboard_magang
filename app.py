import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Pekerjaan Magang", page_icon="📊", layout="wide")
st.title("📊 Dashboard Laporan Pekerjaan (BOQ)")
st.markdown("---")

# 2. Memuat Data dari Google Sheets
@st.cache_data(ttl=60) 
def load_data():
    sheet_id = "1UIWChBdk8Ny-QXBHnWccHFdkDP5P0Ss_jIeu9H_0CK0" 
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    df = pd.read_csv(url)
    
    # Auto-Cleaning Nilai BOQ
    df["Nilai BOQ"] = df["Nilai BOQ"].astype(str).str.replace(r'\D', '', regex=True)
    df["Nilai BOQ"] = pd.to_numeric(df["Nilai BOQ"], errors='coerce')
    df = df.dropna(subset=['Nilai BOQ'])
    
    # Mengatasi sel kosong (blank) di Excel
    df["Departemen"] = df["Departemen"].fillna("Belum Ditentukan")
    df["Mitra"] = df["Mitra"].fillna("Belum Ditentukan")
    
    return df

df = load_data()

# 3. Sidebar Filter Utama (Mengubah seluruh halaman)
st.sidebar.header("Filter Global")
departemen = st.sidebar.multiselect("Pilih Departemen:", options=df["Departemen"].unique(), default=df["Departemen"].unique())
mitra = st.sidebar.multiselect("Pilih Mitra:", options=df["Mitra"].unique(), default=df["Mitra"].unique())

df_selection = df.query("Departemen == @departemen & Mitra == @mitra")

if df_selection.empty:
    st.warning("⚠️ Data tidak tersedia berdasarkan filter yang dipilih!")
    st.stop()

# 4. Membuat Sistem Tab (Ditambah Tab ke-3)
tab1, tab2, tab3 = st.tabs(["📋 Executive Summary", "🔍 Detail & Analisis Lanjutan", "🏢 Profil Departemen (Search)"])

# --- ISI TAB 1: SUMMARY ---
with tab1:
    st.subheader("Ringkasan Eksekutif")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nilai BOQ", f"Rp {int(df_selection['Nilai BOQ'].sum()):,}")
    col2.metric("Total Proyek", len(df_selection))
    col3.metric("PO Released", len(df_selection[df_selection["PO"] == "Relaesed"]))
    col4.metric("Proyek Selesai (Done)", len(df_selection[df_selection["Status Kerjaan"] == "Done"]))
    st.markdown("---")
    
    kiri, kanan = st.columns(2)
    with kiri:
        boq_by_dept = df_selection.groupby("Departemen")["Nilai BOQ"].sum().reset_index()
        fig_dept = px.bar(boq_by_dept, x="Departemen", y="Nilai BOQ", title="Total Nilai BOQ per Departemen", color="Departemen")
        st.plotly_chart(fig_dept, use_container_width=True)
    with kanan:
        status_counts = df_selection["Status Kerjaan"].value_counts().reset_index()
        status_counts.columns = ['Status Kerjaan', 'Jumlah']
        fig_status = px.pie(status_counts, names="Status Kerjaan", values="Jumlah", title="Distribusi Status Pekerjaan", hole=0.4)
        st.plotly_chart(fig_status, use_container_width=True)

# --- ISI TAB 2: DETAIL ---
with tab2:
    st.subheader("Analisis Mitra & Kategori")
    kiri2, kanan2 = st.columns(2)
    with kiri2:
        boq_by_mitra = df_selection.groupby("Mitra")["Nilai BOQ"].sum().reset_index()
        fig_mitra = px.bar(boq_by_mitra, x="Mitra", y="Nilai BOQ", title="Nilai BOQ berdasarkan Mitra", color="Mitra")
        st.plotly_chart(fig_mitra, use_container_width=True)
    with kanan2:
        if "Kategory" in df_selection.columns:
            kategori_counts = df_selection["Kategory"].value_counts().reset_index()
            kategori_counts.columns = ['Kategori', 'Jumlah']
            fig_kategori = px.bar(kategori_counts, x="Kategori", y="Jumlah", title="Jumlah Proyek per Kategori")
            st.plotly_chart(fig_kategori, use_container_width=True)

    st.markdown("---")
    st.subheader("Analisis Detail per Site ID")
    df_site = df_selection.dropna(subset=["Site ID"])
    if not df_site.empty:
        boq_by_site = df_site.groupby("Site ID")["Nilai BOQ"].sum().reset_index().sort_values(by="Nilai BOQ", ascending=False)
        fig_site = px.bar(boq_by_site, x="Site ID", y="Nilai BOQ", title="Total Nilai BOQ berdasarkan Site ID", text_auto='.2s')
        fig_site.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_site, use_container_width=True)

# --- ISI TAB 3: PROFIL DEPARTEMEN (FITUR SEARCH) ---
with tab3:
    st.subheader("🔍 Pencarian Spesifik Departemen")
    st.markdown("Ketik nama departemen pada kotak di bawah ini untuk membedah detail informasinya.")
    
    # Membuat daftar nama departemen
    list_departemen = df_selection["Departemen"].dropna().unique().tolist()
    
    # Fitur pencarian otomatis
    pilih_dept = st.selectbox("Cari Departemen:", options=["-- Ketik / Pilih Departemen --"] + list_departemen)
    
    # Jika pengguna sudah memilih sebuah departemen, tampilkan datanya
    if pilih_dept != "-- Ketik / Pilih Departemen --":
        st.markdown(f"### 🏢 Detail Area: **{pilih_dept}**")
        
        # Saring data HANYA untuk departemen yang dicari
        df_khusus = df_selection[df_selection["Departemen"] == pilih_dept]
        
        # Tampilkan metrik khusus departemen tersebut
        c1, c2, c3 = st.columns(3)
        c1.metric(label="Total Proyek di Area Ini", value=len(df_khusus))
        c2.metric(label="Total Serapan BOQ", value=f"Rp {int(df_khusus['Nilai BOQ'].sum()):,}")
        
        # Mencari Mitra yang paling banyak memegang proyek di departemen ini
        mitra_terbanyak = df_khusus['Mitra'].mode()[0] if not df_khusus['Mitra'].empty else "-"
        c3.metric(label="Mitra Paling Dominan", value=mitra_terbanyak)
        
        st.markdown("#### 📑 Daftar Proyek Berjalan")
        
        # Menampilkan tabel bersih khusus departemen ini (menyembunyikan kolom tidak penting)
        kolom_penting = ["Site ID", "Mitra", "Deskripsi pekerjaan", "Status Kerjaan", "Nilai BOQ"]
        kolom_tersedia = [col for col in kolom_penting if col in df_khusus.columns]
        
        st.dataframe(df_khusus[kolom_tersedia], use_container_width=True, hide_index=True)