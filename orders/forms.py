from django import forms

from .models import Order, Customer, OrderProduct


class OrderProductForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


OrderProductFormSet = forms.inlineformset_factory(
    Order,
    OrderProduct,
    form=OrderProductForm,
    extra=1,
    can_delete=True,
)


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['order_date', 'customer', 'products',]


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ['user', 'company',]