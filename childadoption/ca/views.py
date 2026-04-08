from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import View
from django.views.generic import UpdateView, ListView, DetailView, TemplateView, CreateView
from ca.models import UserCust, AdoptionRequest, ChildDetails, Organization, ChildAppointment, Donation, SponserShipApplicants, LifeTimeSponserShip, LifeTimeSponserShipNeeds
from ca.forms import UserRegisterForm, LoginForm, UserUpdateForm, ChildForm, AdoptionRequestForm, AdoptionRequestFormO, ChildAppointmentForm, DonationForm, LifeTimeSponserShipForm, LifeTimeSponserShipNeedsForm, OrganizationRegisterForm
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.contrib.auth import get_user_model
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.core.exceptions import ValidationError
from django.conf import settings
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Sum

logger = logging.getLogger(__name__)


def get_verified_organization_or_redirect(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to access this page.")
        return None, redirect("login")

    try:
        organization = Organization.objects.get(user=request.user)
    except Organization.DoesNotExist:
        messages.error(request, "You don't have an organization. Please contact admin.")
        return None, redirect("home")

    if organization.verification_status == 'verified':
        return organization, None

    if organization.verification_status == 'pending':
        messages.warning(request, "Your organization account is waiting for admin approval.")
    else:
        messages.error(request, "Your organization registration was rejected. Please contact admin.")
    return None, redirect("home")

# Initialize Razorpay client
try:
    razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
    razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
    
    if razorpay_key_id and razorpay_key_secret:
        razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        logger.info("Razorpay client initialized successfully")
    else:
        logger.error("Razorpay credentials not found in settings")
        razorpay_client = None
except Exception as e:
    logger.error(f"Failed to initialize Razorpay client: {e}")
    razorpay_client = None

def signin_required(fn):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return fn(request, *args, **kwargs)
        else:
            messages.error(request, "Please login to access this page.")
            return redirect("login")
    return wrapper

class HomeView(View):
    def get(self, request, *args, **kwargs):
        # Check if logged in user is an organization and redirect to org home
        if request.user.is_authenticated:
            try:
                organization = Organization.objects.get(user=request.user)
                if organization.verification_status == 'verified':
                    return redirect("org")
            except Organization.DoesNotExist:
                pass
        
        try:
            organizations = Organization.objects.filter(verification_status='verified')
            
            if request.user.is_authenticated:
                user_id = request.user.id
                user_obj = UserCust.objects.get(id=user_id)
                
        except Exception as e:
            logger.error(f"Error in HomeView: {e}")
            organizations = Organization.objects.filter(verification_status='verified')

        # Payment success/failure handling
        status = request.GET.get('status')
        payment_type = request.GET.get('type')
        payment_id = request.GET.get('payment_id')
        order_id = request.GET.get('order_id')
        signature = request.GET.get('signature')
        code = request.GET.get('code')
        description = request.GET.get('description')

        logger.debug(f"Status: {status}, Type: {payment_type}, Payment ID: {payment_id}, Order ID: {order_id}, Signature: {signature}, Code: {code}, Description: {description}")

        if status == 'success':
            if payment_type == 'donation':
                donation_id = request.GET.get('donation_id')
                logger.debug(f"Donation ID: {donation_id}")
                if donation_id:
                    try:
                        donation = Donation.objects.get(id=donation_id)
                        donation.is_paid = True
                        donation.status = 'paid'
                        donation.save()
                        messages.success(request, "Donation payment successful. Thank you for your generosity!")
                    except Donation.DoesNotExist:
                        messages.error(request, "Donation record not found.")
                else:
                    messages.error(request, "Invalid donation ID.")
            elif payment_type == 'sponsorship':
                sp_child_id = request.GET.get('sp_child_id')
                logger.debug(f"Sponsorship Child ID: {sp_child_id}")
                if sp_child_id:
                    try:
                        sponsorship = SponserShipApplicants.objects.get(id=sp_child_id)
                        sponsorship.is_paid = True
                        sponsorship.save()
                        messages.success(request, "Sponsorship payment successful. Thank you for supporting a child!")
                    except SponserShipApplicants.DoesNotExist:
                        messages.error(request, "Sponsorship record not found.")
                else:
                    messages.error(request, "Invalid sponsorship child ID.")
            elif payment_type == 'need':
                need_id = request.GET.get('need_id')
                if need_id:
                    try:
                        need = LifeTimeSponserShipNeeds.objects.get(id=need_id)
                        need.is_paid = True
                        need.save()
                        messages.success(request, "Need payment successful. Thank you for your support!")
                    except LifeTimeSponserShipNeeds.DoesNotExist:
                        messages.error(request, "Need record not found.")
                else:
                    messages.error(request, "Invalid need ID.")        
        elif status == 'failed':
            messages.error(request, f"{payment_type.capitalize()} payment failed: {description}")

        return render(request, "home.html", {"orgs": organizations})
    
    

class ServiceView(View):
    def get(self, request, *args, **kwargs):
        org_id = kwargs.get('pk')
        return render(request, "service.html", {"org_id": org_id})

class RegisterView(View):
    def get(self, request, *args, **kwargs):
        form = UserRegisterForm()
        return render(request, "register.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.instance.user_type = 'User'
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'register.html', {"form": form})


class OrganizationRegisterView(View):
    def get(self, request, *args, **kwargs):
        form = OrganizationRegisterForm()
        return render(request, "organization_register.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = OrganizationRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Organization registration submitted successfully. Please wait for admin approval before accessing the organization panel.",
            )
            return redirect('login')

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return render(request, "organization_register.html", {"form": form})

class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff or user.is_superuser:
                    # redirect to admin dashboard namespace
                    return redirect('admin_panel:dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid username or password")
                return render(request, 'login.html', {'form': form})
        else:
            messages.error(request, "Form is not valid")
            return render(request, 'login.html', {'form': form})
    

class LogoutView(View):
    def get(self, request, pk, *args, **kwargs):  # Added pk parameter
        logout(request)
        messages.success(request, "Logged out successfully.")
        return redirect("home")

@method_decorator(signin_required, name="dispatch")
class DonationView(View):
    """Step 1: Display donation form and handle form submission"""
    
    def get(self, request, org_id, *args, **kwargs):
        org_obj = get_object_or_404(Organization, id=org_id)
        categories = Donation.category_choices
        
        return render(request, "donation.html", {
            'categories': categories,
            'org': org_obj,
        })

    def post(self, request, org_id, *args, **kwargs):
        print(f"DEBUG: Starting donation POST for org_id: {org_id}")
        print(f"DEBUG: User ID: {request.user.id}")
        print(f"DEBUG: POST data: {dict(request.POST)}")
        
        try:
            # Get organization and user
            org_obj = get_object_or_404(Organization, id=org_id)
            print(f"DEBUG: Organization found: {org_obj.name}")
            
            user_obj = get_object_or_404(UserCust, id=request.user.id)
            print(f"DEBUG: User found: {user_obj.username}")
            
            # Get form data
            category = request.POST.get('category')
            amount = request.POST.get('amount')
            
            print(f"DEBUG: Category: {category}, Amount: {amount}")
            
            # Validate inputs
            if not amount:
                print("DEBUG: Amount is missing")
                messages.error(request, "Amount is required.")
                return redirect('donate', org_id=org_id)
            
            if not category:
                print("DEBUG: Category is missing")
                messages.error(request, "Category is required.")
                return redirect('donate', org_id=org_id)
            
            try:
                amount_in_rupees = int(amount)
                if amount_in_rupees <= 0:
                    print(f"DEBUG: Invalid amount: {amount_in_rupees}")
                    messages.error(request, "Amount must be greater than 0.")
                    return redirect('donate', org_id=org_id)
            except ValueError:
                print(f"DEBUG: Invalid amount format: {amount}")
                messages.error(request, "Please enter a valid amount.")
                return redirect('donate', org_id=org_id)
            
            # Create donation record
            print(f"DEBUG: Creating donation...")
            donation = Donation.objects.create(
                category=category,
                amount=amount_in_rupees,
                personal_details=user_obj,
                organization=org_obj,
                status='pending',
                is_paid=False
            )
            
            print(f"✅ DEBUG: Donation created: ID {donation.id}, Amount: ₹{donation.amount}")
            
            # Redirect to payment processing page
            print(f"DEBUG: Redirecting to process_payment with donation_id={donation.id}")
            return redirect('process_payment', donation_id=donation.id)
            
        except Exception as e:
            print(f"❌ DEBUG: Error in DonationView.post: {str(e)}")
            import traceback
            traceback.print_exc()  # This will show the full error trace
            messages.error(request, f"Error creating donation: {str(e)}")
            return redirect('donate', org_id=org_id)
# Add this to views.py for debugging
def debug_donation_flow(request):
    """Debug view to test donation creation"""
    try:
        # Get first organization
        org = Organization.objects.first()
        if not org:
            return HttpResponse("No organizations found. Please create one first.")
        
        # Get current user
        user = request.user
        
        # Create a test donation
        donation = Donation.objects.create(
            category='education',
            amount=100,
            personal_details=user,
            organization=org,
            status='pending',
            is_paid=False
        )
        
        print(f"DEBUG: Test donation created: {donation.id}")
        
        # Try to redirect to payment page
        return redirect('process_payment', donation_id=donation.id)
        
    except Exception as e:
        return HttpResponse(f"Debug Error: {str(e)}")


@method_decorator(signin_required, name="dispatch")
class ProcessPaymentView(View):
    def get(self, request, donation_id, *args, **kwargs):
        logger.info(f"Processing payment for donation_id: {donation_id}")
        
        try:
            donation = get_object_or_404(Donation, id=donation_id)
            
            if donation.personal_details.id != request.user.id:
                messages.error(request, "You are not authorized to process this payment.")
                return redirect('home')
            
            if donation.is_paid:
                messages.info(request, "This donation has already been paid.")
                return redirect('home')
            
            if donation.amount <= 0:
                messages.error(request, "Invalid donation amount.")
                return redirect('donate', org_id=donation.organization.id)
            
            amount_in_paise = int(donation.amount * 100)
            
            api_key = getattr(settings, 'RAZORPAY_KEY_ID', '')
            razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
            
            # Try to create Razorpay order
            order = None
            razorpay_available = False
            
            if razorpay_client and api_key and razorpay_key_secret:
                try:
                    order_data = {
                        'amount': amount_in_paise,
                        'currency': 'INR',
                        'payment_capture': '1',
                        'notes': {
                            'donation_id': str(donation.id),
                            'user_id': str(request.user.id),
                            'organization': donation.organization.name,
                            'category': donation.category
                        }
                    }
                    
                    logger.info(f"Creating Razorpay order: Amount ₹{donation.amount} ({amount_in_paise} paise)")
                    order = razorpay_client.order.create(order_data)
                    razorpay_available = True
                    logger.info(f"✅ Razorpay order created: {order['id']}")
                    donation.order_id = order['id']
                    donation.save()
                except Exception as e:
                    logger.warning(f"⚠️ Razorpay order creation failed: {e}")
                    # Create fallback order so payment page still works
                    order = {
                        'id': f'order_fallback_{donation.id}_{int(timezone.now().timestamp())}',
                        'amount': amount_in_paise,
                        'currency': 'INR'
                    }
                    razorpay_available = False
                    logger.info(f"Using fallback order for donation {donation.id}")
            else:
                logger.warning("Razorpay client not available - using fallback order")
                # Create fallback order so payment page still works
                order = {
                    'id': f'order_fallback_{donation.id}_{int(timezone.now().timestamp())}',
                    'amount': amount_in_paise,
                    'currency': 'INR'
                }
                razorpay_available = False
            
            # Ensure all required fields are present
            user_name = f"{donation.personal_details.fname or 'User'} {donation.personal_details.lname or ''}".strip()
            user_email = donation.personal_details.emailaddress or donation.personal_details.email or ''
            user_contact = donation.personal_details.phone_number or ''
            
            context = {
                'order_id': order['id'] if order else None,
                'amount': amount_in_paise,
                'amount_display': donation.amount,
                'api_key': api_key if razorpay_available else None,
                'donation': donation,
                'user_name': user_name,
                'user_email': user_email,
                'user_contact': user_contact,
                'organization': donation.organization,
                'razorpay_available': razorpay_available,
            }
            
            logger.info(f"Rendering payment page for donation {donation.id} - Razorpay available: {razorpay_available}")
            return render(request, "payment_checkout.html", context)
            
        except Exception as e:
            logger.error(f"❌ Error in ProcessPaymentView: {e}", exc_info=True)
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('home')

def payment_success(request):
    payment_id = request.GET.get('razorpay_payment_id') or request.GET.get('payment_id')
    order_id = request.GET.get('razorpay_order_id') or request.GET.get('order_id')
    signature = request.GET.get('razorpay_signature') or request.GET.get('signature')
    donation_id = request.GET.get('donation_id')
    
    logger.info(f"Payment success callback - Payment ID: {payment_id}, Order ID: {order_id}, Donation ID: {donation_id}")
    
    donation = None
    if donation_id:
        try:
            donation = Donation.objects.get(id=donation_id)
            
            donation.is_paid = True
            donation.status = 'paid'
            if payment_id:
                donation.payment_id = payment_id
            donation.save()
            
            logger.info(f"✅ Payment successful for donation {donation.id}")
            messages.success(request, f"Thank you for your donation of ₹{donation.amount}!")
            
            try:
                if donation.personal_details.email:
                    send_mail(
                        f'Donation Successful - ₹{donation.amount}',
                        f'''Dear {donation.personal_details.get_full_name()},

Thank you for your generous donation of ₹{donation.amount} to {donation.organization.name}.

Payment Details:
- Amount: ₹{donation.amount}
- Category: {donation.get_category_display()}
- Payment ID: {payment_id or "N/A"}
- Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}

Thank you for making a difference!

Best regards,
Take Care Foundation Team''',
                        settings.EMAIL_HOST_USER,
                        [donation.personal_details.email],
                        fail_silently=True,
                    )
            except Exception as email_error:
                logger.error(f"Failed to send confirmation email: {email_error}")
            
        except Donation.DoesNotExist:
            messages.error(request, "Donation record not found.")
    
    return render(request, 'payment_success.html', {
        'payment_id': payment_id,
        'order_id': order_id,
        'signature': signature,
        'donation': donation
    })

def payment_failure(request):
    code = request.GET.get('code')
    description = request.GET.get('description')
    error = request.GET.get('error')
    
    logger.error(f"Payment failed - Code: {code}, Description: {description}, Error: {error}")
    
    return render(request, 'payment_failure.html', {
        'code': code,
        'description': description,
        'error': error
    })

@method_decorator(signin_required, name="dispatch")
class PrivacyView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "privacy.html")

@method_decorator(signin_required, name="dispatch")
class DonatePayment(View):
    def get(self, request, *args, **kwargs):
        organizations = Organization.objects.all()
        return render(request, "donatepayment.html", {
            'organizations': organizations
        })

class UserProfileEdit(UpdateView):
    template_name = "userprofileedit.html"
    form_class = UserUpdateForm
    model = UserCust
    success_url = reverse_lazy("home")

class UserProfile(DetailView):
    template_name = "userprofile.html"
    form_class = UserUpdateForm
    model = UserCust
    context_object_name = "user"


@method_decorator(signin_required, name="dispatch")
class AdoptionRequestView(View):
    def get(self, request, *args, **kwargs):
        try:
            org_id = kwargs.get("org_id")
            organization = get_object_or_404(Organization, id=org_id)
            form = AdoptionRequestForm(org_id=org_id)
            has_approved_request = AdoptionRequest.objects.filter(
                organization=organization, personal_details=request.user, status='A'
            ).exists()
            return render(request, "adoption.html", {'form': form, 'has_approved_request': has_approved_request, "org_id": org_id})
        except Organization.DoesNotExist:
            return HttpResponse("Organization not found.", status=404)
        except Exception as e:
            print(f"Error: {e}")
            return HttpResponse("An error occurred.", status=500)
    
    def post(self, request, *args, **kwargs):
        try:
            org_id = kwargs.get("org_id")
            organization = get_object_or_404(Organization, id=org_id)
            form = AdoptionRequestForm(request.POST, request.FILES)
            
            if form.is_valid():
                user_obj = UserCust.objects.get(id=request.user.id)
                adoption_request = form.save(commit=False)
                adoption_request.personal_details = user_obj
                adoption_request.organization = organization
                adoption_request.save()
                messages.success(request, "Adoption request submitted successfully!")
                return redirect('ad_rq')
            
            has_approved_request = AdoptionRequest.objects.filter(
                organization=organization, personal_details=request.user, status='A'
            ).exists()
            return render(request, "adoption.html", {'form': form, 'has_approved_request': has_approved_request, "org_id": org_id})
        except Organization.DoesNotExist:
            return HttpResponse("Organization not found.", status=404)
        except UserCust.DoesNotExist:
            return HttpResponse("User not found.", status=404)
        except Exception as e:
            print(f"Error: {e}")
            return HttpResponse("An error occurred.", status=500)
        

@method_decorator(signin_required, name="dispatch")
class SponsorChildView(View):
    def get(self, request, org_id, *args, **kwargs):
        organization = get_object_or_404(Organization, id=org_id)
        
        sponsorship_applicants = SponserShipApplicants.objects.filter(child__organization=organization)
        
        unique_children = {}
        for applicant in sponsorship_applicants:
            if applicant.child_id not in unique_children:
                unique_children[applicant.child_id] = applicant.child
        
        child_list = list(unique_children.values())
        
        return render(request, "sponser.html", {'child_list': child_list, 'organization': organization})

class success_sponcer(TemplateView):
    template_name = "sponsor_success.html"

class OrganizationHome(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                organization = Organization.objects.get(user=request.user)
                childs = ChildDetails.objects.filter(organization=organization).count()
            except Organization.DoesNotExist:
                childs = 0
            context = {
                "childs": childs
            }
        else:
            return redirect('login')
        
        return render(request, "organization_panel.html", context=context)

class OrgHome(View):
    def get(self, request, *args, **kwargs):
        organization, redirect_response = get_verified_organization_or_redirect(request)
        if redirect_response:
            return redirect_response

        childs_count = ChildDetails.objects.filter(organization=organization).count()
        donation_amt = Donation.objects.filter(organization=organization, is_paid=True)
        total_amt = donation_amt.aggregate(total=Sum('amount'))['total'] or 0
            
        context = {
            "childs": childs_count,  # This is the count for the home page
            "total_amt": total_amt,
            "organization": organization,
        }
        return render(request, "org_home.html", context)

class ChildView(View):
    def get(self, request, *args, **kwargs):
        print(f"DEBUG GET: User authenticated: {request.user.is_authenticated}")
        print(f"DEBUG GET: User: {request.user}")
        
        organization, redirect_response = get_verified_organization_or_redirect(request)
        if redirect_response:
            return redirect_response
        print(f"DEBUG GET: Found organization: {organization.name}")
        childs = ChildDetails.objects.filter(organization=organization).order_by('-id')
        print(f"DEBUG GET: Found {childs.count()} childs")

        form = ChildForm()
        return render(request, "org_child.html", {
            'childs': childs, 
            'form': form,
            'organization': organization
        })

    def post(self, request, *args, **kwargs):
        print(f"\n" + "="*60)
        print("DEBUG POST: Child form submission")
        
        organization, redirect_response = get_verified_organization_or_redirect(request)
        if redirect_response:
            return redirect_response
        print(f"DEBUG POST: Organization: {organization.name}")
        
        # Get existing children for context (in case we need to re-render)
        childs = ChildDetails.objects.filter(organization=organization).order_by('-id')
        
        form = ChildForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Save child with organization
                child = form.save(commit=False)
                child.organization = organization
                child.save()
                
                print(f"✅ DEBUG POST: Child saved successfully!")
                print(f"  Name: {child.name}")
                print(f"  Age: {child.age}")
                print(f"  Gender: {child.gender}")
                print(f"  Since: {child.since}")
                print(f"  Organization: {child.organization.name}")
                print(f"  Total children now: {ChildDetails.objects.filter(organization=organization).count()}")
                
                messages.success(request, f"Child '{child.name}' has been added successfully!")
                return redirect('chi')  # Redirect back to child page
                
            except Exception as e:
                print(f"❌ DEBUG POST: Error saving child: {str(e)}")
                messages.error(request, f"Error saving child: {str(e)}")
                # Re-render with errors
                return render(request, "org_child.html", {
                    'childs': childs, 
                    'form': form,
                    'organization': organization
                })
        else:
            print(f"❌ DEBUG POST: Form is NOT valid")
            print(f"Form errors: {form.errors}")
            
            # Show specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Re-render with form errors
            return render(request, "org_child.html", {
                'childs': childs, 
                'form': form,
                'organization': organization
            })
        

class ChildEditView(View):
    def get(self, request, pk, *args, **kwargs):
        child = get_object_or_404(ChildDetails, id=pk)
        if request.user.is_authenticated:
            form = ChildForm(instance=child)
            return render(request, "child_edit.html", {'form': form, 'child': child})
        else:
            return redirect('login')

    def post(self, request, pk, *args, **kwargs):
        child = get_object_or_404(ChildDetails, pk=pk)
        if request.user.is_authenticated:
            form = ChildForm(request.POST, request.FILES, instance=child)
            if form.is_valid():
                form.save()
                messages.success(request, "Child details updated successfully!")
                return redirect('chi')
            return render(request, "child_edit.html", {'form': form, 'child': child})
        else:
            return redirect('login')

class ChildDeleteView(View):
    def get(self, request, pk, *args, **kwargs):
        child = get_object_or_404(ChildDetails, id=pk)
        if request.user.is_authenticated:
            child.delete()
            messages.success(request, "Child deleted successfully!")
            return redirect('chi')
        else:
            return redirect('login')

class AdoptionRequestViewO(View):
    def get(self, request, *args, **kwargs):
        organization, redirect_response = get_verified_organization_or_redirect(request)
        if redirect_response:
            return redirect_response
        adoption_requests = AdoptionRequest.objects.filter(organization=organization).order_by('-id')
        context = {
            'adoption_requests': adoption_requests
        }
        return render(request, "adoption_request.html", context)

class VerifyAdoptionRequest(View):
    def get(self, request, pk, sk, *args, **kwargs):
        adoption_request = get_object_or_404(AdoptionRequest, pk=pk)
        
        if sk == 'A':
            adoption_request.status = 'A'
            messages.success(request, "Adoption request approved.")
        elif sk == 'R':
            adoption_request.status = 'R'
            messages.success(request, "Adoption request rejected.")
        elif sk == 'P':
            adoption_request.status = 'P'
            messages.success(request, "Adoption request marked as pending.")
        
        adoption_request.save()
        return redirect('ad_rst')

class UserAdoptionRequest(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = get_object_or_404(UserCust, id=request.user.id)
        adoption_requests = AdoptionRequest.objects.filter(personal_details=user).order_by('-id')
        
        return render(request, "ad_re.html", {"ad_rq": adoption_requests})

        
class UserChildList(View):
    def get(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            org_obj = get_object_or_404(Organization, id=pk)
            child_objs = ChildDetails.objects.filter(organization=org_obj)
            
            user_appointments = ChildAppointment.objects.filter(user=request.user)
            child_appointments = user_appointments.values_list('child_id', flat=True)
            
        except Organization.DoesNotExist:
            return HttpResponse("Organization not found.", status=404)
        
        form = ChildAppointmentForm()
        return render(request, "user_child_list.html", {
            "child_objs": child_objs,
            "form": form,
            "org_id": pk,
            "child_appointments": list(child_appointments)
        })

class ChildAppointmentView(View):
    def get(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        child = get_object_or_404(ChildDetails, id=pk)
        form = ChildAppointmentForm()
        
        return render(request, "appoinment.html", {
            "form": form,
            "child": child
        })
    
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            ch_obj = get_object_or_404(ChildDetails, id=pk)
            org_id = ch_obj.organization.id
            user_obj = get_object_or_404(UserCust, id=request.user.id)
            
            form = ChildAppointmentForm(request.POST)
            
            if form.is_valid():
                date = form.cleaned_data.get('date')
                
                existing_appointment = ChildAppointment.objects.filter(
                    user=user_obj,
                    child=ch_obj,
                    date=date
                ).exists()
                
                if existing_appointment:
                    messages.error(request, "You have already scheduled an appointment for this child on this date.")
                    return render(request, "appoinment.html", {"form": form, "child": ch_obj})
                
                appointment = form.save(commit=False)
                appointment.user = user_obj
                appointment.child = ch_obj
                appointment.save()
                
                messages.success(request, "Appointment scheduled successfully!")
                return redirect('usr_ch_li', pk=org_id)
            
        except (ChildDetails.DoesNotExist, UserCust.DoesNotExist):
            messages.error(request, "Child or user details not found.")
            return redirect('home')
        
        return render(request, "appoinment.html", {"form": form, "child": ch_obj})
    
    
@method_decorator(signin_required, name="dispatch")   
class AppoinmentListView(View):
    def get(self, request, *args, **kwargs):
        user_obj = get_object_or_404(UserCust, id=request.user.id)
        appointments = ChildAppointment.objects.filter(user=user_obj)
        
        return render(request, "appoinment_list.html", {
            'appointments': appointments
        })

class ChildAppoinmentDeleteView(View):
    def get(self, request, pk, *args, **kwargs):
        appointment = get_object_or_404(ChildAppointment, id=pk)
        
        if request.user.is_authenticated and appointment.user == request.user:
            org_id = appointment.child.organization.id
            
            appointment.delete()
            messages.success(request, "Appointment deleted successfully!")
            
            return redirect('usr_ch_li', pk=org_id)
        else:
            messages.error(request, "You are not authorized to delete this appointment.")
            return redirect('login')
        
class OrgSponserShipApplicants(View):
    def get(self, request, *args, **kwargs):
        try:
            org_obj, redirect_response = get_verified_organization_or_redirect(request)
            if redirect_response:
                return redirect_response
            child_list = SponserShipApplicants.objects.filter(child__organization=org_obj)
            og_childs = ChildDetails.objects.filter(organization=org_obj)
            return render(request, "org_sponser.html", {
                'child_list': child_list,
                "og_childs": og_childs, 
                'organization': org_obj
            })
        except Organization.DoesNotExist:
            return HttpResponseBadRequest("Organization not found")
        except Exception as e:
            logger.error(f"Error in OrgSponserShipApplicants: {e}")
            return HttpResponseBadRequest(f"An error occurred: {str(e)}")

    def post(self, request, *args, **kwargs):
        try:
            child = request.POST.get('child')
            amount = request.POST.get('amount')
            sponsor_category = request.POST.get('sponsor_category')
            
            child_obj = get_object_or_404(ChildDetails, id=child)
            SponserShipApplicants.objects.create(
                child=child_obj,
                sponsor_category=sponsor_category,
                amount=amount
            )
            messages.success(request, "Sponsorship applicant created successfully!")
            return redirect('org_sp')
        except ChildDetails.DoesNotExist:
            messages.error(request, "Child not found")
            return redirect('org_sp')
        except Exception as e:
            logger.error(f"Error creating sponsorship applicant: {e}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('org_sp')

class DeleteSponserShipApplicants(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            sponsorship_applicant = get_object_or_404(SponserShipApplicants, id=pk)
            sponsorship_applicant.delete()
            messages.success(request, "Sponsorship applicant deleted successfully!")
            return redirect('org_sp')
        except SponserShipApplicants.DoesNotExist:
            messages.error(request, "Sponsorship applicant not found.")
            return redirect('org_sp')
        except Exception as e:
            logger.error(f"Error deleting sponsorship applicant: {e}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('org_sp')

class SponserList(View):
    def get(self, request, sp_child, *args, **kwargs):
        child = get_object_or_404(ChildDetails, id=sp_child)
        sponsorship_list = SponserShipApplicants.objects.filter(child=child, is_paid=False).order_by('-id')
       
        return render(request, 'pay_sponser.html', {
            "sponsorship_list": sponsorship_list,
            "child": child
        })

def sponser_payment(request, sp_child):
    try:
        sp_child_obj = SponserShipApplicants.objects.get(id=sp_child)
        amount_paise = sp_child_obj.amount * 100
        
        order = None
        razorpay_available = False
        
        # Try to create Razorpay order
        if razorpay_client:
            try:
                order_data = {
                    'amount': amount_paise,
                    'currency': 'INR',
                    'payment_capture': '1',
                    'notes': {
                        'sponsorship_id': str(sp_child_obj.id),
                        'user_id': str(request.user.id),
                        'child_id': str(sp_child_obj.child.id)
                    }
                }
                order = razorpay_client.order.create(order_data)
                razorpay_available = True
                logger.info(f"✅ Razorpay order created: {order['id']} for sponsorship {sp_child_obj.id}")
            except Exception as e:
                logger.warning(f"⚠️ Razorpay order creation failed: {e}")
                # Create a fallback order ID so payment page can still work
                order = {
                    'id': f'order_fallback_{sp_child_obj.id}_{int(timezone.now().timestamp())}',
                    'amount': amount_paise,
                    'currency': 'INR'
                }
                razorpay_available = False
                logger.info(f"Using fallback order for sponsorship {sp_child_obj.id}")
        else:
            logger.warning("Razorpay client not initialized - using fallback order")
            # Create a fallback order ID so payment page can still work
            order = {
                'id': f'order_fallback_{sp_child_obj.id}_{int(timezone.now().timestamp())}',
                'amount': amount_paise,
                'currency': 'INR'
            }
            razorpay_available = False
        
        context = {
            'sp_child': sp_child_obj,
            'amount_display': sp_child_obj.amount,
            'amount': amount_paise,
            'api_key': settings.RAZORPAY_KEY_ID if razorpay_available else None,
            'order_id': order['id'] if order else None,
            'razorpay_available': razorpay_available,
        }
        
        return render(request, "payment_screen.html", context)
        
    except SponserShipApplicants.DoesNotExist:
        logger.error(f"SponserShipApplicants not found: {sp_child}")
        messages.error(request, "Sponsorship not found.")
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in sponser_payment: {e}")
        messages.error(request, "Error processing payment. Please try again later.")
        return redirect('home')

def payment_success_sp(request):
    payment_id = request.GET.get('payment_id') or request.GET.get('razorpay_payment_id')
    order_id = request.GET.get('order_id') or request.GET.get('razorpay_order_id')
    signature = request.GET.get('signature') or request.GET.get('razorpay_signature')
    sp_child = request.GET.get('sp_child')
    
    sponsorship = None
    if sp_child:
        try:
            sponsorship = SponserShipApplicants.objects.get(id=sp_child)
            sponsorship.is_paid = True
            sponsorship.save()
            messages.success(request, "Sponsorship payment successful!")
        except SponserShipApplicants.DoesNotExist:
            pass
    
    return render(request, 'payment_success_sp.html', {
        'payment_id': payment_id,
        'order_id': order_id,
        'signature': signature,
        'sponsorship': sponsorship
    })

def payment_failure_sp(request):
    code = request.GET.get('code')
    description = request.GET.get('description')
    error = request.GET.get('error')
    
    return render(request, 'payment_failure_sp.html', {
        'code': code,
        'description': description,
        'error': error
    })

@signin_required
def create_sponsorship(request, pk):
    user_obj = get_object_or_404(UserCust, id=request.user.id)
    child_obj = get_object_or_404(ChildDetails, id=pk)

    existing_sponsorship = LifeTimeSponserShip.objects.filter(
        sponser=user_obj, 
        child=child_obj
    ).exists()

    if existing_sponsorship:
        messages.error(request, 'You have already sponsored this child. Please choose another child.')
        return redirect('sponsor_child', org_id=child_obj.organization.id)

    if request.method == 'POST':
        form = LifeTimeSponserShipForm(request.POST)
        if form.is_valid():
            sponsorship = form.save(commit=False)
            sponsorship.child = child_obj
            sponsorship.sponser = user_obj
            sponsorship.save()
            messages.success(request, 'Sponsorship created successfully!')
            return redirect('sponsor_child', org_id=child_obj.organization.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LifeTimeSponserShipForm()

    return render(request, 'life_time.html', {'form': form})

def user_sponser_view(request):
    user_obj = get_object_or_404(UserCust, id=request.user.id)
    current_date = timezone.now().date()
    life_time_sp = LifeTimeSponserShip.objects.filter(sponser=user_obj, date_to__gt=current_date)
    return render(request, 'user_sponsorships.html', {'life_time_sp': life_time_sp})

def life_sponser_need_list(request, pk):
    l_s = get_object_or_404(LifeTimeSponserShip, id=pk)
    life_sposer_needs = LifeTimeSponserShipNeeds.objects.filter(
        lifeTimesponserShip=l_s, 
        is_paid=False
    )
    return render(request, 'needs.html', {
        'life_sposer_needs': life_sposer_needs,
        'lifetime_sponsorship': l_s
    })

def need_payment(request, need_id):
    try:
        need = LifeTimeSponserShipNeeds.objects.get(id=need_id)
        amount_paise = need.amount * 100
        
        order = None
        razorpay_available = False
        
        # Try to create Razorpay order
        if razorpay_client:
            try:
                order_data = {
                    'amount': amount_paise,
                    'currency': 'INR',
                    'payment_capture': '1',
                    'notes': {
                        'need_id': str(need.id),
                        'user_id': str(request.user.id),
                        'sponsorship_id': str(need.lifeTimesponserShip.id)
                    }
                }
                order = razorpay_client.order.create(order_data)
                razorpay_available = True
                logger.info(f"✅ Razorpay order created: {order['id']} for need {need.id}")
            except Exception as e:
                logger.warning(f"⚠️ Razorpay order creation failed for need {need.id}: {e}")
                # Create fallback order so payment page still works
                order = {
                    'id': f'order_fallback_{need.id}_{int(timezone.now().timestamp())}',
                    'amount': amount_paise,
                    'currency': 'INR'
                }
                razorpay_available = False
                logger.info(f"Using fallback order for need {need.id}")
        else:
            logger.warning("Razorpay client not initialized - using fallback order for need")
            # Create fallback order so payment page still works
            order = {
                'id': f'order_fallback_{need.id}_{int(timezone.now().timestamp())}',
                'amount': amount_paise,
                'currency': 'INR'
            }
            razorpay_available = False
        
        context = {
            'need': need,
            'amount_display': need.amount,
            'amount': amount_paise,
            'api_key': settings.RAZORPAY_KEY_ID if razorpay_available else None,
            'order_id': order['id'] if order else None,
            'razorpay_available': razorpay_available,
        }
        
        return render(request, "need_payment.html", context)
        
    except LifeTimeSponserShipNeeds.DoesNotExist:
        logger.error(f"LifeTimeSponserShipNeeds not found: {need_id}")
        messages.error(request, "Need not found.")
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in need_payment: {e}")
        messages.error(request, "Error processing payment. Please try again later.")
        return redirect('home')

def org_donation(request):
    org, redirect_response = get_verified_organization_or_redirect(request)
    if redirect_response:
        return redirect_response
    donations = Donation.objects.filter(organization=org).order_by('-id')
    return render(request, 'org_donation.html', {"dons": donations})

def org_child_appointments(request):
    org, redirect_response = get_verified_organization_or_redirect(request)
    if redirect_response:
        return redirect_response
    appointments = ChildAppointment.objects.filter(child__organization=org).order_by('-id')
    return render(request, 'org_ch_appo.html', {"appoinments": appointments})

def org_child_sponser_list(request):
    org, redirect_response = get_verified_organization_or_redirect(request)
    if redirect_response:
        return redirect_response
    
    sponserships = LifeTimeSponserShip.objects.filter(child__organization=org)
    child_ids = set()
    unique_sponserships = []
    
    for sponsorship in sponserships:
        if sponsorship.child.id not in child_ids:
            unique_sponserships.append(sponsorship)
            child_ids.add(sponsorship.child.id)
    
    return render(request, 'org_child_sponser.html', {"childs": unique_sponserships})

def org_child_detail_sp(request, pk):
    lifetime_sponsership = get_object_or_404(LifeTimeSponserShip, id=pk)
    today = timezone.now().date()
    lifetime_sponserships = LifeTimeSponserShip.objects.filter(
        child=lifetime_sponsership.child, 
        date_to__gte=today
    )
    
    if request.method == 'POST':
        form = LifeTimeSponserShipNeedsForm(request.POST)
        if form.is_valid():
            sponsorship_need = form.save(commit=False)
            sponsorship_need.lifeTimesponserShip = lifetime_sponsership
            sponsorship_need.save()
            messages.success(request, "Sponsorship need added successfully!")
            return redirect('org_csl')
    else:
        form = LifeTimeSponserShipNeedsForm()

    return render(request, 'org_life_t_childs.html', {
        'lifetime_sponserships': lifetime_sponserships,
        'form': form
    })
