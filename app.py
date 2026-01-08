import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# --- AYARLAR ---
st.set_page_config(page_title="Çoklu Sınav Sistemi", layout="wide", page_icon="📚")

# --- KLASÖR AYARLARI ---
ANAHTAR_KLASORU = "cevap_anahtarlari"
if not os.path.exists(ANAHTAR_KLASORU):
    os.makedirs(ANAHTAR_KLASORU)


# --- YARDIMCI FONKSİYONLAR ---
def tr_karakter_duzelt(metin):
    kaynak = "şŞıİğĞüÜöÖçÇ"
    hedef = "sSiIgGuUoOcC"
    ceviri_tablosu = str.maketrans(kaynak, hedef)
    return str(metin).translate(ceviri_tablosu)


def pdf_olustur(ogrenci_adi, sinav_adi, dogru, yanlis, bos, net, df_detay):
    pdf = FPDF()
    pdf.add_page()

    # Başlık
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, tr_karakter_duzelt("SINAV SONUC BELGESI"), ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, tr_karakter_duzelt(f"Sinav: {sinav_adi}"), ln=True, align='C')
    pdf.ln(5)

    # Öğrenci Bilgisi
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, tr_karakter_duzelt(f"Ogrenci Adi: {ogrenci_adi}"), ln=True)
    pdf.cell(0, 10, f"Tarih: {pd.Timestamp.now().strftime('%d-%m-%Y')}", ln=True)
    pdf.ln(5)

    # Puan Tablosu
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Dogru", 1)
    pdf.cell(40, 10, "Yanlis", 1)
    pdf.cell(40, 10, "Bos", 1)
    pdf.cell(40, 10, "NET", 1)
    pdf.ln()

    pdf.set_font("Arial", size=12)
    pdf.cell(40, 10, str(dogru), 1)
    pdf.cell(40, 10, str(yanlis), 1)
    pdf.cell(40, 10, str(bos), 1)
    pdf.cell(40, 10, f"{net:.2f}", 1)
    pdf.ln(15)

    # Detaylar
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, tr_karakter_duzelt("Soru Detaylari"), ln=True)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(20, 8, "Soru", 1)
    pdf.cell(30, 8, "Cevabiniz", 1)
    pdf.cell(30, 8, "Dogru Cvp", 1)
    pdf.cell(40, 8, "Durum", 1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for index, row in df_detay.iterrows():
        pdf.cell(20, 8, str(row['Soru']), 1)
        pdf.cell(30, 8, str(row['Verilen']), 1)
        pdf.cell(30, 8, str(row['Gerçek']), 1)
        pdf.cell(40, 8, tr_karakter_duzelt(row['Durum']), 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')


# --- UYGULAMA BAŞLANGICI ---
st.title("📚 Online Deneme Sınavı Merkezi")
st.markdown("---")

# Session State
if 'sonuc_hesaplandi' not in st.session_state:
    st.session_state.sonuc_hesaplandi = False
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# --- SOL MENÜ (AYARLAR) ---
st.sidebar.header("Sınav Ayarları ⚙️")

# 1. Dosya Seçimi
dosyalar = [f for f in os.listdir(ANAHTAR_KLASORU) if f.endswith('.xlsx')]
secilen_sinav = None
cevap_anahtari_string = ""

# 2. Seviye Seçimi (YENİ EKLENEN KISIM)
st.sidebar.subheader("Sınav Seviyesi")
seviye = st.sidebar.radio(
    "Öğrenci Grubu Seçiniz:",
    ["Lise", "Ortaokul"]
)

# Seviyeye göre ayarları yap
if "Lise" in seviye:
    secenekler = ["-", "A", "B", "C", "D", "E"]
    yanlis_goturme_orani = 4.0
else:
    secenekler = ["-", "A", "B", "C", "D"]
    yanlis_goturme_orani = 3.0

if not dosyalar:
    st.sidebar.error("⚠️ Klasörde sınav dosyası bulunamadı!")
else:
    secilen_dosya_adi = st.sidebar.selectbox("Sınav Seçiniz:", dosyalar)

    if secilen_dosya_adi:
        tam_dosya_yolu = os.path.join(ANAHTAR_KLASORU, secilen_dosya_adi)
        try:
            df_anahtar = pd.read_excel(tam_dosya_yolu)
            if 'Cevap' in df_anahtar.columns:
                cevap_anahtari_string = "".join(df_anahtar['Cevap'].astype(str).tolist()).upper()
                secilen_sinav = secilen_dosya_adi.replace(".xlsx", "")

                # Bilgi kutusu
                st.sidebar.success(f"✅ Sınav Yüklendi")
                st.sidebar.info(f"""
                **Seçilen:** {secilen_sinav}
                
                **Soru Sayısı:** {len(cevap_anahtari_string)}
                
                """)
            else:
                st.sidebar.error("Excel'de 'Cevap' sütunu yok!")
        except Exception as e:
            st.sidebar.error(f"Hata: {e}")

# --- ÖĞRENCİ EKRANI ---
if cevap_anahtari_string and secilen_sinav:
    st.info(f"Şu an **{secilen_sinav}** sınavını çözmektesiniz. Başarılar!")

    with st.form("sinav_formu"):
        st.write("### 👤 Öğrenci Bilgileri")
        ogrenci_adi_input = st.text_input("Adınız Soyadınız", placeholder="Örn: Ahmet Yılmaz")

        st.write("---")
        st.write("### ✍️ Cevap Kağıdı (Optik Form)")

        # Optik Form Düzeni
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]

        verilen_cevaplar_listesi = []
        soru_sayisi = len(cevap_anahtari_string)
        soru_per_col = (soru_sayisi // 3) + 1

        for i in range(soru_sayisi):
            current_col = cols[i // soru_per_col] if i // soru_per_col < 3 else cols[2]
            with current_col:
                # DİNAMİK SEÇENEKLER (Burada ayara göre 4 veya 5 şık geliyor)
                secilen = st.radio(
                    f"**{i + 1}. Soru**",
                    options=secenekler,
                    horizontal=True,
                    key=f"{secilen_sinav}_{seviye}_soru_{i}",
                    index=0
                )
                verilen_cevaplar_listesi.append(secilen)

        st.write("---")
        submitted = st.form_submit_button("Sınavı Bitir ve Sonuçları Gör", type="primary", use_container_width=True)

    # --- HESAPLAMA ---
    if submitted:
        if not ogrenci_adi_input:
            st.error("⚠️ Lütfen adınızı giriniz.")
        else:
            dogru, yanlis, bos = 0, 0, 0
            detaylar = []

            for i in range(len(cevap_anahtari_string)):
                o_c = verilen_cevaplar_listesi[i]
                g_c = cevap_anahtari_string[i]

                if o_c == "-":
                    bos += 1
                    durum = "Boş"
                elif o_c == g_c:
                    dogru += 1
                    durum = "Doğru"
                else:
                    yanlis += 1
                    durum = "Yanlış"

                detaylar.append({"Soru": i + 1, "Verilen": o_c, "Gerçek": g_c, "Durum": durum})

            # DİNAMİK NET HESABI (3 veya 4 yanlış götürme)
            net = dogru - (yanlis / yanlis_goturme_orani)

            df_sonuc = pd.DataFrame(detaylar)

            st.session_state.sonuc_hesaplandi = True
            st.session_state.ogrenci_adi = ogrenci_adi_input
            st.session_state.sinav_adi = secilen_sinav
            st.session_state.dogru = dogru
            st.session_state.yanlis = yanlis
            st.session_state.bos = bos
            st.session_state.net = net
            st.session_state.df_sonuc = df_sonuc

            pdf_bytes = pdf_olustur(ogrenci_adi_input, secilen_sinav, dogru, yanlis, bos, net, df_sonuc)
            st.session_state.pdf_data = pdf_bytes

    # --- SONUÇ EKRANI ---
    if st.session_state.sonuc_hesaplandi:
        st.write("---")
        st.balloons()
        st.success(f"Tebrikler {st.session_state.ogrenci_adi}, {st.session_state.sinav_adi} Tamamlandı!")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Doğru", st.session_state.dogru)
        c2.metric("Yanlış", st.session_state.yanlis)
        c3.metric("Boş", st.session_state.bos)
        c4.metric("NET", f"{st.session_state.net:.2f}")


        def renk(row):
            if row.Durum == "Yanlış": return ['background-color: #ffcccc'] * len(row)
            if row.Durum == "Doğru": return ['background-color: #ccffcc'] * len(row)
            return [''] * len(row)


        st.dataframe(st.session_state.df_sonuc.style.apply(renk, axis=1), use_container_width=True)

        st.write("### 📄 Sonuç Belgesi")
        st.download_button(
            label="Sonuçları PDF Olarak İndir",
            data=st.session_state.pdf_data,
            file_name=f"{st.session_state.ogrenci_adi}_sonuc.pdf",
            mime="application/pdf",
            type="primary"
        )

        if st.button("Yeni Sınav / Temizle"):
            st.session_state.sonuc_hesaplandi = False
            st.rerun()

elif not dosyalar:
    st.warning("👈 Cevap anahtarı klasörü boş.")
else:
    st.info("👈 Lütfen sol menüden sınav seçimi yapınız.")