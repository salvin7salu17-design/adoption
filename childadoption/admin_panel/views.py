from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone

# import models from main app
from ca.models import UserCust, Organization, ChildDetails, AdoptionRequest, Donation, SponserShipApplicants
from .forms import AdminUserForm, AdminOrganizationForm, AdminChildForm


def staff_required(view_func):
	"""Decorator to allow only staff or superuser access."""
	return user_passes_test(lambda u: u.is_authenticated and (u.is_staff or u.is_superuser))(view_func)


@staff_required
def dashboard(request):
	# Simple overview statistics
	context = {
		'user_count': UserCust.objects.count(),
		'org_count': Organization.objects.count(),
		'pending_org_count': Organization.objects.filter(verification_status='pending').count(),
		'child_count': ChildDetails.objects.count(),
		'adoption_count': AdoptionRequest.objects.count(),
		'donation_count': Donation.objects.count(),
		'sponsor_count': SponserShipApplicants.objects.count(),
	}
	return render(request, 'admin_panel/dashboard.html', context)


@staff_required
def user_list(request):
	users = UserCust.objects.all().order_by('id')
	return render(request, 'admin_panel/user_list.html', {'users': users})


@staff_required
def user_detail(request, user_id):
	user_obj = get_object_or_404(UserCust, id=user_id)
	fields = [
		("Username", user_obj.username),
		("First Name", user_obj.fname or user_obj.first_name or "-"),
		("Last Name", user_obj.lname or user_obj.last_name or "-"),
		("Email", user_obj.emailaddress or user_obj.email or "-"),
		("Gender", user_obj.gender or "-"),
		("Location", user_obj.location or "-"),
		("Address", user_obj.addresss or "-"),
		("Phone", user_obj.phone_number or "-"),
		("Active", "Yes" if user_obj.is_active else "No"),
		("Staff", "Yes" if user_obj.is_staff else "No"),
		("Superuser", "Yes" if user_obj.is_superuser else "No"),
		("Organization User", "Yes" if user_obj.is_organization else "No"),
	]
	return render(
		request,
		"admin_panel/entity_detail.html",
		{
			"title": "View User",
			"page_title": "User Details",
			"fields": fields,
			"edit_url": reverse("admin_panel:user_edit", args=[user_obj.id]),
			"delete_url": reverse("admin_panel:user_delete", args=[user_obj.id]),
			"back_url": reverse("admin_panel:user_list"),
		},
	)


@staff_required
def user_edit(request, user_id):
	user_obj = get_object_or_404(UserCust, id=user_id)
	if request.method == "POST":
		form = AdminUserForm(request.POST, instance=user_obj)
		if form.is_valid():
			form.save()
			messages.success(request, f"User #{user_obj.id} updated successfully.")
			return redirect("admin_panel:user_list")
	else:
		form = AdminUserForm(instance=user_obj)

	return render(
		request,
		"admin_panel/entity_form.html",
		{
			"title": "Edit User",
			"page_title": "Edit User",
			"form": form,
			"back_url": reverse("admin_panel:user_list"),
			"submit_label": "Save User",
		},
	)


@staff_required
def user_delete(request, user_id):
	if request.method != "POST":
		return redirect("admin_panel:user_list")

	user_obj = get_object_or_404(UserCust, id=user_id)
	if user_obj.id == request.user.id:
		messages.error(request, "You cannot delete your own account.")
		return redirect("admin_panel:user_list")

	user_obj.delete()
	messages.success(request, f"User #{user_id} deleted successfully.")
	return redirect("admin_panel:user_list")


@staff_required
def organization_list(request):
	orgs = Organization.objects.select_related('user').annotate(children_count=Count('childdetails')).order_by('id')
	total_orgs = orgs.count()
	verified_count = orgs.filter(verification_status='verified').count()
	pending_count = orgs.filter(verification_status='pending').count()
	total_children = ChildDetails.objects.count()
	verified_percent = round((verified_count / total_orgs) * 100) if total_orgs else 0
	return render(
		request,
		'admin_panel/organization_list.html',
		{
			'orgs': orgs,
			'verified_count': verified_count,
			'pending_count': pending_count,
			'total_children': total_children,
			'verified_percent': verified_percent,
		},
	)


@staff_required
def organization_request_list(request):
	org_requests = Organization.objects.select_related('user').filter(
		verification_status__in=['pending', 'rejected']
	).order_by('-created_at', '-id')
	return render(
		request,
		'admin_panel/organization_request_list.html',
		{
			'org_requests': org_requests,
			'pending_count': org_requests.filter(verification_status='pending').count(),
			'rejected_count': org_requests.filter(verification_status='rejected').count(),
		},
	)


@staff_required
def update_organization_status(request, org_id, status):
	if request.method != 'POST':
		return redirect('admin_panel:organization_request_list')

	org = get_object_or_404(Organization, id=org_id)
	if status == 'approve':
		org.verification_status = 'verified'
		org.approved_at = timezone.now()
		org.user.is_organization = True
		org.user.save(update_fields=['is_organization'])
		org.save(update_fields=['verification_status', 'approved_at'])
		messages.success(request, f"{org.name} has been approved successfully.")
	elif status == 'reject':
		org.verification_status = 'rejected'
		org.approved_at = None
		org.save(update_fields=['verification_status', 'approved_at'])
		messages.success(request, f"{org.name} has been rejected.")
	else:
		messages.error(request, "Invalid organization status update.")

	return redirect('admin_panel:organization_request_list')


