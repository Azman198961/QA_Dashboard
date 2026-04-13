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
    .skill-container {{ background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 2px solid white; margin-bottom: 20px; }}
    .param-row {{ border-bottom: 1px solid #444; padding: 10px 0; }}
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

# --- 4. MAIN APP ---
else:
    st.sidebar.info(f"Role: {st.session_state.role}")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["Audit View"]
    }
    choice = st.sidebar.selectbox("Navigate", nav[st.session_state.role])
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
                if st.form_submit_button("Save"):
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
        with t3: st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- QA AUDIT ENTRY (FIXED LAYOUT & DEMARK) ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        sel_ch = st.selectbox("1. Select Channel First", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        active_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        # Initial Info Section
        c1, c2 = st.columns(2)
        ag_nm = c1.selectbox("2. Agent Name", [""] + active_agents['Name'].tolist())
        eid = active_agents[active_agents['Name'] == ag_nm]['ID'].values[0] if ag_nm else "---"
        c2.info(f"ID: {eid}")
        
        f1, f2, f3 = st.columns(3)
        int_id, int_dt, int_tm = f1.text_input("Interaction ID"), f2.date_input("Date"), f3.text_input("Time (Manual)")

        # Prepare Scoring Storage
        scores = {}
        all_params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_ch]

        # SEPARATE SECTIONS FOR SKILLS
        for skill_type in ["Soft Skill", "Service Skill"]:
            st.markdown(f'<div class="skill-container"><h3>{skill_type} Section</h3>', unsafe_allow_html=True)
            skill_params = all_params[all_params['Skill_Type'] == skill_type]
            
            if skill_params.empty:
                st.write("No parameters added for this skill.")
            else:
                for _, row in skill_params.iterrows():
                    p_name = row['Parameter']
                    p_max = row['Max_Score']
                    
                    st.markdown(f'<div class="param-row">', unsafe_allow_html=True)
                    cols = st.columns([4, 2, 4])
                    cols[0].write(f"**{p_name}** (Max: {p_max})")
                    is_demark = cols[1].checkbox("Demark", key=f"dm_{p_name}")
                    
                    if is_demark:
                        reason = cols[2].text_input("Demark Reason", key=f"res_{p_name}")
                        scores[p_name] = f"0 ({reason})"
                    else:
                        scores[p_name] = p_max
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Submit Audit Report", type="primary"):
            if ag_nm and int_id:
                # Calc Weightage
                def clean_val(v): return 0 if isinstance(v, str) else v
                
                soft_list = all_params[all_params['Skill_Type'] == 'Soft Skill']['Parameter'].tolist()
                serv_list = all_params[all_params['Skill_Type'] == 'Service Skill']['Parameter'].tolist()
                
                sft_earned = sum([clean_val(scores[p]) for p in soft_list if p in scores])
                sft_max = all_params[all_params['Skill_Type'] == 'Soft Skill']['Max_Score'].sum()
                srv_earned = sum([clean_val(scores[p]) for p in serv_list if p in scores])
                srv_max = all_params[all_params['Skill_Type'] == 'Service Skill']['Max_Score'].sum()
                
                entry = {
                    'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                    'Agent Name': ag_nm, 'Employee ID': eid, 'Channel': sel_ch,
                    'Eval_ID': int_id, 'Interaction Date': str(int_dt), 'Interaction Time': int_tm,
                    'Status': 'Pending'
                }
                entry.update(scores)
                entry['Total Score'] = sum([clean_val(v) for v in scores.values()])
                entry['Soft Skill %'] = round((sft_earned/sft_max)*100, 2) if sft_max > 0 else 0
                entry['Service Skill %'] = round((srv_earned/srv_max)*100, 2) if srv_max > 0 else 0
                
                st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                save_data(st.session_state.audit_logs, AUDIT_FILE)
                st.success("Evaluation Saved!")
                st.rerun()

    # --- PUBLISH AUDITS ---
    elif choice == "Publish Audits":
        st.header("📢 Pending Publications")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        if not pending.empty:
            st.dataframe(pending)
            if st.button("Publish All", type="primary"):
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()
        else: st.info("Clear!")

    # --- AUDIT LOGS & AUDIT VIEW ---
    elif choice in ["Audit Logs", "Audit View"]:
        st.header("📊 Detailed Audit View")
        logs = st.session_state.audit_logs.copy()
        if choice == "Audit View": logs = logs[logs['Status'] == 'Published']
        
        if not logs.empty:
            weeks = ["All"] + sorted(list(logs['Week'].unique().astype(str)))
            sel_week = st.selectbox("Week Filter", weeks)
            if sel_week != "All": logs = logs[logs['Week'].astype(str) == sel_week]
            
            # Reorder
            base = ['Week', 'Evaluation Date', 'Agent Name', 'Employee ID', 'Channel', 'Eval_ID', 'Interaction Date', 'Interaction Time']
            results = ['Total Score', 'Soft Skill %', 'Service Skill %', 'Status']
            params_cols = [c for c in logs.columns if c not in base + results]
            st.dataframe(logs[base + params_cols + results], use_container_width=True)

    # --- PARAMETERS SETUP ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters Setup")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            pc = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            ps = c2.selectbox("Skill Group", ["Soft Skill", "Service Skill"])
            pn = st.text_input("Parameter Name")
            pm = st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[pc, ps, pn, pm]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)
