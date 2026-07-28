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
    
    # Tambahan: Mengatasi sel kosong di kolom Quarter (Q)
    if "Q" in df.columns:
        df["Q"] = df["Q"].fillna("Belum Ditentukan")
        
    return df

df = load_data()

# 3. Sidebar Filter Utama (Mengubah seluruh halaman)
st.sidebar.header("Filter Global")

# --- TAMBAHAN BARU: FILTER QUARTER (Q) ---
if "Q" in df.columns:
    quarter = st.sidebar.multiselect("Pilih Quarter (Q):", options=df["Q"].unique(), default=df["Q"].unique())
else:
    quarter = []

departemen = st.sidebar.multiselect("Pilih Departemen:", options=df["Departemen"].unique(), default=df["Departemen"].unique())
mitra = st.sidebar.multiselect("Pilih Mitra:", options=df["Mitra"].unique(), default=df["Mitra"].unique())

# --- UPDATE LOGIKA FILTER ---
if "Q" in df.columns:
    df_selection = df.query("Q == @quarter & Departemen == @departemen & Mitra == @mitra")
else:
    df_selection = df.query("Departemen == @departemen & Mitra == @mitra")

if df_selection.empty:
    st.warning("⚠️ Data tidak tersedia berdasarkan filter yang dipilih!")
    st.stop()

# 4. Membuat Sistem Tab
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
    
    # Menambahkan gap="large" agar ada spasi pemisah di antara kedua kolom
    kiri, kanan = st.columns(2, gap="large")
    
    with kiri:
        boq_by_dept = df_selection.groupby("Departemen")["Nilai BOQ"].sum().reset_index()
        fig_dept = px.bar(boq_by_dept, x="Departemen", y="Nilai BOQ", title="Total Nilai BOQ per Departemen", color="Departemen")
        
        # 1. Menghilangkan legend yang memakan tempat agar grafik lebih lebar
        fig_dept.update_layout(showlegend=False)
        
        klik_grafik = st.plotly_chart(fig_dept, use_container_width=True, on_select="rerun")
        
    with kanan:
        status_counts = df_selection["Status Kerjaan"].value_counts().reset_index()
        status_counts.columns = ['Status Kerjaan', 'Jumlah']
        
        # 1. PERUBAHAN: Menukar X dan Y, lalu menghapus orientation='h'
        fig_status = px.bar(status_counts, x="Status Kerjaan", y="Jumlah", 
                            title="Distribusi Status Pekerjaan", color="Status Kerjaan")
        
        fig_status.update_layout(showlegend=False)
        klik_status = st.plotly_chart(fig_status, use_container_width=True, on_select="rerun")

    # --- LOGIKA INTERAKTIF (MUNCUL DI BAWAH GRAFIK) ---
    
    # 1. Jika Bar Chart (Departemen) diklik (TIDAK BERUBAH)
    if "selection" in klik_grafik and len(klik_grafik["selection"]["points"]) > 0:
        dept_terpilih = klik_grafik["selection"]["points"][0]["x"]
        
        st.markdown("---")
        st.markdown(f"### 🎯 Detail Area: **{dept_terpilih}**")
        
        df_klik = df_selection[df_selection["Departemen"] == dept_terpilih]
        kolom_penting = ["Q", "Site ID", "Mitra", "Deskripsi pekerjaan", "Status Kerjaan", "Invoice", "Nilai BOQ"]
        kolom_tersedia = [col for col in kolom_penting if col in df_klik.columns]
        st.dataframe(df_klik[kolom_tersedia], use_container_width=True, hide_index=True)

    # 2. Jika Bar Chart (Status Kerjaan) diklik
    if "selection" in klik_status and len(klik_status["selection"]["points"]) > 0:
        # 2. PERUBAHAN: Karena grafik sudah vertikal, kita menangkap klik dari sumbu "x"
        status_terpilih = klik_status["selection"]["points"][0]["x"]
        
        st.markdown("---")
        st.markdown(f"### 📋 Daftar Pekerjaan dengan Status: **{status_terpilih}**")
        st.markdown(f"Berikut adalah rincian departemen dan proyek yang saat ini berstatus **{status_terpilih}**:")
        
        df_status = df_selection[df_selection["Status Kerjaan"] == status_terpilih]
        
        kolom_status = ["Departemen", "Q", "Site ID", "Mitra", "Deskripsi pekerjaan", "Invoice", "Nilai BOQ"]
        kolom_tersedia_status = [col for col in kolom_status if col in df_status.columns]
        
        st.dataframe(df_status[kolom_tersedia_status], use_container_width=True, hide_index=True)

