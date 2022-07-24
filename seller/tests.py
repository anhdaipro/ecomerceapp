from django.test import TestCase

# Create your tests here.
        if time=='currentday':
            vouchers_user=vouchers_user.filter(created__date__gte=current_date).annotate(day=TruncHour('created'))
            vouchers_last_user=vouchers_last_user.filter(created__date=(current_date - timedelta(days=1)))
        if time=='day':
            day=pd.to_datetime(time_choice)
            order=orders.filter(created__date=day).annotate(day=TruncHour('created'))
            vouchers_last_user=vouchers_last_user.filter(Q(created__date=(day - timedelta(days=1))))
        if time=='yesterday':
            vouchers_user=vouchers_user.filter(created__date=yesterday).annotate(day=TruncHour('created'))
            vouchers_last_user=vouchers_last_user.filter(Q(created__date=(yesterday - timedelta(days=1))))
        if time=='week_before':
            vouchers_user=vouchers_user.filter(created__date__gte=week,created__date__lte=start_date).annotate(day=TruncDay('created'))
            vouchers_last_user=vouchers_last_user.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        if time=='week':  
            week=pd.to_datetime(time_choice)
            orders=Order.objects.filter(created__week=week.isocalendar()[1],created__year=week.year).annotate(day=TruncDay('created'))
            vouchers_last_user=vouchers_last_user.filter(Q(created__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            vouchers_user=vouchers_user.filter(created__month=month.month,created__year=month.year).annotate(day=TruncDay('created'))
            vouchers_last_user=vouchers_last_user.filter(Q(created__month=(month.month - 1)))
        if time=='month_before':
            vouchers_user=vouchers_user.filter(created__date__gte=month,created__date__lte=start_date).annotate(day=TruncDay('created'))
            orders_last=list_order_last.filter(Q(created__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 