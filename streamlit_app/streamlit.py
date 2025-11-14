import streamlit as st
import requests
from PIL import Image 


BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="INMAR set up", layout="centered")


#------------authentication set up---------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "token" not in st.session_state:
    st.session_state.token = None

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

# -----------------Function def----------
def go_home():
    st.session_state.page = "home"

def go_login():
    st.session_state.page = "login"

def go_register():
    st.session_state.page = "register"
#-----------------home set up----------------------
if st.session_state.page == "home" and not st.session_state.is_logged_in:
    st.title(" INMAR Authentication Portal")
    st.info("New User? Please register to login.")

    col1, col2 = st.columns(2)

    with col1:
        st.button(" Login", on_click=go_login)
    with col2:
        st.button(" Register", on_click=go_register)
#-------------login set up--------------------------

elif st.session_state.page == "login" and not st.session_state.is_logged_in:
    st.header(" Login to Your Account")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        payload = {"email": email, "password": password}

        try:
            res = requests.post(f"{BASE_URL}/users/login", data=payload)
            
            if res.status_code == 200:
                data = res.json()
                st.success(data["message"])

                st.session_state.token = data["access_token"]
                st.session_state.user_email = data["email"]
                st.session_state.is_logged_in = True
                st.session_state.page = "dashboard"

            else:
                st.error(res.json().get("detail"))

        except Exception as e:
            st.error(f"Error: {e}")

    st.button(" Back", on_click=go_home)

#------------register set up ----------------------
elif st.session_state.page == "register" and not st.session_state.is_logged_in:
    st.header(" Register New User")

    username = st.text_input("Username")
    email = st.text_input("Email")
    contact = st.text_input("Contact Number")
    role = st.selectbox("Role", ["admin", "user"])
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "contact_number": contact,
            "role": role
        }

        try:
            res = requests.post(f"{BASE_URL}/users/register", json=payload)
            if res.status_code == 201:
                st.success("Registration successful! You can now login.")
            else:
                st.error(res.json().get("detail"))

        except Exception as e:
            st.error(f"Error: {e}")

    st.button(" Back", on_click=go_home)
#----------------------------------------------------------------------
# -----------Login dashboard----------------
elif st.session_state.is_logged_in:
    st.title(" Welcome to INMAR Dashboard")
    st.success(f"Logged in as: {st.session_state.user_email}")
    img = Image.open("dodge.jpg") 
    st.image(img, width=1000, onclick=None)

    if st.button("Logout"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            res = requests.post(f"{BASE_URL}/users/logout", headers=headers)

            if res.status_code == 200:
                st.success("Logout successful!")
                st.session_state.is_logged_in = False
                st.session_state.token = None
                st.session_state.page = "home"
            else:
                st.error(res.json().get("detail"))

        except Exception as e:
            st.error(f"Error: {e}")
# ------------------------------------------------