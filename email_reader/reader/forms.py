from django import forms
class AccountSettingsForm(forms.Form):
    accounts = forms.CharField(label='Accounts', widget=forms.Textarea)
    num_messages = forms.IntegerField(label='Number of Messages')