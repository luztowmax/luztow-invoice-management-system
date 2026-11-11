from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q,Sum
from django.http import FileResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from .models import Customer,Invoice,AuditEvent
from .forms import CustomerForm,InvoiceForm,ItemFormSet,PaymentForm
from .services import issue_invoice,record_payment
from .pdf import generate_invoice_pdf

@staff_member_required(login_url='login')
def dashboard(request):
 invoices=Invoice.objects.select_related('customer').prefetch_related('items','payments')
 active=[i for i in invoices if i.status!=Invoice.Status.CANCELLED]
 return render(request,'invoices/dashboard.html',{'invoice_count':len(active),'issued_total':sum((i.total for i in active if i.status!='draft'),0),'outstanding':sum((i.balance for i in active if i.status in ['issued','part_paid']),0),'recent':list(invoices.order_by('-created_at')[:10])})
@staff_member_required(login_url='login')
def customers(request):
 return render(request,'invoices/customers.html',{'customers':Customer.objects.order_by('name')})
@staff_member_required(login_url='login')
def customer_form(request,pk=None):
 obj=get_object_or_404(Customer,pk=pk) if pk else None
 form=CustomerForm(request.POST or None,instance=obj)
 if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Customer saved.');return redirect('customers')
 return render(request,'invoices/form.html',{'form':form,'heading':'Edit customer' if obj else 'New customer'})
@staff_member_required(login_url='login')
def invoice_list(request):
 qs=Invoice.objects.select_related('customer').order_by('-created_at')
 q=request.GET.get('q','').strip();status=request.GET.get('status','')
 if q:qs=qs.filter(Q(number__icontains=q)|Q(customer__name__icontains=q))
 if status in dict(Invoice.Status.choices):qs=qs.filter(status=status)
 return render(request,'invoices/invoice_list.html',{'invoices':qs[:200],'q':q,'status':status,'statuses':Invoice.Status.choices})
@staff_member_required(login_url='login')
def invoice_create(request):
 invoice=Invoice(created_by=request.user)
 form=InvoiceForm(request.POST or None,instance=invoice)
 formset=ItemFormSet(request.POST or None,instance=invoice,prefix='items')
 if request.method=='POST' and form.is_valid() and formset.is_valid():
  with transaction.atomic():
   invoice=form.save(commit=False);invoice.created_by=request.user;invoice.full_clean();invoice.save()
   formset.instance=invoice;formset.save()
   AuditEvent.objects.create(invoice=invoice,actor=request.user,action='created')
  messages.success(request,'Draft invoice created.');return redirect('invoice_detail',pk=invoice.pk)
 return render(request,'invoices/invoice_form.html',{'form':form,'formset':formset})
@staff_member_required(login_url='login')
def invoice_detail(request,pk):
 invoice=get_object_or_404(Invoice.objects.select_related('customer').prefetch_related('items','payments','events'),pk=pk)
 return render(request,'invoices/invoice_detail.html',{'invoice':invoice,'payment_form':PaymentForm()})
@staff_member_required(login_url='login')
@require_POST
def invoice_issue(request,pk):
 try:issue_invoice(pk,request.user);messages.success(request,'Invoice issued and locked.')
 except ValidationError as e:messages.error(request,' '.join(e.messages))
 return redirect('invoice_detail',pk=pk)
@staff_member_required(login_url='login')
@require_POST
def payment_add(request,pk):
 form=PaymentForm(request.POST)
 if form.is_valid():
  try:record_payment(pk,request.user,form);messages.success(request,'Payment recorded.')
  except ValidationError as e:messages.error(request,' '.join(e.messages))
 else:messages.error(request,'Invalid payment: '+str(form.errors.as_text()))
 return redirect('invoice_detail',pk=pk)
@staff_member_required(login_url='login')
def invoice_pdf(request,pk):
 invoice=get_object_or_404(Invoice.objects.select_related('customer').prefetch_related('items','payments'),pk=pk)
 if invoice.status=='draft':messages.error(request,'Issue the invoice before downloading.');return redirect('invoice_detail',pk=pk)
 return FileResponse(generate_invoice_pdf(invoice),as_attachment=True,filename=f'{invoice.number}.pdf',content_type='application/pdf')

