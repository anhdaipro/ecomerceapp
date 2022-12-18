none=[None]
            list_color=Color.objects.all().order_by('-id')[:len(color_value)]
            list_size=Size.objects.all().order_by('-id')[:len(size_value)]
            price=request.POST.getlist('price')
            inventory=request.POST.getlist('inventory')
            sku=request.POST.getlist('sku')
            variant_list =list(itertools.product(list_size,list_color))
            
            if len(list_color)==0 and len(list_size) > 0:
                variant_list=list(itertools.product(list_size,none))
            elif len(list_size)==0 and len(list_color) >0:
                variant_list=list(itertools.product(none,list_color))
            elif len(list_size) == 0 and len(list_color)==0:
                variant_list=list(itertools.product(none,none))
            
            # bulk_create() prohibited to prevent data loss due to unsaved related object 'color'. do chưa save từng thằng color
            size_variation=[]
            color_variation=[]
            for i,j in variant_list:
                size_variation.append(i),color_variation.append(j)
            variation_content=list(zip(size_variation,color_variation,price,inventory,sku))
            product_id_remove=request.POST.getlist('product_id_remove')
            Variation.objects.filter(id__in=product_id_remove).delete()
            list_variation = [
                Variation(
                item=item,
                color=color,
                size=size,
                price=int(price),
                inventory=int(inventory),
                sku_classify=sku,
                ) 
                for size,color,price,inventory,sku in variation_content
            ]
            Variation.objects.bulk_create(list_variation)