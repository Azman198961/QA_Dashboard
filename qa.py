import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- custom pathao style inject ---
# Define specific Pathao red color shade
PATHAO_RED = "#ED1C24"

# Set up global style using HTML/CSS
style = f"""
<style>
    /* 1. Global Page Background and Text Color */
    .stApp {{
        background-color: #FFFFFF; /* Pure White background */
        color: #000000; /* Primary Text Color: Black */
    }}

    /* 2. Custom Fonts for English and Bengali */
    /* Use English: Comic Sans MS family | Bengali: Anek Bangla family */
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;700&family=Comic+Sans+MS&display=swap');

    html, body, [class*="st-"] {{
        /* Custom Font Stack, targeting English first */
        font-family: "Comic Sans MS", Comic Sans, "Anek Bangla", Arial, sans-serif !important;
    }}

    /* Specific Font for all Bengali Text nodes */
    /* Target via specific Unicode range and Anek Bangla font */
    div, span, p, h1, h2, h3, h4, h5, h6, input, select, textarea {{
        font-family: "Comic Sans MS", Comic Sans, "Anek Bangla", Arial, sans-serif !important;
    }}
    
    /* Ensure Bengali characters use Anek Bangla directly */
    @font-face {{
        font-family: "Anek Bangla";
        src: local("Anek Bangla");
        font-display: swap;
    }}
    
    *:lang(bn) {{
        font-family: "Anek Bangla", sans-serif !important;
    }}

    /* Target specific Bengali Unicode range for bold/normal weight */
    h1, h2, h3, h4, h5, h6 {{ font-weight: 700; }}
    
    /* 3. Primary Red Elements */
    /* Color all primary interactive elements */
    [data-baseweb="button"] > div {{ font-weight: bold; color: {PATHAO_RED} !important; }}
    button[kind="primary"] {{ 
        background-color: {PATHAO_RED} !important; 
        color: white !important; 
        border-color: {PATHAO_RED} !important; 
    }}
    
    /* Input field borders and icons */
    .stTextInput>div>div>input {{ border-color: #E0E0E0; }}
    [data-baseweb="select"] > div {{ border-color: #E0E0E0; }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{ border-color: #4A4A4A; }}

    /* Select box arrow icon */
    [data-baseweb="select"] div[data-baseweb="select__control-icon"] {{ color: {PATHAO_RED}; }}

    /* Red highlights for success/warning */
    .stAlert {{ background-color: #FFF5F5; color: #CC0000; border-color: #FFC0C0; }}
    
    /* Metric label color */
    .stMetric label {{ color: {PATHAO_RED} !important; }}
    .stMetric [data-testid="stMetricValue"] {{ color: black !important; font-weight: bold; }}

    /* Sidebar and Navigation colors */
    [data-testid="stSidebar"] {{ 
        background-color: #F8F9FA; 
        color: black !important;
        border-right: 1px solid #E0E0E0;
    }}
    [data-testid="stSidebar"] h1 {{ color: {PATHAO_RED} !important; }}
    [data-testid="stSidebar"] .stSelectbox label {{ color: {PATHAO_RED} !important; font-weight: bold; }}

    /* Table border color */
    .stDataFrame table {{ border-color: #F0F0F0; }}
    .stDataFrame table tr:nth-child(even) {{ background-color: #F9F9F9; }}
    .stDataFrame table th {{ background-color: #FAFAFA; color: {PATHAO_RED}; }}
    
    /* Main logo section custom container */
    .main-logo-container {{
        display: flex;
        align-items: center;
        padding-bottom: 20px;
        margin-bottom: 20px;
        border-bottom: 1px solid #F0F0F0;
    }}
    
    .logo-img {{
        width: 100px;
        height: auto;
        margin-right: 20px;
    }}
    
    .logo-text {{
        font-size: 24px;
        font-weight: bold;
        color: black;
        font-family: "Comic Sans MS", Comic Sans, Arial, sans-serif !important;
    }}
    
    /* Fix for specific English titles in Sidebar */
    [data-testid="stSidebar"] .main-logo-container h1,
    [data-testid="stSidebar"] .main-logo-container .logo-text {{
        font-family: "Comic Sans MS", Comic Sans, Arial, sans-serif !important;
        color: black !important;
        font-size: 28px !important;
    }}

</style>
"""

