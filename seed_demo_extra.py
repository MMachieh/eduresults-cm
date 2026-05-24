"""
Extra seed: adds Sequence 2 marks (published), student4, parent2, and a second class.
Run with: python manage.py shell < seed_demo_extra.py
"""
import datetime
from accounts.models import User, Teacher, Student, Parent
from school.models import AcademicYear, Term, Sequence, Class, Subject, TeacherAssignment, Enrollment
from marks.models import Mark

ay = AcademicYear.objects.get(label='2024-2025')
term1 = Term.objects.get(academic_year=ay, name='1')
seq1 = Sequence.objects.get(term=term1, name='1')
seq2, _ = Sequence.objects.get_or_create(term=term1, name='2')

teacher = User.objects.get(username='teacher1').teacher_profile
form5a = Class.objects.get(academic_year=ay, level='Form 5', suffix='A')

subjects = {s.name: s for s in Subject.objects.all()}

# Student list
students = [User.objects.get(username=f'student{i}').student_profile for i in range(1, 4)]

# ── Extra student: student4 / Deborah Fon ──────────────────────────────
if not User.objects.filter(username='student4').exists():
    s_user = User.objects.create_user('student4', 'student4@school.cm', 'student123',
                                       first_name='Deborah', last_name='Fon', role='student')
    stu4 = Student.objects.create(user=s_user, matricule='STU2024004', date_of_birth=datetime.date(2008, 9, 10))
    print("Created Student: Deborah Fon (student4 / student123, STU2024004)")
else:
    stu4 = User.objects.get(username='student4').student_profile
    print("Found Student: student4")
Enrollment.objects.get_or_create(student=stu4, class_group=form5a, academic_year=ay)
students.append(stu4)

# Marks for student4 in Seq 1 (if missing)
marks_s4_seq1 = {'Mathematics': 13.0, 'English Language': 15.0, 'French': 11.5,
                 'Biology': 14.0, 'Chemistry': 12.5, 'Physics': 10.5,
                 'History': 16.0, 'Geography': 13.5, 'ICT': 14.5}
for subj_name, val in marks_s4_seq1.items():
    Mark.objects.get_or_create(
        student=stu4, subject=subjects[subj_name], sequence=seq1,
        defaults={'teacher': teacher, 'value': val, 'remark': 'Good'}
    )

# ── Sequence 2 marks for all 4 students ───────────────────────────────
marks_seq2 = {
    # Slightly different from seq1 to show trend
    'student1': {'Mathematics': 17.5, 'English Language': 15.0, 'French': 14.0,
                 'Biology': 18.0, 'Chemistry': 16.0, 'Physics': 14.5,
                 'History': 18.5, 'Geography': 15.5, 'ICT': 19.5},
    'student2': {'Mathematics': 12.0, 'English Language': 14.0, 'French': 11.5,
                 'Biology': 13.5, 'Chemistry': 10.5, 'Physics': 12.5,
                 'History': 15.0, 'Geography': 13.0, 'ICT': 16.0},
    'student3': {'Mathematics': 7.5,  'English Language': 10.5, 'French': 8.5,
                 'Biology': 9.0,  'Chemistry': 11.0, 'Physics': 7.0,
                 'History': 12.0, 'Geography': 8.5,  'ICT': 13.0},
    'student4': {'Mathematics': 14.0, 'English Language': 16.0, 'French': 12.5,
                 'Biology': 15.5, 'Chemistry': 13.5, 'Physics': 11.5,
                 'History': 17.0, 'Geography': 14.5, 'ICT': 15.5},
}
for uname, mark_map in marks_seq2.items():
    stu = User.objects.get(username=uname).student_profile
    for subj_name, val in mark_map.items():
        Mark.objects.get_or_create(
            student=stu, subject=subjects[subj_name], sequence=seq2,
            defaults={'teacher': teacher, 'value': val, 'remark': 'Good'}
        )
print("Created Sequence 2 marks for 4 students.")

# Publish Sequence 2
seq2.is_published = True
seq2.save()
print(f"Published: {seq2}")

# ── parent2 linked to Bob Tabi (student2) ─────────────────────────────
student2 = User.objects.get(username='student2').student_profile
if not User.objects.filter(username='parent2').exists():
    p_user = User.objects.create_user('parent2', 'parent2@gmail.com', 'parent123',
                                       first_name='George', last_name='Tabi', role='parent')
    parent2 = Parent.objects.create(user=p_user)
    parent2.students.add(student2)
    print("Created Parent: George Tabi (parent2 / parent123) — linked to Bob Tabi")
else:
    print("Found Parent: parent2")

# ── Second class: Form 4A with 3 students ────────────────────────────
form4a, created = Class.objects.get_or_create(
    academic_year=ay, level='Form 4', suffix='A',
    defaults={'class_teacher': teacher}
)
if created:
    print("Created Class: Form 4A")

# Add subjects to Form 4A
for subj in subjects.values():
    subj.classes.add(form4a)

# teacher2
if not User.objects.filter(username='teacher2').exists():
    t2_user = User.objects.create_user('teacher2', 'teacher2@school.cm', 'teacher123',
                                        first_name='Grace', last_name='Ndeh', role='teacher')
    from accounts.models import Teacher as TeacherModel
    teacher2 = TeacherModel.objects.create(user=t2_user, staff_id='TCH002', specialisation='English Language')
    print("Created Teacher: Grace Ndeh (teacher2 / teacher123)")
