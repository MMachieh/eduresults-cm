import datetime
from accounts.models import User, Teacher, Student, Parent
from school.models import AcademicYear, Term, Sequence, Class, Subject, TeacherAssignment, Enrollment
from marks.models import Mark

print("Cleaning database...")
# Delete all users except 'admin'
User.objects.exclude(username='admin').delete()

# Delete structural data
AcademicYear.objects.all().delete()
Subject.objects.all().delete()

print("Creating Academic Year, Term, Sequence...")
ay = AcademicYear.objects.create(label='2024-2025', start_date=datetime.date(2024, 9, 2), end_date=datetime.date(2025, 6, 15), is_active=True)
term1 = Term.objects.create(academic_year=ay, name='1')
seq1 = Sequence.objects.create(term=term1, name='1', is_published=True)

print("Creating Subjects...")
subjects_data = [
    ('Mathematics', 4), ('English Language', 4), ('French', 3), 
    ('Physics', 3), ('History', 2)
]
subjects = []
for name, coeff in subjects_data:
    subj = Subject.objects.create(name=name, coefficient=coeff)
    subjects.append(subj)

print("Creating Classes...")
form1a = Class.objects.create(academic_year=ay, level='Form 1', suffix='A')
form1b = Class.objects.create(academic_year=ay, level='Form 1', suffix='B')
for subj in subjects:
    subj.classes.add(form1a)
    subj.classes.add(form1b)

print("Creating Users & Profiles...")
# Principal
u_princ = User.objects.create_superuser('principal', 'principal@school.cm', 'principal123', first_name='John', last_name='Doe', role='admin')

# Teachers
u_t1 = User.objects.create_user('teacher1', 'teacher1@school.cm', 'teacher123', first_name='Mary', last_name='Jane', role='teacher')
t1 = Teacher.objects.create(user=u_t1, staff_id='TCH001', specialisation='Mathematics')

u_t2 = User.objects.create_user('teacher2', 'teacher2@school.cm', 'teacher123', first_name='Paul', last_name='Smith', role='teacher')
t2 = Teacher.objects.create(user=u_t2, staff_id='TCH002', specialisation='Arts')

form1a.class_teacher = t1
form1a.save()
form1b.class_teacher = t2
form1b.save()

# Assign teachers to subjects
TeacherAssignment.objects.create(teacher=t1, subject=subjects[0], class_group=form1a, academic_year=ay) # Math
TeacherAssignment.objects.create(teacher=t1, subject=subjects[3], class_group=form1a, academic_year=ay) # Physics
TeacherAssignment.objects.create(teacher=t2, subject=subjects[1], class_group=form1a, academic_year=ay) # English
TeacherAssignment.objects.create(teacher=t2, subject=subjects[2], class_group=form1a, academic_year=ay) # French
TeacherAssignment.objects.create(teacher=t2, subject=subjects[4], class_group=form1a, academic_year=ay) # History

# Students
u_s1 = User.objects.create_user('student1', 'student1@school.cm', 'student123', first_name='Alice', last_name='Wonder', role='student')
s1 = Student.objects.create(user=u_s1, matricule='STU001', date_of_birth=datetime.date(2010, 5, 12))
Enrollment.objects.create(student=s1, class_group=form1a, academic_year=ay)

u_s2 = User.objects.create_user('student2', 'student2@school.cm', 'student123', first_name='Bob', last_name='Builder', role='student')
s2 = Student.objects.create(user=u_s2, matricule='STU002', date_of_birth=datetime.date(2010, 8, 22))
Enrollment.objects.create(student=s2, class_group=form1a, academic_year=ay)

u_s3 = User.objects.create_user('student3', 'student3@school.cm', 'student123', first_name='Charlie', last_name='Chaplin', role='student')
s3 = Student.objects.create(user=u_s3, matricule='STU003', date_of_birth=datetime.date(2010, 11, 2))
Enrollment.objects.create(student=s3, class_group=form1b, academic_year=ay)

# Parents
u_p1 = User.objects.create_user('parent1', 'parent1@school.cm', 'parent123', first_name='Mr', last_name='Wonder', role='parent')
p1 = Parent.objects.create(user=u_p1)
p1.students.add(s1)

u_p2 = User.objects.create_user('parent2', 'parent2@school.cm', 'parent123', first_name='Mrs', last_name='Builder', role='parent')
p2 = Parent.objects.create(user=u_p2)
p2.students.add(s2)

print("Creating Marks...")
marks_s1 = [15.5, 14.0, 12.0, 16.0, 13.5]
for i, m in enumerate(marks_s1):
    Mark.objects.create(student=s1, subject=subjects[i], sequence=seq1, teacher=t1 if i in [0,3] else t2, value=m, remark='Good')

marks_s2 = [9.0, 11.5, 8.0, 10.0, 12.0]
for i, m in enumerate(marks_s2):
    Mark.objects.create(student=s2, subject=subjects[i], sequence=seq1, teacher=t1 if i in [0,3] else t2, value=m, remark='Average')

print("Database fully seeded!")
