import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import time
import psycopg2
from contextlib import closing
import os


# Define the weights for each expert
expert_weights = {
    'Expert A': 0.3,
    'Expert B': 0.5,
    'Expert C': 0.2
}

# Define the relevance levels
relevance_levels = {
    1: 'Low',
    2: 'Medium',
    3: 'High'
}

# Define the score mappings for each question
score_mappings = {
    'Does your child look at you when you call his/her name?': {
        'Always': 0,
        'Usually': 1,
        'Sometimes': 2,
        'Rarely': 3,
        'Never': 4
    },
    'How easy is it for you to get eye contact with your child?': {
        'Very Easy': 0,
        'Quite Easy': 1,
        'Quite Difficult': 2,
        'Very Difficult': 3,
        'Impossible': 4
    },
    'Does your child point to indicate that s/he wants something (e.g. a toy that is out of reach)?': {
        'many times a day': 0,
        'a few times a day': 1,
        'a few times a week': 2,
        'less than once a week': 3,
        'never': 4
    },
    'Does your child point to share interest with you (e.g. pointing at an interesting sight)?': {
        'many times a day': 0,
        'a few times a day': 1,
        'a few times a week': 2,
        'less than once a week': 3,
        'never': 4
    },
    'Does your child pretend (e.g. care for dolls, talk on a toy phone)?': {
        'Very Easy': 0,
        'Easy': 1,
        'Difficult': 2,
        'Very Difficult': 3,
        'Impossible': 4
    },
    'Does your child follow where you were looking?': {
        'many times a day': 0,
        'a few times a day': 1,
        'a few times a week': 2,
        'less than once a week': 3,
        'never': 4
    },
    'Does your child place your hand on an object when s/he wants you to use (e.g. on a door handle when s/he wants you to open the door, on a toy when s/he wants you to activate it)?': {
        'many times a day': 4,
        'a few times a day': 3,
        'a few times a week': 2,
        'less than once a week': 1,
        'never': 0
    },
    'Does your child walk on tiptoe?': {
        'Always': 4,
        'Usually': 3,
        'Sometimes': 2,
        'Rarely': 1,
        'Never': 0
    },
    'If you or someone else in the family is visibly upset does your child show signs of wanting to comfort them (e.g. stroking their hair, hugging them)?': {
        'many times a day': 0,
        'a few times a day': 1,
        'a few times a week': 2,
        'less than once a week': 3,
        'never': 4
    },
    'Does your child do the same thing over and over again (e.g. running the tap, turning the light switch on and off, opening and closing doors)?': {
        'many times a day': 4,
        'a few times a day': 3,
        'a few times a week': 2,
        'less than once a week': 1,
        'never': 0
    },
    'Would you describe your childs first words as:': {
        'very typical': 0,
        'quite typical': 1,
        'slightly unusual': 2,
        'very unusual': 3,
        'my child doesnot speak': 4
    },
    'Does your child use simple gestures (e.g. wave goodbye)?': {
        'many times a day': 0,
        'a few times a day': 1,
        'a few times a week': 2,
        'less than once a week': 3,
        'never': 4
    },
    'Does your child twiddle objects repetitively (e.g. pieces of string)?': {
        'many times a day': 4,
        'a few times a day': 3,
        'a few times a week': 2,
        'less than once a week': 1,
        'never': 0
    }
}

# Define the questions and their trait levels
questions = [
    'Does your child look at you when you call his/her name?',
    'How easy is it for you to get eye contact with your child?',
    'Does your child point to indicate that s/he wants something (e.g. a toy that is out of reach)?',
    'Does your child point to share interest with you (e.g. pointing at an interesting sight)?',
    'Does your child pretend (e.g. care for dolls, talk on a toy phone)?',
    'Does your child follow where you were looking?',
    'Does your child place your hand on an object when s/he wants you to use (e.g. on a door handle when s/he wants you to open the door, on a toy when s/he wants you to activate it)?',
    'Does your child walk on tiptoe?',
    'If you or someone else in the family is visibly upset does your child show signs of wanting to comfort them (e.g. stroking their hair, hugging them)?',
    'Does your child do the same thing over and over again (e.g. running the tap, turning the light switch on and off, opening and closing doors)?',
    'Would you describe your childs first words as:',
    'Does your child use simple gestures (e.g. wave goodbye)?',
    'Does your child twiddle objects repetitively (e.g. pieces of string)?'
]

