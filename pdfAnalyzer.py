from PyPDF2 import PdfReader
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def analyze_text_with_openai(text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": '''
                ***TASK***:
                You are tasked with extracting and formatting information from a course syllabus. The syllabus may include various events such as lectures, assignments, midterms, exams, or quizzes. Your goal is to extract and present the dates and times of each event in a structured plain text format using ISO 8601 format for all date and time entries. Make sure to include the course name and code in the summary of each event.

                ***RULES***:
                1. **Lectures, Laboratories/Labs,Tutorials, and DGDS**: Provide both date and time for each session in ISO 8601 format. If multiple sessions are listed for different sections or days, list each separately. Include the course code and name at the beginning of each entry. If in the PDF it is written as "Laboratories", shorten it to "Lab" for the output.
                2. **Midterms and Exams**: Extract both the date and time for midterm tests and final exams in ISO 8601 format. Include the course code and name at the beginning of each entry. If only a date is provided without a specific time, mention "Time not specified".
                3. **Assignments**: List each assignment with its due date in ISO 8601 format. Include the course code and name at the beginning of each entry. If a time is provided without a specific start time, assume the start time is one hour before the given time, and the end time is the given time.Example: ITI1120 - Introduction to Computing I Python: Assignment 5 : 2023-11-20T08:00:00 only have one time right therefore change it in this format ITI1120 - Introduction to Computing I Python: Assignment 5 : 2023-11-20T0:7:00:00, 2023-11-20T08:00:00 where originally there was only one time which was the 8am but now we have a start time which is 7am and an end time which is 8am.
                4. **Quizzes**: If quizzes are mentioned, extract the date and time for each quiz in ISO 8601 format. Include the course code and name at the beginning of each entry. If the time is not specified, mention "Time not specified".
                5. **Output Format**:
                   - List each event on a new line in plain text.
                   - Include details such as "COURSE_CODE - COURSE_NAME: Lecture - Section A: 2024-01-08T16:00:00, 2024-01-08T17:20:00", "COURSE_CODE - COURSE_NAME: Midterm Test: 2024-03-02T17:00:00, 2024-03-02T19:00:00", "COURSE_CODE - COURSE_NAME: Assignment 1: 2024-02-02", "COURSE_CODE - COURSE_NAME: Tutorial: 2024-02-02T17:00:00, 2024-02-02T18:20:00", "COURSE_CODE - COURSE_NAME: Lab: 2024-02-02T17:00:00, 2024-02-02T18:20:00".
                   - Always use ": " to separate the summary and the date and time.
                   - If their is an available time do not extract that information, ONLY extract the due date and time.
                
                ***OUTPUT EXAMPLE***:
                ITI 1121 - Introduction to Computing II: Lecture - Section A: 2024-01-08T16:00:00, 2024-01-08T17:20:00
                ITI 1121 - Introduction to Computing II: Lecture - Section B: 2024-01-10T16:00:00, 2024-01-10T17:20:00
                ITI 1121 - Introduction to Computing II: Midterm Test: 2024-03-02T17:00:00, 2024-03-02T19:00:00
                ITI 1121 - Introduction to Computing II: Final Exam: 2024-04-25T09:00:00, 2024-04-25T12:00:00
                ITI 1121 - Introduction to Computing II: Assignment 1 : 2024-02-02
                ITI 1121 - Introduction to Computing II: Quiz 1: 2024-02-15T00:00:00, Time not specified
                ITI 1121 - Introduction to Computing II: Tutorial: 2024-03-01T17:00:00, 2024-03-01T19:00:00
                ITI 1121 - Introduction to Computing II: Lab: 2024-05-01T17:00:00, 2024-05-01T19:00:00

                - **Note**: Ensure each event is clearly defined with its relevant details. If you cannot determine a date or time, state "Date not specified" or "Time not specified".
                '''
            },
            {
                "role": "user",
                "content": f"Extract the dates and details of lectures, assignments, midterms, exams, and quizzes from the following text:\n\n{text}"
            }
        ]
    )

    return response.choices[0].message.content
