import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. PATHAO BRANDING & STYLE SETUP ---
PATHAO_RED = "#F08080"

style = f"""
<style>
    /* Global Background and Text Color */
    .stApp {{ background-color: {PATHAO_RED}; color: white; }}
    
    /* Font Styling */
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');
    html, body, [class*="st-"] {{ 
        font-family: "Comic Sans MS", "Anek Bangla", sans-serif !important; 
        font-size: 13px; 
    }}
    
    h1 {{ font-size: 20px !important; margin-bottom: 10px; }}
    h2 {{ font-size: 17px !important; }}
    h3 {{ font-size: 15px !important; }}

    /* Input Boxes & Black Background Styling */
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
    
    /* Labels and Help Text */
    label, .stMarkdown p {{ color: white !important; font-weight: bold; }}
    
    /* White Buttons */
    button[kind="primary"] {{ 
        background-color: white !important; 
        color: {PATHAO_RED} !important; 
        border-radius: 4px; 
        font-weight: bold; 
        border: none;
    }}

    /* Very Small Delete Button (Black themed) */
    .stButton > button[key^="del_"] {{
        background-color: #000000 !important; 
        color: white !important; 
        border: 1px solid white !important; 
        padding: 0px 5px !important; 
        font-size: 10px !important; 
        height: 22px !important;
        line-height: 1 !important;
    }}

    /* Parameter Row Styling */
    .param-box {{
        background-color: black; 
        padding: 8px; 
        border-radius: 5px; 
        margin-bottom: 5px; 
        border: 1px solid white;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{ 
        background-color: {PATHAO_RED}; 
        border-right: 1px solid white; 
    }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

# --- 2. DATABASE LOGIC ---
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

# --- 3. SESSION STATE INITIALIZATION ---
agent_cols = ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status']
if 'agent_db' not in st.session_state:
    st.session_state.agent_db = load_data(AGENT_FILE, agent_cols)

if 'param_db' not in st.session_state:
    st.session_state.param_db = load_data(PARAM_FILE, ['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = load_data(AUDIT_FILE, [
        'Week', 'Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 
        'Channel', 'Interaction Date', 'Interaction Time', 'Eval_ID', 'QA Feedback', 'Status', 'Total Score'
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 4. APP LOGIC ---
if not st.session_state.logged_in:
    # Login Page
    st.markdown('<img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" style="width:60px; margin-bottom:10px;">', unsafe_allow_html=True)
    st.title("Pathao Quality Tool")
    with st.form("login"):
        role = st.selectbox("Role", ["Admin", "QA", "Agent"])
        u_id = st.text_input("Username/Email")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "1234":
                st.session_state.logged_in, st.session_state.role, st.session_state.user_id = True, role, u_id
                st.rerun()
            else: st.error("Wrong Password")
else:
    # Sidebar Navigation
    st.sidebar.markdown('<img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" style="width:40px;">', unsafe_allow_html=True)
    st.sidebar.info(f"User: {st.session_state.user_id} ({st.session_state.role})")
    
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

    # --- AGENT DETAILS SECTION ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        tab1, tab2, tab3 = st.tabs(["Add New Agent", "Update Existing Agent", "Agent List"])
        
        with tab1:
            with st.form("add_agent_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                new_id = c1.text_input("Employee ID")
                new_name = c2.text_input("Agent Name")
                new_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                new_stat = c2.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save New Agent", type="primary"):
                    if new_id and new_name:
                        st.session_state.agent_db.loc[len(st.session_state.agent_db)] = [new_id, new_name, "Male", "N/A", "N/A", new_chan, new_stat]
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success("Agent added!")
                        st.rerun()

        with tab2:
            agent_ids = st.session_state.agent_db['ID'].astype(str).tolist()
            selected_id = st.selectbox("Select Agent ID to Update", [""] + agent_ids)
            if selected_id:
                agent_info = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == selected_id].iloc[0]
                with st.form("update_agent"):
                    u_name = st.text_input("Name", value=agent_info['Name'])
                    u_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(agent_info['Channel']))
                    u_stat = st.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(agent_info['Status']))
                    if st.form_submit_button("Update Info"):
                        idx = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == selected_id].index[0]
                        st.session_state.agent_db.loc[idx, ['Name', 'Channel', 'Status']] = [u_name, u_chan, u_stat]
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success("Updated!")
                        st.rerun()

        with tab3:
            st.subheader("Master Agent List")
            # Channel Filter
            list_filter = st.selectbox("Filter by Channel", ["All"] + ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            display_df = st.session_state.agent_db if list_filter == "All" else st.session_state.agent_db[st.session_state.agent_db['Channel'] == list_filter]
            
            for i, row in display_df.iterrows():
                col1, col2, col3 = st.columns([1, 6, 1])
                col1.write(f"**{row['ID']}**")
                col2.write(f"{row['Name']} ({row['Channel']}) - {row['Status']}")
                if col3.button("🗑️", key=f"del_{row['ID']}"): # Small delete button
                    st.session_state.agent_db = st.session_state.agent_db.drop(i)
                    save_data(st.session_state.agent_db, AGENT_FILE)
                    st.rerun()
                st.divider()

    # --- QA AUDIT ENTRY SECTION ---
    elif choice == "QA Audit Entry":
        st.header("📝 QA Audit Entry")
        with st.form("audit_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            # 1. Channel Select
            sel_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            
            # 2. Dynamic Agent List based on Channel
            filtered_agents = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
            sel_agent = c2.selectbox("Agent Name", ["Select Agent"] + filtered_agents['Name'].tolist())
            
            # 3. Auto Employee ID
            emp_id = filtered_agents[filtered_agents['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""
            c3.info(f"Emp ID: {emp_id}")
            
            f1, f2, f3 = st.columns(3)
            eval_id = f1.text_input("Interaction ID")
            inter_date = f2.date_input("Interaction Date")
            inter_time = f3.text_input("Interaction Time (e.g. 11:30 AM)") # Manual Time Input
            
            feedback = st.text_area("QA Feedback")
            st.divider()
            
            # Parameters Scoring
            params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
            audit_scores = {}
            for idx, row in params.iterrows():
                st.markdown(f'<div class="param-box"><span style="color:{PATHAO_RED};">{row["Parameter"]} ({row["Max_Score"]})</span></div>', unsafe_allow_html=True)
                is_demarked = st.checkbox(f"Demark", key=f"dm_{idx}")
                audit_scores[row['Parameter']] = 0 if is_demarked else row['Max_Score']

            if st.form_submit_button("Submit Audit", type="primary"):
                if sel_agent != "Select Agent" and eval_id:
                    entry = {
                        'Week': datetime.now().isocalendar()[1], 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': st.session_state.user_id, 'Agent Name': sel_agent, 'Employee ID': emp_id,
                        'Channel': sel_chan, 'Interaction Date': str(inter_date), 'Interaction Time': inter_time,
                        'Eval_ID': eval_id, 'QA Feedback': feedback, 'Status': 'Pending', 'Total Score': sum(audit_scores.values())
                    }
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Audit Recorded!")
                    st.rerun()
                else: st.error("Missing Info!")

    # --- AUDIT PARAMETERS SECTION ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameter Setup")
        with st.form("p_form", clear_on_submit=True):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add Parameter"):
                st.session_state.param_db.loc[len(st.session_state.param_db)] = [p_chan, "Skill", p_name, p_score]
                save_data(st.session_state.param_db, PARAM_FILE); st.rerun()
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- PUBLISH & LOGS ---
    elif choice == "Publish Audits":
        st.header("📢 Publish Hub")
        pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        st.dataframe(pending, use_container_width=True)
        if not pending.empty and st.button("Publish All", type="primary"):
            st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
            save_data(st.session_state.audit_logs, AUDIT_FILE); st.rerun()

    elif choice == "Audit Logs":
        st.header("📋 Master Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
