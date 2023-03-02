import streamlit as st
import psycopg2
import pandas as pd
# import streamlit_authenticator as stauth
from pathlib import Path
import pickle

st.write(st.experimental_user['email'])
# names = ["Tyler Smith", "Ava"]
# usernames = ["tysmithyyy", "aavvaa"]

# file_path = Path(__file__).parent / "hashed_pw.pkl"
# with file_path.open("rb") as file:
#     hashed_passwords = pickle.load(file)

# authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "budget_app_auth", "budget_app_auth")

# name, authentication_status, username = authenticator.login("Login", "main")

# if authentication_status:
#     authenticator.logout('Logout', 'main')
#     st.write(f'Welcome *{name}*')
#     st.title('Some content')
# elif authentication_status is False:
#     st.error('Username/password is incorrect')
# elif authentication_status is None:
#     st.warning('Please enter your username and password')

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

rows = run_query("SELECT * from userTable;")

# Print results.
for row in rows:
    st.write(f"{row[0]} has a :{row[1]}:")

# SIDEBAR
# authenticator.logout("Logout", "sidebar")
# st.sidebar.title(f"Welcom {name}")
st.sidebar.header("This is the sidebar")