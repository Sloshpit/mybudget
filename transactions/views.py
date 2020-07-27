from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.template import loader
from django.db.models import Sum
from .models import Transaction
from budgettracker.models import BudgetTracker
from categories.models import Category
from accounts.models import Account
from accounthistory.models import AccountHistory
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from .forms import CreateTransactionForm, UpdateTransactionForm
from django.shortcuts import render, redirect, reverse
from datetime import datetime, date, timedelta
from calendar import monthrange
import calendar
from mybudget.common import get_first_of_month, get_last_of_month, get_first_of_next_month
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from dateutil import tz
from django.utils import timezone
@login_required


def index(request):
    template = loader.get_template('transactions/index.html')
    today = datetime.today()
    enddate = get_last_of_month (today)
    startdate = get_first_of_month(today)
    show_transactions = Transaction.objects.filter(user=request.user).order_by('-trans_date')
    total = Transaction.objects.filter(trans_date__range=[startdate, enddate], user=request.user).aggregate(sum=Sum('amount'))['sum'] or 0.00
    total = "{:.2f}".format(total)

    context = {
        'show_transactions':show_transactions,
        'total': total,
    }
    return HttpResponse(template.render(context, request))

class TransactionCreate (LoginRequiredMixin, CreateView):

     template_name = 'transactions/transaction_form.html'
     form_class = CreateTransactionForm
     success_url = reverse_lazy('transaction-index') 
     model = Transaction
     def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(logged_user_id=self.request.user.id)

        return kwargs

     def form_valid(self, form):
        now = datetime.today()
        now_string = now.strftime('%Y-%m-%d %H:%M:%S')
        store = form.cleaned_data ['store']
        category = form.cleaned_data ['category']
        acct_name = form.cleaned_data['account_name']
        amount = form.cleaned_data['amount']
        trans_date = form.cleaned_data['trans_date']
        trans_date_no_time_string = str(trans_date.year)+'-' + str(trans_date.month) + '-'+ str(trans_date.day)
        trans_date_no_time = trans_date
        form.instance.user = self.request.user   
        user_id = self.request.user.id
        self.object = form.save()
     #   bud_date = str(trans_date.year) +"-" +str(trans_date.month) + "-"+ "1"
        bud_date = get_first_of_month(trans_date)
        #create a category budget for a transaction if it does not exist
 #       if (str(category) != 'Income' and str(category) !='Initial Balance'):
 #           print ('--------inside not!!!!!!!!!--------')
 #           if not BudgetTracker.objects.filter(date=bud_date, user=self.request.user, category__category=category).exists():
 #               budget_does_not_exist = 'Create a budget for this category before adding a transaction'
 #               bud_amount = amount
 #               if amount < 0:
 #                   bud_amount = bud_amount *-1
 #               new_budget = BudgetTracker(category=category, budget_amount = bud_amount, monthly_spend = '0', date = bud_date, user=self.request.user)
 #               new_budget.save()
        # get the latest account balance based on the transaction date.  This should account for a present record and going into the past.

        #latest_account = AccountBalance.objects.filter(account__account_name=acct_name).values('account__account_name', 'balance', 'balance_date').latest('balance_date')
       # get all accounts that are gte transaction
       
       
        latest_account = AccountHistory.objects.filter(account__account_name = acct_name, balance_date__lte=trans_date, account__user=self.request.user).values('account__account_name', 'balance', 'ate').order_by("-date")[0]
        print (latest_account)
        print('--------latest acount----')

        latest_account_date = latest_account['date']
        print (trans_date_no_time)
        if latest_account_date == trans_date:
            #just update the existing balance if a balance exists for date the transaction is suppsoed to 
            new_balance = latest_account['balance'] + amount
            print ('latest account balance:')
            print (latest_account['balance'])
            print ('new balance:')
            print (new_balance)
            update_account = AccountHistory.objects.filter(account__account_name = acct_name, balance_date=trans_date, account__user=self.request.user).update(balance = new_balance)
            print ('update')
            print (update_account)
            records_to_update = AccountHistory.objects.filter(account__account_name=acct_name, account__user=self.request.user, balance_date__gt=trans_date)
            print ('records to update:')
            print (records_to_update)
        #update all potential future record balances
            for record in records_to_update:
                record.balance = record.balance + amount
                record.save() 
            # create a new record for account history
            print ('----new balance before account history add')
            print (new_balance)
            print (trans_date)
            print (latest_account['balance'])
      #      new_account_history_record = AccountHistory(user=self.request.user, account = acct_name, transaction=self.object, date=trans_date, balance = new_balance)
      #      new_account_history_record.save()
            new_acct_records_to_update = AccountHistory.objects.filter(account=acct_name, user=self.request.user, date__gt=trans_date, date__lte = now)
            print ('-----new acct records to update------')
            print (new_acct_records_to_update)
            for record in new_acct_records_to_update:
                print (record.balance)
                record.balance = record.balance + amount
                record.save()

        else:
            print ('-------IN ELSE?????')
        #create a new balance record if one doesn't exist for that date
            balance_description = str(store) +" "+ str(category)
            new_account_balance=amount + float(latest_account['balance'])   
            print('new account balance-----')
            print (new_account_balance)     
      #      new_record = AccountBalance(account=acct_name, balance_description = balance_description, balance=new_account_balance, balance_date=trans_date)
      #      new_record.save()
            new_account_history_record = AccountHistory(user=self.request.user, account = acct_name, transaction=self.object, date=trans_date, balance = new_account_balance)
            new_account_history_record.save() 
            new_acct_records_to_update = AccountHistory.objects.filter(account=acct_name, user=self.request.user, date__gt=trans_date, date__lte = now)
       #     records_to_update = AccountBalance.objects.filter(account__account_name=acct_name, account__user=self.request.user,balance_date__gt=trans_date, balance_date__lte = now.date())
            print ('----new account history reords to update ------')
            print (new_acct_records_to_update)
            print (records_to_update)
        #update any potential future records
        #    for record in records_to_update:
        #        record.balance = record.balance + amount
         #       record.save() 

            for record in new_acct_records_to_update:
                record.balance = record.balance + amount
                record.save()

        first_of_month = get_first_of_month(trans_date)

        next_first_of_month = get_first_of_next_month(trans_date)
 #get all transactions for this month, get the budget for the category, do the math on that category
        transaction_spend = Transaction.objects.filter(category__category = category, trans_date__range = [first_of_month, trans_date], user=self.request.user).aggregate(sum=Sum('amount'))['sum'] or 0.00
        print ('transaction spend so far--------------:')
        print (transaction_spend)

        category_budget = BudgetTracker.objects.filter(category__category = category, date__range = [first_of_month, trans_date], user=self.request.user)

        #category_spend = budget_amount - transaction_spend
        print ('cagegory_budget no user')
        print (category_budget)           
        for spend in category_budget:
             print ('inside loop------------')
             print (spend.monthly_spend)
             spend.monthly_spend = transaction_spend
             print (spend.monthly_spend)
             spend.save()
        
        check_category_carryover = Category.objects.filter(category=category, user=self.request.user).values('carry_over')
        print ('check_category_carryover-------')
        print (category)
        print (check_category_carryover)
        if check_category_carryover:
            category_budget_next = BudgetTracker.objects.filter(category__category = category, date = next_first_of_month, user=self.request.user)
            # if a budget doesn't exist for a category budget then create a new one
            if not category_budget_next:
                #get current month budget amount
                #
                print ('category_budget next month:')
                print (category_budget)

                for budget in category_budget:
                    budget_current_month = budget.budget_amount + amount
                    BudgetTracker.objects.create(category=budget.category, date = next_first_of_month, user=self.request.user, budget_amount=budget_current_month)
            # otherwise update the next month budget
            else:
                for budget in category_budget_next:
                     print (budget.monthly_spend)
                     budget.budget_amount =  budget.budget_amount +  amount
                     budget.save()      

        print ('-------end of create Transaction class')             
        return super().form_valid(form)

    #fields = '__all__'

