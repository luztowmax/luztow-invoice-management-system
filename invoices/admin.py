from django.contrib import admin
from .models import Customer,Invoice,InvoiceItem,Payment,InvoiceSequence,AuditEvent,BankAccount
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):list_display=('name','email','phone');search_fields=('name','email')
class ItemInline(admin.TabularInline):model=InvoiceItem;extra=0;can_delete=False;readonly_fields=('description','quantity','unit_price')
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
 list_display=('number','customer','issue_date','status');list_filter=('status',);search_fields=('number','customer__name');inlines=[ItemInline]
 def has_add_permission(self,request):return False
 def has_change_permission(self,request,obj=None):return False
 def has_delete_permission(self,request,obj=None):return False
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
 list_display=('invoice','amount','method','payment_date');readonly_fields=('invoice','amount','method','payment_date','reference','recorded_by','created_at')
 def has_add_permission(self,request):return False
 def has_change_permission(self,request,obj=None):return False
 def has_delete_permission(self,request,obj=None):return False
@admin.register(AuditEvent)
class AuditAdmin(admin.ModelAdmin):
 list_display=('invoice','actor','action','created_at')
 def has_add_permission(self,request):return False
 def has_change_permission(self,request,obj=None):return False
 def has_delete_permission(self,request,obj=None):return False

from .models import BankAccount

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "bank_name",
        "account_name",
        "account_number",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = (
        "bank_name",
        "account_name",
        "account_number",
    )