else:
    teacher2 = User.objects.get(username='teacher2').teacher_profile
    print("Found Teacher: teacher2")

# Assign teacher2 to English Language in Form 4A
TeacherAssignment.objects.get_or_create(
    teacher=teacher2, subject=subjects['English Language'], class_group=form4a, academic_year=ay
)
# Assign teacher to remaining subjects in Form 4A
for subj in subjects.values():
    if subj.name != 'English Language':
        TeacherAssignment.objects.get_or_create(
            teacher=teacher, subject=subj, class_group=form4a, academic_year=ay
        )

# Form 4A students: student5, student6, student7
form4_students_data = [
    ('student5', 'Emmanuel', 'Mbah',  'STU2024005', datetime.date(2009, 2, 14)),
    ('student6', 'Faith',    'Obi',   'STU2024006', datetime.date(2009, 7, 28)),
    ('student7', 'Grace',    'Atanga','STU2024007', datetime.date(2009, 4, 3)),
]
form4_students = []
for uname, first, last, matric, dob in form4_students_data:
    if not User.objects.filter(username=uname).exists():
        s_user = User.objects.create_user(uname, f'{uname}@school.cm', 'student123',
                                           first_name=first, last_name=last, role='student')
        stu = Student.objects.create(user=s_user, matricule=matric, date_of_birth=dob)
        print(f"Created Student: {first} {last} ({uname})")
    else:
        stu = User.objects.get(username=uname).student_profile
        print(f"Found Student: {uname}")
    Enrollment.objects.get_or_create(student=stu, class_group=form4a, academic_year=ay)
    form4_students.append(stu)

# Marks for Form 4A Seq 1
form4_marks_seq1 = {
    0: {'Mathematics': 14.0, 'English Language': 16.5, 'French': 13.0,
        'Biology': 15.0, 'Chemistry': 14.5, 'Physics': 12.0,
        'History': 17.0, 'Geography': 15.5, 'ICT': 18.0},
    1: {'Mathematics': 9.5,  'English Language': 12.0, 'French': 8.5,
        'Biology': 11.5, 'Chemistry': 8.0,  'Physics': 9.0,
        'History': 13.0, 'Geography': 10.5, 'ICT': 14.0},
    2: {'Mathematics': 11.0, 'English Language': 13.5, 'French': 10.0,
        'Biology': 12.5, 'Chemistry': 11.5, 'Physics': 10.0,
        'History': 14.5, 'Geography': 12.0, 'ICT': 15.5},
}
for i, stu in enumerate(form4_students):
    for subj_name, val in form4_marks_seq1[i].items():
        Mark.objects.get_or_create(
            student=stu, subject=subjects[subj_name], sequence=seq1,
            defaults={'teacher': teacher, 'value': val, 'remark': 'Good'}
        )
print("Created Form 4A marks for Seq 1.")

# Marks for Form 4A Seq 2
form4_marks_seq2 = {
    0: {'Mathematics': 15.5, 'English Language': 17.0, 'French': 14.5,
        'Biology': 16.0, 'Chemistry': 15.0, 'Physics': 13.5,
        'History': 18.0, 'Geography': 16.5, 'ICT': 19.0},
    1: {'Mathematics': 10.5, 'English Language': 13.0, 'French': 9.5,
        'Biology': 12.0, 'Chemistry': 9.0,  'Physics': 10.5,
        'History': 14.0, 'Geography': 11.0, 'ICT': 15.0},
    2: {'Mathematics': 12.0, 'English Language': 14.5, 'French': 11.0,
        'Biology': 13.5, 'Chemistry': 12.0, 'Physics': 11.5,
        'History': 15.5, 'Geography': 13.0, 'ICT': 16.5},
}
for i, stu in enumerate(form4_students):
    for subj_name, val in form4_marks_seq2[i].items():
        Mark.objects.get_or_create(
            student=stu, subject=subjects[subj_name], sequence=seq2,
            defaults={'teacher': teacher2, 'value': val, 'remark': 'Good'}
        )
print("Created Form 4A marks for Seq 2.")

# Update teacher staff_id if missing
try:
    t_obj = teacher.user.teacher_profile
    if not t_obj.staff_id:
        t_obj.staff_id = 'TCH001'
        t_obj.save()
except Exception:
    pass

print("\n=== Extra Seed Complete ===")
print("New accounts:")
print("  Student: student4 / student123  (Deborah Fon, STU2024004) — Form 5A")
print("  Student: student5 / student123  (Emmanuel Mbah, STU2024005) — Form 4A")
print("  Student: student6 / student123  (Faith Obi, STU2024006) — Form 4A")
print("  Student: student7 / student123  (Grace Atanga, STU2024007) — Form 4A")
print("  Teacher: teacher2 / teacher123  (Grace Ndeh) — Form 4A, English")
print("  Parent:  parent2  / parent123   (George Tabi) — linked to Bob Tabi")
print("Sequence 2 (Term 1) published with marks for all 7 students.")