class TransactionUpdate (LoginRequiredMixin, UpdateView):
    template_name = 'transactions/transaction_update.html'
    form_class = UpdateTransactionForm
    success_url = reverse_lazy('transaction-index') 
    #form = CreateTransactionForm
    #success_url = reverse_lazy ('transaction-index')
    model = Transaction
    #fields = ['store', 'description', 'amount','trans_date', 'category', 'account_name']
    #get the date of the transaction
    #get all the transactions from that date to present date (today)
    #perform calculation on the updated balance for each
    #write the balance to the db, along with any other changes.
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(logged_user_id=self.request.user.id)
        return kwargs
        
    def form_valid(self, form):
        self.object = self.get_object()
        today = datetime.today()
        store = form.cleaned_data ['store']
        category = form.cleaned_data ['category']
        acct_name = form.cleaned_data['account_name']
        amount = form.cleaned_data['amount']
        print ('------AMOUNT')
        print (amount)
        print (self.object.amount)
        if amount < 0:
            print ('less than zero amount')
            amount = amount *-1        
            amount_difference = amount + self.object.amount
        else:
            print ('greater than zero amount')
            amount_difference = self.object.amount - amount

        print ('--------amount difference------')
        print (amount_difference)
        trans_date = form.cleaned_data['trans_date']
        trans_date_no_time_string = str(trans_date.year)+'-' + str(trans_date.month) + '-'+ str(trans_date.day)
        trans_date_no_time = trans_date     
        self.object = form.save()

        acct_history_records = AccountHistory.objects.filter (account=acct_name, date__range = [trans_date, today], user=self.request.user)
        balance_records = AccountBalance.objects.filter(account__account_name=acct_name, balance_date__range = [trans_date_no_time, today], account__user=self.request.user )
        print (balance_records)
        print (acct_history_records)
        for record in balance_records:
            record.balance = record.balance - amount_difference
            print (record.balance)
            record.save()
  
        for record in acct_history_records:
            record.balance = record.balance - amount_difference
            record.save()            
   #get all transactions for this month, get the budget for the category, do the math on that category      
        first_of_month = get_first_of_month(trans_date)
        next_first_of_month = get_first_of_next_month(trans_date)
        transaction_spend = Transaction.objects.filter(category__category = category, trans_date__range = [first_of_month, trans_date], user=self.request.user).aggregate(sum=Sum('amount'))['sum'] or 0.00
        category_budget = BudgetTracker.objects.filter(category__category = category, date__range = [first_of_month, trans_date], user=self.request.user)
        category_budget_next_month = BudgetTracker.objects.filter(category__category = category, date = next_first_of_month, user=self.request.user)

        #category_spend = budget_amount - transaction_spend
  
        for spend in category_budget:
             spend.monthly_spend = transaction_spend
             spend.save()
             for budget in category_budget_next_month:
                 print (spend.budget_amount)
                 print (budget.budget_amount)
                 budget.budget_amount = spend.budget_amount + transaction_spend
                 print (budget.budget_amount)
                 budget.save()


       # for budget in category_budget:
       #     budget.budget_amount =  budget.budget_amount + transaction_spend
       #     budget.save()        

        return super().form_valid(form)