# Results provided by the experts
items = [
    ['Q1', 'Does your child look at you when you call his/her name?', 'High'],
    ['Q2', 'How easy is it for you to get eye contact with your child?', 'High'],
    ['Q5', 'Does your child point to indicate that s/he wants something (e.g. a toy that is out of reach)?', 'High'],
    ['Q6', 'Does your child point to share interest with you (e.g. pointing at an interesting sight)?', 'High'],
    ['Q9', 'Does your child pretend (e.g. care for dolls, talk on a toy phone)?', 'Medium'],
    ['Q10','Does your child follow where you were looking?', 'High'],
    ['Q12','Does your child place your hand on an object when s/he wants you to use (e.g. on a door handle when s/he wants you to open the door, on a toy when s/he wants you to activate it)?', 'High'],
    ['Q13','Does your child walk on tiptoe?', 'Medium'],
    ['Q15','If you or someone else in the family is visibly upset does your child show signs of wanting to comfort them (e.g. stroking their hair, hugging them)?', 'Medium'],
    ['Q16','Does your child do the same thing over and over again (e.g. running the tap, turning the light switch on and off, opening and closing doors)?', 'High'],
    ['Q17','Would you describe your childs first words as:', 'Medium'],
    ['Q19','Does your child use simple gestures (e.g. wave goodbye)?'	, 'Medium'],
    ['Q23','Does your child twiddle objects repetitively (e.g. pieces of string)?', 'High']
]


def create_connection():
    # Retrieve DATABASE_URL from environment, use external or internal URL as appropriate
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://quickscreen_user:gFKXmyrBnQPtad3OS3s1AehpJJdkPoJA@dpg-csf1f8u8ii6s739abkf0-a.oregon-postgres.render.com/quickscreen")
    return psycopg2.connect(DATABASE_URL)



# Classification function
def get_classification(total_score):
    if total_score >= 30.0:
        return "Yes, autism with high traits"
    elif total_score >= 20.0:
        return "Yes, autism with medium traits"
    elif total_score >= 10.0:
        return "Yes, autism with low traits"
    else:
        return "No autism"


