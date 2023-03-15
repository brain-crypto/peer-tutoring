import mysql.connector, numpy
subjects = ["English", "Literature", "Language", "Maths", "CS", "Science", "Physics", "Chemistry", "Biology", "Humanities", "History", "Classics", "Psychology", "Sociology", "Geography", "Accounting", "Business", "Economics", "Spanish", "Chinese", "Art", "DT", "Music", "Drama", "PE"]
filepath = "C:\\Users\\Brian\\peer tutoring v2\\pairs.txt" # replace this with your output file path
exclude = [['John Smith', 'William Jones'], ['Michael Johnson', 'Chris Brown']] # list of people who don't want to be paired together. format [tutor, student]

db = mysql.connector.connect(host="localhost", user="[Your name]", password="[Your password]", database="peerTutor")
cursor = db.cursor()
    
# Ask user for confirmation before running an sql script
def run_sql(sql, ask_confirmation):
    if ask_confirmation:
        print(sql) # print out the sql code for the user to review
        confirm = input("Confirm?(y/n) ")
        if confirm == "y":
            try:
                cursor.execute(sql)
                db.commit()
            except Exception as e:
                print(e) # if there is any error print it out
        else:
            print("Rejected")
    else:
        cursor.execute(sql)
        db.commit()

def add_tutor(name, year, subjects, ask_confirmation=True):
    fields = ""
    data = ""
    for subject in subjects: # make a list of fields and a list of values to be inserted
        fields += ", " + subject[0]
        data += ", " + str(subject[1])
    sql = "INSERT INTO tutors (name, year_level, tasks" + fields + ") VALUES ('{}', {}, 0".format(name, year) + data + ");"
    run_sql(sql, ask_confirmation)

def add_student(name, year, subjects, ask_confirmation):
    fields = ""
    values = ""
    for subject in subjects: # make a list of fields and a list of values to be inserted
        fields += ", " + subject[0] 
        values += ", " + str(subject[1])
    sql = "INSERT INTO students (name, year_level" + fields + ") VALUES ('{}', {}".format(name, year) + values + ");"
    run_sql(sql, ask_confirmation)
    add_remaining(name, subjects) # copy the same row to remaining_students

def add_remaining(name, subjects, ask_confirmation):
    cursor.execute("SELECT 1 FROM remaining_students WHERE name = '{}'".format(name))
    if cursor.fetchone() == None: # if the student doesn't already exist, add their name to remaining_students
        sql = "INSERT INTO remaining_students (name) VALUES ('{}');".format(name)
        run_sql(sql, ask_confirmation)
    sql = "UPDATE remaining_students SET "
    for subject in subjects: # make a list of values to be updated
        sql += "{} = {}, ".format(subject[0], subject[1])
    sql = sql[:-2] + " WHERE name = '{}';".format(name) # remove the trailing ", " and add "WHERE name = 'NAME'"
    run_sql(sql, ask_confirmation)

def add_pair(tutor, student, subject, level, ask_confirmation):
    sql = "INSERT INTO pairs (tutor, student, subject, level) VALUES ('{}', '{}', '{}', {});".format(tutor, student, subject, level)
    run_sql(sql, ask_confirmation)

    cursor.execute("SELECT COUNT(*) FROM pairs WHERE tutor = '{}' AND student = '{}'".format(tutor, student))
    exist = cursor.fetchone()[0]
    if exist == 1: # if the pair is the first time this student has been paired with this tutor, add 1 to the tutor's number of tasks
        sql = "UPDATE tutors SET tasks = tasks + 1 WHERE name = '{}'".format(tutor)
        run_sql(sql, ask_confirmation)
    
    sql = "UPDATE remaining_students SET {} = NULL WHERE name = '{}'".format(subject, student) # remove this subject from this student's entry in remaining_student
    run_sql(sql, ask_confirmation)

def add_subject(subject): # adding a new subject field to the 2 tables
    if subject not in subjects:
        print("Please manually add this subject to the end of 'subjects' on line 2 first!")
    else:
        cursor.execute("ALTER TABLE students ADD {} INT;".format(subject))
        cursor.execute("ALTER TABLE tutors ADD {} INT;".format(subject))
        cursor.execute("ALTER TABLE remaining_students ADD {} INT;".format(subject))

def update_tutor(name, year, subjects, ask_confirmation=True):
    sql = "UPDATE tutors SET year_level = {}".format(year)
    for subject in subjects:
        sql += ", {} = {}".format(subject[0], subject[1])
    sql += " WHERE name = '{}';".format(name)
    run_sql(sql, ask_confirmation)

def update_student(name, year, subjects, ask_confirmation=True):
    sql = "UPDATE students SET year_level = {}".format(year)
    for subject in subjects:
        sql += ", {} = {}".format(subject[0], subject[1])
    sql += " WHERE name = '{}';".format(name)
    run_sql(sql, ask_confirmation)
    add_remaining(name, subjects)
    