# Inject custom styles
st.markdown(style, unsafe_allow_html=True)

# Function to render the main logo and tool name
def render_logo():
    # Load and display logo (using Pathao image reference from user)
    # Define a custom HTML block for logo and text side-by-side
    st.markdown(f'''
    <div class="main-logo-container">
        <img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png/v1/fill/w_400,h_400,al_c,q_85,usm_0.66_1.00_0.01,enc_avif/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" class="logo-img" alt="Pathao Logo">
        <h1 class="logo-text">Quality Tool</h1>
    </div>
    ''', unsafe_allow_html=True)

# Function to render specific title and subtitles for English/Bengali
# This helper ensures the correct fonts are always applied
def custom_title(english, bengali="", title_level="h1"):
    # Target exact fonts
    if bengali:
        st.markdown(f'<{title_level}><span style="font-family: \'Comic Sans MS\', Comic Sans, Arial, sans-serif;">{english}</span> | <span lang="bn" style="font-family: \'Anek Bangla\', sans-serif; color: black;">{bengali}</span></{title_level}>', unsafe_allow_html=True)
    else:
        st.markdown(f'<{title_level}><span style="font-family: \'Comic Sans MS\', Comic Sans, Arial, sans-serif; color: black;">{english}</span></{title_level}>', unsafe_allow_html=True)

# --- DATABASE FILES PATH ---
AGENT_FILE = "agents.csv"
PARAM_FILE = "parameters.csv"
AUDIT_FILE = "audit_logs.csv"

# --- DATA LOAD & SAVE FUNCTIONS ---
def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# --- SESSION STATE HANDLING ---
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

# --- LOGIN FUNCTION ---
def login():
    render_logo()
    
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

