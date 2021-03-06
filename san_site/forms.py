import datetime

from django import forms
from django.conf import settings

from .cart.cart import Cart, Currency
from .models import Order, OrderItem, Person, Customer, get_person
from .tasks import order_request as task_order_request

import pytz


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class PasswordResetForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput)


class PasswordChangeForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label='Текущий')
    password_new = forms.CharField(widget=forms.PasswordInput, label='Новый')
    password_repeat = forms.CharField(widget=forms.PasswordInput, label='Повтор')


class EnterQuantity(forms.Form):
    def __new__(cls, initial, max_value):
        obj_cls = super().__new__(cls)
        obj_cls.quantity = forms.IntegerField(min_value=1,
                                              max_value=max_value,
                                              required=False,
                                              label='Добавить в заказ')
        obj_cls.base_fields['quantity'] = obj_cls.quantity
        return obj_cls

    def __init__(self, initial, max_value, **kwargs):
        super().__init__(initial, max_value, **kwargs)


class EnterQuantityError(forms.Form):
    pass


class OrdersFilterList(forms.Form):
    begin_date = forms.DateField(widget=forms.DateInput)
    end_date = forms.DateField(widget=forms.DateInput)


class OrderCreateForm(forms.ModelForm):
    customer = forms.ChoiceField(choices=[], required=True, label='Покупатель',
                                 widget=forms.Select(attrs={'style':  'width: 300px;'}))
    delivery = forms.DateField(
        help_text=' если заказ до 15.00 - поставка на следующий день, иначе через день',
        widget=forms.DateInput,
        label='Срок поставки')
    shipment = forms.ChoiceField(choices=Order.SHIPMENT_TYPE, required=True,
                                 initial=Order.SHIPMENT_TYPE[0], label='Способ доставки')
    payment = forms.ChoiceField(choices=Order.PAYMENT_FORM, required=True,
                                initial=Order.PAYMENT_FORM[1], label='Форма оплаты')
    comment = forms.CharField(widget=forms.Textarea, label='Комментарий к заказу', required=False)

    class Meta:
        model = Order
        fields = ['customer', 'delivery', 'shipment', 'payment', 'comment']

    def clean_customer(self):
        guid = self.cleaned_data['customer']
        try:
            return Customer.objects.get(guid=guid)
        except Customer.DoesNotExist:
            raise forms.ValidationError(
                "ошибка! нет такого покупателя"
            )

    def clean_delivery(self):
        now = datetime.date.today()
        if self.cleaned_data['delivery'] <= now:
            raise forms.ValidationError(
                "! на следующий день - заказ до 15.00, иначе через день !"
            )
        delivery = self.cleaned_data['delivery']
        return datetime.datetime(delivery.year, delivery.month, delivery.day, 12, 0, 0) \
            .astimezone(tz=pytz.timezone(settings.TIME_ZONE))

    def clean(self):
        pass

    def save(self, commit=True, **kwargs):
        request = kwargs.get('request', None)
        if request is None:
            return

        cart = Cart(request)
        if len(cart) == 0:
            return

        person = get_person(request.user)
        if person is None:
            return
        if person.lock:
            cart.clear()
            raise Order.LockOrderError
        else:
            person.lock = True

        order = Order.objects.create(
            person=person,
            customer=self.cleaned_data['customer'],
            delivery=self.cleaned_data['delivery'],
            shipment=self.cleaned_data['shipment'],
            payment=self.cleaned_data['payment'],
            comment=self.cleaned_data['comment']
        )
        order.save()

        for item in cart:
            try:
                currency = Currency.objects.get(id=item['currency_id'])
            except Currency.DoesNotExist:
                currency = None
                pass
            item = OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                price_ruble=item['price_ruble'],
                quantity=item['quantity']
            )
            if currency:
                item.currency = currency
            item.save()

        cart.clear()

        if settings.CELERY_NO_CREATE_ORDERS:
            try:
                order.request_order()
            except Order.RequestOrderError:
                pass
        else:
            task_order_request.delay(order.id)

        return order
