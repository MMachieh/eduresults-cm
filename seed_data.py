"""
Seed script: creates a full dataset for end-to-end testing of EduResults CM.
Run with: venv\Scripts\python manage.py shell < seed_data.py
"""
import django, os, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduresults_cm.settings')
django.setup()

from accounts.models import User, Teacher, Student, Parent
from school.models import AcademicYear, Term, Sequence, Class, Subject, TeacherAssignment, Enrollment
from marks.models import Mark

print("=== EduResults CM Seed Script ===\n")

# ── 1. Academic Year ────────────────────────────────────────────────
ay, created = AcademicYear.objects.get_or_create(
    label='2024-2025',
    defaults={
        'start_date': datetime.date(2024, 9, 1),
        'end_date':   datetime.date(2025, 7, 31),
        'is_active':  True,
    }
)
ay.is_active = True; ay.save()
print(f"{'Created' if created else 'Found'} Academic Year: {ay}")

# ── 2. Terms & Sequences ────────────────────────────────────────────
seqs = {}
for t_num in ['1', '2', '3']:
    term, _ = Term.objects.get_or_create(academic_year=ay, name=t_num)
    for s_num in ['1', '2']:
        seq, _ = Sequence.objects.get_or_create(term=term, name=s_num)
        seqs[f"T{t_num}S{s_num}"] = seq
        print(f"  Sequence: {seq}")

# ── 3. Subjects ─────────────────────────────────────────────────────
subject_data = [
    ('Mathematics',       4, 'english'),
    ('English Language',  4, 'english'),
    ('French',            3, 'french'),
    ('Biology',           3, 'english'),
    ('Chemistry',         3, 'english'),
    ('Physics',           3, 'english'),
    ('History',           2, 'english'),
    ('Geography',         2, 'english'),
    ('ICT',               2, 'english'),
]
subjects = {}
for name, coeff, lang in subject_data:
    subj, _ = Subject.objects.get_or_create(name=name, defaults={'coefficient': coeff, 'language': lang})
    subjects[name] = subj
print(f"Created {len(subjects)} subjects.")

# ── 4. Teacher account ──────────────────────────────────────────────
if not User.objects.filter(username='teacher1').exists():
    t_user = User.objects.create_user('teacher1', 'teacher1@school.cm', 'teacher123',
                                       first_name='John', last_name='Kimbi', role='teacher')
    teacher = Teacher.objects.create(user=t_user, specialisation='BSc Mathematics', staff_id='TCH001')
    print("Created Teacher: John Kimbi (teacher1 / teacher123)")
else:
    t_user = User.objects.get(username='teacher1')
    try:
        teacher = t_user.teacher_profile
    except Exception:
        teacher = Teacher.objects.create(user=t_user, specialisation='BSc Mathematics', staff_id='TCH001')
    print("Found Teacher: teacher1")

# ── 5. Class ────────────────────────────────────────────────────────
form5a, created = Class.objects.get_or_create(
    academic_year=ay, level='Form 5', suffix='A',
    defaults={'class_teacher': teacher}
)
if created:
    print("Created Class: Form 5A")

# Assign subjects to class
for subj in subjects.values():
    subj.classes.add(form5a)

# ── 6. Teacher Assignments ──────────────────────────────────────────
for subj in subjects.values():
    TeacherAssignment.objects.get_or_create(
        teacher=teacher, subject=subj, class_group=form5a, academic_year=ay
    )
print(f"Assigned {teacher} to all subjects in Form 5A.")

# ── 7. Student accounts ─────────────────────────────────────────────
students_data = [
    ('student1', 'Alice',    'Ngo',  'STU2024001', datetime.date(2008, 3, 15)),
    ('student2', 'Bob',      'Tabi', 'STU2024002', datetime.date(2007, 11, 22)),
    ('student3', 'Carol',    'Sama', 'STU2024003', datetime.date(2008, 6, 5)),
]
students = []
for uname, first, last, matric, dob in students_data:
    if not User.objects.filter(username=uname).exists():
        s_user = User.objects.create_user(uname, f'{uname}@school.cm', 'student123',
                                           first_name=first, last_name=last, role='student')
        stu = Student.objects.create(user=s_user, matricule=matric, date_of_birth=dob)
        print(f"Created Student: {first} {last} ({uname} / student123, matricule: {matric})")
    else:
        s_user = User.objects.get(username=uname)
        stu = s_user.student_profile
        print(f"Found Student: {uname}")
    students.append(stu)
    Enrollment.objects.get_or_create(student=stu, class_group=form5a, academic_year=ay)

# ── 8. Parent account ───────────────────────────────────────────────
if not User.objects.filter(username='parent1').exists():
    p_user = User.objects.create_user('parent1', 'parent1@gmail.com', 'parent123',
                                       first_name='Mary', last_name='Ngo', role='parent')
    parent = Parent.objects.create(user=p_user)
    parent.students.add(students[0])  # Link to Alice
    print("Created Parent: Mary Ngo (parent1 / parent123) — linked to Alice Ngo")
else:
    p_user = User.objects.get(username='parent1')
    parent = p_user.parent_profile
    print("Found Parent: parent1")

# ── 9. Marks for Sequence 1, Term 1 ────────────────────────────────
seq1 = seqs['T1S1']
marks_data = {
    # student_idx: {subject_name: mark_value}
    0: {'Mathematics': 16.5, 'English Language': 14.0, 'French': 12.5,
        'Biology': 17.0, 'Chemistry': 15.5, 'Physics': 13.0,
        'History': 18.0, 'Geography': 14.5, 'ICT': 19.0},
    1: {'Mathematics': 11.0, 'English Language': 13.5, 'French': 10.0,
        'Biology': 12.0, 'Chemistry': 9.5,  'Physics': 11.0,
        'History': 14.0, 'Geography': 12.5, 'ICT': 15.0},
    2: {'Mathematics': 8.0,  'English Language': 11.0, 'French': 9.0,
        'Biology': 7.5,  'Chemistry': 10.0, 'Physics': 8.5,
        'History': 13.0, 'Geography': 9.5,  'ICT': 12.0},
}
for i, stu in enumerate(students):
    for subj_name, val in marks_data[i].items():
        Mark.objects.get_or_create(
            student=stu, subject=subjects[subj_name], sequence=seq1,
            defaults={'teacher': teacher, 'value': val, 'remark': 'Good'}
        )
print(f"Created marks for {len(students)} students in Sequence 1, Term 1.")

# ── 10. Publish Sequence 1 ──────────────────────────────────────────
seq1.is_published = True
seq1.save()
print(f"\nPublished: {seq1}")

print("\n=== Seed Complete! ===")
print("Accounts:")
print("  Admin:   admin / mywebapp")
print("  Teacher: teacher1 / teacher123")
print("  Student: student1 / student123  (Alice Ngo,  STU2024001)")
print("  Student: student2 / student123  (Bob Tabi,   STU2024002)")
print("  Student: student3 / student123  (Carol Sama, STU2024003)")
print("  Parent:  parent1  / parent123   (Mary Ngo, linked to Alice)")