class TransactionDelete (LoginRequiredMixin, DeleteView):
    model = Transaction
    form_class = CreateTransactionForm
    #success_url = reverse_lazy('transaction-index') 
    template_name = 'transactions/transaction_delete.html'
#    context_object_name = 'transaction'
    success_url = reverse_lazy('transaction-index')
    #fields ='__all__'


    def delete(self, *args, **kwargs):
        today = datetime.today()
        self.object = self.get_object()
        print (self.object)
        amount = self.object.amount
        trans_date = self.object.trans_date
        acct_name = self.object.account_name
        category = self.object.category
        print ('user!!')
        user = self.object.user
        print (user)
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/New_York')        
        print ('---------Transaciton date------------')
        print (trans_date)
        print (today)
      #  trans_date = (timezone.localtime(trans_date))
#        trans_date = form.cleaned_data['trans_date']
        trans_date_no_time_string = str(trans_date.year)+'-' + str(trans_date.month) + '-'+ str(trans_date.day)
        trans_date_no_time = trans_date    
        print ('----transactiondate no time')
        print (trans_date_no_time)


 #   account_record_to_delete = AccountBalance.objects.filter(account__user=user,balance_date=trans_date, account=acct_name).delete()
        print ('----SUER a')
        print (user)
        print (acct_name)
        records_to_update = AccountBalance.objects.filter(account__user=user, account=acct_name, balance_date__range=[trans_date_no_time, today])       
        acct_hist_records_to_update = AccountHistory.objects.filter(user=user, account=acct_name, date__gt=trans_date, date__lte = today)
        print ('records to update')
        print (records_to_update)
        for record in records_to_update:
            print ('-----record balance')
            print (record.balance)
            record.balance = record.balance - amount
            print (amount)
            print (record.balance)
            record.save()

        for record in acct_hist_records_to_update:
            record.balance = record.balance - amount
            record.save()            
   #get all transactions for this month, get the budget for the category, do the math on that category      
        first_of_month = get_first_of_month(trans_date)
        next_first_of_month = get_first_of_next_month(trans_date)
        transaction_spend = Transaction.objects.filter(user=user, category__category = category, trans_date__range = [first_of_month, trans_date]).aggregate(sum=Sum('amount'))['sum'] or 0.00

        category_budget = BudgetTracker.objects.filter(user=user, category__category = category, date__range = [first_of_month, trans_date])
        category_budget_next_month = BudgetTracker.objects.filter(user=user,category__category = category, date = next_first_of_month)

        #category_spend = budget_amount - transaction_spend
  
        for spend in category_budget:
             spend.monthly_spend = spend.monthly_spend - amount
             spend.save()
             for budget in category_budget_next_month:
                 budget.budget_amount = budget.budget_amount - amount
                 budget.save()

        return super(TransactionDelete, self).delete(*args, **kwargs)

