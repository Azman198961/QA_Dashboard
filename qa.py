import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="Support Quality Tool", layout="wide")

# --- সেশন স্টেট হ্যান্ডলিং ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None

if 'agent_db' not in st.session_state:
    st.session_state.agent_db = pd.DataFrame(columns=['ID', 'Name', 'Gender', 'Contact', 'Channel', 'Status'])

if 'param_db' not in st.session_state:
    st.session_state.param_db = pd.DataFrame(columns=['Channel', 'Skill_Type', 'Parameter', 'Max_Score'])

if 'audit_logs' not in st.session_state:
    # Status কলাম যোগ করা হয়েছে পাবলিশিং ট্র্যাকিংয়ের জন্য
    st.session_state.audit_logs = pd.DataFrame()

# --- লগইন ফাংশন ---
def login():
    st.title("🛡️ Customer Support Quality Tool")
    col1, _ = st.columns([1, 1])
    with col1:
        user_role = st.selectbox("Login as:", ["Select Role", "Admin", "Agent"])
        u_id = st.text_input("User ID (For Agent, enter Employee ID)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == "1234":
                st.session_state.logged_in = True
                st.session_state.role = user_role
                st.session_state.user_id = u_id
                st.rerun()
            else:
                st.error("Invalid Password!")

if not st.session_state.logged_in:
    login()
else:
    # --- মেনু সেটআপ (রোল অনুযায়ী) ---
    if st.session_state.role == "Admin":
        menu = ["Agent Details", "Audit Parameters", "QA Audit Entry", "Publish Audits", "Audit Logs"]
    else:
        menu = ["My Performance"] # এজেন্টের জন্য শুধু পারফরম্যান্স ভিউ
    
    st.sidebar.title(f"Logged in as: {st.session_state.role}")
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    # --- ১. এজেন্ট ডিটেইলস (Admin Only) ---
    if choice == "Agent Details":
        st.header("👥 Agent Management")
        with st.expander("Add New Agent"):
            with st.form("agent_form"):
                col1, col2 = st.columns(2)
                a_id = col1.text_input("Employee ID")
                a_name = col2.text_input("Agent Name")
                a_chan = col2.selectbox("Assigned Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                a_stat = col1.selectbox("Status", ["Active", "Resigned"])
                if st.form_submit_button("Save"):
                    new_agent = pd.DataFrame([[a_id, a_name, "Male", "N/A", a_chan, a_stat]], columns=st.session_state.agent_db.columns)
                    st.session_state.agent_db = pd.concat([st.session_state.agent_db, new_agent]).drop_duplicates(subset=['ID'], keep='last')
                    st.success("Saved!")
        st.dataframe(st.session_state.agent_db, use_container_width=True)

    # --- ২. অডিট প্যারামিটারস (Admin Only) ---
    elif choice == "Audit Parameters":
        st.header("⚙️ Parameters")
        with st.form("p_form"):
            p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            p_skill = st.radio("Skill Category", ["Soft Skill", "Service Skill"])
            p_name = st.text_input("Parameter Name")
            p_score = st.number_input("Max Score", min_value=1, value=10)
            if st.form_submit_button("Add"):
                new_p = pd.DataFrame([[p_chan, p_skill, p_name, p_score]], columns=st.session_state.param_db.columns)
                st.session_state.param_db = pd.concat([st.session_state.param_db, new_p], ignore_index=True)
                st.success("Added!")
        st.dataframe(st.session_state.param_db, use_container_width=True)

    # --- ৩. QA অডিট এন্ট্রি (Admin Only) ---
    elif choice == "QA Audit Entry":
        st.header("📝 Quality Audit Form")
        today = datetime.now()
        current_date = today.strftime("%d %B, %Y")
        current_day = today.strftime("%A")
        
        # সপ্তাহ ক্যালকুলেশন (Sunday starts the week)
        week_num = today.isocalendar()[1] if current_day != "Sunday" else today.isocalendar()[1] + 1
        
        c_date, c_day, c_week = st.columns(3)
        c_date.info(f"📅 **Date:** {current_date}")
        c_day.info(f"⏳ **Day:** {current_day}")
        c_week.success(f"🗓️ **Week Number:** {week_num}")

        if current_day == "Saturday":
            st.warning("⚠️ Today is the last day for this week's Audit!")

        with st.container():
            c1, c2, c3 = st.columns(3)
            evaluator = c1.text_input("Evaluator Name")
            sel_chan = c2.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
            agent_list = st.session_state.agent_db[(st.session_state.agent_db['Channel'] == sel_chan) & (st.session_state.agent_db['Status'] == 'Active')]
            sel_agent = c3.selectbox("Agent Name", ["Select Agent"] + agent_list['Name'].tolist())
            
            emp_id = agent_list[agent_list['Name'] == sel_agent]['ID'].values[0] if sel_agent != "Select Agent" else ""
            f1, f2, f3, f4 = st.columns(4)
            f1.text_input("Employee ID", value=emp_id, disabled=True)
            eval_id = f2.text_input("Call/Chat ID")
            inter_date = f3.date_input("Interaction Date")
            feedback = st.text_area("QA Feedback")

        st.divider()
        params = st.session_state.param_db[st.session_state.param_db['Channel'] == sel_chan]
        if not params.empty:
            audit_scores = {}
            for idx, row in params.iterrows():
                u_key = f"dm_{idx}_{row['Parameter']}"
                if u_key not in st.session_state: st.session_state[u_key] = False
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**{row['Skill_Type']}**: {row['Parameter']}")
                if col_b.button("Demark", key=f"btn_{u_key}"):
                    st.session_state[u_key] = not st.session_state[u_key]
                audit_scores[row['Parameter']] = 0 if st.session_state[u_key] else row['Max_Score']
                col_b.caption(f"Score: {audit_scores[row['Parameter']]}")

            if st.button("Submit Audit", type="primary"):
                entry = {
                    'Week': week_num,
                    'Evaluation Date': datetime.now().strftime("%Y-%m-%d"),
                    'Evaluator Name': evaluator,
                    'Agent Name': sel_agent,
                    'Employee ID': emp_id,
                    'Channel': sel_chan,
                    'Eval_ID': eval_id,
                    'QA Feedback': feedback,
                    'Status': 'Pending'  # ডিফল্ট পেন্ডিং
                }
                entry.update(audit_scores)
                entry['Total Score'] = sum(audit_scores.values())
                new_row = pd.DataFrame([entry])
                st.session_state.audit_logs = pd.concat([st.session_state.audit_logs, new_row], ignore_index=True)
                st.success("Audit Logged as Pending!")

    # --- ৪. পাবলিশ অডিট (Admin Only) ---
    elif choice == "Publish Audits":
        st.header("📢 Review & Publish Audits")
        pending_audits = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
        
        if pending_audits.empty:
            st.info("No pending audits to publish.")
        else:
            st.write(f"Total Pending Audits: {len(pending_audits)}")
            st.dataframe(pending_audits, use_container_width=True)
            
            if st.button("Publish All Pending Audits"):
                st.session_state.audit_logs.loc[st.session_state.audit_logs['Status'] == 'Pending', 'Status'] = 'Published'
                st.success("All audits have been published and are now visible to Agents!")
                st.balloons()

    # --- ৫. অডিট লগ (Admin View) ---
    elif choice == "Audit Logs":
        st.header("📊 Full Audit History")
        st.dataframe(st.session_state.audit_logs, use_container_width=True)

    # --- ৬. এজেন্ট পারফরম্যান্স ভিউ (Agent Only) ---
    elif choice == "My Performance":
        st.header(f"📈 Performance Report for ID: {st.session_state.user_id}")
        # শুধু এই এজেন্টের এবং শুধুমাত্র 'Published' অডিটগুলো দেখাবে
        my_audits = st.session_state.audit_logs[
            (st.session_state.audit_logs['Employee ID'] == st.session_state.user_id) & 
            (st.session_state.audit_logs['Status'] == 'Published')
        ]
        
        if my_audits.empty:
            st.warning("No published audits found for your ID yet.")
        else:
            avg_score = my_audits['Total Score'].mean()
            st.metric("Your Average Score", f"{avg_score:.2f}")
            st.dataframe(my_audits, use_container_width=True)