def main_menu():
    # Title only appears on the main (login) page
    st.markdown(
        """
        <div style='text-align: center; background-color: #97dddf; padding: 6px;border-radius: 10px;'>
        <h1 style='color: #1b21a0;'>QuickScreen: Expert-Guided Autism Insight</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    
    # Add space with a margin
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    
    st.image("SAiEML6.png", use_column_width=True)
   


def insert_result(name, age, gender, state, classification, total_score, diagnosis, *scores):
    # Use with closing to manage connection
    with closing(create_connection()) as conn:
        with conn.cursor() as c:
            # Ensure Diagnosis is the last column in the table definition
            c.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    name TEXT, 
                    age TEXT, 
                    gender TEXT, 
                    state TEXT, 
                    classification TEXT,
                    total_score REAL, 
                    Q1 TEXT, 
                    Q2 TEXT, 
                    Q3 TEXT, 
                    Q4 TEXT, 
                    Q5 TEXT, 
                    Q6 TEXT,
                    Q7 TEXT, 
                    Q8 TEXT, 
                    Q9 TEXT, 
                    Q10 TEXT, 
                    Q11 TEXT, 
                    Q12 TEXT, 
                    Q13 TEXT,
                    diagnosis TEXT
                )
            ''')
            # Insert data including diagnosis
            c.execute(
                '''
                INSERT INTO results (name, age, gender, state, classification, total_score, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, diagnosis)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''',
                (name, age, gender, state, classification, total_score, *scores, diagnosis)
            )
            conn.commit()


def prediction_page():
    st.markdown(
    """
    <div style="border: 2px solid #008080; padding: 10px; border-radius: 5px; background-color: #e0f7fa; font-size: 20px; color: #333;">
        <h4>Please fill out the following information based on your child's usual behavior.</h4>
        <p>This page consists of two sections: <b>Section 1</b> covers your child's details, and <b>Section 2</b> includes quick screen autism questions.</p>
        <p>Please ensure you answer all questions.</p>
    </div>
    """,
    unsafe_allow_html=True
)



    st.write("## Section 1. Toddler Details")
   # st.write("Please fill out the following about how your child usually is. Answer all questions")

    # Basic input details
    name = st.text_input("Name:")
    age = st.selectbox("Age range of your child:", ["1-4 (Toddlers)", "5-12 (Children)"])
    gender = st.radio("Gender:", ['Female', 'Male'])
    states_malaysia = [
        "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", 
        "Pahang", "Perak", "Perlis", "Pulau Pinang", "Sabah", 
        "Sarawak", "Selangor", "Terengganu", "Wilayah Persekutuan"
    ]
    selected_state = st.selectbox("Select a state in Malaysia:", states_malaysia)
    st.divider()
    st.write('## Section 2. Quick screen autism questions.')
    st.write('Please rate the following traits based on the observed behavior.')
    #st.divider()
    scores = []
    for i, item in enumerate(items, start=1):
        st.subheader(f'{item[0]}: {item[1]}')
        score_mapping = score_mappings.get(item[1], {})
        trait_levels = list(score_mapping.keys())
        if score_mapping:
            score = st.radio("Select the trait level:", trait_levels, key=f'radio_{i}')
            scores.append(score)

    # Capture diagnosis as input (no need to set in st.session_state)
    #diagnosis = st.radio("Has your child been properly screened/diagnosed with Autism before?", ["Yes", "No"], key="diagnosis")


    # Display alert message with custom styling
    st.markdown(
        """
        <div style='padding: 10px; border: 2px solid red; background-color: #f8d7da; color: #721c24; border-radius: 5px; margin-bottom: 10px;'>
            <strong>IMPORTANT!</strong> Has your child been properly screened/diagnosed with Autism before?
        </div>
        """,
        unsafe_allow_html=True
    )

    # Capture diagnosis as input (no need to set in st.session_state)
    diagnosis = st.radio("Diagnosis Status:", ["Yes, my child has been screened/diagnosed with autism.", 
                                              "No, my child was screened, but no autism was found.",
                                              "Yes, my child has been screened, and I've been informed there may be a possibility of mild autism.",
                                              "No, my child has never been screened.",], key="diagnosis")



    if st.button('Quick Screen'):
        total_score = sum(
            score_mappings[q][score] * expert_weights[expert]
            for q, score in zip(questions, scores)
            for expert in expert_weights
            if score in score_mappings[q]
        )
        classification = get_classification(total_score)
        insert_result(name, age, gender, selected_state, classification, total_score, diagnosis, *scores)

        # Set other values in session state (excluding diagnosis)
        st.session_state.name = name
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.state = selected_state
        st.session_state.classification = classification
        st.session_state.total_score = total_score

        #st.write("# Prediction Completed")
        #st.write("### Prediction is complete. Please click 'Autism Result' in the navigation bar to view your results.")
        st.markdown(
            """
            <div style="border: 2px solid #e0f7fa; padding: 15px; border-radius: 10px; background-color: #E6FFE6;">
                <h1 style="color: #1b21a0;">QuickScreen Completed</h1>
                <h3 style="color: #1b21a0;">Please click 'Autism Result' in the navigation bar to view your results.</h3>
            </div>
            """,
         unsafe_allow_html=True
)
import streamlit as st
from fpdf import FPDF

def result_page():
    st.title("Autism Result")

    if "classification" not in st.session_state:
        st.session_state.classification = None  # or a default value like "No autism"

    
    if 'total_score' in st.session_state:
        st.write("Name:", st.session_state.name)
        st.write("Age:", st.session_state.age)
        st.write("Gender:", st.session_state.gender)
        st.write("State:", st.session_state.state)

        # Set color based on classification
        box_color = 'green' if st.session_state.classification == "No autism" else \
                   ('red' if st.session_state.classification == "Yes, autism with high traits" else 'orange')
        
        # Set font size based on classification
        font_size = '36px' if st.session_state.classification in ["Yes, autism with high traits", "Yes, autism with medium traits"] else '24px'
        
        # Additional statement based on classification
        additional_statement = ""
        if st.session_state.classification == "No autism":
            additional_statement = "**No further action required.**"
        elif st.session_state.classification == "Yes, autism with low traits":
            additional_statement = "**No further action required unless ongoing surveillance indicates risk for ASD.**"
        elif st.session_state.classification == "Yes, autism with high traits":
            additional_statement = "**Please refer immediately to see a psychiatrist for diagnostic evaluation and early intervention.**"
        elif st.session_state.classification == "Yes, autism with medium traits":
            additional_statement = "**Please refer for diagnostic evaluation and eligibility evaluation for early intervention.**"

        # Display Result Box
        st.markdown(f"""
        <div style='
            border: 4px solid {box_color}; 
            background-color: #f8f9fa; 
            padding: 20px; 
            font-size: {font_size}; 
            border-radius: 15px; 
            text-align: center; 
            font-weight: bold;
            color: {box_color};
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        '>
            <p>{st.session_state.classification}</p>
            <p>{additional_statement}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
     
        # Button to generate PDF
        if st.button("Download Result as PDF"):
            # Create PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

             # Set Title
            pdf.set_font("Arial", size=16, style='B')  # Bold for title
            pdf.cell(200, 10, txt="Autism Result", ln=True, align='C')
            pdf.ln(10)  # Line break

            # Set content font
            pdf.set_font("Arial", size=12)

            # Add content to PDF
            pdf.cell(200, 10, txt=f"Name: {st.session_state.name}", ln=True)
            pdf.cell(200, 10, txt=f"Age: {st.session_state.age}", ln=True)
            pdf.cell(200, 10, txt=f"Gender: {st.session_state.gender}", ln=True)
            pdf.cell(200, 10, txt=f"State: {st.session_state.state}", ln=True)
            pdf.cell(200, 10, txt=f"Classification: {st.session_state.classification}", ln=True)
            pdf.cell(200, 10, txt=f"Additional Info: {additional_statement}", ln=True)

            # Add line break before disclaimer
            pdf.ln(10)

            # Draw the rectangle for the disclaimer box
            pdf.set_fill_color(230, 230, 230)  # Light gray background
            pdf.set_draw_color(255, 0, 0)      # Red border for alert
            pdf.rect(10, pdf.get_y(), 190, 60, style='FD')  # Draw rectangle with fill and border

            # Add disclaimer text inside the box
            disclaimer_text = """
           **********************************************DISCLAMER********************************************
            This questionnaire is a subset of the Quantitative Checklist for Autism in Toddlers (Q-CHAT), 
            a screening tool designed to identify toddlers aged 18 to 30 months who may be at risk for autism 
            spectrum disorder. The Q-CHAT consists of 25 questions, and a subset of these questions has been 
            selected using machine learning algorithms with experts insights for the purposes of PhD research project.

            Please note that the results generated by this tool are intended for research purposes only and should 
            not be used as a diagnostic tool. This result does not constitute a clinical diagnosis, and individuals 
            are advised to seek professional medical consultation for a comprehensive evaluation and diagnosis.
            """

            # Position disclaimer text inside the box
            pdf.set_xy(15, pdf.get_y() + 5)  # Position cursor slightly inside the rectangle
            pdf.set_font("Arial", size=10)  # Smaller font size for disclaimer
            pdf.multi_cell(180, 4, disclaimer_text, align='L')

            # Save the PDF to a file
            pdf_output = "autism_result_with_disclaimer.pdf"
            pdf.output(pdf_output)

            # Offer the file for download
            with open(pdf_output, "rb") as pdf_file:
                st.download_button("Download PDF", pdf_file, file_name=pdf_output, mime="application/pdf")

      #st.divider()
        
    if st.session_state.classification != "No autism":
         # Initialize high_trait_features to an empty list
            high_trait_features = [item[1] for item in items if item[2] == 'High']
    else:
        # Initialize high_trait_features to an empty list when no autism traits are found
         high_trait_features = []

    # Check if high_trait_features has any items
    if high_trait_features:
    # Using Streamlit's built-in Markdown with custom background
     st.markdown("""
    <div style="padding: 10px; background-color: #f0f8f8; border-left: 5px solid #008080;">
        <p style="font-size: 16px; font-weight: bold; color: #008080;">Traits with high relevance identified by experts:</p>
    """, unsafe_allow_html=True)

    for feature in high_trait_features:
        st.markdown(f"<p style='color: #4b4b4b; font-size: 14px;'>{feature}</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


import time
import streamlit as st
import pandas as pd
from contextlib import closing

# Assuming `create_connection()` is already defined to connect to your database
# You might need to adjust the connection setup if necessary.

# Admin Login page
def admin_page():
    st.title("Admin Login")
    st.markdown("<div style='margin-bottom: 20px;'>Please enter your admin credentials to access the Autism Dashboard.</div>", unsafe_allow_html=True)

    # Input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Hardcoded admin credentials (replace with secure storage in production)
    admin_credentials = {
        "admin": "admin123"  # Username: admin, Password: admin123
    }

    # Login button
    if st.button("Login"):
        if username in admin_credentials and password == admin_credentials[username]:
            # Set session state on successful login
            st.session_state["authenticated"] = True
            st.session_state["page"] = "Dashboard"  # Set page to Dashboard
            st.success("Login successful! Redirecting to the Dashboard...")
            time.sleep(2)  # Optional delay for a smooth transition
            st.rerun()  # Rerun the app to go to Dashboard
        else:
            st.error("Invalid username or password. Please try again.")


def dashboard_page():
    # Check if user is authenticated
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        # If not authenticated, redirect to the login page
        admin_page()
    else:
        # If authenticated, show the dashboard
        st.title("Real-time Dashboard")
        st.write("Welcome to the admin dashboard!")

        # Add a logout button
        if st.button("Logout"):
            st.session_state["authenticated"] = False  # Clear authentication state
            st.success("You have been logged out.")
            st.rerun()  # Rerun to show the login page

        # Fetch data from the database
        with closing(create_connection()) as conn:
            with conn.cursor() as c:
                c.execute('SELECT * FROM results')  # Adjust your SQL query as needed
                rows = c.fetchall()
                # Create a dataframe from the query results
                df = pd.DataFrame(rows, columns=[
                    'Name', 'Age', 'Gender', 'State', 'Classification', 'total_score', 
                    'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10', 'Q11', 'Q12', 'Q13', 'Diagnosis'
                ])

        # Check if the dataframe is empty
        if df.empty:
            st.warning("No records found in the database.")
            return

        # Display the data as a table
        st.subheader("Toddlers Data")
        st.dataframe(df)

        # Display the classification distribution as a bar chart
        st.subheader("Classification Distribution")
        classification_counts = df['Classification'].value_counts()
        st.bar_chart(classification_counts)

        # Display state distribution as a bar chart
        st.subheader("State Distribution")
        state_counts = df['State'].value_counts()
        st.bar_chart(state_counts)

        # Filter data by state
        st.subheader("Filter Data")
        selected_state = st.selectbox("Select State", df['State'].unique())
        filtered_data = df[df['State'] == selected_state]
        st.write(f"Showing data for {selected_state} state:")
        st.dataframe(filtered_data)



def autism_protocols_page():
    st.title("Autism Health Services Protocols")
    
    # Content description for the protocols in a styled box
    content = """
    <div style="border: 2px solid #008080; padding: 20px; background-color: #e0f7fa; font-size: 20px; color: #333;">
        <strong>Here are the steps to access autism health services:</strong>
        <ol>
            <li>Go to the nearest clinic.</li>
            <li>Get an appointment for a consultation.</li>
            <li>Follow through with the necessary diagnostic evaluations.</li>
            <li>Consult with specialists for therapy and interventions.</li>
        </ol>
        <p><strong>For more detailed information on autism services, visit the following link:</strong></p>
        <p><a href="https://www.nasom.org.my/our-centres/" target="_blank" style="color: #00796b; font-size: 18px;">Click here for autism service centers</a></p>
    </div>
    """

    # Display the content with the styling
    st.markdown(content, unsafe_allow_html=True)


# Main function to handle page routing
def main():
    # Initialize session state if not set
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Welcome", "Autism Quick Screen", "Autism Result", "Autism Health Services Protocols", "Autism Dashboard"])

    # Additional sidebar information
    st.sidebar.caption(
        "<div style='text-align: justify;'>"
        "Welcome to the Quick Screen Autism Traits Predictor. This app is designed to predict autism traits using a machine learning model integrated with expert insights. Its goal is to offer a more efficient and simplified alternative to traditional autism screening, providing reliable and accurate results to support early decision-making."
        "</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.image("umpsa.png", use_column_width=True)
    st.sidebar.image("psis2019.png", use_column_width=True)

    # Page routing based on selected option
    if page == "Welcome":
        main_menu()  # Define the main menu function
    elif page == "Autism Quick Screen":
        prediction_page()  # Define the prediction page function
    elif page == "Autism Result":
        result_page()  # Define the result page function
    elif page == "Autism Health Services Protocols":
        autism_protocols_page()  # Display autism protocols page
    elif page == "Autism Dashboard":
        # Check if user is authenticated
        if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
            # If not authenticated, show the login page first
            admin_page()
        else:
            # If authenticated, show the dashboard
            dashboard_page()
    

    # Footer
    st.markdown(
        """ <div style='text-align: center; background-color: rgba(75, 75, 75, 0.5); padding: 2px; border: 2px solid #A6A6A6; border-radius: 5px; margin-top: 15px;'>
        <p style='color: white;'>© 2024 QuickScreen: Expert-Guided Autism Insight.[ainie_hayati@psis.edu.my] All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Run the application
if __name__ == "__main__":
    main()