@staff_required
def organization_detail(request, org_id):
	org = get_object_or_404(Organization, id=org_id)
	fields = [
		("Organization", org.name),
		("Contact Email", org.user.emailaddress or org.user.email or "-"),
		("Contact Number", org.contact_number or "-"),
		("Address", org.address or "-"),
		("Owner Username", org.user.username),
		("Verification Status", org.get_verification_status_display()),
	]
	return render(
		request,
		"admin_panel/entity_detail.html",
		{
			"title": "View Organization",
			"page_title": "Organization Details",
			"fields": fields,
			"edit_url": reverse("admin_panel:organization_edit", args=[org.id]),
			"delete_url": reverse("admin_panel:organization_delete", args=[org.id]),
			"back_url": reverse("admin_panel:organization_list"),
		},
	)


@staff_required
def organization_edit(request, org_id):
	org = get_object_or_404(Organization, id=org_id)
	if request.method == "POST":
		form = AdminOrganizationForm(request.POST, instance=org)
		if form.is_valid():
			form.save()
			messages.success(request, f"Organization #{org.id} updated successfully.")
			return redirect("admin_panel:organization_list")
	else:
		form = AdminOrganizationForm(instance=org)

	return render(
		request,
		"admin_panel/entity_form.html",
		{
			"title": "Edit Organization",
			"page_title": "Edit Organization",
			"form": form,
			"back_url": reverse("admin_panel:organization_list"),
			"submit_label": "Save Organization",
		},
	)


@staff_required
def organization_delete(request, org_id):
	if request.method != "POST":
		return redirect("admin_panel:organization_list")

	org = get_object_or_404(Organization, id=org_id)
	org.delete()
	messages.success(request, f"Organization #{org_id} deleted successfully.")
	return redirect("admin_panel:organization_list")


@staff_required
def child_list(request):
	children = ChildDetails.objects.all().order_by('id')
	return render(request, 'admin_panel/child_list.html', {'children': children})


@staff_required
def child_detail(request, child_id):
	child = get_object_or_404(ChildDetails, id=child_id)
	fields = [
		("Name", child.name),
		("Age", child.age),
		("Gender", child.gender or "-"),
		("Organization", child.organization.name if child.organization else "-"),
		("Since", child.since),
		("Blood Group", child.blood_group or "-"),
		("Education", child.education or "-"),
	]
	return render(
		request,
		"admin_panel/entity_detail.html",
		{
			"title": "View Child",
			"page_title": "Child Details",
			"fields": fields,
			"edit_url": reverse("admin_panel:child_edit", args=[child.id]),
			"delete_url": reverse("admin_panel:child_delete", args=[child.id]),
			"back_url": reverse("admin_panel:child_list"),
		},
	)


@staff_required
def child_edit(request, child_id):
	child = get_object_or_404(ChildDetails, id=child_id)
	if request.method == "POST":
		form = AdminChildForm(request.POST, instance=child)
		if form.is_valid():
			form.save()
			messages.success(request, f"Child #{child.id} updated successfully.")
			return redirect("admin_panel:child_list")
	else:
		form = AdminChildForm(instance=child)

	return render(
		request,
		"admin_panel/entity_form.html",
		{
			"title": "Edit Child",
			"page_title": "Edit Child",
			"form": form,
			"back_url": reverse("admin_panel:child_list"),
			"submit_label": "Save Child",
		},
	)


@staff_required
def child_delete(request, child_id):
	if request.method != "POST":
		return redirect("admin_panel:child_list")

	child = get_object_or_404(ChildDetails, id=child_id)
	child.delete()
	messages.success(request, f"Child #{child_id} deleted successfully.")
	return redirect("admin_panel:child_list")


@staff_required
def adoption_request_list(request):
	requests = AdoptionRequest.objects.all().order_by('-id')
	return render(request, 'admin_panel/adoption_request_list.html', {'requests': requests})


@staff_required
def update_request_status(request, request_id):
    if request.method == 'POST':
        adoption_request = get_object_or_404(AdoptionRequest, id=request_id)
        new_status = request.POST.get('status')
        
        if new_status in ['A', 'R', 'P']:
            adoption_request.status = new_status
            adoption_request.save()
            
            status_display = {'A': 'approved', 'R': 'rejected', 'P': 'pending'}[new_status]
            messages.success(request, f'Adoption request #{request_id} has been {status_display}.')
        else:
            messages.error(request, 'Invalid status update request.')
            
    return redirect('admin_panel:adoption_request_list')


@staff_required
def donation_list(request):
	donations = Donation.objects.all().order_by('-id')
	return render(request, 'admin_panel/donation_list.html', {'donations': donations})


@staff_required
def sponsorship_list(request):
	sponsors = SponserShipApplicants.objects.all().order_by('-id')
	return render(request, 'admin_panel/sponsorship_list.html', {'sponsors': sponsors})


