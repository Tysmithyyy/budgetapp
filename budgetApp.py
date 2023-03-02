import streamlit as st
import psycopg2
import pandas as pd
# import streamlit_authenticator as stauth
from pathlib import Path
import pickle


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()
    
@st.cache_data(ttl=600)
def run_command(command):
    with conn.cursor() as cur:
        cur.execute(command)
        conn.commit()

st.title("Smith Budgets")
useremail = st.experimental_user['email']

users = run_query("SELECT * FROM public.userstable")
user_email_list =  []
for row in users:
    user_email_list.append(row[0])

if useremail not in user_email_list:
    st.write("Looks like you're new here!")
    st.write("What is your name?")
    new_user_name = st.text_input("Name")
    if st.button("Sign me up!"):
        command = (f"INSERT INTO userstable (email, name) VALUES ('{useremail}', '{new_user_name}')")
        run_command(command) 
        users = run_query("SELECT * FROM userstable")
        for row in users:
            user_email_list.append(row[0])

if useremail in user_email_list:
    st.write(f"Welcome!")
    budgets = run_query("SELECT * from budgettable;")

    st.subheader("Which budget do you want to look at?")

    col1, col2 = st.columns(2)

    with col1:
        budget_names = []
        for row in budgets:
            budget_names.append(row[0])
        budget_name = st.selectbox("Budgets", budget_names)
    with col2:
        st.header("Or...")
        st.subheader("Create New Budget")
        new_budget_name = st.text_input("New Budget Name")
        new_budget_allotment = st.number_input("New Budget Allotment")
        if st.button("Save New Budget"):
            run_command(f"INSERT INTO public.budgettable (budgetname, email, budgetallotment) VALUES ('{new_budget_name}', '{useremail}', '{new_budget_allotment}')")

    # INSERT INTO films (code, title, did, date_prod, kind)
    #     VALUES ('T_601', 'Yojimbo', 106, '1961-06-16', 'Drama');


    st.subheader(budget_name)
    tab1, tab2, tab3 = st.tabs(["View Budget", "Add Transaction", "Budget Settings"])

    with tab1:
        st.header("View Budget")
        budget_df = pd.read_sql(f"SELECT * FROM transactionTable WHERE budgetName = '{budget_name}'", conn)

    with tab2:
        st.header("Add Transaction")
        new_transaction_date = st.date_input("Transaction Date")
        new_transaction_ammount = st.number_input("Transaction Ammount",step=0.1)
        new_transaction_note = st.text_area("Note/Description", "input note here", 2)
        st.button("Add Transaction")

    with tab3:
        st.header("Budget Settings")
    # SIDEBAR
    # authenticator.logout("Logout", "sidebar")
    # st.sidebar.title(f"Welcom {name}")
    # st.sidebar.header("This is the sidebar")
    # st.sidebar.sub