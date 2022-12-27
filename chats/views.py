from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.db.models import F
from django.utils import timezone
# Create your views here.
from .models import *
from shop.models import *
from orders.models import *
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView,GenericAPIView,
)
from .serializers import ThreadinfoSerializer,MessageSerializer,ThreaddetailSerializer,MediathreadSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


class ActionThread(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        action=request.GET.get('action')
        user_id=request.GET.get('user_id')
        offset=request.GET.get('offset')
        keyword=request.GET.get('keyword') 
        if action=='showmessage':
            listmessage=Message.objects.filter(thread_id=id).prefetch_related('message_media').select_related('order').select_related('product').order_by('-id')
            Member.objects.filter(thread_id=id,user=request.user).update(is_seen=True,count_message_unseen=0)
            count_message=listmessage.count()
            item_from=0
            if offset:
                item_from=int(offset)
            to_item=item_from+10
            if item_from>=count_message:
                to_item=count_message
            listmessage=listmessage[item_from:to_item]
            serializer = MessageSerializer(listmessage,many=True, context={"request": request})
            return Response(serializer.data)
        else:
            shop=Shop.objects.get(user_id=user_id)
            if action=='showitem':
                list_items=Item.objects.filter(shop=shop).order_by('-id')
                if keyword:
                    list_items=list_items.filter(name__startswith=keyword)
                count_product=shop.count_product()
                item_from=0
                if offset:
                    item_from=int(offset)
                to_item=item_from+5
                if item_from+5>=count_product:
                    to_item=count_product
                list_items=list_items[item_from:to_item]
                data={'count_product':shop.count_product(),
                    'list_items':[{'name':i.name,'image':i.get_image_cover(),'number_order':i.number_order(),
                    'id':i.id,'inventory':i.total_inventory(),'max_price':i.max_price(),'percent_discount':i.percent_discount(),
                    'min_price':i.min_price()
                    } for i in list_items]
                }
                return Response(data)
            else:
                list_orders=Order.objects.filter(shop=shop,user=request.user,ordered=True).order_by('-id')
                count_order=list_orders.count()
                item_from=0
                if offset:
                    item_from=int(offset)
                to_item=item_from+5
                if item_from>=count_order:
                    to_item=count_order
                list_orders=list_orders[item_from:to_item]
                data={'count_order':count_order,
                    'list_orders':[{
                    'id':order.id,'total_final_order':order.total_final_order(),
                    'count_item':order.count_item_cart(),'shop_id':order.shop_id,
                    'cart_item':[{'image':cartitem.get_image(),'url':cartitem.product.item.slug,
                    'name':cartitem.product.item.name,'color_value':cartitem.product.get_color(),
                    'quantity':cartitem.quantity,'discount_price':cartitem.product.total_discount(),
                    'size_value':cartitem.product.get_size(),'price':cartitem.product.price,
                    'total_price':cartitem.total_discount_cartitem()
                    } for cartitem in order.items.all()]} for order in list_orders]
                }
                return Response(data)

    def post(self,request,id,*args, **kwargs):
        action=request.POST.get('action')
        send_to=request.POST.get('send_to')
        send_by=request.POST.get('send_by')
        sender=Member.objects.get(thread_id=id,user_id=send_by)
        receiver=Member.objects.get(thread_id=id,user_id=send_to)
        listmessage=list()
        thread=Thread.objects.get(id=id)
        if action=='gim': 
            if sender.gim:
                sender.gim=False
            else:
                sender.gim=True
            sender.save()
        elif action=='create-message':
            if receiver.block:
                return Response({'error':"Bạn đã bị block"})
            else:
                msg = request.data.get('message')
                image=request.FILES.getlist('image')
                file=request.FILES.getlist('file')
                file_preview=request.FILES.getlist('file_preview')
                duration=request.POST.getlist('duration')
                order_id=request.POST.get('order_id') 
                item_id=request.POST.get('item_id')  
                if order_id:
                    Member.objects.filter(user_id=send_to,thread_id=id).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1)
                    message,created=Message.objects.get_or_create(thread=thread,user=request.user,order_id=order_id,message_type='5')
                    listmessage.append({'id':message.id,'message_type':message.message_type,
                    'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_order(),
                    })
                if item_id:
                    Member.objects.filter(user_id=send_to,thread_id=id).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1)
                    message,created=Message.objects.get_or_create(thread=thread,user=request.user,product_id=item_id,message_type='4')
                    listmessage.append({'id':message.id,'message_type':message.message_type,
                    'user_id':message.user_id,'date_created':message.date_created,'message_product':message.message_product(),
                    })
                if msg:   
                    Member.objects.filter(user_id=send_to,thread_id=id).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1) 
                    message=Message.objects.create(thread_id=id,user=request.user,message=msg,message_type='1')
                    listmessage.append({'id':message.id,'message':message.message,'message_type':message.message_type,
                    'user_id':message.user_id,'date_created':message.date_created})
                if image:
                    Member.objects.filter(user_id=send_to,thread_id=id).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1)
                    message=Message.objects.create(thread_id=id,user=request.user,message_type='2')
                    list_file_chat=Messagemedia.objects.bulk_create([Messagemedia(upload_by=request.user,file=image[i],message=message) for i in range(len(image))])
                    listmessage.append({'id':message.id,'message_type':message.message_type,
                            'user_id':message.user_id,'date_created':message.date_created,
                            'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,}
                    for uploadfile in list_file_chat
                    ]})
                if file: 
                    Member.objects.filter(user_id=send_to,thread_id=id).update(is_seen=False,count_message_unseen=F('count_message_unseen')+len(file))
                    list_file_preview=[None for i in range(len(file))]
                    for i in range(len(list_file_preview)):
                        for j in range(len(file_preview)):
                            if i==j:
                                list_file_preview[i]=file_preview[j]
                    messages=Message.objects.bulk_create([
                    Message(thread_id=id,
                        user=request.user,
                        message_type='3'
                    ) for i in range(len(file))]) 
                    items=list([message.id for message in messages])        
                    Messagemedia.objects.bulk_create([Messagemedia(message_id=items[i],upload_by=request.user,duration=float(duration[i]),file_preview=list_file_preview[i],file=file[i]) for i in range(len(file))])
                    listmessage=[{'id':message.id,'message_type':message.message_type,
                    'user_id':message.user_id,'date_created':message.date_created,
                    'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,
                    'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,}
                    for uploadfile in message.message_media.all()
                    ]} for message in messages]
                return Response(listmessage)
        elif action=='seen':
            if sender.is_seen:
                sender.is_seen=False
                sender.count_message_unseen=1
            else:
                sender.is_seen=True
                sender.count_message_unseen=0
            sender.save()
        elif action=='block':
            if receiver.block:
                receiver.block=False
            else:
                receiver.block=True
            receiver.save()
        elif action=='report':
            Reportuser.objects.get_or_create(thread_id=id,user=request.user,reported_id=send_to)
        else:
            thread.delete()
        return Response(listmessage)

