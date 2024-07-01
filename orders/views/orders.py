from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from util.security.auth_tools import is_admin_provider, is_admin_required

from orders.models import Order, Customer, Product
from orders.forms import OrderForm, OrderProductFormSet


class ListOrders(View):
    template_name = "orders/order_list.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_provider)
    def get(self, request, is_admin):
        orders = Order.objects.all()

        paginator = Paginator(orders, 9)
        page_number = request.GET.get("page", 1)
        page_orders = paginator.get_page(page_number)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "page_orders": page_orders,
            "primary_title": "Orders",
        })

    # @method_decorator(login_required)
    # def get(self, request):
    #
    #     is_cancelled = request.GET.get('is_cancelled') == True
    #
    #     # orders = Order.objects.filter(customer__id=request.user.id,
    #     #                               is_cancelled=is_cancelled)
    #
    #     orders = Order.objects.all()
    #     print(orders)
    #     # customers = {order.customer_id: get_object_or_404(Customer, id=order.customer_id) for order in orders}
    #
    #     # for customer in customers.values():
    #     #     customer.company = Company.query.get(customer.company_id)
    #     #     customer.user = User.query.get(customer.user_id)
    #
    #     context = {
    #         "primary_title": "Orders",
    #         "orders": orders,
    #         # "customers": customers,
    #     }
    #
    #     return render(request, 'orders/order_list.html', context)


# Display order details
class DetailOrder(View):
    template_name = "orders/order_detail.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_provider)
    def get(self, request, order_id, is_admin):
        order = get_object_or_404(Order, id=order_id)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "order": order,
            "primary_title": f"{order}",
        })


class CreateOrder(View):
    template_name = "orders/order_form.html"

    def get_context_data(self):
        products = Product.objects.all()
        customers = Customer.objects.all()

        return {
            "primary_title": "Create Order",
            "action": "create",
            "form": OrderForm(),
            "formset": OrderProductFormSet(),
            "products": products,
            "customers": customers,
        }

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST)
        formset = OrderProductFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            new_order = form.save(commit=False)
            new_order.author = request.user
            new_order.save()
            order_products = formset.save(commit=False)
            for order_product in order_products:
                if order_product.quantity == 0:
                    order_product.delete()
                else:
                    order_product.order = new_order
                order_product.save()
            formset.save_m2m()

            return redirect('orders:detail-order', order_id=new_order.id)

        context = self.get_context_data()
        context['form'] = form
        context['formset'] = formset
        return render(request, self.template_name, context)


class EditOrder(View):
    template_name = "orders/order_form.html"

    def get_context_data(self, order):
        products = Product.objects.all()
        customers = Customer.objects.all()

        return {
            "primary_title": "Edit Order",
            "action": "update",
            "form": OrderForm(instance=order),
            "formset": OrderProductFormSet(instance=order),
            "products": products,
            "customers": customers,
            "order": order,
        }

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id)
        context = self.get_context_data(order)
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id)
        form = OrderForm(request.POST, instance=order)
        formset = OrderProductFormSet(request.POST, instance=order)

        if form.is_valid() and formset.is_valid():
            order = form.save()
            order_products = formset.save(commit=False)
            for deleted_order in formset.deleted_objects:
                deleted_order.delete()
            for order_product in order_products:
                if order_product.quantity == 0:
                    order_product.delete()
                else:
                    order_product.order = order
                    order_product.save()
            formset.save_m2m()

            return redirect('orders:detail-order', order_id=order.id)

        context = self.get_context_data(order)
        context['form'] = form
        context['formset'] = formset
        return render(request, self.template_name, context)


class DeleteOrder(View):
    template_name = "orders/order_confirm_delete.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        context = {
            "primary_title": f"Delete Order: {order.order_date} by {order.customer.name}",
            "order": order,
        }
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        return redirect('orders:list-orders')