def pairing():
    cursor.execute("SELECT * FROM remaining_students;")
    students = numpy.array(cursor.fetchall())
    cursor.execute("SELECT * FROM tutors;")
    tutors = numpy.array(cursor.fetchall())
    s = len(students)
    t = len(tutors)
    # calculating how suitable each tutor is for each student based on their number of overlapping subjects 
    scores = numpy.zeros((s+1, t+1))
    for i in range(s):
        cursor.execute("SELECT year_level FROM students WHERE name = '{}'".format(students[i][0]))
        year = cursor.fetchone()[0]
        for j in range(t):
            if tutors[j][1] >= year and [tutors[j][0], students[i][0]] not in exclude: # make sure the tutor isn't younger than the student and don't mind being paired with the student
                num_matches = 0
                for k in range(len(subjects)): # counts the number of matching subjects
                    if students[i][k+1] != None and tutors[j][k+3] != None:
                        if students[i][k+1] <= tutors[j][k+3]:
                            num_matches += 1
                scores[i][j] = num_matches**2 # favours a large number of overlapping subjects. increase to 3 maybe?
                scores[i][t] += scores[i][j]
                scores[s][j] += scores[i][j]
    # print(scores) # for debug
    # assigning tutor to each student
    for i in range(s):
        best_score = 0
        best_tutor = -1
        for j in range(t): # finds the tutor with the highest overall score
            # 100**tutors[j][2] scales the score down if the tutor is already teaching a lot of other students) and also prevents DIV0
            # scores[s][j] scales the score down if the tutor can teach a lot of other students in the list, as it = sum of all scores for that tutor
            new_score = scores[i][j] / (scores[s][j] + 100**tutors[j][2])
            if new_score > best_score:
                best_score = new_score
                best_tutor = j
        if best_tutor != -1:
            for k in range(len(subjects)):
                if students[i][k+1] != None and tutors[best_tutor][k+3] != None:
                     if students[i][k+1] <= tutors[best_tutor][k+3]:
                            add_pair(tutors[best_tutor][0], students[i][0], subjects[k], students[i][k+1], True)

def find_tutor():
    year = input("Year level: ")
    subject = input("Subject: ")
    if subject not in subjects:
        print("Subject does not exist.")
        return
    level = input("Subject level: ")
    num_s = input("Maximum number of tasks: ")
    cursor.execute("SELECT name, year_level, tasks FROM tutors WHERE year_level >= {} AND {} >= {} AND tasks <= {}".format(year, subject, level, num_s))
    print(cursor.fetchall())

def add_tutor_ui():
    print("Enter # for name to exit the loop.")
    while True:
        update = False
        name = input("Name: ")
        if name == "#":
            break
        cursor.execute("SELECT * FROM tutors WHERE name = '{}'".format(name))
        existing = cursor.fetchone()
        if existing != None:
            print(existing)
            print("Tutor already exists. Entering update mode.")
            update = True
        year = input("Year level: ")
        add_subjects = []
        print("Enter # for subject to exit the loop.")
        while True:
            subject = input("Subject: ")
            if subject == "#":
                break
            elif subject not in subjects:
                print("Subject does not exist.")
            else:
                level  = input("Level: ")
                add_subjects.append([subject, level])
        if update:
            update_tutor(name, year, add_subjects)
        else:
            add_tutor(name, year, add_subjects)

def add_student_ui():
    print("Enter # for name to exit the loop.")
    while True:
        update = False
        name = input("Name: ")
        if name == "#":
            break
        cursor.execute("SELECT * FROM students WHERE name = '{}'".format(name))
        existing = cursor.fetchone()
        if existing != None:
            print(existing)
            print("Student already exists. Entering update mode.")
            update = True
        year = input("Year level: ")
        add_subjects = []
        print("Enter # for subject to exit the loop.")
        while True:
            subject = input("Subject: ")
            if subject == "#":
                break
            elif subject not in subjects:
                print("Subject does not exist.")
            else:
                level  = input("Level: ")
                add_subjects.append([subject, level])
        if update:
            update_student(name, year, add_subjects)
        else:
            add_student(name, year, add_subjects)

def add_pair_ui():
    print("Enter # for tutor to exit the loop.")
    while True:
        tutor = input("Tutor: ")
        if tutor == "#":
            break
        student = input("Student: ")
        subject = input("Subject: ")
        if subject not in subjects and subject != "NA":
            print("Subject doesn't exist")
            continue
        level = int(input("Level: "))
        add_pair(tutor, student, subject, level, True)

def delete_tutor():
    tutor = input("Name: ")
    cursor.execute("SELECT tutor, student, subject, level FROM pairs WHERE tutor = '{}'".format(tutor))
    pairs = cursor.fetchall()
    if pairs != []:
        print("Please delete the following pairs before deleting the tutors")
        print(pairs)
    else:
        run_sql("DELETE FROM tutors WHERE name = '{}'".format(tutor), True)

def delete_student():
    student = input("Name: ")
    cursor.execute("SELECT tutor, student, subject, level FROM pairs WHERE student = '{}'".format(student))
    pairs = cursor.fetchall()
    if pairs != []:
        print("Please delete the following pairs before deleting the tutors")
        print(pairs)
    else:
        run_sql("DELETE FROM remaining_students WHERE name = '{}'".format(student), True)
        run_sql("DELETE FROM students WHERE name = '{}'".format(student), True)

