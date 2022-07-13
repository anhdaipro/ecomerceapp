from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.utils import timezone
# Create your views here.
from .models import *
from shop.models import *
from orders.models import *
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView,GenericAPIView,
)
from .serializers import ThreadinfoSerializer,MessageSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


class ActionThread(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        listmessage=Message.objects.filter(thread_id=id).prefetch_related('message_media').select_related('order').select_related('product').order_by('-id')
        Member.objects.filter(thread_id=id,user=request.user).update(is_seen=True)
        count_message=listmessage.count()
        item_from=0
        offset=request.GET.get('offset') 
        if offset:
            item_from=int(offset)
        to_item=item_from+10
        if item_from>=count_message:
            to_item=count_message
        listmessage=listmessage[item_from:to_item]
        serializer = MessageSerializer(listmessage,many=True, context={"request": request})
        return Response(serializer.data)
    def post(self,request,id,*args, **kwargs):
        action=request.POST.get('action')
        member=Member.objects.get(thread_id=id,user=request.user)
        listmessage=list()
        thread=Thread.objects.get(id=id)
        if action=='gim': 
            if member.gim:
                member.gim=False
            else:
                member.gim=True
            member.save()
        elif action=='create-message':
            msg = request.data.get('message')
            image=request.FILES.getlist('image')
            file=request.FILES.getlist('file')
            file_preview=request.FILES.getlist('file_preview')
            duration=request.POST.getlist('duration')
            order_id=request.POST.getlist('order_id') 
            item_id=request.POST.get('item_id') 
            if order_id:
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,order_id=order_id)
                listmessage.append({'id':message.id,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_order(),
                })
            if item_id:
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,item_id=item_id)
                listmessage.append({'id':message.id,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_product(),
                })
            if msg:    
                message=Message.objects.create(thread_id=id,user=request.user,message=msg)
                listmessage.append({'id':message.id,'message':message.message,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'story_id':message.story_id,'media_story':message.get_story(),
                'list_file':[]})
            if image:
                message=Message.objects.create(thread_id=id,user=request.user)
                list_file_chat=Messagemedia.objects.bulk_create([Messagemedia(upload_by=request.user,file=image[i],message=message) for i in range(len(image))])
                listmessage.append({'id':message.id,'message':message.message,'message_type':message.message_type,
                        'user_id':message.user_id,'date_created':message.date_created,
                        'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'filetype':uploadfile.get_filetype()}
                for uploadfile in list_file_chat
                ]})
            if file: 
                list_file_preview=[None for i in range(len(file))]
                for i in range(len(list_file_preview)):
                    for j in range(len(file_preview)):
                        if i==j:
                            list_file_preview[i]=file_preview[j]
                count=Message.objects.last().id
                messages=Message.objects.bulk_create([
                Message(thread_id=id,
                    id=count+i+1,
                    user=request.user
                ) for i in range(len(file))]) 
                        
                Messagemedia.objects.bulk_create([Messagemedia(message_id=messages[i].id,upload_by=request.user,duration=float(duration[i]),file_preview=list_file_preview[i],file=file[i],file_name=name[i]) for i in range(len(file))])
                listmessage=[{'id':message.id,'message':message.message,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,
                'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
                for uploadfile in message.message_file.all()
                ]} for message in messages]
            return Response(listmessage)
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
        user=request.user
        threads=Thread.objects.filter(participants=user)
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
        listmessage=list()
        listuser=User.objects.filter(id__in=member).select_related('profile')
        thread=Thread.objects.filter(participants=request.user)
        for user in listuser:
            thread=thread.filter(participants=user)
        if thread.exists():
            listmember=Member.objects.filter(thread=thread[0]).select_related('user__profile')
            messages=Message.objects.filter(thread=thread.first()).prefetch_related('message_file').order_by('-id')[:10]
            listmessage=[{'id':message.id,'message':message.message,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_order(),
                'message_product':message.message_product(),
                'list_file':[{'id':uploadfile.id,'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.get_filetype()}
                for uploadfile in message.message_file.all()
                ]} for message in messages
                ]
            data={'messages':listmessage,
            'thread':{'id':thread[0].id,'count_message':thread[0].count_message()},
            'members':[{'user_id':member.user_id,'id':member.id,
            'avatar':member.user.profile.avatar.url,'username':member.user.username,
            'online':member.user.profile.online,'is_online':member.user.profile.is_online} for member in listmember]}
            return Response(data)
        else:
            thread=Thread.objects.create(admin=request.user)
            thread.participants.add(*member)
            thread.save()
            Member.objects.bulk_create([
                Member(user=listuser[i],thread=thread)
                for i in range(len(list(listuser)))
            ])
            if order_id:
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,order_id=order_id)
                listmessage.append({'id':message.id,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_order(),
                })
            if item_id:
                message,created=Message.objects.get_or_create(thread=thread,user=request.user,item_id=item_id)
                listmessage.append({'id':message.id,'message_type':message.message_type,
                'user_id':message.user_id,'date_created':message.date_created,'message_order':message.message_product(),
                })

            data={'messages':listmessage,'thread':{'id':thread.id,'count_message':0},'members':[{'user_id':member.id,'avatar':member.profile.avatar.url,'username':member.username,
            'online':member.profile.online,'is_online':member.profile.is_online} for member in listuser]}
            return Response(data)

class ShopchatAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        offset=request.GET.get('offset')
        shop_name=request.GET.get('shop_name')
        item=request.GET.get('item')
        order=request.GET.get('order')
        type_chat=request.GET.get('type_chat')
        limit=10
        threads = Thread.objects.filter(participants=user)
        data={}
        if shop_name:
            shop=Shop.objects.get(name=shop_name)
            if item:
                to_item=shop.count_product()
                if offset:
                    to_item=int(offset)
                from_item=to_item-5
                list_items=Item.objects.filter(shop=shop).order_by('-id')[from_item:to_item]
                data.update({'count_product':shop.count_product(),
                    'list_items':[{'item_name':i.name,'item_image':i.get_image_cover(),'number_order':i.number_order(),
                    'item_id':i.id,'item_inventory':i.total_inventory(),'max_price':i.max_price(),
                    'min_price':i.min_price()
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
                    'order_item':[{'item_image':order_item.product.item.media_upload.all()[0].get_media(),'item_url':order_item.product.item.get_absolute_url(),
                    'item_name':order_item.product.item.name,'color_value':order_item.product.get_color(),
                    'quantity':order_item.quantity,'discount_price':order_item.product.total_discount(),
                    'size_value':order_item.product.get_size(),'price':order_item.product.price,
                    'total_price':order_item.total_discount_cartitem()
                    } for order_item in order.items.all()]} for order in list_orders]
                })
        else:
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
       
        return Response(data)
    def post(self, request, *args, **kwargs):
        user=request.user
        participants=request.POST.getlist('participants')
        thread_id=request.POST.get('thread_id')
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



