import streamlit as st
import google.generativeai as genai
import pypdf
from docx import Document
from PIL import Image

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="JobMatch Pro", page_icon="💼", layout="wide")

# --- GÜVENLİK VE API KURULUMU ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ API Anahtarı hatası! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
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

def get_gemini_response(input_text, image_data=None, prompt_text=""):
    # EN GÜNCEL VE HIZLI MODEL: gemini-1.5-flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        if image_data:
            response = model.generate_content([prompt_text, input_text, image_data])
        else:
            response = model.generate_content([prompt_text, input_text])
        return response.text
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("JobMatch Pro")
    st.info("Bu uygulama Google Gemini 1.5 Flash modeli ile çalışır.")

# --- ANA EKRAN ---
st.title("🚀 CV ve İlan Analiz Asistanı")

col1, col2 = st.columns(2)

# SOL: CV
with col1:
    st.subheader("1. CV Yükle")
    cv_file = st.file_uploader("PDF veya Word", type=["pdf", "docx"])
    cv_text = ""
    if cv_file:
        if cv_file.type == "application/pdf":
            cv_text = read_pdf(cv_file)
        else:
            cv_text = read_docx(cv_file)
        st.success("CV Alındı ✅")

# SAĞ: İLAN
with col2:
    st.subheader("2. İlan Yükle")
    tab1, tab2 = st.tabs(["Metin", "Resim"])
    job_text = ""
    img_data = None
    
    with tab1:
        job_text = st.text_area("İlan Metni")
    with tab2:
        img_file = st.file_uploader("İlan Resmi", type=["png", "jpg", "jpeg"])
        if img_file:
            img_data = Image.open(img_file)
            st.image(img_file, width=200)

# BUTON
if st.button("Analiz Et", type="primary"):
    if cv_text and (job_text or img_data):
        with st.spinner("Yapay Zeka düşünüyor..."):
            prompt = """
            Sen uzman bir İnsan Kaynakları yöneticisisin. 
            Görev: Verilen CV'yi ve İş İlanını karşılaştır.
            
            Çıktıyı şu başlıklarla ver:
            1. Uyum Skoru (100 üzerinden)
            2. Eksik Yetkinlikler
            3. Aday İçin Tavsiyeler
            4. Kısa Ön Yazı Örneği
            """
            
            # Eğer resim varsa onu gönder, yoksa metni gönder
            content_input = job_text if job_text else "İlan görseldedir."
            final_image = img_data if img_data else None
            
            result = get_gemini_response(cv_text + "\n\n" + content_input, final_image, prompt)
            st.markdown(result)
    else:
        st.warning("Lütfen hem CV yükleyin hem de İlan girin.")
