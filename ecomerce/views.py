from discount.models import *
from django.shortcuts import render,redirect
from shop.models import *
from cart.models import *
from category.models import *
from city.models import *
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, HttpResponseRedirect,JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate,login,logout

def category(request,slug):
    return render(request,'index.html')
def product(request,slug):
    recently_viewed_products = None
    if 'recently_viewed' in request.session:
        if slug in request.session['recently_viewed']:
            request.session['recently_viewed'].remove(slug)
        products = Item.objects.filter(slug__in=request.session['recently_viewed'])
        recently_viewed_products = sorted(products, 
            key=lambda x: request.session['recently_viewed'].index(x.slug)
            )
        request.session['recently_viewed'].insert(0, slug)
        if len(request.session['recently_viewed']) > 5:
             request.session['recently_viewed'].pop()
    else:
        request.session['recently_viewed'] = [slug]

    request.session.modified = True
    return render(request,'product.html')

def bundle_deal(request,id):
    return render(request,'promotion_combo.html')
def deal_shock(request,id):
    return render(request,'deal_shock.html')
def sendEmail(request, order):
    mail_subject = 'Thank you for your order!'
    message = render_to_string('order_recieved_email.html', {
        'user': request.user,
        'order': order
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()
        
  