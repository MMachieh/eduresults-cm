import datetime
import random
from accounts.models import User, Teacher, Student, Parent
from school.models import AcademicYear, Term, Sequence, Class, Subject, TeacherAssignment, Enrollment
from marks.models import Mark

print("Cleaning database...")
User.objects.exclude(username__in=['admin', 'principal']).delete()
AcademicYear.objects.all().delete()
Subject.objects.all().delete()

print("Creating Academic Year, Terms, Sequences...")
ay = AcademicYear.objects.create(label='2024-2025', start_date=datetime.date(2024, 9, 2), end_date=datetime.date(2025, 6, 15), is_active=True)

term1 = Term.objects.create(academic_year=ay, name='1')
term2 = Term.objects.create(academic_year=ay, name='2')
term3 = Term.objects.create(academic_year=ay, name='3')

seqs = [
    Sequence.objects.create(term=term1, name='1', is_published=True),
    Sequence.objects.create(term=term1, name='2', is_published=True),
    Sequence.objects.create(term=term2, name='1', is_published=True),
    Sequence.objects.create(term=term2, name='2', is_published=True),
    Sequence.objects.create(term=term3, name='1', is_published=True),
    Sequence.objects.create(term=term3, name='2', is_published=True),
]

print("Creating Subjects...")
subjects_data = [
    ('Mathematics', 4), ('English Language', 4), ('French', 3), 
    ('Physics', 3), ('Chemistry', 3), ('Biology', 3), 
    ('History', 2), ('Geography', 2), ('Economics', 2), 
    ('Literature', 2), ('ICT', 2), ('Citizenship', 1), ('Religious Studies', 1)
]
subjects = []
for name, coeff in subjects_data:
    subj = Subject.objects.create(name=name, coefficient=coeff)
    subjects.append(subj)

print("Creating Classes...")
classes_to_create = [
    ('Form 1', 'A'), ('Form 1', 'B'),
    ('Form 2', 'A'),
    ('Form 3', 'A'),
    ('Form 4', 'Science'), ('Form 4', 'Arts'),
    ('Form 5', 'Science'), ('Form 5', 'Arts'),
    ('Lower Sixth', 'Science'), ('Lower Sixth', 'Arts'),
    ('Upper Sixth', 'Science'), ('Upper Sixth', 'Arts')
]

created_classes = []
for lvl, sfx in classes_to_create:
    cls_obj = Class.objects.create(academic_year=ay, level=lvl, suffix=sfx)
    created_classes.append(cls_obj)
    for subj in subjects:
        subj.classes.add(cls_obj)

print("Creating Teachers...")
u_t1 = User.objects.create_user('teacher1', 'teacher1@school.cm', 'teacher123', first_name='Mary', last_name='Jane', role='teacher')
t1 = Teacher.objects.create(user=u_t1, staff_id='TCH001', specialisation='Mathematics')

u_t2 = User.objects.create_user('teacher2', 'teacher2@school.cm', 'teacher123', first_name='Paul', last_name='Smith', role='teacher')
t2 = Teacher.objects.create(user=u_t2, staff_id='TCH002', specialisation='Arts')

u_t3 = User.objects.create_user('teacher3', 'teacher3@school.cm', 'teacher123', first_name='Susan', last_name='Storm', role='teacher')
t3 = Teacher.objects.create(user=u_t3, staff_id='TCH003', specialisation='Science')

teachers = [t1, t2, t3]

created_classes[0].class_teacher = t1
created_classes[0].save()
created_classes[1].class_teacher = t2
created_classes[1].save()

for i, cls in enumerate(created_classes):
    for j, subj in enumerate(subjects):
        TeacherAssignment.objects.get_or_create(teacher=teachers[j % 3], subject=subj, class_group=cls, academic_year=ay)

print("Creating Students...")
students_data = [
    ('student1', 'Alice', 'Wonder', 'STU001', created_classes[0], 'excellent'),
    ('student2', 'Bob', 'Builder', 'STU002', created_classes[0], 'poor'),
    ('student3', 'Charlie', 'Chaplin', 'STU003', created_classes[0], 'average'),
    ('student4', 'Diana', 'Prince', 'STU004', created_classes[1], 'good'),
    ('student5', 'Eve', 'Polastri', 'STU005', created_classes[4], 'mixed'), 
]

created_students = []
student_profiles = {}
for uname, fn, ln, mat, cls, perf in students_data:
    u = User.objects.create_user(uname, f'{uname}@school.cm', 'student123', first_name=fn, last_name=ln, role='student')
    s = Student.objects.create(user=u, matricule=mat, date_of_birth=datetime.date(2008, 1, 1))
    Enrollment.objects.create(student=s, class_group=cls, academic_year=ay)
    created_students.append(s)
    student_profiles[s.id] = perf

print("Creating Parents...")
u_p1 = User.objects.create_user('parent1', 'parent1@school.cm', 'parent123', first_name='Mr', last_name='Wonder', role='parent')
p1 = Parent.objects.create(user=u_p1)
p1.students.add(created_students[0])

u_p2 = User.objects.create_user('parent2', 'parent2@school.cm', 'parent123', first_name='Mrs', last_name='Builder', role='parent')
p2 = Parent.objects.create(user=u_p2)
p2.students.add(created_students[1])

print("Creating Marks for Full Year...")
for stu in created_students:
    enroll = stu.enrollments.first()
    cls = enroll.class_group
    perf = student_profiles[stu.id]
    
    for subj in cls.subjects.all():
        assignment = TeacherAssignment.objects.filter(subject=subj, class_group=cls, academic_year=ay).first()
        tch = assignment.teacher if assignment else t1
        
        for seq in seqs:
            if perf == 'excellent':
                val = random.uniform(14.0, 19.5)
                remark = 'Excellent'
            elif perf == 'poor':
                val = random.uniform(4.0, 9.5)
                remark = 'Poor effort'
            elif perf == 'average':
                val = random.uniform(9.0, 13.0)
                remark = 'Average'
            elif perf == 'good':
                val = random.uniform(12.0, 16.0)
                remark = 'Good'
            else: # mixed
                val = random.uniform(6.0, 18.0)
                remark = 'Inconsistent'
                
            val = round(val * 2) / 2 # Snap to .0 or .5
            Mark.objects.create(student=stu, subject=subj, sequence=seq, teacher=tch, value=val, remark=remark)

print("Database fully extended and seeded for the entire year!")
