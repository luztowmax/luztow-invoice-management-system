
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction, IntegrityError
from django.db.models import Sum
from django.utils import timezone


CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(
        CENT,
        rounding=ROUND_HALF_UP
    )


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class InvoiceSequence(models.Model):
    year = models.PositiveIntegerField(unique=True)
    last_number = models.PositiveIntegerField(default=0)


class Invoice(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PART_PAID = "part_paid", "Partially paid"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="invoices"
    )

    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    apply_vat = models.BooleanField(
        default=False,
        verbose_name="Apply 7.5% VAT to Service Charge"
    )

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_invoices"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if (
            self.due_date
            and self.issue_date
            and self.due_date < self.issue_date
        ):
            raise ValidationError({
                "due_date": "Due date must not precede issue date."
            })

        if self.vat_rate is not None and not (
            Decimal("0") <= self.vat_rate <= Decimal("100")
        ):
            raise ValidationError({
                "vat_rate": "VAT rate must be between 0 and 100."
            })

    def save(self, *args, **kwargs):
        if self.pk or self.number:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            try:
                with transaction.atomic():
                    InvoiceSequence.objects.get_or_create(
                        year=self.issue_date.year
                    )
            except IntegrityError:
                pass

            seq = InvoiceSequence.objects.select_for_update().get(
                year=self.issue_date.year
            )

            seq.last_number += 1
            seq.save(update_fields=["last_number"])

            self.number = (
                f"LUZ-{self.issue_date.year}-"
                f"{seq.last_number:05d}"
            )

            return super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return money(
            sum(
                (item.line_total for item in self.items.all()),
                Decimal("0.00")
            )
        )

    @property
    def vat_amount(self):
        if not self.apply_vat:
            return Decimal("0.00")

        service_charge_total = sum(
            (
                item.line_total
                for item in self.items.all()
                if item.description.strip().casefold()
                == "service charge"
            ),
            Decimal("0.00")
        )

        return money(
            service_charge_total * Decimal("0.075")
        )

    @property
    def total(self):
        return money(self.subtotal + self.vat_amount)

    @property
    def amount_paid(self):
        return money(
            self.payments.aggregate(
                s=Sum("amount")
            )["s"] or 0
        )

    @property
    def balance(self):
        return money(self.total - self.amount_paid)

    @property
    def overdue(self):
        return (
            self.status in [
                self.Status.ISSUED,
                self.Status.PART_PAID
            ]
            and self.due_date < timezone.localdate()
            and self.balance > 0
        )

    def __str__(self):
        return self.number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        on_delete=models.CASCADE
    )

    description = models.CharField(max_length=255)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({
                "quantity": "Quantity must be positive."
            })

        if self.unit_price is not None and self.unit_price < 0:
            raise ValidationError({
                "unit_price": "Price cannot be negative."
            })

    @property
    def line_total(self):
        return money(self.quantity * self.unit_price)


class Payment(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name="payments",
        on_delete=models.PROTECT
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    payment_date = models.DateField(
        default=timezone.localdate
    )

    method = models.CharField(
        max_length=30,
        choices=[
            ("bank", "Bank transfer"),
            ("cash", "Cash"),
            ("other", "Other")
        ]
    )

    reference = models.CharField(
        max_length=120,
        blank=True
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                "amount": "Amount must be positive."
            })

    def __str__(self):
        return f"{self.invoice.number}: {self.amount}"


class AuditEvent(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="events"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    action = models.CharField(max_length=80)
    details = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]


class BankAccount(models.Model):
    bank_name = models.CharField(max_length=150)
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=30)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
