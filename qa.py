import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- custom pathao style inject ---
PATHAO_RED = "#F08080"

style = f"""
<style>
    /* 1. Global Page Background - Red and Text - White */
    .stApp {{
        background-color: {PATHAO_RED};
        color: white;
    }}

    /* 2. Fonts and Font Sizes (3-4 size smaller) */
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');

    html, body, [class*="st-"] {{
        font-family: "Comic Sans MS", "Anek Bangla", sans-serif !important;
        font-size: 13px; /* Smaller default size */
    }}

    h1 {{ font-size: 20px !important; margin-bottom: 8px; }}
    h2 {{ font-size: 16px !important; }}
    h3 {{ font-size: 14px !important; }}

    /* 3. Black Background Area (Input Boxes & Parameters) */
    div[data-baseweb="select"] > div, 
    .stTextInput input, 
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input {{
        background-color: #000000 !important;
        color: {PATHAO_RED} !important;
        border: 1px solid white !important;
        font-size: 13px !important;
    }}

    /* Labels within the red background must be white */
    label, .stMarkdown p {{
        color: white !important;
        font-size: 13px !important;
    }}

    /* Demark Section Background Black and Text Red */
    div.stButton > button[key^="btn_"] {{
        background-color: #000000 !important;
        color: white !important;
        border: 1px solid white !important;
    }}

    /* 4. Primary White Buttons */
    button[kind="primary"] {{ 
        background-color: white !important; 
        color: {PATHAO_RED} !important; 
        border-radius: 4px;
        font-weight: bold;
    }}

    /* 5. Sidebar Styling */
    [data-testid="stSidebar"] {{ 
        background-color: {PATHAO_RED}; 
        border-right: 1px solid white;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}

    /* Logo Styling */
    .logo-img {{ width: 50px; height: auto; margin-bottom: 5px; }}

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

# --- APP LOGIC ---
if not st.session_state.logged_in:
    st.markdown('<img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png/v1/fill/w_400,h_400,al_c,q_85,usm_0.66_1.00_0.01,enc_avif/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" class="logo-img">', unsafe_allow_html=True)
    st.title("Pathao Quality Tool")
    
    with st.form("login_form"):
        role = st.selectbox("Login as:", ["Admin", "QA", "Agent"])
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
    st.sidebar.info(f"{st.session_state.role}: {st.session_state.user_id}")
    
    if st.session_state.role == "Admin":
        menu = ["Agent Details", "Audit Parameters", "Audit Logs"]
    elif st.session_state.role == "QA":
        menu = ["QA Audit Entry", "Publish Audits", "Audit Logs"]
    else:
        menu = ["My Performance"]
    
    choice = st.sidebar.selectbox("Navigation", menu)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- ১. এজেন্ট ডিটেইলস ---
    if choice == "Agent Details":
        st.header("Agent Management")
        with st.form("agent_form"):
            c1, c2 = st.columns(2)
            a_id = c1.text_input("Employee ID")
            a_name = c2.text_input("Agent Name")
            a_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            if st.form_submit_button("Save Agent"):
                st.session_state.agent_db.loc[len(st.session_state.agent_db)] = [a_id, a_name, "Male", a_chan, "Active"]
                save_data(st.session_state.agent_db, AGENT_FILE)
                st.success("Agent Saved!")
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- ২. অডিট প্যারামিটারস ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Audit Parameters")
        with st.form("p_form"):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add Parameter"):
                st.session_state.param_db.loc[len(st.session_state.param_db)] = [p_chan, "Skill", p_name, p_score]
                save_data(st.session_state.param_db, PARAM_FILE)
                st.success("Parameter Added!")
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA অডিট এন্ট্রি (All Fields Restored) ---
    elif choice == "QA Audit Entry":
        st.header("📝 Quality Audit Entry")
        today = datetime.now()
        week_num = today.isocalendar()[1] if today.strftime("%A") != "Sunday" else today.isocalendar()[1] + 1
        
        # Header Info
        st.markdown(f"**Auditor:** {st.session_state.user_id} | **Week:** {week_num}")
        
        # All Required Fields
        c1, c2, c3 = st.columns(3)
        sel_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
        sel_agent = c2.selectbox("Agent Name", ["Select Agent"] + agent_list['Name'].tolist())
        eval_id = c3.text_input("Call/Chat ID")
        
        emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""
        
        f1, f2 = st.columns(2)
        f1.text_input("Employee ID", value=emp_id, disabled=True)
        inter_date = f2.date_input("Interaction Date")
        
        feedback = st.text_area("QA Feedback")

        st.divider()
        # Parameter Scoring Section
        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        if params.empty:
            st.warning("No parameters found for this channel.")
        else:
            audit_scores = {}
            for idx, row in params.iterrows():
                u_key = f"dm_{idx}"
                if u_key not in st.session_state: st.session_state[u_key] = False
                
                # Black Background for Parameter Row
                with st.container():
                    st.markdown(f'<div style="background-color:black; padding:8px; border-radius:5px; margin-bottom:5px;">'
                                f'<span style="color:{PATHAO_RED}; font-weight:bold;">{row["Parameter"]} (Max: {row["Max_Score"]})</span>'
                                f'</div>', unsafe_allow_html=True)
                    
                    if st.button(f"Demark {row['Parameter']}", key=f"btn_{idx}"):
                        st.session_state[u_key] = not st.session_state[u_key]
                    
                    current_score = 0 if st.session_state[u_key] else row['Max_Score']
                    audit_scores[row['Parameter']] = current_score
                    st.caption(f"Current Score: {current_score}")

            if st.button("Submit Audit", type="primary"):
                if sel_agent == "Select Agent" or not eval_id:
                    st.error("Please fill all required fields!")
                else:
                    entry = {
                        'Week': week_num, 'Evaluation Date': today.strftime("%Y-%m-%d"),
                        'Evaluator Name': st.session_state.user_id, 'Agent Name': sel_agent, 'Employee ID': emp_id,
                        'Channel': sel_chan, 'Interaction Date': str(inter_date), 'Eval_ID': eval_id,
                        'QA Feedback': feedback, 'Status': 'Pending', 'Total Score': sum(audit_scores.values())
                    }
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Audit submitted to Pending list!")
                    st.balloons()

    # --- ৪. পাবলিশ অডিট ---
    elif choice == "Publish Audits":
        st.header("📢 Publish Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        if pending.empty:
            st.info("No pending audits.")
        else:
            st.dataframe(pending, use_container_width=True)
            if st.button("Publish All", type="primary"):
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                save_data(st.session_state.audit_logs, AUDIT_FILE)
                st.success("All audits published!")
                st.rerun()

    # --- ৫. অডিট লগস ---
    elif choice == "Audit Logs":
        st.header("📋 Master Audit Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    # --- ৬. মাই পারফরম্যান্স ---
    elif choice == "My Performance":
        st.header("📈 My Performance")
        my_data = st.session_state.audit_logs[(st.session_state.audit_logs['Employee ID'].astype(str) == str(st.session_state.user_id)) & (st.session_state.audit_logs['Status'] == 'Published')]
        if my_data.empty:
            st.info("No published audits found.")
        else:
            st.dataframe(my_data, use_container_width=True)
