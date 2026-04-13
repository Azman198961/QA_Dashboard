import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. THEME & UI ---
PATHAO_RED = "#F08080"
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

# --- 2. DATA MANAGEMENT ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE = "agents.csv", "parameters.csv", "audit_logs.csv"
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
audit_cols = ['Week', 'Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 'Channel', 'Interaction Date', 'Interaction Time', 'Eval_ID', 'QA Feedback', 'Status', 'Total Score']

def load_data(file, cols):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# Session States
if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, ['Channel', 'Parameter', 'Max_Score'])
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, audit_cols)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.title("Pathao QA Portal")
    with st.form("login_gate"):
        role = st.selectbox("Select Role", ["Admin", "QA", "Agent"])
        u_id = st.text_input("Username/ID")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role, "user_id": u_id})
                st.rerun()
            else: st.error("Invalid Credential")

# --- 4. DASHBOARD ---
else:
    st.sidebar.subheader(f"Role: {st.session_state.role}")
    
    # Navigation Logic
    nav_map = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["My Performance"]
    }
    choice = st.sidebar.selectbox("Go to", nav_map[st.session_state.role])
    if st.sidebar.button("Logout"): st.session_state.logged_in = False; st.rerun()

    # --- AGENT DETAILS (Admin) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        t1, t2, t3 = st.tabs(["Add Agent", "Update Agent", "Agent List"])
        with t1:
            with st.form("add_ag", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_id, n_name = c1.text_input("Employee ID"), c2.text_input("Agent Name")
                n_gen, n_con = c1.selectbox("Gender", ["Male", "Female", "Other"]), c2.text_input("Contact Number")
                n_emg, n_chan = c1.text_input("Emergency Contact"), c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                n_stat = st.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save"):
                    st.session_state.agent_db.loc[len(st.session_state.agent_db)] = [n_id, n_name, n_gen, n_con, n_emg, n_chan, n_stat]
                    save_data(st.session_state.agent_db, AGENT_FILE); st.success("Added!"); st.rerun()
        with t3:
            filt = st.selectbox("Filter", ["All", "Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            df = st.session_state.agent_db if filt == "All" else st.session_state.agent_db[st.session_state.agent_db['Channel'] == filt]
            for i, row in df.iterrows():
                col1, col2, col3 = st.columns([1, 6, 1])
                col1.write(row['ID'])
                col2.write(f"{row['Name']} ({row['Channel']})")
                if col3.button("🗑️", key=f"del_{row['ID']}"):
                    st.session_state.agent_db = st.session_state.agent_db.drop(i)
                    save_data(st.session_state.agent_db, AGENT_FILE); st.rerun()
                st.divider()

    # --- QA AUDIT ENTRY (QA) ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        with st.form("eval_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            ch = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            # Filter Agents by Channel
            active = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == ch) & (st.session_state.agent_db['Status'] == 'Active')]
            ag = c2.selectbox("Agent", ["Select"] + active['Name'].tolist())
            # Auto Employee ID
            eid = active[active['Name'] == ag]['ID'].values[0] if ag != "Select" else ""
            c3.info(f"ID: {eid}")
            
            f1, f2, f3 = st.columns(3)
            iid, idt = f1.text_input("Interaction ID"), f2.date_input("Date")
            itm = f3.text_input("Time (Manual Input)") # Manual Time
            
            feed = st.text_area("Feedback")
            # Scoring Parameters
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == ch]
            scores = {}
            for idx, row in params.iterrows():
                st.markdown(f'<div class="param-box">{row["Parameter"]} ({row["Max_Score"]})</div>', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{idx}")
                scores[row['Parameter']] = 0 if dm else row['Max_Score']

            if st.form_submit_button("Submit"):
                if ag != "Select" and iid:
                    entry = {
                        'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': st.session_state.user_id, 'Agent Name': ag, 'Employee ID': eid,
                        'Channel': ch, 'Interaction Date': str(idt), 'Interaction Time': itm,
                        'Eval_ID': iid, 'QA Feedback': feed, 'Status': 'Pending', 'Total Score': sum(scores.values())
                    }
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE); st.success("Submitted!"); st.rerun()

    # --- OTHER SECTIONS ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters")
        with st.form("p_f"):
            pc, pn, ps = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"]), st.text_input("Name"), st.number_input("Score", min_value=1)
            if st.form_submit_button("Add"):
                st.session_state.param_db.loc[len(st.session_state.param_db)] = [pc, pn, ps]
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.table(st.session_state.param_db)

    elif choice == "Publish Audits":
        st.header("📢 Publish evaluations")
        pend = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pend)
        if not pend.empty and st.button("Publish All"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    elif choice in ["Audit Logs", "My Performance"]:
        st.header("📋 Logs")
        data = st.session_state.audit_logs
        if st.session_state.role == "Agent":
            data = data[(data['Employee ID'].astype(str) == str(st.session_state.user_id)) & (data['Status'] == 'Published')]
        st.dataframe(data)
