from django import forms

from .models import Order, Customer, OrderProduct, ShippingAddress


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
    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        if hasattr(self.instance, 'customer'):
            self.fields['shipping_address'].queryset = ShippingAddress.objects.filter(customer=self.instance.customer)
        else:
            self.fields['shipping_address'].queryset = ShippingAddress.objects.none()

    order_date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = Order
        fields = ['order_date', 'customer', 'shipping_address', 'is_cancelled',]


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ['user', 'company',]


class ShippingAddressForm(forms.ModelForm):

    class Meta:
        model = ShippingAddress
        exclude = ['id', 'customer',]