from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from .models import Customer,Invoice,InvoiceItem
from .services import issue_invoice
class InvoiceTests(TestCase):
 def setUp(self):
  self.user=get_user_model().objects.create_superuser('owner','owner@example.com','test-password-123')
  self.customer=Customer.objects.create(name='Example customer')
  today=timezone.localdate()
  self.invoice=Invoice.objects.create(customer=self.customer,issue_date=today,due_date=today+timedelta(days=14),created_by=self.user,vat_rate=Decimal('7.50'))
  InvoiceItem.objects.create(invoice=self.invoice,description='Consulting',quantity=2,unit_price=Decimal('100.00'))
 def test_totals_and_sequence(self):
  self.assertTrue(self.invoice.number.startswith('LUZ-'))
  self.assertEqual(self.invoice.total,Decimal('215.00'))
 def test_pdf_requires_staff(self):
  self.assertEqual(self.client.get(reverse('invoice_pdf',args=[self.invoice.pk])).status_code,302)
 def test_issue(self):
  issue_invoice(self.invoice.pk,self.user);self.invoice.refresh_from_db();self.assertEqual(self.invoice.status,'issued')
  self.client.force_login(self.user)
  self.assertEqual(self.client.get(reverse('invoice_pdf',args=[self.invoice.pk])).status_code,200)
