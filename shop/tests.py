        shop=Shop.objects.get(user=request.user)
        vouchers=voucher_combo.objects.filter(shop=shop).prefetch_related('products__media_upload')
        if choice:
            if choice=='current':
                vouchers=vouchers.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                vouchers=vouchers.filter(valid_from__gt=timezone.now())
            else:
                vouchers=voucherss.filter(valid_to__lt=timezone.now())
        count=vouchers.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        vouchers=vouchers[from_item:to_item]
        return Response({'vouchers':vouchers,'count':count})