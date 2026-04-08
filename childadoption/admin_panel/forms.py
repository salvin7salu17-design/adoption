from django import forms

from ca.models import ChildDetails, Organization, UserCust


class BootstrapFormMixin:
    def _apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} form-control".strip()


class AdminUserForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = UserCust
        fields = [
            "username",
            "fname",
            "lname",
            "emailaddress",
            "gender",
            "location",
            "addresss",
            "phone_number",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_organization",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Keep base AbstractUser fields in sync with legacy custom fields.
        instance.first_name = instance.fname or ""
        instance.last_name = instance.lname or ""
        instance.email = instance.emailaddress or ""
        if commit:
            instance.save()
        return instance


class AdminOrganizationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "address", "contact_number", "verification_status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class AdminChildForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ChildDetails
        fields = ["organization", "name", "age", "gender", "since", "blood_group", "education"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()
