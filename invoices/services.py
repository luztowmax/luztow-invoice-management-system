from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Invoice,Payment,AuditEvent
@transaction.atomic
def issue_invoice(invoice_id,user):
 invoice=Invoice.objects.select_for_update().get(pk=invoice_id)
 if invoice.status!=Invoice.Status.DRAFT: raise ValidationError('Only draft invoices may be issued.')
 if not invoice.items.exists(): raise ValidationError('Add at least one invoice item.')
 if invoice.total<=0: raise ValidationError('Invoice total must be positive.')
 invoice.status=Invoice.Status.ISSUED;invoice.save(update_fields=['status','updated_at'])
 AuditEvent.objects.create(invoice=invoice,actor=user,action='issued')
 return invoice
@transaction.atomic
def record_payment(invoice_id,user,form):
 invoice=Invoice.objects.select_for_update().get(pk=invoice_id)
 if invoice.status not in [Invoice.Status.ISSUED,Invoice.Status.PART_PAID]: raise ValidationError('Invoice must be issued and unpaid.')
 amount=form.cleaned_data['amount']
 if amount<=0 or amount>invoice.balance: raise ValidationError('Payment must be positive and not exceed the outstanding balance.')
 payment=form.save(commit=False);payment.invoice=invoice;payment.recorded_by=user;payment.full_clean();payment.save()
 invoice.status=Invoice.Status.PAID if invoice.balance==0 else Invoice.Status.PART_PAID
 invoice.save(update_fields=['status','updated_at'])
 AuditEvent.objects.create(invoice=invoice,actor=user,action='payment_recorded',details=f'{payment.amount} via {payment.method}')
 return payment
