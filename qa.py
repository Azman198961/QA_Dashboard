import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Support Quality Tool", layout="wide")

# --- ডাটাবেস ফাইল পাথ (পার্মানেন্ট স্টোরেজ) ---
AGENT_FILE = "agents.csv"
PARAM_FILE = "parameters.csv"
AUDIT_FILE = "audit_logs.csv"

# --- ডাটা লোড ও সেভ ফাংশন ---
def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- ৩. সেশন স্টেট হ্যান্ডলিং (পার্মানেন্ট স্টোরেজ থেকে লোড) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None

if 'agent_db' not in st.session_state:
    st.session_state.agent_db = load_data(AGENT_FILE, ['ID', 'Name', 'Gender', 'Contact', 'Emergency_Contact', 'Channel', 'Status'])

if 'param_db' not in st.session_state:
    st.session_state.param_db = load_data(PARAM_FILE, ['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])

if 'audit_logs' not in st.session_state:
    audit_cols = ['Week', 'Evaluation Date', 'Evaluator Name', 'Agent Name', 'Employee ID', 
                  'Channel', 'Interaction Date', 'Eval_ID', 'QA Feedback', 'Status', 'Total Score']
    st.session_state.audit_logs = load_data(AUDIT_FILE, audit_cols)

# --- ৪. লগইন ফাংশন ---
def login():
    st.title("🛡️ Customer Support Quality Tool")
    col1, _ = st.columns([1, 1])
    with col1:
        user_role = st.selectbox("Login as:", ["Select Role", "Admin", "Agent"])
        u_id = st.text_input("User ID (For Agent, enter Employee ID)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == "1234":
                if user_role == "Select Role":
                    st.error("Please select a role!")
                else:
                    st.session_state.logged_in = True
                    st.session_state.role = user_role
                    st.session_state.user_id = u_id
                    st.rerun()
            else:
                st.error("Invalid Password!")

# --- মেইন অ্যাপ লজিক ---
if not st.session_state.logged_in:
    login()
else:
    # রোল অনুযায়ী মেনু ফিল্টার
    if st.session_state.role == "Admin":
        menu = ["Agent Details", "Audit Parameters", "QA Audit Entry", "Publish Audits", "Audit Logs"]
    else:
        menu = ["My Performance"]
    
    st.sidebar.title(f"Logged in as: {st.session_state.role}")
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- ১. এজেন্ট ডিটেইলস (Add/Update/Permanent Save) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        tab1, tab2 = st.tabs(["Add/Update Agent", "View Agent List"])
        
        with tab1:
            st.subheader("Manage Agent Information")
            existing_agents = st.session_state.agent_db['ID'].astype(str).tolist()
            edit_id = st.selectbox("Select Agent ID to Update (or leave empty for New)", [""] + existing_agents)
            
            if edit_id:
                agent_data = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == edit_id].iloc[0]
                default_name = agent_data['Name']
                default_gender = agent_data['Gender']
                default_contact = agent_data['Contact']
                default_emg = agent_data['Emergency_Contact']
                default_chan = agent_data['Channel']
                default_stat = agent_data['Status']
                button_label = "Update Agent Information"
            else:
                default_name, default_gender, default_contact, default_emg, default_chan, default_stat = "", "Male", "", "", "Inbound", "Active"
                button_label = "Save New Agent"

            with st.form("agent_form", clear_on_submit=not edit_id):
                col1, col2 = st.columns(2)
                a_id = col1.text_input("Employee ID", value=edit_id if edit_id else "")
                a_name = col2.text_input("Agent Name", value=default_name)
                
                a_gen = col1.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(default_gender))
                a_con = col2.text_input("Contact Number", value=default_contact)
                
                a_emg = col1.text_input("Emergency Contact Number", value=default_emg)
                a_chan = col2.selectbox("Assigned Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"],
                                       index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(default_chan))
                
                a_stat = col1.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(default_stat))
                
                if st.form_submit_button(button_label):
                    if a_id and a_name:
                        new_data = [a_id, a_name, a_gen, a_con, a_emg, a_chan, a_stat]
                        if edit_id:
                            st.session_state.agent_db.loc[st.session_state.agent_db['ID'].astype(str) == edit_id] = new_data
                        else:
                            st.session_state.agent_db.loc[len(st.session_state.agent_db)] = new_data
                        
                        save_data(st.session_state.agent_db, AGENT_FILE)
                        st.success("Agent data saved successfully!")
                        st.rerun()
                    else:
                        st.error("Employee ID and Name are mandatory!")

        with tab2:
            st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- ২. অডিট প্যারামিটারস ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Audit Parameters Configuration")
        with st.form("p_form"):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_skill = st.radio("Skill Category", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add Parameter"):
                if p_name:
                    st.session_state.param_db.loc[len(st.session_state.param_db)] = [p_chan, p_skill, p_name, p_score]
                    save_data(st.session_state.param_db, PARAM_FILE)
                    st.success(f"Parameter '{p_name}' added!")
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA অডিট এন্ট্রি ---
    elif choice == "QA Audit Entry":
        st.header("📝 Quality Audit Form")
        today = datetime.now()
        current_date = today.strftime("%d %B, %Y")
        current_day = today.strftime("%A")
        week_num = today.isocalendar()[1] if current_day != "Sunday" else today.isocalendar()[1] + 1
        
        c_date, c_day, c_week = st.columns(3)
        c_date.info(f"📅 **Date:** {current_date}")
        c_day.info(f"⏳ **Day:** {current_day}")
        c_week.success(f"🗓️ **Week Number:** {week_num}")

        if current_day == "Saturday":
            st.warning("⚠️ Today is the last day for this week's Audit!")

        st.divider()
        with st.container():
            c1, c2, c3 = st.columns(3)
            evaluator = c1.text_input("Evaluator Name")
            sel_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
            sel_agent = c3.selectbox("Agent Name", ["Select Agent"] + agent_list['Name'].tolist())
            
            emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""
            f1, f2, f3 = st.columns(3)
            f1.text_input("Employee ID", value=emp_id, disabled=True)
            eval_id = f2.text_input("Call/Chat ID")
            inter_date = f3.date_input("Interaction Date")
            feedback = st.text_area("QA Feedback")

        st.divider()
        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        if params.empty:
            st.warning("Please add parameters for this channel first!")
        else:
            audit_scores = {}
            for idx, row in params.iterrows():
                u_key = f"dm_{idx}_{row['Parameter']}"
                if u_key not in st.session_state: st.session_state[u_key] = False
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**{row['Skill_Type']}**: {row['Parameter']} (Max: {row['Max_Score']})")
                if col_b.button("Demark", key=f"btn_{u_key}"):
                    st.session_state[u_key] = not st.session_state[u_key]
                audit_scores[row['Parameter']] = 0 if st.session_state[u_key] else row['Max_Score']
                col_b.caption(f"Score: {audit_scores[row['Parameter']]}")

            if st.button("Submit Audit", type="primary"):
                if not evaluator or sel_agent == "Select Agent" or not eval_id:
                    st.error("Please fill all required fields!")
                else:
                    entry = {
                        'Week': week_num, 'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                        'Evaluator Name': evaluator, 'Agent Name': sel_agent, 'Employee ID': emp_id,
                        'Channel': sel_chan, 'Interaction Date': str(inter_date), 'Eval_ID': eval_id,
                        'QA Feedback': feedback, 'Status': 'Pending', 'Total Score': sum(audit_scores.values())
                    }
                    entry.update(audit_scores)
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Audit submitted successfully!")
                    st.balloons()

    # --- ৪. পাবলিশ অডিট ---
    elif choice == "Publish Audits":
        st.header("📢 Review & Publish Audits")
        if st.session_state.audit_logs.empty:
            st.info("No audits found.")
        else:
            pending_audits = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
            if pending_audits.empty:
                st.info("No pending audits.")
            else:
                st.dataframe(pending_audits, use_container_width=True)
                if st.button("Publish All to Agents", type="primary"):
                    st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Audits published!")
                    st.rerun()

    # --- ৫. অডিট লগ ---
    elif choice == "Audit Logs":
        st.header("📊 Full Audit History")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)
        st.download_button("Download Master CSV", st.session_state.audit_logs.to_csv(index=False), "QA_Master_Report.csv")

    # --- ৬. এজেন্ট পারফরম্যান্স (Agent View) ---
    elif choice == "My Performance":
        st.header(f"📈 My Performance (ID: {st.session_state.user_id})")
        my_audits = st.session_state.audit_logs[(st.session_state.audit_logs['Employee ID'].astype(str) == str(st.session_state.user_id)) & (st.session_state.audit_logs['Status'] == 'Published')]
        if my_audits.empty:
            st.warning("No published audits found.")
        else:
            st.metric("Average Score", f"{my_audits['Total Score'].mean():.2f}")
            st.dataframe(my_audits, use_container_width=True)
