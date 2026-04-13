import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- custom pathao style inject ---
PATHAO_RED = "#F08080"

style = f"""
<style>
    .stApp {{ background-color: {PATHAO_RED}; color: white; }}
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');
    html, body, [class*="st-"] {{ font-family: "Comic Sans MS", "Anek Bangla", sans-serif !important; font-size: 13px; }}
    h1 {{ font-size: 20px !important; margin-bottom: 8px; }}
    h2 {{ font-size: 16px !important; }}
    h3 {{ font-size: 14px !important; }}

    /* Input & Table Styling */
    div[data-baseweb="select"] > div, .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {{
        background-color: #000000 !important; color: {PATHAO_RED} !important; border: 1px solid white !important; font-size: 13px !important;
    }}
    label, .stMarkdown p {{ color: white !important; }}
    
    /* Buttons */
    button[kind="primary"] {{ background-color: white !important; color: {PATHAO_RED} !important; border-radius: 4px; font-weight: bold; }}
    
    /* Custom Delete Button Style */
    .stButton > button[key^="del_"] {{
        background-color: #000000 !important; color: white !important; border: 1px solid white !important; padding: 2px 10px !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: {PATHAO_RED}; border-right: 1px solid white; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
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
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
if 'agent_db' not in st.session_state:
    st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)
if 'param_db' not in st.session_state:
    st.session_state.param_db = load_data(PARAM_FILE, ['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = load_data(AUDIT_FILE, ['Week', 'Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 'Channel', 'Interaction Date', 'Eval_ID', 'QA Feedback', 'Status', 'Total Score'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- APP LOGIC ---
if not st.session_state.logged_in:
    st.title("Pathao Quality Tool Login")
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        u_id = st.text_input("Username/Email")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "1234":
                st.session_state.logged_in, st.session_state.role, st.session_state.user_id = True, role, u_id
                st.rerun()
else:
    # Sidebar
    st.sidebar.info(f"{st.session_state.role}: {st.session_state.user_id}")
    menu = ["Agent Details", "Audit Parameters", "Audit Logs"] if st.session_state.role == "Admin" else ["QA Audit Entry", "Publish Audits", "Audit Logs"]
    choice = st.sidebar.selectbox("Navigation", menu)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- AGENT DETAILS (With Delete Feature) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        tab1, tab2, tab3 = st.tabs(["Add New Agent", "Update Existing Agent", "Agent List"])
        
        with tab1:
            with st.form("add_agent_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                new_id = c1.text_input("Employee ID")
                new_name = c2.text_input("Agent Name")
                new_gen = c1.selectbox("Gender", ["Male", "Female", "Other"])
                new_con = c2.text_input("Contact Number")
                new_emg = c1.text_input("Emergency Contact")
                new_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                new_stat = c1.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save New Agent", type="primary"):
                    if new_id and new_name:
                        new_data = [new_id, new_name, new_gen, new_con, new_emg, new_chan, new_stat]
                        st.session_state.agent_db.loc[len(st.session_state.agent_db)] = new_data
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success("Agent Added!")
                        st.rerun()

        with tab2:
            agent_ids = st.session_state.agent_db['ID'].astype(str).tolist()
            selected_id = st.selectbox("Select Agent ID to Update", [""] + agent_ids)
            if selected_id:
                agent_info = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == selected_id].iloc[0]
                with st.form("update_agent_form"):
                    c1, c2 = st.columns(2)
                    u_name = c1.text_input("Name", value=agent_info['Name'])
                    u_gen = c2.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(agent_info['Gender']))
                    u_con = c1.text_input("Contact", value=agent_info['Contact'])
                    u_emg = c2.text_input("Emergency Contact", value=agent_info['Emergency_Contact'])
                    u_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(agent_info['Channel']))
                    u_stat = c2.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(agent_info['Status']))
                    if st.form_submit_button("Update Agent Information", type="primary"):
                        idx = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == selected_id].index[0]
                        st.session_state.agent_db.loc[idx] = [selected_id, u_name, u_gen, u_con, u_emg, u_chan, u_stat]
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success("Updated!")
                        st.rerun()

        with tab3:
            st.subheader("Master Agent List")
            # টেবিল ফরম্যাটে ডিলিট বাটন দেখানো
            for i, row in st.session_state.agent_db.iterrows():
                col1, col2, col3 = st.columns([1, 6, 2])
                col1.write(f"**{row['ID']}**")
                col2.write(f"{row['Name']} ({row['Channel']}) - {row['Status']}")
                
                # Delete button with confirmation
                if col3.button(f"🗑️ Delete", key=f"del_{row['ID']}"):
                    st.session_state.agent_db = st.session_state.agent_db.drop(i)
                    save_data(st.session_state.agent_db, AGENT_FILE)
                    st.warning(f"Agent {row['Name']} removed.")
                    st.rerun()
                st.divider()

    # --- ২. AUDIT PARAMETERS ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameter Setup")
        with st.form("p_form", clear_on_submit=True):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add Parameter"):
                st.session_state.param_db.loc[len(st.session_state.param_db)] = [p_chan, "Skill", p_name, p_score]
                save_data(st.session_state.param_db, PARAM_FILE)
                st.success("Added!")
                st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA AUDIT ENTRY ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        today = datetime.now()
        week_num = today.isocalendar()[1] if today.strftime("%A") != "Sunday" else today.isocalendar()[1] + 1
        
        with st.form("audit_entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            sel_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
            sel_agent = c2.selectbox("Agent Name", ["Select Agent"] + agent_list['Name'].tolist())
            eval_id = c3.text_input("Call/Chat ID")
            
            emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""
            
            f1, f2 = st.columns(2)
            f1.info(f"ID: {emp_id}")
            inter_date = f2.date_input("Interaction Date")
            feedback = st.text_area("QA Feedback")

            st.divider()
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
            audit_scores = {}
            for idx, row in params.iterrows():
                is_demarked = st.checkbox(f"Demark: {row['Parameter']} (Max: {row['Max_Score']})", key=f"dm_{idx}")
                audit_scores[row['Parameter']] = 0 if is_demarked else row['Max_Score']

            if st.form_submit_button("Submit Audit", type="primary"):
                if sel_agent != "Select Agent" and eval_id:
                    entry = {'Week': week_num, 'Evaluation Date': today.strftime("%Y-%m-%d"), 'Evaluator Name': st.session_state.user_id, 'Agent Name': sel_agent, 'Employee ID': emp_id, 'Channel': sel_chan, 'Interaction Date': str(inter_date), 'Eval_ID': eval_id, 'QA Feedback': feedback, 'Status': 'Pending', 'Total Score': sum(audit_scores.values())}
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Submitted!")
                    st.rerun()

    # --- ৪. PUBLISH AUDITS ---
    elif choice == "Publish Audits":
        st.header("📢 Publish Audits")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending, use_container_width=True)
        if not pending.empty and st.button("Publish All", type="primary"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE)
            st.success("Published!")
            st.rerun()

    # --- 5. AUDIT LOGS ---
    elif choice == "Audit Logs":
        st.header("📋 Master Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
