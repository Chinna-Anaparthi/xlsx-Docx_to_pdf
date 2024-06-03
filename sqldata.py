from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import uvicorn
import google.generativeai as genai
load_dotenv()

app = FastAPI()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME")
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
        raise HTTPException(status_code=500, detail="Database connection failed")
    return connection

# class User(BaseModel):
#     name: str
#     address: str

# @app.post("/add-user")
# def add_user(user: User):
#     connection = create_connection()
#     query = "INSERT INTO stable (name, address) VALUES (%s, %s)"
#     values = (user.name, user.address)
#     cursor = connection.cursor()
#     try:
#         cursor.execute(query, values)
#         connection.commit()
#         return {"message": "User added successfully"}
#     except Error as e:
#         print(f"The error '{e}' occurred")
#         raise HTTPException(status_code=500, detail="Failed to add user")
#     finally:
#         cursor.close()
#         connection.close()


# Function to execute SQL query
def execute_sql_query(sql):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        connection.commit()
        print(rows)
        return rows
    except Error as e:
        print(f"The error '{e}' occurred")
        raise HTTPException(status_code=500, detail="Failed to execute query")
    finally:
        cursor.close()
        connection.close()

# Endpoint to execute SQL query
prompt = [
    """
    You are an expert in converting English questions to SQL query!
    The SQL database has the name stable and has the following columns - name, address.
    \n\nFor example,\nExample 1: How many entries of records are present? 
    The SQL command will be something like this: SELECT COUNT(*) FROM stable;
    \nExample 2: Tell me all the students staying in Vizag? 
    The SQL command will be something like this: SELECT * FROM name      
    WHERE address='Vizag'; 
    also the sql code should not have ``` in beginning or end and sql word in output
    """
]

def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([str(prompt[0]), str(question)])
    print(response)
    return response.text.strip()

class User2(BaseModel):
    question:str
@app.get("/ask-question")
def ask_question(question: User2):
    if not question:
        raise HTTPException(status_code=400, detail="Question parameter is required")
    
    response = get_gemini_response(question, prompt)
    print(f"Generated SQL Query: {response}")
    results = execute_sql_query(response)
    print("The Response is:")
    return {"results": results,"query":response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
