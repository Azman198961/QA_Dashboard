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
    .stButton > button {{ background-color: black !important; color: white !important; border: 1px solid white !important; }}
    .param-box {{ background-color: black; padding: 8px; border-radius: 5px; border: 1px solid white; margin-bottom: 5px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA CONSTANTS ---
AGENT_FILE, PARAM_FILE, AUDIT_FILE = "agents.csv", "parameters.csv", "audit_logs.csv"
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
param_cols = ['Channel', 'Skill_Type', 'Parameter', 'Max_Score']

# --- 3. DATABASE FUNCTIONS ---
def load_data(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df if not df.empty else pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# Initialize Session States
if 'agent_db' not in st.session_state: st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state: st.session_state.param_db = load_data(PARAM_FILE, param_cols)
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = load_data(AUDIT_FILE, [])
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.title("Pathao Quality Portal")
    with st.form("login_form"):
        role = st.selectbox("Login Role", ["Admin", "QA", "Agent"])
        
        # Dynamic Agent Selection for Login
        selected_agent_name = ""
        if role == "Agent":
            l_ch = st.selectbox("Select Your Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            ag_list = st.session_state.agent_db[st.session_state.agent_db['Channel'] == l_ch]['Name'].tolist()
            selected_agent_name = st.selectbox("Select Your Name", ag_list)
            u_id = st.text_input("Username (Optional for Agents)")
        else:
            u_id = st.text_input("Username/ID")
            
        pwd = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", type="primary"):
            if pwd == "1234":
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.user_id = selected_agent_name if role == "Agent" else u_id
                st.rerun()
            else: st.error("Invalid Credentials")

# --- 5. MAIN APPLICATION ---
else:
    st.sidebar.info(f"Welcome, {st.session_state.user_id} ({st.session_state.role})")
    nav = {
        "Admin": ["Agent Details", "Audit Parameters", "Audit Logs"],
        "QA": ["QA Audit Entry", "Publish Audits", "Audit Logs"],
        "Agent": ["My Audits"]
    }
    choice = st.sidebar.selectbox("Navigation", nav[st.session_state.role])
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()

    # --- AGENT DETAILS (Admin) ---
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
                    new_row = pd.DataFrame([[n_id, n_name, n_gen, n_con, n_emg, n_chan, n_stat]], columns=agent_cols)
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_row], ignore_index=True)
                    save_data(st.session_state.agent_db, AGENT_FILE)
                    st.success("Agent Saved!")
        with t2:
            up_name = st.selectbox("Select Agent to Update", [""] + st.session_state.agent_db['Name'].tolist())
            if up_name:
                curr = st.session_state.agent_db[st.session_state.agent_db['Name'] == up_name].iloc[0]
                with st.form("up_ag"):
                    u_id = st.text_input("ID", value=curr['ID'])
                    u_ch = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(curr['Channel']))
                    u_st = st.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(curr['Status']))
                    if st.form_submit_button("Update"):
                        idx = st.session_state.agent_db[st.session_state.agent_db['Name'] == up_name].index[0]
                        st.session_state.agent_db.loc[idx, ['ID', 'Channel', 'Status']] = [u_id, u_ch, u_st]
                        save_data(st.session_state.agent_db, AGENT_FILE); st.rerun()
        with t3:
            st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- QA AUDIT ENTRY (QA) ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        q_ch = st.selectbox("Select Channel First", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
        relevant_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == q_ch) & (st.session_state.agent_db['Status'] == 'Active')]
        
        with st.form("audit_form"):
            c1, c2 = st.columns(2)
            ag_name = c1.selectbox("Agent Name", [""] + relevant_agents['Name'].tolist())
            emp_id = relevant_agents[relevant_agents['Name'] == ag_name]['ID'].values[0] if ag_name else "---"
            c2.info(f"ID: {emp_id}")
            
            f1, f2, f3 = st.columns(3)
            i_id, i_dt, i_tm = f1.text_input("Interaction ID"), f2.date_input("Date"), f3.text_input("Time (Manual)")
            feedback = st.text_area("QA Feedback")
            
            # Parameters
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == q_ch]
            scores = {}
            for _, row in params.iterrows():
                st.markdown(f'<div class="param-box">{row["Skill_Type"]} | {row["Parameter"]} ({row["Max_Score"]})</div>', unsafe_allow_html=True)
                dm = st.checkbox("Demark", key=f"dm_{row['Parameter']}")
                scores[row['Parameter']] = 0 if dm else row['Max_Score']
            
            if st.form_submit_button("Submit Audit"):
                if ag_name and i_id:
                    # Logic for Skill Grouping
                    soft_total = sum([scores[p] for p in scores if params[params['Parameter']==p]['Skill_Type'].values[0] == "Soft Skill"])
                    soft_max = sum([params[params['Parameter']==p]['Max_Score'].values[0] for p in scores if params[params['Parameter']==p]['Skill_Type'].values[0] == "Soft Skill"])
                    
                    serv_total = sum([scores[p] for p in scores if params[params['Parameter']==p]['Skill_Type'].values[0] == "Service Skill"])
                    serv_max = sum([params[params['Parameter']==p]['Max_Score'].values[0] for p in scores if params[params['Parameter']==p]['Skill_Type'].values[0] == "Service Skill"])
                    
                    entry = {
                        'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': st.session_state.user_id, 'Agent Name': ag_name, 'Employee ID': emp_id,
                        'Channel': q_ch, 'Interaction Date': str(i_dt), 'Interaction Time': i_tm,
                        'Eval_ID': i_id, 'QA Feedback': feedback, 'Status': 'Pending'
                    }
                    entry.update(scores) # individual marks
                    entry['Total Score'] = sum(scores.values())
                    entry['Soft Skill %'] = round((soft_total/soft_max)*100, 2) if soft_max > 0 else 0
                    entry['Service Skill %'] = round((serv_total/serv_max)*100, 2) if serv_max > 0 else 0
                    
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Audit Submitted for Approval!")

    # --- PUBLISH AUDITS (QA) ---
    elif choice == "Publish Audits":
        st.header("📢 Pending Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        if not pending.empty:
            st.dataframe(pending, use_container_width=True)
            if st.button("Publish All Audits", type="primary"):
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                save_data(st.session_state.audit_logs, AUDIT_FILE)
                st.success("All audits published successfully!")
                st.rerun()
        else:
            st.info("No pending audits to publish.")

    # --- AUDIT LOGS (Admin/QA) ---
    elif choice == "Audit Logs":
        st.header("📋 Master Audit Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    # --- MY AUDITS (Agent) ---
    elif choice == "My Audits":
        st.header(f"📊 Audits for {st.session_state.user_id}")
        # Show only published audits for this agent
        my_data = st.session_state.audit_logs[
            (st.session_state.audit_logs['Agent Name'] == st.session_state.user_id) & 
            (st.session_state.audit_logs['Status'] == 'Published')
        ]
        
        # Filter by Employee ID for the agent
        e_id_search = st.text_input("Filter by Employee ID")
        if e_id_search:
            my_data = my_data[my_data['Employee ID'].astype(str).str.contains(e_id_search)]
            
        st.dataframe(my_data, use_container_width=True)

    # --- PARAMETERS (Admin) ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameter Setup")
        with st.form("p_f"):
            c1, c2 = st.columns(2)
            p_ch = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_sk = c2.selectbox("Skill Type", ["Soft Skill", "Service Skill"])
            p_nm = st.text_input("Parameter Name")
            p_mx = st.number_input("Max Score", min_value=1)
            if st.form_submit_button("Add Parameter"):
                new_p = pd.DataFrame([[p_ch, p_sk, p_nm, p_mx]], columns=param_cols)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.table(st.session_state.param_db)
