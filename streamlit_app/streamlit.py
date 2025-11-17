import streamlit as st
import requests
from PIL import Image 
from fastapi import HTTPException

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="INMAR set up", layout="centered")


#------------authentication set up---------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "token" not in st.session_state:
    st.session_state.token = None

if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

# -----------------Function def----------
def go_home():
    st.session_state.page = "home"

def go_login():
    st.session_state.page = "login"

def go_register():
    st.session_state.page = "register"

#logout function
def Logout_user():
   
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        res = requests.post(f"{BASE_URL}/users/logout", headers=headers)
        if res.status_code == 200:
                
            st.toast("Logout successful!")
            st.session_state.is_logged_in = False
            st.session_state.token = None
            st.session_state.page = "home"
            st.rerun()               
        else:
            st.error(res.json().get("detail"))

    except Exception as e:
        st.error(f"Logout Error: {e}")
#-----------------------------------templates-----------------------------------------------------------------------------
# creating and updating template functions
def create_template_ui():
    st.header("Create Template")

    Temp_name = st.text_input("Template Name")
    Temp_desc = st.text_area("Template Description")
    created_by = st.text_input("Creator User ID")

    if st.button("Create Template"):
        if not Temp_name or not created_by:
            st.error("Template name and creator ID are required")
            return

        headers = {"Authorization": f"Bearer {st.session_state.token}"}

        payload = {
            "Temp_name": Temp_name,
            "Temp_desc": Temp_desc,
            "created_by": int(created_by)
        }

        try:
            res = requests.post(f"{BASE_URL}/templates/fill",json=payload,headers=headers)

            if res.status_code == 201:
                st.success("Template created successfully!")
            else:
                st.error(res.json().get("detail"))

        except Exception as e:
            st.error(f"Error: {e}")


    # update templates
def update_template_ui():
    try:
        st.header("Update Template")

        headers = {"Authorization": f"Bearer {st.session_state.token}"}

        # fetch template list
        st.subheader(" Update Template Details (Admin Only)")

        # Input fields
        temp_id = st.number_input("Template ID", min_value=1, step=1)
        new_name = st.text_input("New Template Name")
        new_desc = st.text_area("New Template Description")

        # Update Button
        if st.button("Update Template"):
            if not new_name.strip() or not new_desc.strip():
                st.warning("Name and description cannot be empty.")
            else:
                payload = {
                    "name": new_name,
                    "desc": new_desc
                }

                try:
                    # PUT request with query param
                    res = requests.put(f"{BASE_URL}/templates/update_template_details?temp_id={temp_id}",json=payload,headers=headers)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.success(data["message"])
                        st.json(data["data"])
                    else:
                        st.error(res.json().get("detail", "Unknown error"))

                except Exception as e:
                    st.error(f"Streamlit Error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"template error occured for updating: {str(e)}")
def view_templates_ui():
    st.header("viewing Existing Template")
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        res = requests.get(f"{BASE_URL}/list/list_items?template=true",headers=headers)
        data = res.json()

        if res.status_code == 200:
            st.success(f"Templates Loaded: {data['count']}")
            st.table(data["data"])
        else:
            st.error(data.get("detail", "Error occurred"))

    except Exception as e:
        st.error(f"Streamlit Error: {e}")
#-----------------------------------------------------------------------------------------------------------------
#-------------Section function-------------------------------------------------------------------------
def create_section_ui():

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    st.subheader(" Create Section (Admin Only)")

    section_name = st.text_input("Section Name")
    section_desc = st.text_area("Section Description")
    template_id = st.number_input("Template ID", min_value=1, step=1)
    order = st.number_input("Order", min_value=1, step=1)

    if st.button("Create Section"):
        if not section_name.strip() or not section_desc.strip():
            st.warning("Section name and description cannot be empty.")
        else:
            payload = {
                "section_name": section_name,
                "section_desc": section_desc,
                "template_id": template_id,
                "order": order
            }

            try:
                res = requests.post(f"{BASE_URL}/sections/fill_the_section",json=payload,headers=headers)
                if res.status_code == 201:
                    st.success("Section created successfully!")
                    st.json(res.json()["data"])
                elif res.status_code == 400:
                    st.warning(res.json().get("detail"))
                else:
                    st.error(f"Error: {res.text}")

            except Exception as e:
                st.error(f"Streamlit Error/ Request failed: {e}")

def update_section_ui():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    st.subheader("Update_section")
    section_id = st.number_input("Section ID", min_value=1, step=1)
    new_name = st.text_input("New Section Name")
    new_desc = st.text_area("New Section Description")
    if st.button("Update_Section"):


        payload = {
            "name": new_name,
            "desc": new_desc
        }

        try:

            res = requests.put(f"{BASE_URL}/sections/update_section_details?section_id={section_id}",json=payload,headers=headers)
                    
            if res.status_code == 200:
                data = res.json()
                st.success(data["message"])
                st.json(data["data"])
            else:
                st.error(res.json().get("detail", "Unknown error"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"error in updatin:{str(e)}")





#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------

# Admin dashboard function
def admin_dashboard():
    st.info("Admin Dashboard")
    st.success(f"Logged in as ADMIN: {st.session_state.user_email}")

    st.subheader("Admin Menu")

    choice = st.selectbox(
        "Select a template action",
        ["Create Template", "Update Template", "View templates"]
    )

    if choice == "Create Template":
        create_template_ui()
        
    
    elif choice == "Update Template":
        update_template_ui()

    elif choice == "View templates":
        view_templates_ui()
    img = Image.open("dodge.jpg")
    st.image(img, width=1000)

    choice = st.selectbox(
        "Select a Section action",
        ["Create Section", "Update Section", "View Section"]
    )
    if choice == "Create Section":
        create_section_ui()

    if choice == "Update Section":
        update_section_ui()

    if choice == "View Section":
        st.write("View option inum velai seiyala...")



    if st.button("Logout"):
        Logout_user()

# user dashboard function
def user_dashboard():
    st.title("Welcome to Inmar")
    st.success(f"Logged in as USER: {st.session_state.user_email}")
    st.subheader("User Menu")
    img = Image.open("dodge.jpg")
    st.image(img, width=1000)
    if st.button("View templates"):
        view_templates_ui()
    if st.button("Logout"):
        Logout_user()
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
                st.session_state.role = data['role']
                st.session_state.page = "dashboard"
                st.rerun()
                

            else:
                st.error(res.json().get("detail"))

        except Exception as e:
            raise HTTPException(status_code=500, detail= f"Follow back the Error: str{(e)}")

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
                st.toast("Registration successful! You can now login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(res.json().get("detail"))

        except Exception as e:
            st.error(f"Error: {e}")

    st.button(" Back", on_click=go_home)
#----------------------------------------------------------------------
# -----------Login dashboard----------------
elif st.session_state.is_logged_in:
    try:

        if st.session_state.role == "admin":
            admin_dashboard()
        else:
            user_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"dashboard error occured: {str(e)}")
    # st.title(" Welcome to INMAR Dashboard")
    # st.success(f"Logged in as: {st.session_state.user_email}")
    # try:
    #     img = Image.open("dodge.jpg")
    #     st.image(img, width=1000)



    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"login error occured:{str(e)}")


    # if st.button("Logout"):    
    #     Logout_user()

#------------------------------------------