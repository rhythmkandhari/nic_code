#.\venv\Scripts\activate
import streamlit as st
import pandas as pd
import speech_recognition as sr
import torch
from gpt4all import GPT4All
from sentence_transformers import SentenceTransformer, util
from deep_translator import GoogleTranslator
import cx_Oracle
from datetime import datetime


st.set_page_config(page_title="NIC Code Finder", layout="wide")
st.session_state["user_email"] = "anonymous"


if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
    st.session_state["user_email"] = "anonymous"

@st.cache_resource
def load_gpt4all():
    return GPT4All("Llama-3.2-1B-Instruct-Q4_0.gguf", device="cpu")

@st.cache_resource
def load_sentence_transformer():
    return SentenceTransformer("all-MiniLM-L6-v2").to("cpu")

@st.cache_resource
def load_nic_data(file_path=r"final_k/NIC_5digit.csv"):
    df = pd.read_csv(file_path)
    df["NICcode"] = df["NICcode"].astype(str).str.zfill(5)  # Ensure 5-digit NIC codes
    df["Embeddings"] = semantic_model.encode(df["NIC description"].tolist(), convert_to_tensor=True, dtype=torch.float32).cpu().tolist()
    return df

model = load_gpt4all()
semantic_model = load_sentence_transformer()
df = load_nic_data()


embeddings = semantic_model.encode(df["NIC description"].tolist(), convert_to_tensor=True, dtype=torch.float32)
df["Embeddings"] = embeddings.cpu().tolist()

def refine_query(details):
    """Refine user query into a structured format using GPT-4All"""
    prompt = f"Convert the following business description into a structured search query: {details}"
    response = model.generate(prompt, max_tokens=50)
    return response.strip()

def get_nic_code(details, df, top_n=5):
    """Find the most relevant NIC codes using semantic similarity"""
    refined_query = refine_query(details)
    query_embedding = semantic_model.encode([refined_query], convert_to_tensor=True, dtype=torch.float32).cpu()

    
    stored_embeddings = torch.tensor(df["Embeddings"].tolist(), dtype=torch.float32)

   
    similarity_scores = util.pytorch_cos_sim(query_embedding, stored_embeddings)[0]

  
    top_matches_idx = torch.topk(similarity_scores, top_n).indices.tolist()
    top_matches = df.iloc[top_matches_idx][["NICcode", "NIC description"]].to_dict(orient="records")
    result = "\n".join(f"{row['NICcode']}: {row['NIC description']}" for row in top_matches)

    return result

def translate_to_english(text):
    return GoogleTranslator(source='auto', target='en').translate(text)


def recognize_speech():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("Listening... Speak now!")
            audio = recognizer.listen(source, timeout=120)
            text = recognizer.recognize_google(audio)
            return text
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Speech recognition service unavailable."
    except Exception as e:
        return f"Microphone Error: {str(e)}"


if "history" not in st.session_state:
    st.session_state["history"] = []
if "voice_input" not in st.session_state:
    st.session_state["voice_input"] = ""

