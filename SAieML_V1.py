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
    st.write("## Toddler Details")
    st.write("Please fill out the following about how your child usually is. Answer all questions")

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

    st.write('## Please rate the following traits based on the observed behavior.')
    st.divider()
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
    diagnosis = st.radio("Diagnosis Status", ["Yes, my child has been screened/diagnosed with autism.", 
                                              "No, my child was screened, but no autism was found.",
                                              "No, my child has never been screened."], key="diagnosis")



    if st.button('Predict'):
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

        st.write("## Prediction Completed")
        st.write("Prediction is completed. Please click 'Result' in the navigation bar to view the result.")



def result_page():
    st.write("## Result")
    if 'total_score' in st.session_state:
        st.write("Name:", st.session_state.name)
        st.write("Age:", st.session_state.age)
        st.write("Gender:", st.session_state.gender)
        st.write("State:", st.session_state.state)

        box_color = 'blue' if st.session_state.classification == "No autism" else ('green' if st.session_state.classification == "Yes, autism with low traits" else 'red')
        font_size = '24px' if st.session_state.classification in ["Yes, autism with high traits.", "Yes, autism with medium traits."] else '16px'
        
        additional_statement = ""
        if st.session_state.classification == "No autism":
            additional_statement = "**No further action required.**"
        elif st.session_state.classification == "Yes, autism with low traits":
            additional_statement = "**No further action required unless ongoing surveillance indicates risk for ASD.**"
        elif st.session_state.classification == "Yes, autism with high traits":
            additional_statement = "**Please refer immediately to see a psychiatrist for diagnostic evaluation and early intervention.**"
        elif st.session_state.classification == "Yes, autism with medium traits":
            additional_statement = "**Please refer for diagnostic evaluation and eligibility evaluation for early intervention.**"

        st.markdown(f"<div style='border: 2px solid {box_color}; padding: 10px; font-size: {font_size}'>{st.session_state.classification}<br>{additional_statement}</div>", unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.classification != "No autism":
            st.write("### Features Identified by Experts")
            high_trait_features = [item[1] for item in items if item[2] == 'High']
            if high_trait_features:
                st.write("**Traits with high relevance identified by experts:**")
                for feature in high_trait_features:
                    st.write(f"- {feature}")

def dashboard_page():
    st.write("## Real-time Dashboard")
    with closing(create_connection()) as conn:
        with conn.cursor() as c:
            c.execute('SELECT * FROM results')
            rows = c.fetchall()
            df = pd.DataFrame(rows, columns=[
                'Name', 'Age', 'Gender', 'State', 'Classification', 'total_score', 
                'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10', 'Q11', 'Q12', 'Q13', 'Diagnosis'
            ])

           
    df['total_score'] = pd.to_numeric(df['total_score'], errors='coerce')
    dashboard_placeholder = st.empty()
    with dashboard_placeholder.container():
        st.dataframe(df)
        classification_counts = df['Classification'].value_counts()
        st.bar_chart(classification_counts)
        st.write("### State Distribution")
        state_counts = df['State'].value_counts()
        st.bar_chart(state_counts)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Main Menu", "Prediction", "Result", "Dashboard"])
    st.sidebar.caption(
        "<div style='text-align: justify;'>"
        "Welcome to the Quick Screen Autism Traits Predictor. This app is to predict the autism traits built using machine learning and integrated with experts. The goal is to provide a more efficient and simplified alternative to traditional autism screening and to support early decision making with reliable and accurate results."
        "</div>",
        unsafe_allow_html=True
    )
    st.sidebar.image("umpsa.png", use_column_width=True)
    st.sidebar.image("psis2019.png", use_column_width=True)

    if page == "Main Menu":
        main_menu()
    elif page == "Prediction":
        prediction_page()
    elif page == "Result":
        result_page()
    elif page == "Dashboard":
        dashboard_page()

   # st.markdown("""<div style='text-align: center; margin-top: 50px;'><p style='font-size: 14px;'><b>SAieML: Developed by [Ts. Ainie Hayati Noruzman][ainie_hayati@psis.edu.my]©[2024]</p></div>""", unsafe_allow_html=True)

    st.markdown(
    """ <div style='text-align: center; background-color: rgba(75, 75, 75, 0.5); padding: 2px; border: 2px solid #A6A6A6; border-radius: 5px; margin-top: 15px;'>
    <p style='color: white;'>© 2024 QuickScreen: Expert-Guided Autism Insight.[ainie_hayati@psis.edu.my] All rights reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)
    

if __name__ == "__main__":
    main()
