import streamlit as st
import google.generativeai as genai
import pypdf
from docx import Document
from PIL import Image
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="JobMatch Pro", page_icon="💼", layout="wide")

# --- GÜVENLİK VE API KURULUMU ---
try:
    # Secrets'tan anahtarı al (Adını GOOGLE_API_KEY olarak eşitledik)
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API Anahtarı hatası! Lütfen Streamlit Secrets ayarlarında 'GOOGLE_API_KEY' olduğundan emin olun.")
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
def read_pdf(file):
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def image_to_text(image_file):
    # Görsel okuma için model tanımlama
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(image_file)
    prompt = "Bu bir iş ilanı görselidir. Metni, başlıkları ve gereklilikleri olduğu gibi metne dök."
    
    response = model.generate_content([prompt, img])
    return response.text

def get_full_analysis(cv_text, job_description):
    # Metin analizi için model tanımlama
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f'''
    Sen Kıdemli bir Teknik İşe Alım Yöneticisisin ve aynı zamanda o pozisyonda çalışan bir uzmansın.
    Bugünün tarihi 2025 sonlarıdır. CV'deki 2024-2025 deneyimleri GERÇEKTİR.
    
    GÖREV: Aşağıdaki CV ve İlan için 3 BÖLÜMLÜK detaylı analiz yap.
    Bölümlerin arasına SADECE "|||" işaretini koy.
    
    CV: {cv_text}
    İLAN: {job_description}
    
    --- BÖLÜM 1: UYUMLULUK ANALİZİ ---
    (Markdown kullan)
    ### 🎯 Uyum Skoru
    (100 üzerinden puan ve özet)
    ### ⚙️ Teknik Uyumlar
    (Maddeler halinde, başına ⚙️ koy)
    ### 🧠 Sosyal Yetkinlikler
    (Maddeler halinde, başına ✅ koy)
    ### ❌ Kritik Eksikler
    (Net ve yapıcı dille yaz)

    |||

    --- BÖLÜM 2: İŞ RUTİNİ (ÇALIŞAN SİMÜLASYONU) ---
    (İK dili kullanma. O işi yapan uzman gibi konuş.)
    ### 🔄 Günlük Operasyonel Rutin
    (Teknik görevler - 3 madde)
    ### 📅 Haftalık Kritik Döngüler
    (Sprint, raporlama vb. - 2 madde)
    ### 💡 Kariyer Koçu Soruları
    (Adayın kendine sorması gereken 3 zorlayıcı soru)

    |||

    --- BÖLÜM 3: ÖN YAZI ---
    (Aday gözüyle. Kısa, samimi, değer odaklı. Max 150 kelime.)
    '''
    
    response = model.generate_content(prompt)
    return response.text

# --- SIDEBAR (YAN MENÜ) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3067/3067260.png", width=60)
    st.title("JobMatch Pro")
    st.caption("Developed by Mehmet Onur Pirencioğlu")
    st.markdown("---")
    st.info("💡 **Nasıl Kullanılır?**\n1. CV'nizi yükleyin.\n2. İlanı (Metin veya Resim) girin.\n3. Arkanıza yaslanın.")
    st.markdown("---")
    st.markdown("🔒 *Verileriniz işlendikten sonra silinir.*")

# --- ANA EKRAN ---
st.title("🚀 Kariyer Analiz ve Simülasyon Aracı")
st.markdown("Yapay Zeka ile CV'nizi ve hayalinizdeki işi saniyeler içinde analiz edin.")

# --- GİRİŞ ALANLARI ---
col1, col2 = st.columns(2)

# SOL: CV
with col1:
    st.subheader("1. Aday CV")
    uploaded_file = st.file_uploader("CV Dosyası (PDF / Word)", type=["pdf", "docx"])
    cv_text = ""
    if uploaded_file:
        try:
            if uploaded_file.type == "application/pdf":
                cv_text = read_pdf(uploaded_file)
            else:
                cv_text = read_docx(uploaded_file)
            st.success(f"✅ {uploaded_file.name} Yüklendi")
        except:
            st.error("Dosya okunamadı.")

# SAĞ: İLAN
with col2:
    st.subheader("2. İlan Detayları")
    tab_text, tab_image = st.tabs(["📝 Metin Yapıştır", "📸 Ekran Görüntüsü"])
    job_description = ""
    
    with tab_text:
        val = st.text_area("İlan Metnini Buraya Yapıştırın", height=150)
        if val: job_description = val
    with tab_image:
        img = st.file_uploader("İlan Resmi Yükle", type=["png", "jpg", "jpeg"])
        if img:
            with st.spinner("Resimdeki metin okunuyor..."):
                try:
                    job_description = image_to_text(img)
                    st.success("✅ Resim başarıyla okundu")
                except Exception as e:
                    st.error("Resim okunamadı.")

# BUTON VE İŞLEM
analyze_btn = st.button("✨ Analizi Başlat", type="primary", use_container_width=True)

if analyze_btn:
    if not cv_text or not job_description:
        st.warning("⚠️ Lütfen hem CV yükleyin hem de İlan girişi yapın.")
    else:
        with st.spinner("Yapay Zeka (Gemini) sizin için çalışıyor..."):
            try:
                full_response = get_full_analysis(cv_text, job_description)
                
                parts = full_response.split("|||")
                p1 = parts[0] if len(parts) > 0 else "Analiz oluşturulamadı."
                p2 = parts[1] if len(parts) > 1 else "Rutin verisi alınamadı."
                p3 = parts[2] if len(parts) > 2 else "Ön yazı oluşturulamadı."

                t1, t2, t3 = st.tabs(["📊 Uyumluluk Raporu", "📅 İş Rutini Simülasyonu", "✍️ Akıllı Ön Yazı"])
                
                with t1: st.markdown(p1)
                with t2: st.markdown(p2)
                with t3: st.markdown(p3)

            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
                st.info("Lütfen biraz bekleyip tekrar deneyin.")