def delete_pair():
    tutor = input("Tutor: ")
    student = input("Student: ")
    subject = input("Subject: ")
    level = input("Level: ")
    cursor.execute("SELECT 1 FROM pairs WHERE tutor = '{}' AND student = '{}' AND subject = '{}' AND level = '{}'".format(tutor, student, subject, level))
    if cursor.fetchone() == None:
        print("The pair described above does not exist.")
        return
    sql = "DELETE FROM pairs WHERE tutor = '{}' AND student = '{}' AND subject = '{}'".format(tutor, student, subject)
    run_sql(sql, True)
    sql = "UPDATE tutors SET tasks = tasks - 1 WHERE name = '{}'".format(tutor)
    run_sql(sql, True)
    add_remaining(student, [[subject, level]], True)

def show_remaining_students():
    cursor.execute("SELECT * FROM remaining_students")
    remaining = cursor.fetchall()
    for student in remaining:
        name = student[0]
        # name = student[-1]
        missing_subjects = []
        for i in range(1, len(student)):
            if student[i] != None:
               missing_subjects.append(subjects[i-1] + str(student[i]))
        if len(missing_subjects) == 0:
           sql = "DELETE FROM remaining_students WHERE name = '{}'".format(student[0])
           run_sql(sql, True)
        else: 
            print(name, missing_subjects)

def mark_tutor():
    print("Enter # for name to exit the loop.")
    while True:
        name = input("Name: ")
        if name == "#":
            break
        busy = input("Change Tasks by: ")
        cursor.execute("SELECT 1 FROM tutors WHERE name = '{}'".format(name))
        if cursor.fetchone() == None:
            print("Tutor does not exist.")
        else:
            sql = "UPDATE tutors SET tasks = tasks + {} WHERE name = '{}'".format(busy, name)
            run_sql(sql, True)

def output_pairs():
    f = open(filepath, "w")
    first = input("Tutor first (y) or student first (n)?")
    if first == "y":
        f.write("TUTOR, STUDENT, SUBJECT\n")
        cursor.execute("SELECT * FROM pairs ORDER BY tutor, student")
        pairs = cursor.fetchall()
        for pair in pairs:
            line = "{}, {}, {}{}\n".format(pair[3], pair[2], pair[0], pair[1])
            f.write(line)
    else:
        f.write("STUDENT, TUTOR, SUBJECT\n")
        cursor.execute("SELECT * FROM pairs ORDER BY student, tutor")
        pairs = cursor.fetchall()
        for pair in pairs:
            line = "{}, {}, {}{}\n".format(pair[2], pair[3], pair[0], pair[1])
            f.write(line)
    f.close()

def show_tutors():
    print("Format: NAME YEAR_LEVEL NUM_OF_STUDENT SUBJECT1 SUBJECT2 ...")
    cursor.execute("SELECT * FROM tutors ORDER BY tasks, year_level, name")
    for tutor in cursor.fetchall():
        line = "{} {} {}".format(tutor[0], tutor[1], tutor[2])
        for i in range(len(subjects)):
            if tutor[i+3] != None:
                line += " " + subjects[i] + str(tutor[i+3])
        print(line)

# print out all unformatted database for debugging
# cursor.execute("SELECT * FROM remaining_students")
# print(cursor.fetchall())
# cursor.execute("SELECT * FROM pairs")
# print(cursor.fetchall())
# print()
# cursor.execute("SELECT * FROM tutors")
# print(cursor.fetchall())
# print()
# cursor.execute("SELECT * FROM students")
# print(cursor.fetchall())
# print()

# print out the number of tutors and students in certain year levels
# cursor.execute("SELECT COUNT(*) FROM tutors WHERE year_level < 12")
# print(cursor.fetchone()[0])
# cursor.execute("SELECT COUNT(*) FROM students WHERE year_level < 12")
# print(cursor.fetchone()[0])

print('''
+-------------------------------+
|             MENU              |
| 1: Pair remaining students    |
| 2: Find tutor for a subject   |
| 3: Add / update tutor         |
| 4: Add / update student       |
| 5: Add pair                   |
| 6: Delete tutor               |
| 7: Delete student             |
| 8: Delete pair                |
| 9: View remaining students    |
| 10: Change tutor's #tasks     |
| 11: Output all pairs as a file|
| 12: Show all tutors           |
| #: Exit                       |
+-------------------------------+
''')
while True:
    option = input("Which process would you like to run: ")
    if option == "1":
        pairing()
    elif option == "2":
        find_tutor()
    elif option == "3":
        add_tutor_ui()
    elif option == "4":
        add_student_ui()
    elif option == "5":
        add_pair_ui()
    elif option == "6":
        delete_tutor()
    elif option == "7":
        delete_student()
    elif option == "8":
        delete_pair()
    elif option == "9":
        show_remaining_students()
    elif option == "10":
        mark_tutor()
    elif option == "11":
        output_pairs()
    elif option == "12":
        show_tutors()
    elif option == "#": 
        break
    else:
        print("Not a valid option!")
