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
    .param-box {{ background-color: black; padding: 10px; border-radius: 5px; border: 1px solid white; margin-bottom: 8px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONFIG ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE = "agents.csv", "parameters.csv", "audit_logs.csv"
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']

def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, [])
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN ---
if not st.session_state.logged_in:
    st.title("Pathao Quality Portal")
    with st.form("login_form"):
        role = st.selectbox("Select Role", ["Admin", "QA", "Agent"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role})
                st.rerun()
            else: st.error("Access Denied")

# --- 4. MAIN APPLICATION ---
else:
    st.sidebar.subheader(f"Role: {st.session_state.role}")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    choice = st.sidebar.selectbox("Go to", nav[st.session_state.role])
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- AGENT DETAILS ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        t1, t2, t3 = st.tabs(["Add Agent", "Update Agent", "Agent List"])
        with t1:
            with st.form("add_ag"):
                c1, c2 = st.columns(2)
                n_id, n_name = c1.text_input("Employee ID"), c2.text_input("Agent Name")
                n_gen, n_con = c1.selectbox("Gender", ["Male", "Female"]), c2.text_input("Contact")
                n_emg, n_chan = c1.text_input("Emergency Contact"), c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                n_stat = st.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save Agent"):
                    new_ag = pd.DataFrame([[n_id, n_name, n_gen, n_con, n_emg, n_chan, n_stat]], columns=agent_cols)
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_ag], ignore_index=True)
                    save_data(st.session_state.agent_db, AGENT_FILE); st.success("Saved!")
        with t2:
            ag_up = st.selectbox("Select Agent", [""] + st.session_state.agent_db['Name'].tolist())
            if ag_up:
                curr = st.session_state.agent_db[st.session_state.agent_db['Name'] == ag_up].iloc[0]
                with st.form("up_ag"):
                    u_id = st.text_input("ID", value=curr['ID'])
                    u_ch = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(curr['Channel']))
                    u_st = st.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(curr['Status']))
                    if st.form_submit_button("Update"):
                        idx = st.session_state.agent_db[st.session_state.agent_db['Name'] == ag_up].index[0]
                        st.session_state.agent_db.loc[idx, ['ID', 'Channel', 'Status']] = [u_id, u_ch, u_st]
                        save_data(st.session_state.agent_db, AGENT_FILE); st.rerun()
        with t3:
            st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- QA AUDIT ENTRY (DEMARK REASON ADDED) ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        sel_ch = st.selectbox("1. Channel First", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            ag_nm = c1.selectbox("2. Agent Name", [""] + active_agents['Name'].tolist())
            eid = active_agents[active_agents['Name'] == ag_nm]['ID'].values[0] if ag_nm else "---"
            c2.info(f"Agent ID: {eid}")
            
            f1, f2, f3 = st.columns(3)
            int_id, int_dt, int_tm = f1.text_input("Interaction ID"), f2.date_input("Date"), f3.text_input("Time (Manual)")
            
            # Parameters with Conditional Reason Box
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
            scores = {}
            for _, row in params.iterrows():
                st.markdown(f'<div class="param-box">{row["Skill_Type"]} | **{row["Parameter"]}** (Max: {row["Max_Score"]})</div>', unsafe_allow_html=True)
                dm = st.checkbox(f"Demark {row['Parameter']}", key=f"dm_{row['Parameter']}")
                
                if dm:
                    reason = st.text_input(f"Reason for Demarking {row['Parameter']}", key=f"reason_{row['Parameter']}")
                    scores[row['Parameter']] = f"0 ({reason})"
                else:
                    scores[row['Parameter']] = row['Max_Score']
            
            if st.form_submit_button("Submit Evaluation"):
                if ag_nm and int_id:
                    # Logic for Soft & Service Skill % (Only taking numeric part)
                    def get_val(v): return 0 if isinstance(v, str) else v
                    
                    soft_p = params[params['Skill_Type'] == 'Soft Skill']
                    serv_p = params[params['Skill_Type'] == 'Service Skill']
                    
                    soft_earned = sum([get_val(scores[p]) for p in soft_p['Parameter'] if p in scores])
                    soft_max = soft_p['Max_Score'].sum()
                    serv_earned = sum([get_val(scores[p]) for p in serv_p['Parameter'] if p in scores])
                    serv_max = serv_p['Max_Score'].sum()
                    
                    entry = {
                        'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Agent Name': ag_nm, 'Employee ID': eid, 'Channel': sel_ch,
                        'Eval_ID': int_id, 'Interaction Date': str(int_dt), 'Interaction Time': int_tm,
                        'Status': 'Pending'
                    }
                    entry.update(scores)
                    entry['Total Score'] = sum([get_val(v) for v in scores.values()])
                    entry['Soft Skill %'] = round((soft_earned/soft_max)*100, 2) if soft_max > 0 else 0
                    entry['Service Skill %'] = round((serv_earned/serv_max)*100, 2) if serv_max > 0 else 0
                    
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE); st.success("Audit submitted with reasons!")

    # --- PUBLISH AUDITS ---
    elif choice == "Publish Audits":
        st.header("📢 Pending Publication")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        if not pending.empty:
            st.dataframe(pending, use_container_width=True)
            if st.button("Publish All Audits", type="primary"):
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()
        else: st.info("No audits pending.")

    # --- AUDIT LOGS & AUDIT VIEW ---
    elif choice in ["Audit Logs", "Audit View"]:
        st.header("📊 Detailed Audit View")
        display_logs = st.session_state.audit_logs.copy()
        if choice == "Audit View":
            display_logs = display_logs[display_logs['Status'] == 'Published']
            
        if not display_logs.empty:
            weeks = ["All"] + sorted(list(display_logs['Week'].unique().astype(str)))
            sel_week = st.selectbox("Filter by Week", weeks)
            if sel_week != "All":
                display_logs = display_logs[display_logs['Week'].astype(str) == sel_week]
            
            emp_search = st.text_input("Filter by Employee ID")
            if emp_search:
                display_logs = display_logs[display_logs['Employee ID'].astype(str).str.contains(emp_search)]

            # Arrange Columns
            base = ['Week', 'Evaluation Date', 'Agent Name', 'Employee ID', 'Channel', 'Eval_ID', 'Interaction Date', 'Interaction Time']
            scores = ['Total Score', 'Soft Skill %', 'Service Skill %', 'Status']
            params_only = [c for c in display_logs.columns if c not in base + scores]
            
            st.dataframe(display_logs[base + params_only + scores], use_container_width=True)
        else:
            st.info("No data available.")

    # --- PARAMETERS ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc, ps = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"]), c2.selectbox("Skill", ["Soft Skill", "Service Skill"])
            pn, pm = st.text_input("Name"), st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[pc, ps, pn, pm]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)
