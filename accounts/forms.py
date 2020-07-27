from django import forms
from bootstrap_datepicker_plus import DateTimePickerInput, DatePickerInput
from django.forms import ModelForm
from .models import Account

class GetDateForm(forms.Form):

    startdate = forms.DateField(
        widget=DatePickerInput(format='%m/%d/%Y')
    )
    enddate = forms.DateField(
        widget=DatePickerInput(format='%m/%d/%Y')
    )


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account

        exclude =('user',)
        widgets = {
            'date': DatePickerInput(), # default date-format %m/%d/%Y will be used
        }
