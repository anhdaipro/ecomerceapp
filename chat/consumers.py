import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from chat.models import *
User = get_user_model()
from shop.models import *
from checkout.models import *
from django.utils import timezone

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def websocket_connect(self, event):
        print('connected', event)
        user = self.scope['user']
        if user.is_authenticated:
    	    await self.update_user_status(user,True)
        chat_room = f'user_chatroom_{user.id}'
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        print('receive', event)
        data = json.loads(event['text'])
        msg = data.get('message')
        sent_by_id = data.get('sent_by')
        send_to_id = data.get('send_to')
        thread_id = data.get('thread_id')
        item_id = data.get('item_id')
        product=data.get('product')
        order_id=data.get('order_id')
        order=data.get('order')
        count_uploadfile = data.get('count_uploadfile')
        list_uploadfile = data.get('list_uploadfile')
        typing = data.get('typing')
        if not msg and not count_uploadfile and not item_id and not order_id and not typing:
            print('Error:: empty message')
            return False
        sent_by_user = await self.get_user_object(sent_by_id)
        send_to_user = await self.get_user_object(send_to_id)
        thread_obj = await self.get_thread(thread_id)
        item_obj = await self.get_item(item_id)
        order_obj = await self.get_order(order_id)
       
        if not sent_by_user:
            print('Error:: sent by user is incorrect')
        if not send_to_user:
            print('Error:: send to user is incorrect')
        if not thread_obj:
            print('Error:: Thread id is incorrect')
        
        count_message=await self.create_chat_message(thread_obj,count_uploadfile,list_uploadfile,sent_by_user,msg,item_obj,order_obj,typing)
        other_user_chat_room = f'user_chatroom_{send_to_id}'
        self_user = self.scope['user']
        response = {
            'typing':typing,
            'message':msg,
            'send_by':sent_by_user.id,
            'sender':sent_by_user.username,
            'send_to':send_to_user.id,
            'thread_id': thread_id,
            'count_unread':count_message,
            'list_uploadfile':list_uploadfile,
            'product':product,
            'order':order
        }
        
        await self.channel_layer.group_send(
            other_user_chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

    async def websocket_disconnect(self, event):
        print('disconnect', event)
        user = self.scope['user']
        
    async def chat_message(self, event):
        print('chat_message', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })


    @database_sync_to_async
    def get_user_object(self, user_id):
        qs = User.objects.filter(id=user_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj
    @database_sync_to_async
    def get_count_unread(self, thread_id):
        count=0
        qs = Thread.objects.filter(id=thread_id)
        if qs.exists():
            obj = qs.first()
            count=Message.objects.filter(thread=obj,seen=False).count()
        return count
    @database_sync_to_async
    def get_thread(self, thread_id):
        qs = Thread.objects.filter(id=thread_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj
    
    @database_sync_to_async
    def get_item(self,item_id):
        obj=None
        qs=Item.objects.filter(id=item_id)
        if qs.exists():
            obj = qs.first()
        return obj
    @database_sync_to_async
    def get_order(self,order_id):
        obj=None
        qs=Order.objects.filter(id=order_id)
        if qs.exists():
            obj = qs.first()
        return obj
   

    @database_sync_to_async
    def create_chat_message(self,thread,count_uploadfile,list_uploadfile,user, msg,item,order,typing):
        count=0
        if typing==None:
            if msg!='':    
                Message.objects.create(thread=thread,user=user, message=msg)
            if item!=None:
                Message.objects.create(thread=thread,user=user,product=item)
            if order!=None:
                Message.objects.create(thread=thread,user=user,order=order)
            if count_uploadfile>0:
                list_image=[obj['file_name'] for obj in list_uploadfile if obj['filetype']=='image'] 
                if len(list_image)>0:
                    messages=Message.objects.create(thread=thread,user=user)
                    obj = UploadFile.objects.filter(file_name__in=list_image,upload_by=user).order_by('-upload_date')[:count_uploadfile]
                    messages.file.add(*obj)
                list_file=[upload['file_name'] for upload in list_uploadfile if upload['filetype']!='image']
                if len(list_file)>0:
                    list_messages=Message.objects.bulk_create([
                        Message(
                    thread=thread,
                    user=user)
                    for i in range(len(list_file))])
                    upload_files=UploadFile.objects.filter(file_name__in=list_file,upload_by=user).order_by('-upload_date')[:count_uploadfile]
                    messages=Message.objects.all().order_by('-id')[:len(list_file)]
                    for message in messages:
                        for files in upload_files:
                            if list(messages).index(message)==list(upload_files).index(files):
                                message.file.add(files)
        return count
    @database_sync_to_async
    def update_user_status(self, user,status):
	    return Profile.objects.filter(user=user).update(online=status)
   

    
                                
                


                
                
                    
   