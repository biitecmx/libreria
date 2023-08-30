from django import forms


PAYMENT_CHOICES = (("mercado_pago", "Mercado Pago"), ("paypal", "PayPal"))
SHIPMENT_CHOICES = (("dhl", "DHL"), ("sepomex", "SEPOMEX"), ("local-pickup", "Entrega directa"))


class CheckoutForm(forms.Form):
    names = forms.CharField(required=False)
    last_names = forms.CharField(required=False)
    phone = forms.CharField(max_length=14)
    email = forms.EmailField(required=True)
    shipping_country = forms.CharField(required=False)
    street_address = forms.CharField(required=False)
    shipping_state = forms.CharField(required=False)
    shipping_city = forms.CharField(required=False)
    # shipping_country = CountryField(blank_label="(select country)").formfield(
    #     required=False,
    #     widget=CountrySelectWidget(
    #         attrs={
    #             "class": "custom-select dBooleanField-block w-100",
    #         }
    #     ),
    # )
    shipping_zip = forms.CharField(required=False, max_length=5)
    save_address = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES
    )
    shipping_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=SHIPMENT_CHOICES
    )

class SearchForm(forms.Form):
    query = forms.CharField(max_length=100, required=True)