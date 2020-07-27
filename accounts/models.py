from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name = "account", null=True)
    account_name = models.CharField (max_length = 200, default='')
    account_type = models.CharField (max_length = 200, default='')
    initial_balance = models.FloatField()
    date = models.DateField()
    
    def get_absolute_url(self):
        return reverse('accounts-index', args=[self.id])

    def __str__(self):
       return '%s' %(self.account_name)