# --- ISI TAB 2: DETAIL ---
with tab2:
    st.subheader("Analisis Mitra & Kategori")
    
    # 1. DUA GRAFIK DI BAGIAN ATAS (TETAP DIPERTAHANKAN)
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

    # 2. GRAFIK SITE ID DI BAGIAN BAWAH (SEKARANG INTERAKTIF)
    st.markdown("---")
    st.subheader("Analisis Detail per Site ID")
    df_site = df_selection.dropna(subset=["Site ID"])
    
    if not df_site.empty:
        boq_by_site = df_site.groupby("Site ID")["Nilai BOQ"].sum().reset_index().sort_values(by="Nilai BOQ", ascending=False)
        fig_site = px.bar(boq_by_site, x="Site ID", y="Nilai BOQ", title="Total Nilai BOQ berdasarkan Site ID", text_auto='.2s')
        fig_site.update_layout(xaxis_tickangle=-45)
        
        # Grafik penangkap klik
        klik_site = st.plotly_chart(fig_site, use_container_width=True, on_select="rerun")
        
        # Logika memunculkan tabel detail di bawah grafik Site ID
        if "selection" in klik_site and len(klik_site["selection"]["points"]) > 0:
            site_terpilih = klik_site["selection"]["points"][0]["x"]
            
            st.markdown("---")
            st.markdown(f"### 📍 Rincian Proyek untuk Site ID: **{site_terpilih}**")
            
            # Memfilter data hanya untuk Site ID yang dipilih
            df_site_klik = df_selection[df_selection["Site ID"] == site_terpilih]
            
            # Menyusun kolom tabel agar informatif
            kolom_site = ["Q", "Departemen", "Mitra", "Deskripsi pekerjaan", "Status Kerjaan", "Invoice", "Nilai BOQ"]
            kolom_tersedia_site = [col for col in kolom_site if col in df_site_klik.columns]
            
            st.dataframe(df_site_klik[kolom_tersedia_site], use_container_width=True, hide_index=True)

# --- ISI TAB 3: PROFIL DEPARTEMEN (FITUR SEARCH) ---
with tab3:
    st.subheader("🔍 Pencarian Spesifik Departemen")
    st.markdown("Ketik nama departemen pada kotak di bawah ini untuk membedah detail informasinya.")
    
    list_departemen = df_selection["Departemen"].dropna().unique().tolist()
    pilih_dept = st.selectbox("Cari Departemen:", options=["-- Ketik / Pilih Departemen --"] + list_departemen)
    
    if pilih_dept != "-- Ketik / Pilih Departemen --":
        st.markdown(f"### 🏢 Detail Area: **{pilih_dept}**")
        
        df_khusus = df_selection[df_selection["Departemen"] == pilih_dept]
        
        c1, c2, c3 = st.columns(3)
        c1.metric(label="Total Proyek di Area Ini", value=len(df_khusus))
        c2.metric(label="Total Serapan BOQ", value=f"Rp {int(df_khusus['Nilai BOQ'].sum()):,}")
        
        mitra_terbanyak = df_khusus['Mitra'].mode()[0] if not df_khusus['Mitra'].empty else "-"
        c3.metric(label="Mitra Paling Dominan", value=mitra_terbanyak)
        
        st.markdown("#### 📑 Daftar Proyek Berjalan")
        # Menambahkan kolom Invoice ke dalam tabel
        kolom_penting = ["Q", "Site ID", "Mitra", "Deskripsi pekerjaan", "Status Kerjaan", "Invoice", "Nilai BOQ"]
        kolom_tersedia = [col for col in kolom_penting if col in df_khusus.columns]
        
        st.dataframe(df_khusus[kolom_tersedia], use_container_width=True, hide_index=True)