st.markdown("""
    <style>
        .message { padding: 15px; margin: 10px; border-radius: 10px; }
        .user-message { background-color: #007bff; color: white; text-align: right; }
        .ai-message { background-color: #f1f1f1; color: black; text-align: left; }
        .chat-container { max-width: 800px; margin: auto; }
        .input-container { position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); width: 80%; }
        .input-box { width: 90%; padding: 12px; border-radius: 10px; font-size: 18px; border: 1px solid #ccc; }
        .send-button { padding: 10px; font-size: 18px; border-radius: 10px; border: none; background-color: #007bff; color: white; }
        .send-button:hover { background-color: #0056b3; }
        .mic-button { padding: 10px; font-size: 18px; border-radius: 10px; border: none; background-color: #28a745; color: white; }
        .mic-button:hover { background-color: #218838; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

st.image("mospi.png", use_container_width=True)

st.markdown("""
    <h1 style="text-align:center;">GovINTEL.AI</h1>
""", unsafe_allow_html=True)


col3, col1, col2 = st.columns([2, 11, 3])
with col1:
    query = st.text_input("", value=st.session_state["voice_input"], placeholder="Enter company description...", key="query", label_visibility="collapsed", max_chars=500)

with col2:
    if st.button("🎙️", help="Speak to search"):
        voice_text = recognize_speech()
        st.session_state["voice_input"] = voice_text
        st.rerun()

if st.button("Find NIC Code", help="Find NIC Code"):
    if query:
        with st.spinner("Fetching NIC code and reasoning..."):
           
            translated_result = translate_to_english(query)
            nic_result = get_nic_code(translated_result, df)

        
        nic_list = nic_result.split("\n")
        formatted_nic_result = "<ul>" + "".join(f"<li><b>{item}</b></li>" for item in nic_list) + "</ul>"
        st.markdown('<div class="nic-header"><b>🏷️ Classified NIC Codes</b></div>', unsafe_allow_html=True)
        st.markdown(formatted_nic_result, unsafe_allow_html=True)

        try:
            st.info("Saving Progress")

            dsn = cx_Oracle.makedsn("127.0.0.1", port=1521, sid="XE")  # or use service_name="your_service_name"
            conn = cx_Oracle.connect(
                user="SYSTEM",
                password="RHYTHM",
                dsn=dsn
            )
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO RESULT_CODES (ID, ACTIVITY_NAME, NIC_CODE, DESCRIPTION, PREDICTED_NIC)
                VALUES (:1, :2, :3, :4, :5)
            """

            result_id = int(datetime.utcnow().timestamp()) 
            values = (
                result_id,               
                query,                  
                "N/A",                  
                translated_result,      
                nic_result              
            )

            cursor.execute(insert_query, values)
            conn.commit()

            st.success("✅ Oracle DB Updated.")
            print("✅ Oracle Insert Successful! Entry ID:", result_id)

        except Exception as e:
            st.error(f"❌ Oracle Insert Failed: {str(e)}")
            print("❌ Oracle Error:", str(e))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


st.sidebar.image("GovINTEL.AI.png", use_container_width=True)
st.sidebar.title("📜 Search History")
if st.session_state["is_authenticated"]:
    try:
        history_records = list(collection.find({"user": st.session_state["user_email"]}).sort("timestamp", -1))
        if history_records:
            for i, entry in enumerate(history_records, start=1):
                st.sidebar.markdown(f"**{i}.** {entry['user_input']}  \n🚀 *{entry['nic_code_result']}*")
        else:
            st.sidebar.info("No history yet.")
    except:
        st.sidebar.error("Search to load history")
else:
    st.sidebar.info("Login to see your history.")


if st.sidebar.button("Clear History"):
    if st.session_state["is_authenticated"]:
        try:
            collection.delete_many({"user": st.session_state["user_email"]})
            st.sidebar.success("Your history cleared!")
        except:
            st.sidebar.error("Error clearing history.")
    else:
        st.sidebar.warning("Login first to clear history.")

st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")


st.markdown("---")
st.header("Upload & Process CSV")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    df_input = pd.read_csv(uploaded_file, header=None, names=['Company Name', 'Details'])
    df_input.dropna(subset=['Details'], inplace=True)

    if st.button("Process CSV", help="Process CSV"):
        with st.spinner("Processing CSV..."):
            df_input['NIC Codes'] = df_input['Details'].apply(lambda x: get_nic_code(x, df))

  
        st.write("### Processed Data Preview:")
        st.dataframe(df_input.head())

       
        output_filename = "processed_nic_codes.csv"
        df_input.to_csv(output_filename, index=False, encoding='utf-8-sig')

        with open(output_filename, "rb") as file:
            st.download_button("Download Processed CSV", file, file_name=output_filename, mime="text/csv", help="Download")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")


st.markdown("---")
st.subheader("Why Choose Us?")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("**⚡ Accuracy:**")
    st.write("AI-powered predictions for precise NIC codes.")
with col2:
    st.markdown("**⏳ Speed:**")
    st.write("Get results instantly, saving valuable time.")
with col3:
    st.markdown("**🛠️ Ease of Use:**")
    st.write("Simple interface for seamless code retrieval.")
with col4:
    st.markdown("**📜 History Tracking:**")
    st.write("Access and review your past searches easily.")


font_choice = st.sidebar.selectbox("🔤 Choose Font Style:", ["Default", "Dyslexic-Friendly"])


if "font_style" not in st.session_state:
    st.session_state["font_style"] = font_choice
else:
    st.session_state["font_style"] = font_choice


dyslexic_font_url = "https://fonts.cdnfonts.com/css/opendyslexic"

t
if st.session_state["font_style"] == "Dyslexic-Friendly":
    font_css = f"""
        <style>
        @import url('{dyslexic_font_url}');
        * {{
            font-family: 'OpenDyslexic', sans-serif !important;
        }}
        </style>
    """
else:
    font_css = """
        <style>
        * {
            font-family: 'Arial', sans-serif !important;
        }
        </style>
    """

st.markdown(font_css, unsafe_allow_html=True)
