from .models import *
from account.models import *
from orders.models import *
from shop.models import *
from rest_framework import serializers
from django.contrib.auth.models import User
from datetime import timedelta
import datetime,jwt

class MemberSerializer(serializers.ModelSerializer):
    count_product_shop=serializers.SerializerMethodField()
    url=serializers.SerializerMethodField()
    avatar=serializers.SerializerMethodField()
    username=serializers.SerializerMethodField()
    class Meta:
        model=Member
        fields=('user_id','count_product_shop','gim','block','url','avatar',
        'count_message_unseen','username')
    def get_count_product_shop(self,obj):
        return obj.user.shop.count_product()
    def get_avatar(self,obj):
        return obj.user.profile.avatar.url
    def get_username(self,obj):
        return obj.user.username
    def get_url(self,obj):
        return obj.user.shop.slug

class ThreadinfoSerializer(serializers.ModelSerializer):
    message_last=serializers.SerializerMethodField()
    count_message=serializers.SerializerMethodField()
    members=serializers.SerializerMethodField()
    class Meta:
        model=Thread
        fields=('id','message_last','members','count_message',)
    def get_message_last(self,obj):
        message=Message.objects.filter(thread=obj)
        if message.exists():
            message=message.last()
            return {'message':message.message,'message_type':message.message_type,
            'user_id':message.user_id,'date_created':message.date_created}
    def get_count_message(self,obj):
        return Message.objects.filter(thread=obj).count()

    def get_members(self,obj):
        request=self.context.get("request") 
        listmember=Member.objects.filter(thread=obj).select_related('user__profile').select_related('user__shop')
        return MemberSerializer(listmember,many=True).data

class MediathreadSerializer(serializers.ModelSerializer):
    file=serializers.SerializerMethodField()
    file_preview=serializers.SerializerMethodField()
    list_file=serializers.SerializerMethodField()
    class Meta:
        model=Messagemedia
        fields=('id','file_preview','file','duration','list_file','message_id',)
    def get_file_preview(self,obj):
        return obj.get_file_preview()
    def get_list_file(self,obj):
        list_media=Filechat.objects.filter(message__thread=obj.message.thread)
        if list_media.count()<=21:
            list_media=list_media
        else:
            if obj in list_media[:20]:
                list_media=list_media.filter(id__gte=obj.id)[:20]
            else:
                list_media=list_media.filter(id__lte=obj.id)[:20]
        return [{'id':media.id,'file':media.file.url,'file_preview':media.get_file_preview()} for media in list_media]
    def get_file(self,obj):
        return obj.file.url
    

class MessageSerializer(serializers.ModelSerializer):
    list_file=serializers.SerializerMethodField()
    message_product=serializers.SerializerMethodField()
    message_order=serializers.SerializerMethodField()
    class Meta:
        model=Message
        fields=('thread','id','user_id','date_created','message_type','message','list_file','message_order','message_product',)
    def get_list_file(self,obj):
        return [{'id':uploadfile.id,'file':uploadfile.file.url,
        'file_preview':uploadfile.get_file_preview(),'duration':uploadfile.duration}
        for uploadfile in obj.message_media.all()]

    def get_message_product(self,obj):
        return obj.message_product()
    def get_message_order(self,obj):
        return obj.message_order()

class ThreaddetailSerializer(serializers.ModelSerializer):
    members=serializers.SerializerMethodField()
    messages=serializers.SerializerMethodField()
    thread=serializers.SerializerMethodField()
    class Meta:
        model=Thread
        fields=('thread','members','messages',)
    def get_thread(self,obj):
        return{'id':obj.id,'count_message':obj.count_message()}
    
    def get_members(self,obj):
        listmember=Member.objects.filter(thread=obj).select_related('user__profile').select_related('user__shop')
        return MemberSerializer(listmember,many=True).data
    def get_messages(self,obj):
        return MessageSerializer(obj.chatmessage_thread.all(),many=True).data

