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
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)

def save_data(df, file): df.to_csv(file, index=False)

if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, audit_cols)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.markdown(f'<img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" style="width:100px;">', unsafe_allow_html=True) #
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        u_id = st.text_input("Username/ID")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role, "user_id": u_id})
                st.rerun()
else:
    st.sidebar.info(f"Role: {st.session_state.role} | {st.session_state.user_id}")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["My Performance"]
    }
    choice = st.sidebar.selectbox("Go to", nav[st.session_state.role])
    if st.sidebar.button("Logout"): st.session_state.logged_in = False; st.rerun()

    # --- AGENT DETAILS (FIXED UPDATE PORTION) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        t1, t2, t3 = st.tabs(["Add Agent", "Update Agent", "Agent List"]) #
        
        with t1: # Add New Agent
            with st.form("add_ag", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_id, n_name = c1.text_input("Employee ID"), c2.text_input("Agent Name")
                n_gen, n_con = c1.selectbox("Gender", ["Male", "Female", "Other"]), c2.text_input("Contact Number")
                n_emg, n_chan = c1.text_input("Emergency Contact"), c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                n_stat = st.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save New Agent"):
                    st.session_state.agent_db.loc[len(st.session_state.agent_db)] = [n_id, n_name, n_gen, n_con, n_emg, n_chan, n_stat]
                    save_data(st.session_state.agent_db, AGENT_FILE); st.success("Added!"); st.rerun()

        with t2: # Update Existing Agent (FIXED)
            ag_list = st.session_state.agent_db['Name'].tolist()
            sel_up = st.selectbox("Select Agent to Update", [""] + ag_list)
            if sel_up:
                data = st.session_state.agent_db[st.session_state.agent_db['Name'] == sel_up].iloc[0]
                with st.form("up_ag"):
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
                        save_data(st.session_state.agent_db, AGENT_FILE); st.success("Updated!"); st.rerun()

        with t3: # Agent List View
            filt = st.selectbox("Filter Channel", ["All", "Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            df = st.session_state.agent_db if filt == "All" else st.session_state.agent_db[st.session_state.agent_db['Channel'] == filt]
            for i, row in df.iterrows():
                col1, col2, col3 = st.columns([1, 6, 1])
                col1.write(f"**{row['ID']}**")
                col2.write(f"{row['Name']} ({row['Channel']}) - {row['Status']}")
                if col3.button("🗑️", key=f"del_{row['ID']}"):
                    st.session_state.agent_db = st.session_state.agent_db.drop(i)
                    save_data(st.session_state.agent_db, AGENT_FILE); st.rerun()
                st.divider()

    # --- QA AUDIT ENTRY (FIXED ID FETCHING) ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        with st.form("eval_f", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            ch = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            active = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == ch) & (st.session_state.agent_db['Status'] == 'Active')]
            ag = c2.selectbox("Agent", ["Select Agent"] + active['Name'].tolist())
            
            # FIXED ID FETCHING
            eid = active[active['Name'] == ag]['ID'].values[0] if ag != "Select Agent" else "---"
            c3.markdown(f"**ID:** <span style='color:black;'>{eid}</span>", unsafe_allow_html=True)
            
            f1, f2, f3 = st.columns(3)
            iid, idt = f1.text_input("Interaction ID"), f2.date_input("Date")
            itm = f3.text_input("Time (Manual Input)") #
            
            feed = st.text_area("Feedback")
            # Scoring
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == ch]
            scores = {}
            for idx, row in params.iterrows():
                st.markdown(f'<div class="param-box">{row["Skill_Type"]} | {row["Parameter"]} ({row["Max_Score"]})</div>', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{idx}")
                scores[row['Parameter']] = 0 if dm else row['Max_Score']

            if st.form_submit_button("Submit Audit"):
                if ag != "Select Agent" and iid:
                    entry = {
                        'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': st.session_state.user_id, 'Agent Name': ag, 'Employee ID': eid,
                        'Channel': ch, 'Interaction Date': str(idt), 'Interaction Time': itm,
                        'Eval_ID': iid, 'QA Feedback': feed, 'Status': 'Pending', 'Total Score': sum(scores.values())
                    }
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE); st.success("Submitted!"); st.rerun()

    # --- PARAMETERS (FIXED SKILL TYPE) ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters Setup") #
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            psk = c2.selectbox("Skill Name", ["Soft Skill", "Service Skill"]) #
            pn = st.text_input("Parameter Name")
            psc = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add Parameter"):
                st.session_state.param_db.loc[len(st.session_state.param_db)] = [pc, psk, pn, psc]
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)

    elif choice == "Publish Audits":
        pend = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pend)
        if st.button("Publish All") and not pend.empty:
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    elif choice in ["Audit Logs", "My Performance"]:
        data = st.session_state.audit_logs
        if st.session_state.role == "Agent":
            data = data[(data['Employee ID'].astype(str) == str(st.session_state.user_id)) & (data['Status'] == 'Published')]
        st.dataframe(data, use_container_width=True)
