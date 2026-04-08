from django import forms 
from ca.models import UserCust,ChildDetails,AdoptionRequest,ChildAppointment,Donation,LifeTimeSponserShip,LifeTimeSponserShipNeeds,Organization
from django.contrib.auth.forms import UserCreationForm
from datetime import date,timedelta
from django.core.exceptions import ValidationError
from datetime import date


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = UserCust
        fields=['fname','lname','emailaddress','gender','phone_number','location','addresss','username']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = user.fname or ''
        user.last_name = user.lname or ''
        user.email = user.emailaddress or ''
        user.user_type = 'User'
        if commit:
            user.save()
        return user


class OrganizationRegisterForm(UserCreationForm):
    organization_name = forms.CharField(max_length=255)
    organization_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    organization_contact_number = forms.CharField(max_length=20)
    organization_image = forms.ImageField()

    class Meta:
        model = UserCust
        fields = [
            'fname', 'lname', 'emailaddress', 'gender', 'phone_number',
            'location', 'addresss', 'username'
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = user.fname or ''
        user.last_name = user.lname or ''
        user.email = user.emailaddress or ''
        user.user_type = 'User'
        user.is_organization = True
        if commit:
            user.save()
            Organization.objects.update_or_create(
                user=user,
                defaults={
                    'name': self.cleaned_data['organization_name'],
                    'address': self.cleaned_data['organization_address'],
                    'contact_number': self.cleaned_data['organization_contact_number'],
                    'image': self.cleaned_data['organization_image'],
                    'verification_status': 'pending',
                    'approved_at': None,
                }
            )
        return user
        
class LoginForm(forms.Form):
    username=forms.CharField()
    password=forms.CharField()

class AdoptionRequestForm(forms.ModelForm):
    child = forms.ModelChoiceField(
        queryset=ChildDetails.objects.none(),
        empty_label="Select a child",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = AdoptionRequest
        fields = [
            "child", "subject", "full_name", "email", "phone", "address", 
            "age", "marital_status", "occupation", "income", 
            "criminal_history", "id_proof", "additional_comments"
        ]
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter age'}),
            'marital_status': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select marital status'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter occupation'}),
            'income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter income'}),
            'criminal_history': forms.Select(attrs={'class': 'form-control'}),
            'id_proof': forms.FileInput(attrs={'class': 'form-control-file'}),
            'additional_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter additional comments'}),
        }

    def __init__(self, *args, **kwargs):
        org_id = kwargs.pop('org_id', None)
        super().__init__(*args, **kwargs)
        if org_id:
            self.fields['child'].queryset = ChildDetails.objects.filter(organization_id=org_id)

    def clean_age(self):
        age = self.cleaned_data['age']
        if age < 18:
            raise forms.ValidationError("Age must be 18 or older.")
        return age
    
class AdoptionRequestFormO(forms.ModelForm):
    class Meta:
        model = AdoptionRequest
        fields = [
        "status"
        ]
        widgets = {
            'status': forms.TextInput(attrs={'class': 'form-control'}),

        }

