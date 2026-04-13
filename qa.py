import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. UI & STYLING ---
PATHAO_RED = "#ED1C24"
st.set_page_config(page_title="Pathao Quality Tool", layout="wide")

st.markdown(f"""
<style>
    .stApp {{ background-color: {PATHAO_RED}; color: white; }}
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');
    html, body, [class*="st-"] {{ font-family: "Comic Sans MS", "Anek Bangla", sans-serif !important; font-size: 13px; }}
    div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {{
        background-color: #000000 !important; color: {PATHAO_RED} !important; border: 1px solid white !important; font-size: 13px !important;
    }}
    label, .stMarkdown p {{ color: white !important; font-weight: bold; }}
    button[kind="primary"] {{ background-color: white !important; color: {PATHAO_RED} !important; border-radius: 4px; font-weight: bold; border: none; }}
    .stButton > button[key^="del_"] {{ background-color: #000000 !important; color: white !important; border: 1px solid white !important; padding: 0px 5px !important; font-size: 10px !important; height: 22px !important; }}
    .param-box {{ background-color: black; padding: 8px; border-radius: 5px; border: 1px solid white; margin-bottom: 5px; }}
    [data-testid="stSidebar"] {{ background-color: {PATHAO_RED}; border-right: 1px solid white; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE LOGIC ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE = "agents.csv", "parameters.csv", "audit_logs.csv"
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']
audit_cols = ['Week', 'Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 'Channel', 'Interaction Date', 'Interaction Time', 'Eval_ID', 'QA Feedback', 'Status', 'Total Score']

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, audit_cols)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.title("Pathao QA Portal")
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        u_id = st.text_input("Username/ID")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role, "user_id": u_id})
                st.rerun()
            else: st.error("Wrong Password")
else:
    st.sidebar.info(f"Role: {st.session_state.role}")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["My Performance"]
    }
    choice = st.sidebar.selectbox("Go to", nav[st.session_state.role])
    if st.sidebar.button("Logout"): st.session_state.logged_in = False; st.rerun()

    # --- AGENT DETAILS ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        t1, t2, t3 = st.tabs(["Add Agent", "Update Agent", "Agent List"])
        
        with t1:
            with st.form("add_ag_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_id = c1.text_input("Employee ID")
                n_name = c2.text_input("Agent Name")
                n_gen = c1.selectbox("Gender", ["Male", "Female", "Other"])
                n_con = c2.text_input("Contact Number")
                n_emg = c1.text_input("Emergency Contact")
                n_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                n_stat = st.selectbox("Status", ["Active", "Resigned"])
                
                if st.form_submit_button("Save New Agent", type="primary"):
                    if n_id and n_name:
                        new_row = pd.DataFrame([[n_id, n_name, n_gen, n_con, n_emg, n_chan, n_stat]], columns=agent_cols)
                        st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_row], ignore_index=True)
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success(f"Saved: {n_name} ({n_chan})")
                        st.rerun()

        with t2:
            ag_list = st.session_state.agent_db['Name'].tolist()
            sel_up = st.selectbox("Select Agent to Update", [""] + ag_list)
            if sel_up:
                data = st.session_state.agent_db[st.session_state.agent_db['Name'] == sel_up].iloc[0]
                with st.form("up_ag_form"):
                    c1, c2 = st.columns(2)
                    u_id = c1.text_input("Employee ID", value=data['ID'])
                    u_gen = c2.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(data['Gender']))
                    u_con = c1.text_input("Contact", value=data['Contact'])
                    u_emg = c2.text_input("Emergency Contact", value=data['Emergency_Contact'])
                    u_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(data['Channel']))
                    u_stat = c2.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(data['Status']))
                    if st.form_submit_button("Update"):
                        idx = st.session_state.agent_db[st.session_state.agent_db['Name'] == sel_up].index[0]
                        st.session_state.agent_db.loc[idx] = [u_id, sel_up, u_gen, u_con, u_emg, u_chan, u_stat]
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success("Updated!")
                        st.rerun()

        with t3:
            filt = st.selectbox("Filter Agent View", ["All", "Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            df_view = st.session_state.agent_db if filt == "All" else st.session_state.agent_db[st.session_state.agent_db['Channel'] == filt]
            st.dataframe(df_view, use_container_width=True)

    # --- QA AUDIT ENTRY (FIXED DYNAMIC FILTERING) ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        
        # ১. আগে চ্যানেল সিলেক্ট করবেন (ফরমের বাইরে রাখা হয়েছে ভালো রিফ্রেশের জন্য)
        sel_ch = st.selectbox("1. Select Channel First", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], key="qa_ch_sel")
        
        # ২. সিলেক্ট করা চ্যানেলের এজেন্টদের ফিল্টার করা
        relevant_agents = st.session_state.agent_db[
            (st.session_state.agent_db['Channel'] == sel_ch) & 
            (st.session_state.agent_db['Status'] == 'Active')
        ]
        
        with st.form("audit_entry_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            # ৩. শুধুমাত্র ওই চ্যানেলের এজেন্টদের ড্রপডাউন
            ag_name = c1.selectbox("2. Select Agent Name", [""] + relevant_agents['Name'].tolist())
            
            # ৪. আইডি অটো বের করা
            if ag_name != "":
                emp_id_val = relevant_agents[relevant_agents['Name'] == ag_name]['ID'].values[0]
            else:
                emp_id_val = "---"
            
            c2.info(f"Agent ID: {emp_id_val}")
            
            f1, f2, f3 = st.columns(3)
            int_id = f1.text_input("Interaction ID")
            int_date = f2.date_input("Date")
            int_time = f3.text_input("Time (Manual)")
            
            f_back = st.text_area("Feedback")
            
            # স্কোরিং প্যারামিটার (চ্যানেল অনুযায়ী)
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
            scores = {}
            if params.empty:
                st.warning(f"No parameters found for {sel_ch}. Please add them in 'Audit Parameters'.")
            else:
                for idx, row in params.iterrows():
                    st.markdown(f'<div class="param-box">{row["Skill_Type"]} | {row["Parameter"]} ({row["Max_Score"]})</div>', unsafe_allow_html=True)
                    dm = st.checkbox(f"Demark", key=f"eval_dm_{idx}")
                    scores[row['Parameter']] = 0 if dm else row['Max_Score']

            if st.form_submit_button("Submit Audit", type="primary"):
                if ag_name != "" and int_id != "":
                    new_audit = {
                        'Week': datetime.now().isocalendar()[1],
                        'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': st.session_state.user_id,
                        'Agent Name': ag_name,
                        'Employee ID': emp_id_val,
                        'Channel': sel_ch,
                        'Interaction Date': str(int_date),
                        'Interaction Time': int_time,
                        'Eval_ID': int_id,
                        'QA Feedback': f_back,
                        'Status': 'Pending',
                        'Total Score': sum(scores.values())
                    }
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([new_audit])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Audit Recorded Successfully!")
                    st.rerun()
                else:
                    st.error("Please select Agent and enter Interaction ID")

    # --- PARAMETERS ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Setup Parameters")
        with st.form("param_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            p_ch = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_sk = c2.selectbox("Skill Type", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_max = st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[p_ch, p_sk, p_name, p_max]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE)
                st.success("Parameter Added!")
                st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)

    elif choice == "Audit Logs":
        st.header("📋 Master Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
