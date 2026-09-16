import streamlit as st
import google.generativeai as genai
import os
import PyPDF2

# 1. ตั้งค่าหน้าเพจและธีมเพิ่มเติม (Neon Effects)
st.set_page_config(page_title="HA SAR 2026 AI Agent", page_icon="🏥", layout="centered")
st.markdown("""
    <style>
    h1 { color: #00f3ff; text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff; font-family: 'Sarabun', sans-serif;}
    .stTextInput>div>div>input { border: 1px solid #9290c3; color: #fff; background-color: #1b1a55; }
    .stTextInput>div>div>input:focus { border: 2px solid #00f3ff; box-shadow: 0 0 10px #00f3ff; }
    .stButton>button { border: 1px solid #00f3ff; color: #00f3ff; background-color: transparent; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #00f3ff; color: #070f2b; box-shadow: 0 0 15px #00f3ff; }
    </style>
""", unsafe_allow_html=True)

# 2. ระบบ Login (ตั้งรหัสผ่านเองที่ Streamlit Secrets)
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # ลบรหัสออกเพื่อความปลอดภัย
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center; color: #9290c3;'>🔒 กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน</h2>", unsafe_allow_html=True)
        st.text_input("รหัสผ่าน (Password)", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; color: #9290c3;'>🔒 กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน</h2>", unsafe_allow_html=True)
        st.text_input("รหัสผ่าน (Password)", type="password", on_change=password_entered, key="password")
        st.error("❌ รหัสผ่านไม่ถูกต้อง")
        return False
    return True

if check_password():
    # 3. กำหนดค่า API ของ Gemini
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    st.markdown("<h1>🏥 HA v.6 SAR Agent (SPA 1-3)</h1>", unsafe_allow_html=True)
    st.caption("✨ ระบบผู้ช่วยวิเคราะห์และเขียนรายงานประเมินตนเองตามมาตรฐาน HA ฉบับที่ 6 ด้วยโครงสร้าง 3P และ 3C-PDSA")

    # ฟังก์ชันอ่านไฟล์ PDF 3 ไฟล์ (เพื่อนำไปเป็น Context ให้ AI)
    @st.cache_resource
    def load_pdf_context():
        # หมายเหตุ: ในการใช้งานจริง ให้อัปโหลดไฟล์ PDF 3 ไฟล์ลงในโฟลเดอร์เดียวกับโค้ด
        # หรือให้ AI อ้างอิงจากความรู้ที่มีอยู่แล้ว
        return "ใช้ความรู้เรื่องมาตรฐาน HA ฉบับที่ 6 พ.ศ. 2565 (2026) ระดับ SPA 1-3 อย่างเคร่งครัด"

    context = load_pdf_context()

    # ตั้งค่า System Prompt
    system_instruction = f"""
    คุณคือผู้เชี่ยวชาญด้านมาตรฐาน HA ฉบับที่ 6 ข้อมูลอ้างอิง: {context}
    หน้าที่ของคุณคือ สัมภาษณ์เชิงลึกผู้ใช้งานเพื่อเขียน SAR ระดับ SPA 1-3 ด้วยรูปแบบ 3P (Purpose, Process, Performance) และ 3C-PDSA
    - ให้ถามทีละข้อ ห้ามถามรวดเดียว
    - หากผู้ใช้ระบุ Process (PDSA) มา แต่ขาดการนำผลไปปรับปรุง (Act) หรือขาดนวัตกรรม ให้ถามจี้ประเด็นนี้เสมอ
    - สรุปรวบยอดเป็นเอกสาร SAR ด้วยภาษาราชการเมื่อได้ข้อมูลครบถ้วน
    """

    # เก็บประวัติการแชท
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # ข้อความแรกจาก AI
        st.session_state.messages.append({"role": "assistant", "content": "สวัสดีครับ! ผมคือ AI ผู้ช่วยเขียน SAR ระบบพร้อมทำงานแล้ว โปรดระบุ 'รหัสมาตรฐานหรือหัวข้อ' ที่ต้องการประเมินครับ 💡"})

    # แสดงประวัติการแชท
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # รับข้อความจากผู้ใช้
    if prompt := st.chat_input("พิมพ์หัวข้อมาตรฐาน หรือข้อมูลของคุณที่นี่..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # ประมวลผลด้วย Gemini
        with st.chat_message("assistant"):
            model = genai.GenerativeModel("gemini-1.5-pro", system_instruction=system_instruction)
            
            # จัดเตรียม History ส่งให้ Gemini
            history = [{'role': 'user' if m['role']=='user' else 'model', 'parts': [m['content']]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            
            with st.spinner("⚡ กำลังวิเคราะห์ข้อมูล..."):
                response = chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
