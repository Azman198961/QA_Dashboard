import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Support Quality Tool", layout="wide")

# --- ডাটাবেস ফাইল পাথ ---
AGENT_FILE = "agents.csv"
PARAM_FILE = "parameters.csv"
AUDIT_FILE = "audit_logs.csv"

# --- ডাটা লোড ও সেভ ফাংশন ---
def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- সেশন স্টেট হ্যান্ডলিং ---
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

# --- লগইন ফাংশন ---
def login():
    st.title("🛡️ Customer Support Quality Tool")
    col1, _ = st.columns([1, 1])
    with col1:
        user_role = st.selectbox("Login as:", ["Select Role", "Admin", "QA", "Agent"])
        
        if user_role == "QA":
            u_id = st.text_input("Email Address (Auditor Email)")
        elif user_role == "Agent":
            u_id = st.text_input("Employee ID")
        else:
            u_id = st.text_input("Username")

        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == "1234":
                if user_role == "Select Role" or not u_id:
                    st.error("Please provide valid credentials!")
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
    # রোল অনুযায়ী মেনু
    if st.session_state.role == "Admin":
        menu = ["Agent Details", "Audit Parameters", "Audit Logs"]
    elif st.session_state.role == "QA":
        menu = ["QA Audit Entry", "Publish Audits", "Audit Logs"]
    else:
        menu = ["My Performance"]
    
    st.sidebar.title(f"Role: {st.session_state.role}")
    st.sidebar.info(f"User: {st.session_state.user_id}")
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- ১. এজেন্ট ডিটেইলস (Admin) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        tab1, tab2 = st.tabs(["Add/Update Agent", "View Agent List"])
        with tab1:
            existing_agents = st.session_state.agent_db['ID'].astype(str).tolist()
            edit_id = st.selectbox("Select Agent ID to Update (or leave empty for New)", [""] + existing_agents)
            
            if edit_id:
                agent_data = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == edit_id].iloc[0]
                d_name, d_gen, d_con, d_emg, d_chan, d_stat = agent_data['Name'], agent_data['Gender'], agent_data['Contact'], agent_data['Emergency_Contact'], agent_data['Channel'], agent_data['Status']
                btn_label = "Update Agent"
            else:
                d_name, d_gen, d_con, d_emg, d_chan, d_stat = "", "Male", "", "", "Inbound", "Active"
                btn_label = "Save Agent"

            with st.form("agent_form"):
                c1, c2 = st.columns(2)
                a_id = c1.text_input("Employee ID", value=edit_id if edit_id else "")
                a_name = c2.text_input("Agent Name", value=d_name)
                a_gen = c1.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(d_gen))
                a_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"], index=["Inbound", "Live Chat", "Report Issue", "Complaint Management"].index(d_chan))
                a_stat = c1.selectbox("Status", ["Active", "Resigned"], index=["Active", "Resigned"].index(d_stat))
                
                if st.form_submit_button(btn_label):
                    new_entry = [a_id, a_name, a_gen, "N/A", "N/A", a_chan, a_stat]
                    if edit_id:
                        st.session_state.agent_db.loc[st.session_state.agent_db['ID'].astype(str) == edit_id] = new_entry
                    else:
                        st.session_state.agent_db.loc[len(st.session_state.agent_db)] = new_entry
                    save_data(st.session_state.agent_db, AGENT_FILE)
                    st.success("Success!")
                    st.rerun()
        with tab2:
            st.dataframe(st.session_state.agent_db)

    # --- ২. অডিট প্যারামিটারস (Admin) ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Audit Parameters")
        with st.form("p_form"):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_skill = st.radio("Skill", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add"):
                st.session_state.param_db.loc[len(st.session_state.param_db)] = [p_chan, p_skill, p_name, p_score]
                save_data(st.session_state.param_db, PARAM_FILE)
                st.rerun()
        st.dataframe(st.session_state.param_db)

    # --- ৩. QA অডিট এন্ট্রি (QA Only) ---
    elif choice == "QA Audit Entry":
        st.header("📝 New Quality Audit")
        today = datetime.now()
        week_num = today.isocalendar()[1] if today.strftime("%A") != "Sunday" else today.isocalendar()[1] + 1
        auditor_name = st.session_state.user_id # Email used as name

        st.info(f"Auditor: **{auditor_name}** | Week: **{week_num}**")
        
        with st.container():
            c1, c2, c3 = st.columns(3)
            sel_chan = c1.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
            sel_agent = c2.selectbox("Agent Name", ["Select Agent"] + agent_list['Name'].tolist())
            eval_id = c3.text_input("Call/Chat ID")
            
            emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""
            f1, f2 = st.columns(2)
            inter_date = f1.date_input("Interaction Date")
            feedback = f2.text_area("QA Feedback")

        st.divider()
        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        if params.empty:
            st.warning("No parameters found.")
        else:
            audit_scores = {}
            for idx, row in params.iterrows():
                u_key = f"dm_{idx}"
                if u_key not in st.session_state: st.session_state[u_key] = False
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**{row['Skill_Type']}**: {row['Parameter']}")
                if col_b.button("Demark", key=f"btn_{u_key}"):
                    st.session_state[u_key] = not st.session_state[u_key]
                audit_scores[row['Parameter']] = 0 if st.session_state[u_key] else row['Max_Score']
                col_b.caption(f"Score: {audit_scores[row['Parameter']]}/{row['Max_Score']}")

            if st.button("Submit Audit", type="primary"):
                if sel_agent == "Select Agent" or not eval_id:
                    st.error("Missing Info!")
                else:
                    entry = {
                        'Week': week_num, 'Evaluation Date': today.strftime("%Y-%m-%d"),
                        'Evaluator Name': auditor_name, 'Agent Name': sel_agent, 'Employee ID': emp_id,
                        'Channel': sel_chan, 'Interaction Date': str(inter_date), 'Eval_ID': eval_id,
                        'QA Feedback': feedback, 'Status': 'Pending', 'Total Score': sum(audit_scores.values())
                    }
                    entry.update(audit_scores)
                    st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, pd.DataFrame([entry])], ignore_index=True)
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success("Submitted to Pending List!")
                    st.balloons()

    # --- ৪. পাবলিশ অডিট (সবার ডাটা একসাথে দেখাবে) ---
    elif choice == "Publish Audits":
        st.header("📢 Central Publish Hub (All QA Pending Audits)")
        
        # এখানে 'Evaluator Name' নির্বিশেষে সব Pending অডিট ফিল্টার করা হয়েছে
        all_pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        
        if all_pending.empty:
            st.info("No pending audits found from any QA.")
        else:
            # ইউনিক সপ্তাহ বের করা (যদি মাল্টিপল সপ্তাহের ডাটা থাকে)
            weeks = all_pending['Week'].unique()
            selected_week = st.multiselect("Filter by Week", options=weeks, default=weeks)
            
            display_pending = all_pending[all_pending['Week'].isin(selected_week)]
            
            st.write(f"Showing **{len(display_pending)}** pending audits across all auditors.")
            st.dataframe(display_pending, use_container_width=True)
            
            col1, col2 = st.columns([1, 4])
            if col1.button("Publish All Selected", type="primary"):
                # ইনডেক্স ধরে স্ট্যাটাস আপডেট করা
                indices = display_pending.index
                st.session_state.audit_logs.loc[indices, 'Status'] = 'Published'
                save_data(st.session_state.audit_logs, AUDIT_FILE)
                st.success(f"Successfully published {len(indices)} audits!")
                st.rerun()

    # --- ৫. অডিট লগস ---
    elif choice == "Audit Logs":
        st.header("📋 Master Audit Logs")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    # --- ৬. মাই পারফরম্যান্স ---
    elif choice == "My Performance":
        st.header(f"📈 My Performance ({st.session_state.user_id})")
        my_data = st.session_state.audit_logs[(st.session_state.audit_logs['Employee ID'].astype(str) == str(st.session_state.user_id)) & (st.session_state.audit_logs['Status'] == 'Published')]
        if my_data.empty:
            st.info("No published results.")
        else:
            st.metric("Avg Score", round(my_data['Total Score'].mean(), 2))
            st.dataframe(my_data)
