from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from util.security.auth_tools import is_admin_provider, is_admin_required

from .models import Order
from .forms import OrderForm


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
            "primary_title": f"{order.customer.user.name} Order, {order.order_date}",
        })


class CreateOrder(View):
    form = OrderForm()
    template_name = "orders/order_form.html"
    context = {
        "primary_title": "Create Order",
        "action": "create",
        "form": form,
    }

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request):
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            return redirect('orders:detail-order', order_id=order.id)
        self.context["form"] = form
        return render(request, self.template_name, self.context)


class EditOrder(View):
    template_name = "orders/order_form.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = OrderForm(instance=order)

        context = {
            "card_image_url": order.card_image_url,
            "stock_image_url": order.stock_image_url,
            "primary_title": f"Edit Order: {order.name}",
            "action": "update", "form": form,
            "order_id": order_id,
        }
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = OrderForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            order.save()
            return redirect('orders:detail-order', order_id=order.id)
        return redirect('orders:edit-order', order_id=order.id)


class DeleteOrder(View):
    template_name = "orders/order_confirm_delete.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        context = {
            "primary_title": f"Delete Order: {order.name}",
            "order": order,
        }
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        return redirect('orders:list-orders')
