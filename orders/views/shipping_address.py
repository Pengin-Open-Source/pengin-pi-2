from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from util.security.auth_tools import is_admin_required

from orders.models import ShippingAddress, Customer
from orders.forms import ShippingAddressForm


class CreateShippingAddress(View):
    template_name = "shipping_address/shipping_address_form.html"

    def get_context_data(self):
        customer_id = self.kwargs.get('customer_id')
        customer = get_object_or_404(Customer, id=customer_id)
        return {
            "primary_title": f"Create Shipping Address for {customer}",
            "action": "create",
            "form": ShippingAddressForm(),
            "customer_id": customer_id,
        }

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, *args, **kwargs):
        form = ShippingAddressForm(request.POST)

        if form.is_valid():
            new_address = form.save(commit=False)
            new_address.customer = get_object_or_404(Customer, id=kwargs.get('customer_id'))
            new_address.save()
            return redirect('customers:detail-customer', customer_id=new_address.customer.id)

        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class EditShippingAddress(View):
    template_name = "shipping_address/shipping_address_form.html"

    def get_context_data(self, address):
        customer_id = self.kwargs.get('customer_id')
        customer = get_object_or_404(Customer, id=customer_id)
        return {
            "primary_title": f"Edit Shipping Address for {customer}",
            "action": "update",
            "form": ShippingAddressForm(instance=address),
            "customer_id": customer_id,
        }

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, address_id, *args, **kwargs):
        address = get_object_or_404(ShippingAddress, id=address_id)
        context = self.get_context_data(address)
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, address_id, *args, **kwargs):
        address = get_object_or_404(ShippingAddress, id=address_id)
        form = ShippingAddressForm(request.POST, instance=address)

        if form.is_valid():
            address = form.save(commit=False)
            address.customer = get_object_or_404(Customer, id=kwargs.get('customer_id'))
            address.save()
            return redirect('customers:detail-customer', customer_id=address.customer.id)

        context = self.get_context_data(address)
        context['form'] = form
        return render(request, self.template_name, context)