class CountThread(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        count=Thread.objects.filter(participants=request.user).count()
        return Response({'count':count})

class ListThreadAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        type_chat=request.GET.get('type_chat')
        member=Member.objects.filter(user=request.user)
        if type_chat:
            if type_chat=='3':
                member=member.filter(gim=True)
            if type_chat=='2':
                member=member.filter(is_seen=False)
        threads=Thread.objects.filter(member_thread__in=member).prefetch_related('member_thread').prefetch_related('chatmessage_thread')
        serializer = ThreadinfoSerializer(threads,many=True, context={"request": request})
        return Response(serializer.data)

class MediathreadAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        id=request.GET.get('id')
        file=Messagemedia.objects.get(id=id)
        serializer = MediathreadSerializer(file, context={"request": request})

class CreateThread(APIView):
    def post(self,request):
        member=request.data.get('member')
        item_id=request.data.get('item_id')
        order_id=request.data.get('order_id')
        send_to=request.data.get('send_to')
        listmessage=list()
        listuser=User.objects.filter(id__in=member).select_related('profile')
        thread=Thread.objects.filter(participants=request.user)
        for user in listuser:
            thread=thread.filter(participants=user)
        if thread.exists():
            listmember=Member.objects.filter(thread=thread[0]).select_related('user__profile')
            if order_id:
                Member.objects.filter(user_id=send_to,thread=thread).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1)
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,order_id=order_id,message_type='5')
            serializer = ThreaddetailSerializer(thread.first(),context={"request": request})
            return Response(serializer.data)
        else:
            thread=Thread.objects.create(admin=request.user)
            thread.participants.add(*member)
            thread.save()
            members=Member.objects.bulk_create([
                Member(user=listuser[i],thread=thread)
                for i in range(len(list(listuser)))
            ])
            if order_id:
                Member.objects.filter(user_id=send_to,thread=thread).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1)
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,order_id=order_id,message_type='5')
                listmessage.append({'id':message.id,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_order(),
                })
            if item_id:
                Member.objects.filter(user_id=send_to,thread=thread).update(is_seen=False,count_message_unseen=F('count_message_unseen')+1)
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,product_id=item_id,message_type='4')
                listmessage.append({'id':message.id,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_product':message.message_product(),
                })

            serializer = ThreaddetailSerializer(thread,context={"request": request})
            return Response(serializer.data)



