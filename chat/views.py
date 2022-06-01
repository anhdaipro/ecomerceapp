from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.utils import timezone
# Create your views here.
from .models import *
from shop.models import *
from checkout.models import *
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView,GenericAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

class MessageAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        threads = Thread.objects.filter(participants=user).order_by('timestamp')
        data = {
            'threads':[{
            'message':[{'read':message.seen,'sender':message.user.username}
            for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
            for thread in threads]
        }
        return Response(data)

class CreateMessage(APIView):
    def post(self,request):
        msg = request.data.get('message')
        sent_by_id = request.data.get('sent_by')
        send_to_id = request.data.get('send_to')
        thread_id = request.data.get('thread_id')
        item_id = request.data.get('item_id')
        order_id=request.data.get('order_id')
        count_uploadfile = request.data.get('count_uploadfile')
        list_uploadfile = request.data.get('list_file')
        thread=Thread.objects.get(id=thread_id)
        if msg!='':    
            Message.objects.create(thread=thread,user_id=sent_by_id, message=msg)
        if item_id:
            Message.objects.create(thread=thread,user_id=sent_by_id,product_id=item_id)
        if order_id:
            Message.objects.create(thread=thread,user_id=sent_by_id,order_id=order_id)
        if count_uploadfile>0:
            list_image=[obj['file_name'] for obj in list_uploadfile if obj['filetype']=='image'] 
            if len(list_image)>0:
                messages=Message.objects.create(thread=thread,user_id=sent_by_id)
                obj = UploadFile.objects.filter(file_name__in=list_image,upload_by_id=sent_by_id).order_by('-upload_date')[:count_uploadfile]
                messages.file.add(*obj)
            list_file=[upload['file_name'] for upload in list_uploadfile if upload['filetype']!='image']
            if len(list_file)>0:
                Message.objects.bulk_create([
                    Message(
                    thread=thread,
                    user_id=sent_by_id)
                for i in range(len(list_file))])

                upload_files=UploadFile.objects.filter(file_name__in=list_file,upload_by_id=sent_by_id).order_by('-upload_date')[:count_uploadfile]
                messages=Message.objects.all().order_by('-id')[:len(list_file)]
                for i in range(len(upload_files)):
                    messages[i].file.add(upload_files[i])
        data={
            'ok':'ok'
        }
        return Response(data)

class ActionThread(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request,id,*args, **kwargs):
        gim=request.POST.get('gim')
        unread=request.POST.get('unread')
        delete=request.POST.get('delete')
        data={}
        thread=Thread.objects.get(id=id)
        if gim:
            if gim=='true':
                thread.gim=True
                data.update({'gim':True})
            else:
                thread.gim=False
                data.update({'gim':False})
            thread.save()
        elif unread:
            if unread=='true':
                messages=Message.objects.filter(thread=thread)
                if messages.exists():
                    messages.last().seen=False
                    messages.last().save()
            else:
                Message.objects.filter(thread=thread).update(seen=True)
        else:
            thread.delete()
        return Response(data)

class ListThreadAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        thread_id=request.GET.get('thread_id')
        offset=request.GET.get('offset')
        shop_name=request.GET.get('shop_name')
        item=request.GET.get('item')
        order=request.GET.get('order')
        list_thread=request.GET.get('list_thread')
        seen=request.GET.get('seen')
        type_chat=request.GET.get('type_chat')
        limit=10
        threads = Thread.objects.filter(participants=user)
        data={}
        if thread_id:
            thread=Thread.objects.get(id=thread_id)
            messages=Message.objects.filter(thread=thread)
            if seen:
                messages.update(seen=True)
            message_count=messages.count()
            to_item=message_count
            if offset:
                to_item=message_count-int(offset)
            from_item=to_item-limit
            if to_item-limit<=0:
                from_item=0
            if from_item<to_item:
                messages=messages[from_item:to_item]
            data.update({
            'messages':[{'text':message.message,
                'sender':message.user.username,'created':message.date_created,
                'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()
                ]} for message in messages]
                })
        
            if list_thread:
                data.update({
                    'threads':[{'id':thread.id,'info_thread':thread.info_thread(),'gim':thread.gim,
                    'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
                    'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
                    'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
                    'list_file':[{'filetype':uploadfile.filetype()}
                    for uploadfile in message.file.all()]}
                    for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
                    for thread in threads]
                })

        elif shop_name:
            shop=Shop.objects.get(name=shop_name)
            if item:
                to_item=shop.count_product()
                if offset:
                    to_item=int(offset)
                from_item=to_item-5
                list_items=Item.objects.filter(shop=shop).order_by('-id')[from_item:to_item]
                data.update({'count_product':shop.count_product(),
                    'list_items':[{'item_name':i.name,'item_image':i.get_media_cover(),'number_order':i.number_order(),
                    'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                    'item_min':i.min_price()
                    } for i in list_items]
                })
            else:
                count_order=Order.objects.filter(shop=shop,user=user,ordered=True).count()
                to_item=count_order
                if offset:
                    to_item=int(offset)
                from_item=to_item-5
                list_orders=Order.objects.filter(shop=shop,user=user).order_by('-id')[from_item:to_item]
                data.update({'count_order':count_order,
                    'list_orders':[{
                    'id':order.id,'shop':order.shop.name,'total_final_order':order.total_final_order(),
                    'count_item':order.count_item_cart(),
                    'order_item':[{'item_image':order_item.product.item.media_upload.all()[0].upload_file(),'item_url':order_item.product.item.get_absolute_url(),
                    'item_name':order_item.product.item.name,'color_value':order_item.product.get_color(),
                    'quantity':order_item.quantity,'discount_price':order_item.product.total_discount(),
                    'size_value':order_item.product.get_size(),'price':order_item.product.price,
                    'total_price':order_item.total_discount_orderitem()
                    } for order_item in order.items.all()]} for order in list_orders]
                })
        if type_chat:
            if type_chat=='2':
                threads = Thread.objects.filter(Q(participants=user)&Q(chatmessage_thread__seen=False) & ~Q(message__user=user))
                data.update({
                'threads':[{'id':thread.id,'info_thread':thread.info_thread(),'gim':thread.gim,
                'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
                'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
                'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()]}
                for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
                for thread in threads]
                })
        else:
            data.update({
            'threads':[{'id':thread.id,'info_thread':thread.info_thread(),'gim':thread.gim,
            'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
            'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
            'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
            'list_file':[{'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()]}
            for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
            for thread in threads]
            })
        return Response(data)
    def post(self, request, *args, **kwargs):
        user=request.user
        participants=request.POST.getlist('participants')
        thread_id=request.POST.get('thread_id')
        group_name=request.POST.get('group_name')
        seen=request.POST.get('seen')
        item_id=request.POST.get('item_id')
        order_id=request.POST.get('order_id')
        if thread_id and seen:
            thread=Thread.objects.get(id=thread_id)
            messages=Message.objects.filter(thread=thread)
            messages.update(seen=True)
            message_count=messages.count()
            messages=messages[message_count-10:message_count]
            data={
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
                'sender':message.user.username,'created':message.date_created,
                'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()
                ]} for message in messages
                ]
            }
            return Response(data)
        elif  participants:
            list_user=User.objects.filter(id__in=participants)
            thread=Thread.objects.create(
            group_name=group_name
            )
            thread.participants.add(*list_user)
            if order_id:
                order=Order.objects.get(id=order_id)
                message,created=Message.objects.get_or_create(
                order=order,user=user
                )
            elif item_id:
                item=Item.objects.get(id=item_id)
                message,created=Message.objects.get_or_create(
                product=item,user=user
                )
        
            threads=Thread.objects.filter(participants=user).order_by('-id')
            messages=Message.objects.filter(thread=thread)
            message_count=messages.count()
            to_item=message_count
            from_item=to_item-10
            if to_item-10<=message_count:
                from_item=0
            if from_item<to_item:
                messages=messages[from_item:to_item]
            data={'threadchoice':{'id':thread.id,'count_message':thread.count_message()},
            'messages':[{'text':message.message,
            'sender':message.user.username,'created':message.date_created,
            'message_order':message.message_order(),'message_product':message.message_product(),
            'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
            'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()
            ]} for message in messages],
            'threads':[{'id':thread.id,'info_thread':thread.info_thread(),'gim':thread.gim,
            'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
            'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
            'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
            'list_file':[{'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()]}
            for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
            for thread in threads]
            }
            
            return Response(data)

class ThreadAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        thread_id=request.GET.get('thread_id')
        type=request.GET.get('type')
        if thread_id:
            thread=Thread.objects.get(id=thread_id)
            messages=Message.objects.filter(thread=thread)
            message_count=messages.count()
            messages=messages[message_count-10:message_count]
            data={
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
                'user_id':message.user_id,'created':message.date_created,'item':[{'item_name':item.name,
                'item_image':item.media_upload.all()[0].upload_file(),'item_url':item.get_absolute_url(),'item_max':item.max_price(),
                'item_min':item.min_price(),'percent_discount':item.percent_discount()
                } for item in Item.objects.filter(message=message)],
                'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()
                ]} for message in messages
                ]
            }
            return Response(data)
    def post(self, request, *args, **kwargs):
        user=request.user
        item=Item.objects.all()
        count=item.count()
        sender=user
        user=user
        thread=Thread.objects.filter(sender=user)
        receiver=request.POST.get('id')
        thread_id=request.POST.get('thread_id')
        seen=request.POST.get('seen')
        receive=User.objects.get(id=receiver)
        if Thread.objects.filter(sender=user,receiver=receive).exists():
            thread=Thread.objects.filter(sender=user,receiver=receive).first()
        elif Thread.objects.filter(sender=receive,receiver=user).exists():
            thread=Thread.objects.filter(sender=receive,receiver=user).first()
        elif thread_id:
            thread=Thread.objects.get(id=thread_id)
            Message.objects.filter(thread=thread,seen=False).update(seen=True)
        else:
            thread,created=Thread.objects.get_or_create(
                sender=sender,
                receiver=receive,
            )
        threads=Thread.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-id')
        messages=Message.objects.filter(thread=thread)
        message_count=messages.count()
        messages=messages[message_count-10:message_count]
        data={'count':count,
            'thread':thread.id,'sender':thread.sender_id,'receiver':thread.receiver_id,
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
            'user_id':message.user_id,'created':message.date_created,'item':message.message_product(),
            'message_order':message.message_order(),
            'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
            'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()
            ]} for message in messages
            ],
            'threads':[{'thread_id':thread.id,'sender':thread.sender.username,'receiver':thread.receiver.username,
            'shop_name_sender':thread.shop_name_sender(),'shop_logo_sender':thread.shop_logo_sender(),
            'count_message_not_seen':thread.count_message_not_seen(),'sender_id':thread.sender_id,
            'receiver_id':thread.receiver_id,
            'shop_name_receiver':thread.shop_name_receiver(),'shop_logo_receiver':thread.shop_logo_receiver(),
            'messages':[{'text':message.message,'file':message.message_file(),'created':message.date_created,
            'message_order':message.message_order(),'message_product':message.message_product(),
            'message_filetype':message.message_filetype(),
            'user_id':message.user_id} for message in thread.chatmessage_thread.all().order_by('-id')[:1]
            ]} for thread in threads
            ]
        }
        
        return Response(data)


