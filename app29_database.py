import streamlit as st
import matplotlib.pyplot as plt
import sqlite3
import pandas as pd

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
    'Does your twiddle objects repetitively (e.g. pieces of string)?': {
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
    'Does your twiddle objects repetitively (e.g. pieces of string)?'
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
    ['Q23','Does your twiddle objects repetitively (e.g. pieces of string)?', 'High']
]
# Connect to the SQLite database
conn = sqlite3.connect('result.db')
c = conn.cursor()

def get_classification(total_score):
    if total_score >= 30.0:
        return "Yes, autism with high traits"
    elif total_score >= 20.0:
        return "Yes, autism with medium traits"
    elif total_score >= 10.0:
        return "Yes, autism with low traits"
    else:
        return "No autism"

def insert_result(name, age, gender, classification):
    c.execute('CREATE TABLE IF NOT EXISTS results (name TEXT, age REAL, gender TEXT, classification TEXT)')
    c.execute('INSERT INTO results (name, age, gender, classification) VALUES (?, ?, ?, ?)', (name, age, gender, classification))
    conn.commit()

def main_menu():
    st.title("Autism Traits Predictor")
    st.write("Welcome to the Autism Traits Predictor.")
    st.write("Please select an option from the menu on the left.")
    st.image("SAiEML2.jpg", use_column_width=True)

def prediction_page():
    st.write('## Please rate the following traits based on the observed behavior.')
    
    # User details input
    st.write("## User Details")
    name = st.text_input("Name:")
    age = st.number_input("Age:")
    gender = st.radio("Gender", ['Female', 'Male'])
    
    # Display radio buttons for each question
    scores = []
    for i, item in enumerate(items, start=1):
        # Display the trait directly instead of question and trait
        st.subheader(f'{item[0]}: {item[1]}')
        
        score_mapping = score_mappings.get(item[1], {})
        trait_levels = list(score_mapping.keys())
        if score_mapping:
            score = st.radio("Select the trait level:", trait_levels, key=f'radio_{i}')
            scores.append(score)
        else:
            st.write("No options to select.")

    # Add a button to trigger the prediction
    if st.button('Predict'):
        # Calculate the total score
        total_score = sum(score_mappings[q][score] * expert_weights[expert] for q, score in zip(questions, scores) for expert in expert_weights)

        # Determine the classification
        classification = get_classification(total_score)

        # Store values in session state
        st.session_state.name = name
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.total_score = total_score
        st.session_state.classification = classification

        # Insert result into the database
        insert_result(name, age, gender, classification)

        st.write("## Prediction Completed")
        st.write("Prediction is completed. Please click 'Result' in the navigation bar to view the result.")

def result_page():
    st.write("## Result")
    if 'total_score' in st.session_state:
        st.write("Name:", st.session_state.name)
        st.write("Age:", st.session_state.age)
        st.write("Gender:", st.session_state.gender)
        
        # Set the box color based on classification
        box_color = 'blue' if st.session_state.classification == "No autism" else ('green' if st.session_state.classification == "Yes, autism with medium traits" else 'red')
        
        st.markdown(f"<div style='border: 2px solid {box_color}; padding: 10px'>{st.session_state.classification}</div>", unsafe_allow_html=True)

        if st.session_state.classification != "No autism":
            high_trait_features = [item[1] for item in items if item[2] == 'High']

            fig, ax = plt.subplots(figsize=(8, 6))  # Increase the figure size here
            ax.barh(high_trait_features, [3] * len(high_trait_features))
            ax.set_xlabel('Relevance Level')
            ax.set_title('Features Identified by Experts')
            ax.invert_yaxis()
            ax.xaxis.tick_top()
            plt.xticks([1, 2, 3], ['Low', 'Medium', 'High'])
            plt.tight_layout()
            st.pyplot(fig)
    else:
       
      st.write("Make a prediction first.")

def view_results():
    st.write("## View Results")
    
    # Query database for results
    c.execute('SELECT * FROM results')
    rows = c.fetchall()
    
    # Convert results to DataFrame
    df = pd.DataFrame(rows, columns=['Name', 'Age', 'Gender', 'Classification'])
    
    # Display results in table
    st.dataframe(df)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Main Menu", "Prediction", "Result", "View Results"])

    if page == "Main Menu":
        main_menu()
    elif page == "Prediction":
        prediction_page()
    elif page == "Result":
        result_page()
    elif page == "View Results":
        view_results()

if __name__ == "__main__":
    main()
