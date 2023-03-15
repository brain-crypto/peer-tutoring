import mysql.connector
subjects = ["English", "Literature", "Language", "Maths", "CS", "Science", "Physics", "Chemistry", "Biology", "Humanities", "History", "Classics", "Psychology", "Sociology", "Geography", "Accounting", "Business", "Economics", "Spanish", "Chinese", "Art", "DT", "Music", "Drama", "PE"]

# create the database peerTutor
db = mysql.connector.connect(host="localhost", user="[Your name]", password="[Your password]")
cursor = db.cursor()
cursor.execute("CREATE DATABASE peerTutor")
db = mysql.connector.connect(host="localhost", user="[Your name]", password="[Your password]", database="peerTutor")
cursor = db.cursor()

# create the tables tutors, students, pairs and remaining_students
# each tutor is stored as a row of (name, year level, how busy they are, the max level of English they can teach, the max level of maths they can teach, ...)
# a subject that they didn't sign up for is stored as NULL
# PT / IST leaders: +1 task. IST tutors but not PT tutors: +1 task. Every new student: +1 task. Don't want to tutor any more students: +5 task. 
# if two people have the same name then add a number to the 2nd person's name and record it down somewhere e.g. Lily Hu from y11 and Lily Hu2 from y10. 
cursor.execute('''CREATE TABLE tutors (
    name VARCHAR(255) PRIMARY KEY, 
    year_level INT, 
    tasks INT
);''')

# each student is stored as a row of (name, year level, the level of English they want to learn, the level of Maths they want to learn, ...)
# a subject that they didn't sign up for is stored as NULL
cursor.execute('''CREATE TABLE students (
    name VARCHAR(255) PRIMARY KEY, 
    year_level INT
);''')

# each pair is stored as a row of (subject, level, student, tutor)
# if a tutor is teaching a student multiple subjects, make multiple entries
cursor.execute('''CREATE TABLE pairs (
    subject VARCHAR(255), 
    level INT, 
    student VARCHAR(255), 
    tutor VARCHAR(255), 
    FOREIGN KEY(student) REFERENCES students(name),
    FOREIGN KEY(tutor) REFERENCES tutors(name)
);''')

# stores the students who haven't been assigned a tutor for all of their subjects, in the same format as TABLE students
# a subject that they didn't sign up for or has been assigned a tutor for is stored as NULL
cursor.execute('''CREATE TABLE remaining_students (
    name VARCHAR(255) PRIMARY KEY
    FOREIGN KEY(name) REFERENCES students(name)
);''')

# adds the subject fields to tutors, students, remaining_students
for subject in subjects:
    cursor.execute("ALTER TABLE remaining_students ADD COLUMN {} INT".format(subject))
    cursor.execute("ALTER TABLE students ADD COLUMN {} INT".format(subject))
    cursor.execute("ALTER TABLE tutors ADD COLUMN {} INT".format(subject))
