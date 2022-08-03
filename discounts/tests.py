from django.test import TestCase

# Create your tests here.
        if time=='currentday':
            number_views=views.filter(created__date__gte=current_date)
            number_views_last=views_last.filter(created__date=(current_date - timedelta(days=1))) 
        if time=='day':
            day=pd.to_datetime(time_choice)
            number_views_last=views_last.filter(Q(created__date=(day - timedelta(days=1))))
        if time=='yesterday':
            number_views=views.filter(created__date=yesterday)
            number_views_last=views_last.filter(Q(created__date=(yesterday - timedelta(days=1))))
        if time=='week_before':
            number_views=views.filter(created__date__gte=week,created__date__lte=yesterday)
            number_views_last=views_last.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        if time=='week':  
            week=pd.to_datetime(time_choice)
            number_views_last=views_last.filter(Q(created__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            number_views=views.filter(created__month=month.month,created__year=month.year)
            number_views_last=views_last.filter(Q(created__month=(month.month - 1)))
        if time=='month_before':
            number_views=views.filter(created__date__gte=month,created__date__lte=yesterday)
            number_views_last=views_last.filter(Q(created__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            year=pd.to_datetime(time_choice)
            number_views=views.filter(ordered_date__year=year.year)
            number_views_last=views_last.filter(Q(ordered_date__year=(year.year - 1))) 