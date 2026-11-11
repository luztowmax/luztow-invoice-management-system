from django import forms
from django.forms import inlineformset_factory
from .models import Customer,Invoice,InvoiceItem,Payment
class StyledForm:
 def style(self):
  for f in self.fields.values(): f.widget.attrs['class']='form-control'
class CustomerForm(StyledForm,forms.ModelForm):
 class Meta: model=Customer;fields=['name','email','phone','address','tax_id']
 def __init__(self,*a,**kw): super().__init__(*a,**kw);self.style()
class InvoiceForm(StyledForm,forms.ModelForm):
 class Meta:
  model=Invoice;fields=['customer','issue_date','due_date','apply_vat','notes'];widgets={'issue_date':forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'),'due_date':forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d')}
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.style();self.fields['issue_date'].input_formats=['%Y-%m-%d'];self.fields['due_date'].input_formats=['%Y-%m-%d']
class ItemForm(StyledForm,forms.ModelForm):
 class Meta: model=InvoiceItem;fields=['description','quantity','unit_price']
 def __init__(self,*a,**kw): super().__init__(*a,**kw);self.style()
ItemFormSet=inlineformset_factory(Invoice,InvoiceItem,form=ItemForm,extra=3,can_delete=True,min_num=1,validate_min=True)
class PaymentForm(StyledForm,forms.ModelForm):
 class Meta: model=Payment;fields=['amount','payment_date','method','reference'];widgets={'payment_date':forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d')}
 def __init__(self,*a,**kw): super().__init__(*a,**kw);self.style();self.fields['payment_date'].input_formats=['%Y-%m-%d']
 class InvoiceForm(forms.ModelForm):
    new_customer_name = forms.CharField(
        max_length=200,
        required=False,
        label="New customer name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter new customer name",
        }),
    ) 
class Meta:
    model = Invoice

    fields = [
        "customer",
        "issue_date",
        "due_date",
        "apply_vat",
        "notes",
    ]

    widgets = {
        "issue_date": forms.DateInput(
            attrs={"type": "date"}
        ),
        "due_date": forms.DateInput(
            attrs={"type": "date"}
        ),
        "apply_vat": forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    }

def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.style()

        self.fields["issue_date"].input_formats = [
            "%Y-%m-%d"
        ]

        self.fields["due_date"].input_formats = [
            "%Y-%m-%d"
        ]

        # Keep checkbox styling separate
        self.fields["apply_vat"].widget.attrs["class"] = (
            "form-check-input"
        )


def clean(self):
    cleaned_data = super().clean()

    customer = cleaned_data.get("customer")
    new_name = (
        cleaned_data.get("new_customer_name") or ""
    ).strip()

    if not customer and not new_name:
        raise forms.ValidationError(
            "Select an existing customer or "
            "enter a new customer name."
        )

    return cleaned_data