class ChildForm(forms.ModelForm):
    class Meta:
        model = ChildDetails
        fields = ['name', 'age', 'image', 'gender', 'since', 'blood_group', 'education']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter child name',
                'required': True
            }),
            'age': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter age (e.g., 5 years)',
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'since': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Year child joined (e.g., 2020)',
                'min': '1900',
                'max': '2024',
                'required': True
            }),
            'blood_group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Blood group (optional)'
            }),
            'education': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Education (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make optional fields not required
        self.fields['image'].required = False
        self.fields['blood_group'].required = False
        self.fields['education'].required = False
        
        # Set choices for gender field
        self.fields['gender'].choices = [
            ('', 'Select Gender'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ]

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = UserCust
        fields = ['fname', 'lname', 'emailaddress', 'gender', 'phone_number', 'location','addresss' ]
        
    
class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['organization', 'personal_details', 'category','amount']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount':forms.NumberInput(attrs={'class': 'form-control'}),
        }

from django import forms
from .models import ChildAppointment
from datetime import date, datetime, time, timedelta  # Add this import at the top
from django.core.exceptions import ValidationError

class ChildAppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Calculate tomorrow's date
        tomorrow = date.today() + timedelta(days=1)
        # Set the min attribute for the date field
        self.fields['date'].widget.attrs.update({'min': tomorrow.isoformat()})
        # Add max date (3 months from now)
        max_date = date.today() + timedelta(days=90)
        self.fields['date'].widget.attrs.update({'max': max_date.isoformat()})
        
        # Set time range for business hours (9 AM to 6 PM)
        self.fields['time'].widget.attrs.update({'min': '09:00', 'max': '18:00'})
    
    # Add new fields
    purpose = forms.ChoiceField(
        choices=[
            ('meet', 'Meet the Child'),
            ('discuss', 'Discuss Adoption Process'),
            ('paperwork', 'Documentation Discussion'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='meet'
    )
    
    additional_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requirements or additional information...'
        })
    )
    
    contact_preference = forms.ChoiceField(
        choices=[
            ('phone', 'Phone Call'),
            ('email', 'Email'),
            ('whatsapp', 'WhatsApp'),
            ('any', 'Any')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='phone'
    )
    
    bring_documents = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I will bring required documents'
    )
    
    number_of_people = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Number of people attending'
    )
    
    duration = forms.ChoiceField(
        choices=[
            ('30', '30 minutes'),
            ('60', '1 hour'),
            ('90', '1.5 hours'),
            ('120', '2 hours')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='60',
        label='Preferred duration'
    )
    
    class Meta:
        model = ChildAppointment
        fields = ['date', 'time', 'purpose', 'additional_notes', 'contact_preference', 
                  'bring_documents', 'number_of_people', 'duration']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'placeholder': 'Select appointment date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control', 
                'type': 'time',
                'placeholder': 'Select appointment time'
            }),
        }
        labels = {
            'date': 'Appointment Date',
            'time': 'Appointment Time',
        }
    
    def clean_date(self):
        date_val = self.cleaned_data.get('date')  # Renamed to avoid shadowing
        if date_val:
            # Check if date is at least tomorrow
            tomorrow = date.today() + timedelta(days=1)
            if date_val < tomorrow:
                raise ValidationError("Appointment date must be at least tomorrow.")
            
            # Check if date is not more than 3 months from now
            max_date = date.today() + timedelta(days=90)
            if date_val > max_date:
                raise ValidationError("Appointment date cannot be more than 3 months from now.")
            
            # Check if it's a weekend
            if date_val.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                raise ValidationError("Appointments are not available on weekends. Please select a weekday.")
            
        return date_val
    
    def clean_time(self):
        time_val = self.cleaned_data.get('time')  # Renamed to avoid confusion
        if time_val:
            # Convert time to datetime for comparison
            from datetime import datetime as dt, time as tm
            time_obj = dt.combine(date.today(), time_val)
            start_time = dt.combine(date.today(), tm(9, 0))
            end_time = dt.combine(date.today(), tm(18, 0))
            
            if time_obj < start_time or time_obj > end_time:
                raise ValidationError("Appointments are only available between 9:00 AM and 6:00 PM.")
            
        return time_val

class LifeTimeSponserShipForm(forms.ModelForm):
    class Meta:
        model = LifeTimeSponserShip
        fields = ['date_from', 'date_to']
        widgets = {
            'date_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        # Check if date_to is before date_from
        if date_to and date_to < date_from:
            self.add_error('date_to', 'End date cannot be before start date.')
        return cleaned_data
    

class LifeTimeSponserShipNeedsForm(forms.ModelForm):
    class Meta:
        model = LifeTimeSponserShipNeeds
        fields = ['sponsor_type', 'amount', 'description']

        widgets = {
            'sponsor_type': forms.Select(attrs={'class': 'form-control'}),
            'lifeTimesponserShip': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
