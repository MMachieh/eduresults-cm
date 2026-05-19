# EduResults CM

EduResults CM is a secure, role-based student results management web application designed for Cameroon Anglophone secondary schools. It digitalizes the traditional mark entry and report card generation process, bringing transparency and efficiency to the school ecosystem.

## Features by Role

### 1. Administrator
- **System Configuration:** Complete CRUD capabilities over the academic structure (Academic Years, Terms, Sequences, Classes, Subjects).
- **User Management:** Create, deactivate, and assign roles for Teachers and Students.
- **Publication Control:** Toggle the publication status of sequences to lock mark entry and reveal results to parents.
- **Batch Operations:** Automatically dispatch email notifications to parents upon publication. Generate and download bulk ZIP files containing PDF report cards for an entire class.

### 2. Teacher
- **Assigned Workflow:** View only the classes and subjects explicitly assigned to you.
- **Bulk Mark Entry:** A streamlined, spreadsheet-style interface to record marks (/20) for all enrolled students at once.
- **Lock Integrity:** Cannot alter marks once an administrator has published the sequence.

### 3. Student
- **Secure Viewing:** View personal sequence averages, class rankings, and detailed subject marks.
- **Official Reports:** Access and print a digital, web-based official report card.

### 4. Parent
- **Self-Registration:** Parents can autonomously create accounts by securely verifying their child's official matricule number.
- **Unified Dashboard:** View the published academic results and online report cards for all linked children from a single dashboard.
- **Automated Alerts:** Receive email notifications whenever new results are published by the administration.

## Technical Details & Security
- **Framework:** Built with Django (Python).
- **Styling:** Bootstrap 5 with a custom navy and amber color palette.
- **PDF Generation:** Powered by `xhtml2pdf` utilizing specialized, stripped-down templates for pixel-perfect printing.
- **Security:**
  - Strict Role-Based Access Control (RBAC) enforced via a custom `@role_required` decorator on every sensitive view.
  - No raw SQL used; heavily relies on the Django ORM to prevent SQL injection.
  - Fully compliant with Django's `--deploy` checklist (HTTPS, Secure Cookies, HSTS) when `DEBUG = False`.
  - Password hashing and secure token-based password reset flows.

## Local Development Setup

1. **Clone the repository.**
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables:**
   Create a `.env` file in the project root containing:
   ```env
   SECRET_KEY=your-secure-secret-key
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   EMAIL_HOST_USER=your_school_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   ```
5. **Database Setup:**
   ```bash
   python manage.py migrate
   ```
6. **Run the server:**
   ```bash
   python manage.py runserver
   ```
