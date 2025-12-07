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
    # Secrets'tan anahtarı al
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API Anahtarı bulunamadı! Lütfen Streamlit Cloud üzerinden 'Settings > Secrets' ayarlarını yapın.")
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
    # MODEL DEĞİŞİKLİĞİ: Flash yerine Pro modelini kullanıyoruz (Daha kararlı)
    model = genai.GenerativeModel('gemini-1.5-pro')
    img = Image.open(image_file)
    prompt = "Bu bir iş ilanı görselidir. Metni, başlıkları ve gereklilikleri olduğu gibi metne dök."
    
    # Multimodal input
    try:
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        return f"Hata: {e}"

def get_full_analysis(cv_text, job_description):
    # MODEL DEĞİŞİKLİĞİ: Flash yerine Pro modelini kullanıyoruz
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f'''
    Sen Kıdemli bir Teknik İşe Alım Yöneticisisin.
    
    GÖREV: Aşağıdaki CV ve İlan için 3 BÖLÜMLÜK detaylı analiz yap.
    Bölümlerin arasına SADECE "|||" işaretini koy.
    
    CV: {cv_text}
    İLAN: {job_description}
    
    --- BÖLÜM 1: UYUMLULUK ANALİZİ ---
    (Markdown kullan)
    ### 🎯 Uyum Skoru
    (100 üzerinden puan ve özet)
    ### ⚙️ Teknik Uyumlar
    (Maddeler halinde)
    ### 🧠 Sosyal Yetkinlikler
    (Maddeler halinde)
    ### ❌ Kritik Eksikler
    (Net ve yapıcı dille yaz)

    |||

    --- BÖLÜM 2: İŞ RUTİNİ SİMÜLASYONU ---
    (O işi yapan uzman gibi konuş.)
    ### 🔄 Günlük Operasyonel Rutin
    (3 madde)
    ### 📅 Haftalık Kritik Döngüler
    (2 madde)
    ### 💡 Mülakat Soruları
    (Adayın kendine sorması gereken 3 soru)

    |||

    --- BÖLÜM 3: ÖN YAZI ---
    (Kısa, samimi, değer odaklı. Max 150 kelime.)
    '''
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Bir hata oluştu: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("JobMatch Pro")
    st.info("💡 **Nasıl Kullanılır?**\n1. CV'nizi yükleyin.\n2. İlanı girin.\n3. Analizi Başlatın.")
    st.markdown("---")
    st.caption("Model: Gemini 1.5 Pro")

# --- ANA EKRAN ---
st.title("🚀 Kariyer Analiz Aracı")
st.markdown("Yapay Zeka (Gemini 1.5 Pro) ile CV analizi.")

col1, col2 = st.columns(2)

# SOL: CV
with col1:
    st.subheader("1. Aday CV")
    uploaded_file = st.file_uploader("CV Yükle", type=["pdf", "docx"])
    cv_text = ""
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            cv_text = read_pdf(uploaded_file)
        else:
            cv_text = read_docx(uploaded_file)
        st.success(f"✅ {uploaded_file.name} Yüklendi")

# SAĞ: İLAN
with col2:
    st.subheader("2. İlan Detayları")
    tab_text, tab_image = st.tabs(["📝 Metin", "📸 Resim"])
    job_description = ""
    
    with tab_text:
        val = st.text_area("İlan Metni", height=150)
        if val: job_description = val
    with tab_image:
        img = st.file_uploader("İlan Resmi", type=["png", "jpg", "jpeg"])
        if img:
            with st.spinner("Resim okunuyor..."):
                job_description = image_to_text(img)
                if "Hata" not in job_description:
                    st.success("✅ Resim okundu")
                else:
                    st.error("Resim okunamadı.")

# BUTON
if st.button("✨ Analizi Başlat", type="primary", use_container_width=True):
    if not cv_text or not job_description:
        st.warning("⚠️ Lütfen CV ve İlan girin.")
    else:
        with st.spinner("Gemini 1.5 Pro analiz ediyor... (Bu işlem 10-15 saniye sürebilir)"):
            full_response = get_full_analysis(cv_text, job_description)
            
            if "Bir hata oluştu" in full_response:
                st.error(full_response)
            else:
                parts = full_response.split("|||")
                # Hata toleransı: Eğer AI bölmeyi unutursa hepsini ilk tab'a bas
                if len(parts) < 3:
                    st.markdown(full_response)
                else:
                    t1, t2, t3 = st.tabs(["📊 Analiz", "📅 Rutin", "✍️ Ön Yazı"])
                    with t1: st.markdown(parts[0])
                    with t2: st.markdown(parts[1])
                    with t3: st.markdown(parts[2])
