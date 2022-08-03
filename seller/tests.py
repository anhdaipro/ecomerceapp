        if time=='currentday':
            gamers=gamers.filter(ordered_date__date__gte=current_date)
            gamers_last=gamers_last.filter(ordered_date__date=(current_date - timedelta(days=1)))
        if time=='day':
            days=pd.to_datetime(time_choice)
            gamers=gamers.filter(ordered_date__date=time_choice).annotate(day=TruncHour('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__date=(days - timedelta(days=1))))
        if time=='yesterday':
            gamers=gamers.filter(ordered_date__date=yesterday).annotate(day=TruncHour('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__date=(yesterday - timedelta(days=1))))
        if time=='week_before':
            times=[int((yesterday - datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)]
            gamers=gamers.filter(ordered_date__date__gte=week,ordered_date__date__lte=yesterday).annotate(day=TruncDay('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))
        if time=='week': 
            week=pd.to_datetime(time_choice)
            day_first_week=week - datetime.timedelta(days=week.isoweekday() % 7)
            times=[int((day_first_week + datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)] 
            gamers=gamers.filter(ordered_date__week=week.isocalendar()[1],ordered_date__year=week.year).annotate(day=TruncDay('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            day_last_month = pd.Period(month,freq='M').end_time.date() 
            times=[int((day_last_month-datetime.timedelta(days=i)).strftime('%d')) for i in range(int(day_last_month.strftime('%d')))]
            gamers=gamers.filter(ordered_date__month=month.month,ordered_date__year=month.year).annotate(day=TruncDay('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__month=(month.month - 1)))
        if time=='month_before':
            times=[int((yesterday-datetime.timedelta(days=i)).date().strftime('%d')) for i in range(30)]
            gamers=gamers.filter(ordered_date__date__gte=month,ordered_date__date__lte=yesterday).annotate(day=TruncDay('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            times=[i for i in range(1,13)]
            year=pd.to_datetime(time_choice)
            gamers=gamers.filter(ordered_date__year=year.year).annotate(day=TruncMonth('ordered_date'))
            gamers_last=gamers_last.filter(Q(ordered_date__year=(year.year - 1)))