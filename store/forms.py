from django import forms

class ShippingAddressForm(forms.Form):
    street_address = forms.CharField(label='Street Address', max_length=255)
    city = forms.CharField(label='City', max_length=100)
    state = forms.CharField(label='State', max_length=100)
    postal_code = forms.CharField(label='Postal Code', max_length=20)
    country = forms.CharField(label='Country', max_length=100)
