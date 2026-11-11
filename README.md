# Luztow Resources Ltd – Private Invoice Portal

## Local setup (Windows PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: replace secret key, add company details, use SQLite locally or PostgreSQL URL
python manage.py makemigrations invoices
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000/accounts/login/ . The Django back office is at /django-admin/ .

## Daily use
1. Sign in as a staff administrator.
2. Add customer under Customers.
3. Create a draft invoice (up to three line rows in this starter UI).
4. Check figures, then **Issue and lock**.
5. Download PDF, send it manually to the customer.
6. Record confirmed payments in the invoice detail page.

Drafts are not downloadable; issued invoices are locked against editing through the custom interface. This starter has no delete/cancel controls and payment records are immutable in the UI. Audit events record invoice creation, issue, and payment.

## Deployment on Render
1. Push this project to a **private** GitHub repository; never commit `.env`.
2. On Render choose New > Blueprint and select this repository; `render.yaml` provisions a Python web service and PostgreSQL database (check plan and billing).
3. Set `COMPANY_*` environment variables in Render to your verified legal company and bank details. Set `DJANGO_ALLOWED_HOSTS` to include both the Render hostname and `invoice.luztowresources.com.ng` during setup; set `DJANGO_CSRF_TRUSTED_ORIGINS` to both HTTPS origins as needed.
4. Once deployed, open Render Shell and run `python manage.py createsuperuser` (or use a one-time secure management job). **Never** create admin credentials in build scripts.
5. In Render, add custom domain `invoice.luztowresources.com.ng` and create the DNS CNAME exactly as Render instructs at your domain registrar. Do not modify the `www` record.
6. Wait for domain verification and HTTPS certificate, then verify login, PDF download, access denial for anonymous visitors, and database persistence.
7. Configure database backups, MFA/SSO via your identity provider or admin access proxy, security monitoring, and periodic restore tests before handling real financial records.

## Important limitations / production hardening
- Uses **NGN only**. VAT is configurable per invoice and defaults to **0%**, because VAT applicability depends on the transaction; get Nigerian tax advice before setting a rate.
- The PDF contains company details from environment variables. Set them correctly; no public invoice links are provided.
- Invoice numbers are generated transactionally; PostgreSQL is recommended for concurrent admins. The initial migration is created by `makemigrations` in the setup steps.
- The current starter supports three line rows and no edit of draft items after save. Add a dynamic formset and a draft-edit view if required.
- Invoice amounts are calculated live from line items; issued invoice items are protected by the application interface, but privileged database access can still alter records. For accounting-grade immutability, store a finalized snapshot and enforce permissions at all write paths.
- The dashboard calculates totals in Python and the invoice list is limited to 200 results; add pagination and aggregate reporting for large datasets.
- Add rate limiting, 2FA, a password reset policy, more detailed audit logging, a private admin network/IP allowlist where practical, error monitoring, and comprehensive tests.
- The app does not integrate with Nigeria's e-invoicing platform or verify regulatory tax compliance. Validate requirements with a qualified accountant before use.
- No automatic email sending or online payments are enabled (Option A).
