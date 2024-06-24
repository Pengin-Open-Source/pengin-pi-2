from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from util.security.auth_tools import is_admin_provider, is_admin_required

from orders.models import Customer
from orders.forms import CustomerForm

from companies.models import Company
from main.models import User


class ListCustomers(View):
    template_name = "customers/customer_list.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_provider)
    def get(self, request, is_admin):
        customers = Customer.objects.all()

        paginator = Paginator(customers, 9)
        page_number = request.GET.get("page", 1)
        page_customers = paginator.get_page(page_number)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "page_customers": page_customers,
            "primary_title": "Customers",
        })


class DetailCustomer(View):
    template_name = "customers/customer_detail.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_provider)
    def get(self, request, customer_id, is_admin):
        customer = get_object_or_404(Customer, id=customer_id)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "customer": customer,
            "primary_title": f"{customer.name}",
        })


class CreateCustomer(View):
    template_name = "customers/customer_form.html"

    def get_context_data(self):
        companies = Company.objects.all()
        users = User.objects.all()

        return {
            "primary_title": "Create Customer",
            "action": "create",
            "form": CustomerForm(),
            "companies": companies,
            "users": users,
        }

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, *args, **kwargs):
        form = CustomerForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('customers:detail-customer', customer_id=new_customer.id)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class EditCustomer(View):
    template_name = "customers/customer_form.html"

    def get_context_data(self, customer):
        companies = Company.objects.all()
        users = User.objects.all()

        return {
            "primary_title": "Edit Customer",
            "action": "update",
            "form": CustomerForm(instance=customer),
            "companies": companies,
            "users": users,
            "customer": customer,
        }

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, customer_id, *args, **kwargs):
        customer = get_object_or_404(Customer, id=customer_id)
        context = self.get_context_data(customer)
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, customer_id, *args, **kwargs):
        customer = get_object_or_404(Customer, id=customer_id)
        form = CustomerForm(request.POST, instance=customer)

        if form.is_valid():
            form.save()
            return redirect('customers:detail-customer', customer_id=customer.id)

        context = self.get_context_data(customer)
        context['form'] = form
        return render(request, self.template_name, context)


class DeleteCustomer(View):
    template_name = "customers/customer_confirm_delete.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, id=customer_id)
        context = {
            "primary_title": f"Delete Customer: {customer.name}",
            "customer": customer,
        }
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, customer_id):
        customer = get_object_or_404(Customer, id=customer_id)
        customer.delete()
        return redirect('customers:list-customers')
