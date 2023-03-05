import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Smith Budgets", page_icon=":money_with_wings:", layout="centered", initial_sidebar_state="auto", menu_items=None)

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()
    
def run_command(command):
    with conn.cursor() as cur:
        cur.execute(command)
        conn.commit()

def get_user_email_list():
    users = run_query("SELECT * FROM public.userstable")
    user_email_list =  []
    for row in users:
        user_email_list.append(row[0])
    return user_email_list

useremail = st.experimental_user['email']
user_email_list = get_user_email_list()
st.title(":money_with_wings: Smith Budgets")


if useremail not in user_email_list:
    st.write("Looks like you're new here!")
    st.write("What is your name?")
    new_user_name = st.text_input("Name")
    if st.button("Sign me up!"):
        command = (f"INSERT INTO userstable (email, name) VALUES ('{useremail}', '{new_user_name}')")
        run_command(command) 
        get_user_email_list()

if useremail in user_email_list:

    if 'budget_name' not in st.session_state:
        st.session_state.budget_name = 'Select a Budget'
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "select" not in st.session_state:
        st.session_state.select = False

    budgets = run_query(f"SELECT * from budgettable WHERE email = '{useremail}' OR sharewith = '{useremail}';")
    transactions = run_query("SELECT * from transactiontable")

    def close_select_container():
        if st.session_state.select:
            st.session_state.select = False
    def close_create_container():
        if st.session_state.submitted:
            st.session_state.submitted = False

    create_budget = st.button("Create New Budget", key="create_budget", use_container_width=True)
    select_budget = st.button("Select Budget", key= "select_budget", use_container_width=True)

    if create_budget:
        close_select_container()

    if select_budget or st.session_state.select:
        st.session_state.select = True
        close_create_container()
        with st.container():
            st.subheader("Which budget do you want to look at?")
            budget_names = []
            budget_names.append("Select a Budget")
            for row in budgets:
                budget_names.append(row[0])
            budget_name = st.selectbox("Select Budget", key="budget_name", options=budget_names, index=0, label_visibility="hidden")

    if create_budget or st.session_state.submitted:
        st.session_state.submitted = True
        with st.container():
            with st.form(key="new_budget_form"):
                new_budget_name = st.text_input("New Budget Name")
                new_budget_allotment = st.number_input("New Budget Allotment")
                new_budget_share = st.text_input("Share with anyone? (Enter email here)")
                submit = st.form_submit_button("Save New Budget")
                if submit:
                    run_command(f"INSERT INTO public.budgettable (budgetname, email, budgetallotment, sharewith) VALUES ('{new_budget_name}', '{useremail}', '{new_budget_allotment}', '{new_budget_share}')")
                    st.session_state.budget_name = new_budget_name
                    st.session_state.submitted = False
                    st.session_state.select = True
                    st.experimental_rerun()

    # if select_budget:
    #     st.session_state.submitted = False
    #     with st.container():
    #         st.subheader("Which budget do you want to look at?")
    #         budget_names = []
    #         for row in budgets:
    #             budget_names.append(row[0])
    #         budget_name = st.selectbox("budgets", key="budget_name", options=budget_names)
            

    # INSERT INTO films (code, title, did, date_prod, kind)
    #     VALUES ('T_601', 'Yojimbo', 106, '1961-06-16', 'Drama');


    if st.session_state.budget_name == "Select a Budget":
        st.subheader("Please Create or Select a budget")
    
    else:
        budget_df = pd.read_sql(f"SELECT * FROM transactionTable WHERE budgetName = '{st.session_state.budget_name}'", conn)
        dash_display = budget_df[['transactionid', 'note', 'transactiondate', 'transactionammount']]
        dash_display.rename(columns = {'transactionid':'ID', 'note':'Purchased', 'transactiondate':'Date','transactionammount':'Ammount'}, inplace = True)
        dash_display.set_index('ID', inplace=True)
        budgets_df = pd.read_sql(f"SELECT * from budgettable WHERE email = '{useremail}' OR sharewith = '{useremail}';", conn, index_col='budgetname')
        balance = float(budgets_df.loc[f'{st.session_state.budget_name}', 'budgetallotment'])
        # locale.setlocale(locale.LC_ALL, '')
        # balance_currency = locale.currency(balance, grouping=True)
        balance_currency = '${:,.2f}'.format(balance)
        st.subheader(st.session_state.budget_name)
        tab1, tab2, tab3 = st.tabs(["View Budget", "Add Transaction", "Budget Settings"])

        with tab1:
            st.header("View Budget")
            col1, col2, col3 = st.columns(3)
            col1.metric("Balance", balance_currency)
            st.dataframe(dash_display, use_container_width=True)

        with tab2:
            st.header("Add Transaction")
            transaction_form = st.form("transaction_form", True)
            with transaction_form:
                new_transaction_id = len(transactions) + 1
                new_transaction_date = st.date_input("Transaction Date")
                new_transaction_ammount = st.number_input("Transaction Ammount",step=0.1)
                new_transaction_note = st.text_area("Note/Description", height=2)
                new_budget_allotment = balance - new_transaction_ammount
                if st.form_submit_button("Add Transaction"):
                    run_command(f"INSERT INTO public.transactiontable (transactionid, budgetname, transactionammount, transactiondate, note) \
                                VALUES ('{new_transaction_id}', '{budget_name}', '{new_transaction_ammount}', '{new_transaction_date}', '{new_transaction_note}')")
                    run_command(f"UPDATE budgettable SET budgetallotment = {new_budget_allotment} WHERE budgetname = '{budget_name}'")
                    st.experimental_rerun()

        with tab3:
            st.header("Budget Settings")
            
            col1, col2 = st.columns(2)
        
            with col1:
                st.text_input("Add/Change user to share this budget with")
                if st.button("Share"):
                    run_command(f"UPDATE budgettable SET sharwith = {new_budget_allotment} WHERE budgetname = '{budget_name}'")
            with col2:
                if st.button("Delete Budget", type="primary"):
                    run_command(f"DELETE FROM budgettable WHERE budgetname = '{budget_name}'")
                    st.experimental_rerun()
                if st.button("Reset Budget (Delete all transactions)", type="primary"):
                    run_command(f"DELETE FROM transactiontable WHERE budgetname = '{budget_name}'")
                    st.experimental_rerun()

#     UPDATE employees SET sales_count = sales_count + 1 FROM accounts
#       WHERE accounts.name = 'Acme Corporation'
#       AND employees.id = accounts.sales_person;
