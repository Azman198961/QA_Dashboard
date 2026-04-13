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
        background-color: #000000 !important; color: {PATHAO_RED} !important; border: 1px solid white !important; font-size: 12px !important;
    }}
    label, .stMarkdown p {{ color: white !important; font-weight: bold; }}
    button[kind="primary"] {{ background-color: white !important; color: {PATHAO_RED} !important; border-radius: 4px; font-weight: bold; border: none; }}
    
    /* Updated Skill Header Style */
    .skill-header {{ 
        background-color: #1e1e1e; 
        padding: 10px; 
        border-radius: 5px; 
        border: 1px solid white; 
        text-align: center;
        margin-bottom: 15px;
    }}
    .param-row {{ 
        background-color: #2b2b2b; 
        padding: 8px; 
        border-radius: 5px; 
        margin-bottom: 8px; 
        border-left: 4px solid white; 
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA HANDLER ---
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
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.update({"logged_in": True, "role": role})
                st.rerun()
            else: st.error("Wrong Password")
else:
    st.sidebar.info(f"Active Role: {st.session_state.role}")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    choice = st.sidebar.selectbox("Navigate", nav[st.session_state.role])
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- QA AUDIT ENTRY (SIDE-BY-SIDE COMPACT HEADERS) ---
    if choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        sel_ch = st.selectbox("1. Select Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        col_id1, col_id2 = st.columns(2)
        ag_nm = col_id1.selectbox("2. Agent Name", [""] + active_agents['Name'].tolist())
        eid = active_agents[active_agents['Name'] == ag_nm]['ID'].values[0] if ag_nm else "---"
        col_id2.info(f"Agent ID: {eid}")
        
        f1, f2, f3 = st.columns(3)
        int_id, int_dt, int_tm = f1.text_input("Interaction ID"), f2.date_input("Date"), f3.text_input("Time (Manual)")

        st.divider()

        # Side by Side Layout
        left_col, right_col = st.columns(2)
        all_params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]
        scores = {}

        # SOFT SKILL (LEFT)
        with left_col:
            st.markdown('<div class="skill-header"><h3>🛡️ Soft Skill</h3></div>', unsafe_allow_html=True)
            soft_params = all_params[all_params['Skill_Type'] == 'Soft Skill']
            for _, row in soft_params.iterrows():
                st.markdown(f'<div class="param-row"><b>{row["Parameter"]}</b> (Max: {row["Max_Score"]})', unsafe_allow_html=True)
                dm_check = st.checkbox("Demark", key=f"dm_{row['Parameter']}")
                if dm_check:
                    res = st.text_input("Reason", key=f"res_{row['Parameter']}", placeholder="Reason for 0")
                    scores[row['Parameter']] = f"0 ({res})"
                else:
                    scores[row['Parameter']] = row['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        # SERVICE SKILL (RIGHT)
        with right_col:
            st.markdown('<div class="skill-header"><h3>🛠️ Service Skill</h3></div>', unsafe_allow_html=True)
            serv_params = all_params[all_params['Skill_Type'] == 'Service Skill']
            for _, row in serv_params.iterrows():
                st.markdown(f'<div class="param-row"><b>{row["Parameter"]}</b> (Max: {row["Max_Score"]})', unsafe_allow_html=True)
                dm_check = st.checkbox("Demark", key=f"dm_{row['Parameter']}")
                if dm_check:
                    res = st.text_input("Reason", key=f"res_{row['Parameter']}", placeholder="Reason for 0")
                    scores[row['Parameter']] = f"0 ({res})"
                else:
                    scores[row['Parameter']] = row['Max_Score']
                st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Submit Audit Report", type="primary", use_container_width=True):
            if ag_nm and int_id:
                def clean_v(v): return 0 if isinstance(v, str) else v
                sft_earned = sum([clean_v(scores[p]) for p in soft_params['Parameter'] if p in scores])
                sft_max = soft_params['Max_Score'].sum()
                srv_earned = sum([clean_v(scores[p]) for p in serv_params['Parameter'] if p in scores])
                srv_max = serv_params['Max_Score'].sum()
                
                entry = {
                    'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                    'Agent Name': ag_nm, 'Employee ID': eid, 'Channel': sel_ch,
                    'Eval_ID': int_id, 'Interaction Date': str(int_dt), 'Interaction Time': int_tm, 'Status': 'Pending'
                }
                entry.update(scores)
                entry['Total Score'] = sum([clean_v(v) for v in scores.values()])
                entry['Soft Skill %'] = round((sft_earned/sft_max)*100, 2) if sft_max > 0 else 0
                entry['Service Skill %'] = round((srv_earned/srv_max)*100, 2) if srv_max > 0 else 0
                
                st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                save_data(st.session_state.audit_logs, AUDIT_FILE)
                st.success("Audit Recorded!")
                st.rerun()

    # --- Other Sections (Remains Unchanged as per instructions) ---
    elif choice == "Agent Details":
        st.header("👥 Agent Management")
        t1, t2, t3 = st.tabs(["Add Agent", "Update Agent", "Agent List"])
        with t1:
            with st.form("add_ag"):
                c1, c2 = st.columns(2)
                n_id, n_name = c1.text_input("Employee ID"), c2.text_input("Agent Name")
                n_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                n_stat = st.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save"):
                    new_ag = pd.DataFrame([[n_id, n_name, "N/A", "N/A", "N/A", n_chan, n_stat]], columns=agent_cols)
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_ag], ignore_index=True)
                    save_data(st.session_state.agent_db, AGENT_FILE); st.success("Saved!")
        with t3: st.dataframe(st.session_state.agent_db, use_container_width=True)

    elif choice == "Publish Audits":
        st.header("📢 Publish Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending, use_container_width=True)
        if st.button("Publish All"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    elif choice in ["Audit Logs", "Audit View"]:
        st.header("📋 Audit Data")
        df = st.session_state.audit_logs.copy()
        if choice == "Audit View": df = df[df['Status'] == 'Published']
        if not df.empty:
            fixed = ['Week', 'Evaluation Date', 'Agent Name', 'Employee ID', 'Channel', 'Eval_ID', 'Interaction Date', 'Interaction Time']
            end = ['Total Score', 'Soft Skill %', 'Service Skill %', 'Status']
            dyn = [c for c in df.columns if c not in fixed + end]
            st.dataframe(df[fixed + dyn + end], use_container_width=True)

    elif choice == "Audit Parameters":
        st.header("⚙️ Settings")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc, ps = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"]), c2.selectbox("Skill", ["Soft Skill", "Service Skill"])
            pn, pm = st.text_input("Param Name"), st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add"):
                new_p = pd.DataFrame([[pc, ps, pn, pm]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)