class TransactionList (LoginRequiredMixin, ListView): 
    template_name = 'transactions/index.html'
    form_class = CreateTransactionForm
    success_url = reverse_lazy ('transaction-index')
    model = Transaction
    context_object_name = 'show_transactions'
    fields ='__all__'

def get_account (request):
    print ('inside get account')
    account = request.GET.get('account', None)
    the_date = AccountBalance.objects.filter(account__id=account, account__user=request.user).values('balance_date').order_by('-balance_date').last()
    formatted_date = (str(the_date['balance_date'].month) +'-'+str(the_date['balance_date'].day)+'-'+str(the_date['balance_date'].year))
    data = {
        'date': formatted_date
    }
    return JsonResponse(data)

def category_details (request,categoryid):
        template = loader.get_template('transactions/category_transactions.html')
        today = datetime.today()
        first_of_month = get_first_of_month(today)
        last_of_month = get_last_of_month(today)
        transactions = Transaction.objects.filter(category=categoryid,trans_date__range=[first_of_month,last_of_month], user=request.user)
        total =  Transaction.objects.filter(category=categoryid,trans_date__range=[first_of_month,last_of_month], user=request.user).aggregate(sum=Sum('amount'))['sum'] or 0.00
        category = Category.objects.filter (id=categoryid, user=request.user)
        print (category)
        category_budget = BudgetTracker.objects.filter(category__category = category[0], date__range = [first_of_month, last_of_month], user=request.user)
        print (category_budget)
        #category_total = BudgetTracker.objects.filter(category=category_name[0])
        context = {
            'transactions': transactions,
            'total': total,
        }
        return HttpResponse(template.render(context, request))

def category_budget_check (request):
   category = request.GET.get ('category',None)
   the_date = request.GET.get ('date', None)
   date_time_obj = datetime.strptime(the_date, '%m/%d/%Y %H:%M:%S')
   string_date = str(date_time_obj.year) + "-" + str(date_time_obj.month) + "-" + "1"
   print (string_date)
   print (request.user)
   print (category)
   print (the_date)
   budget_exist = 'false'
   if (category =='Income' or category== 'Initial Balance'):
       budget_exist = 'true'

   elif BudgetTracker.objects.filter(date=string_date, user=request.user, category__category=category).exists():
        budget_exist = 'true'
   print (budget_exist)
   data = {
     'budget_exist': budget_exist
    }
   return JsonResponse(data)