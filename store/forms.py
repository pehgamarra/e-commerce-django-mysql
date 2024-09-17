from django import forms

class ShippingAddressForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=50)
    last_name = forms.CharField(label='Last Name', max_length=50)
    address_line1 = forms.CharField(label='Address Line 1', max_length=100)
    address_line2 = forms.CharField(label='Complement', max_length=100, required=False)
    city = forms.CharField(label='City', max_length=50)
    state = forms.CharField(label='State', max_length=50)
    postal_code = forms.CharField(label='Postal Code', max_length=20)
    country = forms.CharField(label='Country', max_length=50)
    phone_number = forms.CharField(label='Phone Number', max_length=20)

class PaymentForm(forms.Form):
    card_number = forms.CharField(label='Card Number', max_length=16)
    card_expiry = forms.CharField(label='Expiry Date (MM/YY)', max_length=5)
    card_cvc = forms.CharField(label='CVC', max_length=3)