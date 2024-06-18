from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from util.security.auth_tools import is_admin_provider, is_admin_required

from .models import Order, Customer


class ListOrders(View):
    template_name = "orders/list_orders.html"

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
    #     return render(request, 'orders/list_orders.html', context)


class CreateOrder(View):
    def get(self, request):
        pass
        # return render(request, 'orders/create_order.html', {'primary_title': 'Create Order'})