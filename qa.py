import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- custom pathao style inject ---
PATHAO_RED = "#ED1C24"

style = f"""
<style>
    /* 1. Global Page Background - Red and Text - White */
    .stApp {{
        background-color: {PATHAO_RED};
        color: white;
    }}

    /* 2. Fonts and Font Sizes */
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');

    html, body, [class*="st-"] {{
        font-family: "Comic Sans MS", "Anek Bangla", sans-serif !important;
        font-size: 14px; /* Default font size optimized */
    }}

    /* Header and Title resizing (3-4 size smaller) */
    h1 {{ font-size: 22px !important; margin-bottom: 10px; }}
    h2 {{ font-size: 18px !important; }}
    h3 {{ font-size: 16px !important; }}

    /* 3. Black Background Area (Input Boxes & Parameters) */
    /* Targeting input areas and specific sections */
    div[data-baseweb="select"] > div, 
    .stTextInput input, 
    .stTextArea textarea,
    .stNumberInput input {{
        background-color: #000000 !important;
        color: {PATHAO_RED} !important;
        border: 1px solid white !important;
        font-size: 14px !important;
    }}

    /* Parameter box area background black */
    [data-testid="stVerticalBlock"] > div:has(button[key^="btn_"]) {{
        background-color: #000000;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
    }}

    /* Parameter Text in Black area */
    div:has(button[key^="btn_"]) p, div:has(button[key^="btn_"]) b {{
        color: {PATHAO_RED} !important;
    }}

    /* 4. Buttons */
    button[kind="primary"] {{ 
        background-color: white !important; 
        color: {PATHAO_RED} !important; 
        border-radius: 5px;
        font-weight: bold;
    }}
    
    button[kind="secondary"] {{
        background-color: #000000 !important;
        color: white !important;
        border: 1px solid white !important;
    }}

    /* 5. Sidebar Styling */
    [data-testid="stSidebar"] {{ 
        background-color: {PATHAO_RED}; 
        border-right: 1px solid white;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}

    /* 6. DataFrame/Table colors */
    .stDataFrame {{
        background-color: white;
        border-radius: 5px;
    }}

    /* Logo Styling */
    .logo-img {{ width: 60px; height: auto; margin-bottom: 5px; }}
    .logo-text {{ font-size: 20px !important; color: white !important; }}

</style>
"""

st.markdown(style, unsafe_allow_html=True)

# --- DATABASE LOGIC ---
AGENT_FILE = "agents.csv"
PARAM_FILE = "parameters.csv"
AUDIT_FILE = "audit_logs.csv"

def load_data(file_path, columns):
    if os.path.exists(file_path):
        try: return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None 

if 'agent_db' not in st.session_state:
    st.session_state.agent_db = load_data(AGENT_FILE, ['ID', 'Name', 'Gender', 'Channel', 'Status'])

if 'param_db' not in st.session_state:
    st.session_state.param_db = load_data(PARAM_FILE, ['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = load_data(AUDIT_FILE, ['Week', 'Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 'Channel', 'Interaction Date', 'Eval_ID', 'QA Feedback', 'Status', 'Total Score'])

# --- APP RENDER ---
if not st.session_state.logged_in:
    st.markdown('<img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png/v1/fill/w_400,h_400,al_c,q_85,usm_0.66_1.00_0.01,enc_avif/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" class="logo-img">', unsafe_allow_html=True)
    st.title("Pathao Quality Tool")
    
    with st.form("login_form"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        u_id = st.text_input("Username/Email/ID")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "1234":
                st.session_state.logged_in, st.session_state.role, st.session_state.user_id = True, role, u_id
                st.rerun()
            else: st.error("Wrong Password")
else:
    # Sidebar
    st.sidebar.markdown('<img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png/v1/fill/w_400,h_400,al_c,q_85,usm_0.66_1.00_0.01,enc_avif/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" style="width:50px;">', unsafe_allow_html=True)
    st.sidebar.subheader(f"{st.session_state.role}: {st.session_state.user_id}")
    
    menu = ["Agent Details", "Audit Parameters", "Audit Logs"] if st.session_state.role == "Admin" else \
           ["QA Audit Entry", "Publish Audits", "Audit Logs"] if st.session_state.role == "QA" else ["My Performance"]
    
    choice = st.sidebar.selectbox("Navigation", menu)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Logic per menu
    if choice == "Agent Details":
        st.header("Agent Management")
        with st.form("agent_add"):
            c1, c2 = st.columns(2)
            a_id = c1.text_input("ID")
            a_name = c2.text_input("Name")
            a_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue"])
            if st.form_submit_button("Save"):
                st.session_state.agent_db.loc[len(st.session_state.agent_db)] = [a_id, a_name, "Male", a_chan, "Active"]
                save_data(st.session_state.agent_db, AGENT_FILE)
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    elif choice == "QA Audit Entry":
        st.header("Audit Entry")
        today = datetime.now()
        week = today.isocalendar()[1]
        
        c1, c2 = st.columns(2)
        sel_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue"])
        agents = st.session_state.agent_db[st.session_state.agent_db['Channel'] == sel_chan]['Name'].tolist()
        sel_agent = c2.selectbox("Agent", agents if agents else ["No Agent"])
        
        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        audit_scores = {}
        
        for idx, row in params.iterrows():
            st.markdown(f"**{row['Parameter']}**")
            if st.button(f"Demark {row['Parameter']}", key=f"btn_{idx}"):
                st.session_state[f"score_{idx}"] = 0
            score = st.session_state.get(f"score_{idx}", row['Max_Score'])
            audit_scores[row['Parameter']] = score
            st.caption(f"Score: {score}")

        if st.button("Submit Audit", type="primary"):
            entry = {'Week': week, 'Evaluation Date': today.strftime("%Y-%m-%d"), 'Evaluator Name': st.session_state.user_id, 'Agent Name': sel_agent, 'Status': 'Pending', 'Total Score': sum(audit_scores.values())}
            st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
            save_data(st.session_state.audit_logs, AUDIT_FILE)
            st.success("Audit Saved!")

    elif choice == "Publish Audits":
        st.header("Publishing Hub")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending, use_container_width=True)
        if st.button("Publish All", type="primary"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE)
            st.rerun()

    elif choice == "Audit Logs":
        st.header("Master Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    elif choice == "My Performance":
        st.header("My Performance")
        personal = st.session_state.audit_logs[(st.session_state.audit_logs['Evaluator Name'] == st.session_state.user_id) & (st.session_state.audit_logs['Status'] == 'Published')]
        st.dataframe(personal, use_container_width=True)