# --- MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login()
else:
    # --- SideBar: Logo and Nav ---
    with st.sidebar:
        # custom logo container in sidebar
        st.markdown(f'''
        <div class="main-logo-container">
            <img src="https://static.wixstatic.com/media/252924_6d50ff019be740e599b66059d747d6e6~mv2.png/v1/fill/w_400,h_400,al_c,q_85,usm_0.66_1.00_0.01,enc_avif/252924_6d50ff019be740e599b66059d747d6e6~mv2.png" class="logo-img" alt="Pathao Logo">
            <h1 class="logo-text">Pathao Quality</h1>
        </div>
        ''', unsafe_allow_html=True)
        
        # User Info with custom title component
        custom_title("Role", st.session_state.role, "h3")
        custom_title("User ID", st.session_state.user_id, "h3")
        st.divider()

    # Define menu options based on role
    if st.session_state.role == "Admin":
        menu = ["Agent Details", "Audit Parameters", "Audit Logs"]
    elif st.session_state.role == "QA":
        menu = ["QA Audit Entry", "Publish Audits", "Audit Logs"]
    else:
        menu = ["My Performance"]
    
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Define custom container to manage layout and styles within main view
    with st.container():
        # Add a custom class for styling content and setting the fonts
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        
        # --- ১. এজেন্ট ডিটেইলস (Admin) ---
        if choice == "Agent Details":
            custom_title("👥 Agent Management", "এজেন্ট ম্যানেজমেন্ট", "h1")
            tab1, tab2 = st.tabs(["Add/Update Agent", "View Agent List"])
            with tab1:
                existing_agents = st.session_state.agent_db['ID'].astype(str).tolist()
                edit_id = st.selectbox("Select Agent ID to Update (or leave empty for New)", [""] + existing_agents)
                
                if edit_id:
                    agent_data = st.session_state.agent_db[st.session_state.agent_db['ID'].astype(str) == edit_id].iloc[0]
                    d_name, d_gen, d_chan, d_stat = agent_data['Name'], agent_data['Gender'], agent_data['Channel'], agent_data['Status']
                    btn_label = "Update Agent"
                else:
                    d_name, d_gen, d_chan, d_stat = "", "Male", "Inbound", "Active"
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
                # DataFrame rendering automatically uses the custom styles/fonts
                st.dataframe(st.session_state.agent_db, use_container_width=True)

        # --- ২. অডিট প্যারামিটারস (Admin) ---
        elif choice == "Audit Parameters":
            custom_title("⚙️ Audit Parameters", "অডিট প্যারামিটারস", "h1")
            with st.form("p_form"):
                p_chan = st.selectbox("Channel", ["Inbound", "Live Chat", "Report Issue", "Complaint Management"])
                p_skill = st.radio("Skill", ["Soft Skill", "Service Skill"])
                p_name = st.text_input("Parameter Name")
                p_score = st.number_input("Max Score", min_value=1, value=10)
                if st.form_submit_button("Add Parameter"):
                    st.session_state.param_db.loc[len(st.session_state.param_db)] = [p_chan, p_skill, p_name, p_score]
                    save_data(st.session_state.param_db, PARAM_FILE)
                    st.rerun()
            st.dataframe(st.session_state.param_db, use_container_width=True)

        # --- ৩. QA অডিট এন্ট্রি (QA Only) ---
        elif choice == "QA Audit Entry":
            custom_title("📝 New Quality Audit", "নতুন অডিট এন্ট্রি", "h1")
            today = datetime.now()
            week_num = today.isocalendar()[1] if today.strftime("%A") != "Sunday" else today.isocalendar()[1] + 1
            auditor_name = st.session_state.user_id # Email used as name

            # Use custom_title helper for bilingual header info
            custom_title(f"Auditor: {auditor_name}", f"অডিটর: {auditor_name}", "h3")
            custom_title(f"Week: {week_num}", f"সপ্তাহ: {week_num}", "h3")
            
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
                    
                    # Display bilingual parameter header manually for detailed control
                    st.markdown(f'<div style="font-family: \'Comic Sans MS\', Comic Sans, Arial, sans-serif;"><b>{row["Skill_Type"]}</b>: <span lang="bn" style="font-family: \'Anek Bangla\', sans-serif;">{row["Parameter"]}</span></div>', unsafe_allow_html=True)

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
            custom_title("📢 Central Publish Hub (All QA Pending Audits)", "কেন্দ্রীয় পাবলিশ হাব (পেন্ডিং অডিট)", "h1")
            
            # Filter all Pending audits
            all_pending = st.session_state.audit_logs[st.session_state.audit_logs['Status'] == 'Pending']
            
            if all_pending.empty:
                st.info("No pending audits found from any QA.")
            else:
                weeks = all_pending['Week'].unique()
                selected_week = st.multiselect("Filter by Week", options=weeks, default=weeks)
                
                display_pending = all_pending[all_pending['Week'].isin(selected_week)]
                
                st.write(f"Showing **{len(display_pending)}** pending audits across all auditors.")
                st.dataframe(display_pending, use_container_width=True)
                
                col1, col2 = st.columns([1, 4])
                if col1.button("Publish All Selected", type="primary"):
                    indices = display_pending.index
                    st.session_state.audit_logs.loc[indices, 'Status'] = 'Published'
                    save_data(st.session_state.audit_logs, AUDIT_FILE)
                    st.success(f"Successfully published {len(indices)} audits!")
                    st.rerun()

        # --- ৫. অডিট লগস ---
        elif choice == "Audit Logs":
            custom_title("📋 Master Audit Logs", "মাস্টার অডিট লগস", "h1")
            st.dataframe(st.session_state.audit_logs, use_container_width=True)

        # --- ৬. মাই পারফরম্যান্স ---
        elif choice == "My Performance":
            custom_title(f"📈 My Performance ({st.session_state.user_id})", f"📈 আমার পারফরম্যান্স ({st.session_state.user_id})", "h1")
            my_data = st.session_state.audit_logs[(st.session_state.audit_logs['Employee ID'].astype(str) == str(st.session_state.user_id)) & (st.session_state.audit_logs['Status'] == 'Published')]
            if my_data.empty:
                st.info("No published results found.")
            else:
                st.metric("Avg Score", round(my_data['Total Score'].mean(), 2))
                st.dataframe(my_data, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True) # close content-container div
