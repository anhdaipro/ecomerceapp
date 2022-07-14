for(let i=0 ;i<obj1.data.list_shop.length;i++){
                let list_voucher_items=[]
                for(let j=0;j<obj1.data.cart_item.length;j++){
                    if(obj1.data.cart_item[j].shop_name==obj1.data.list_shop[i].shop_name){
                        if(obj1.data.cart_item[j].voucher_user.length>0){
                            for(let k=0;k<obj1.data.cart_item[j].list_voucher.voucher_info.length;k++){
                                if(list_voucher_items[obj1.data.cart_item[j].list_voucher.voucher_info[k].id]) continue;
                                list_voucher_items[obj1.data.cart_item[j].list_voucher.voucher_info[k].id] = true;
                                obj1.data.list_shop[i].list_voucher_unique.push({'voucher_info':obj1.data.cart_item[j].list_voucher.voucher_info[k],'voucher_user':obj1.data.cart_item[j].voucher_user[k]});
                                obj1.data.list_shop[i].show_voucher=false
                            }
                        }
                    }  
                }
            }
            
            
            for(let j=0;j<obj1.data.cart_item.length;j++){
                if(obj1.data.cart_item[j].promotion){ 
                    list_item_promotions.push(obj1.data.cart_item[j])
                    if(list_item_promotion[obj1.data.cart_item[j].promotion.id]) continue;
                    list_item_promotion[obj1.data.cart_item[j].promotion.id] = true;
                    list_item_promotion_unique.push(obj1.data.cart_item[j])
                }
                if(!obj1.data.cart_item[j].promotion){
                    list_item_remainder.push(obj1.data.cart_item[j])
                }
            }
            for(let j=0;j<list_item_promotion_unique.length;j++){
                for(let k=0;k<list_item_promotions.length;k++){
                    if(list_item_promotion_unique[j].promotion.id==list_item_promotions[k].promotion.id && list_item_promotion_unique[j].product_id!==list_item_promotions[k].product_id){
                        list_item_promotion_unique[j].byproduct.push(list_item_promotions[k])
                    }
                }
            }