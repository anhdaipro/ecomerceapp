from django.db import models
from shop.models import *
from django.db.models import Q
# Create your models here.


#shoe

# Create your models here.
unint_choice=(
    ('1','mAh'),
    ('2','cell'),
    ('3','Wh'),
)


CHOICE_YES_NO=(
    ('Y','Yes'),
    ('N','No')
)
GENDER_CHOICE=(
        ('M','MALE'),
        ('F','FEMALE'),
        ('O','ORTHER')
    )
Packing_style=(
('1','Free size'),
('2','Box')
)
# Create your models here.
class Detail_Item(models.Model):
    item=models.ForeignKey(Item,on_delete=models.CASCADE)
    #clothes jeans
    brand_clothes=models.CharField(max_length=100,null=True,blank=True)#skirt,dress
    material=models.CharField(max_length=100,null=True,blank=True)#skirt
    pants_length=models.CharField(max_length=100,null=True,blank=True)#,dress
    style=models.CharField(max_length=100,null=True,blank=True)#skirt,,dress
    sample=models.CharField(max_length=100,null=True,blank=True)#skirt,dress
    origin=models.CharField(max_length=100,null=True,blank=True)#skirt,dress
    pants_style=models.CharField(max_length=100,null=True,blank=True)
    petite=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)#skirt,dress
    season=models.CharField(max_length=100,null=True,blank=True)#skirt,dress
    waist_version=models.CharField(max_length=100,null=True,blank=True)#skirt,dress
    very_big=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)#skirt,dress
    #skirt
    skirt_length=models.CharField(max_length=100,null=True,blank=True)#dress,
    occasion=models.CharField(max_length=100,null=True,blank=True)#dress
    dress_style=models.CharField(max_length=100,null=True,blank=True)#dress
    #dress
    collar=models.CharField(max_length=100,null=True,blank=True)
    sleeve_lenght=models.CharField(max_length=100,null=True,blank=True)#T-shirt
    #Tanks & Camisoles
    cropped_top=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)
    shirt_length=models.CharField(max_length=100,null=True,blank=True)
    #jean men
    tallfit=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)
    #beaty
    brand_beaty=models.CharField(max_length=100,null=True,blank=True)
    packing_type=models.CharField(choices=Packing_style,null=True,max_length=20)#heath beaty
    date_expiry=models.DateField(null=True,blank=True)#heath beaty
    formula=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    expiry=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    body_care=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    active_ingredients=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    type_of_nutrition=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    volume=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    ingredient=models.CharField(max_length=100,null=True,blank=True)#heath beaty 
    weight=models.CharField(max_length=100,null=True,blank=True)#heath beaty
    sex= models.CharField(max_length=100,null=True,blank=True)#heath beaty
    #heath beaty 
    skin_type=models.CharField(max_length=100,null=True,blank=True)
    product_samples=models.CharField(max_length=100,null=True,blank=True)
    #mobile
    brand_mobile_gadgets=models.CharField(max_length=100,null=True,blank=True)
    sim=models.CharField(max_length=100,null=True,blank=True)
    warranty_period=models.CharField(max_length=100,null=True,blank=True)
    ram=models.CharField(max_length=100,null=True,blank=True)
    memory=models.CharField(max_length=100,null=True,blank=True)
    battery_capacity=models.CharField(max_length=100,null=True,blank=True)
    status=models.CharField(max_length=100,null=True,blank=True)
    warranty_type=models.CharField(max_length=100,null=True,blank=True)
    processor=models.CharField(max_length=100,null=True,blank=True)
    screen=models.CharField(max_length=100,null=True,blank=True)
    number_of_sim_slots=models.CharField(max_length=100,null=True,blank=True)
    mobile_phone=models.CharField(max_length=100,null=True,blank=True)
    main_camera_number=models.CharField(max_length=100,null=True,blank=True)
    phone_features=models.CharField(max_length=100,null=True,blank=True)
    operating_system=models.CharField(max_length=100,null=True,blank=True)
    telephone_cables=models.CharField(max_length=100,null=True,blank=True)
    main_camera=models.CharField(max_length=100,null=True,blank=True)
    camera_selfie=models.CharField(max_length=100,null=True,blank=True)
    
    #shoes mem
    shoe_brand=models.CharField(max_length=100,null=True,blank=True)
    shoe_material=models.CharField(max_length=100,null=True,blank=True)
    shoe_buckle_type=models.CharField(max_length=100,null=True,blank=True)
    leather_outside=models.CharField(max_length=100,null=True,blank=True)
    marker_style=models.CharField(max_length=100,null=True,blank=True)
    high_heel=models.CharField(max_length=100,null=True,blank=True)
    shoe_occasion=models.CharField(max_length=100,null=True,blank=True)
    shoe_leather_type=models.CharField(max_length=100,null=True,blank=True)
    shoe_collar_height=models.CharField(max_length=100,null=True,blank=True)
    suitable_width=models.CharField(max_length=100,null=True,blank=True)
    #Fashion accessories
    #Earring
    occasion_accessories=models.CharField(max_length=100,null=True,blank=True)
    earring_style=models.CharField(max_length=100,null=True,blank=True)#
    material_accessories=models.CharField(max_length=100,null=True,blank=True)
    style_accessories=models.CharField(max_length=100,null=True,blank=True)
    #ring
    accessory_set=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)#
    couple_accessories=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)#
    #Household electrical appliances
    brand_electrical=models.CharField(max_length=100,null=True,blank=True)
    input_voltage=models.CharField(max_length=100,null=True,blank=True)#
    receiver_type=models.CharField(max_length=100,null=True,blank=True)#
    weight=models.CharField(max_length=100,null=True,blank=True)
    dimensions=models.CharField(max_length=100,null=True,blank=True)
    power_consumption=models.CharField(max_length=100,null=True,blank=True)
    warranty_type=models.CharField(max_length=100,null=True,blank=True)

    #Travel & Luggage
    brand_luggage=models.CharField(max_length=100,null=True,blank=True)
    material_luggage=models.CharField(max_length=100,null=True,blank=True)
    waterproof=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)
    feature_folding_bag=models.CharField(max_length=100,null=True,blank=True)
    #Computers & Laptops 

    #Desktop computer
    brand_laptop=models.CharField(max_length=100,null=True,blank=True)
    storage_type=models.CharField(max_length=100,null=True,blank=True)
    optical_drive=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)
    port_interface=models.CharField(max_length=100,null=True,blank=True)
    operating_system_laptop=models.CharField(max_length=100,null=True,blank=True)
    processor_laptop=models.CharField(max_length=100,null=True,blank=True)
    number_of_cores=models.CharField(max_length=100,null=True,blank=True)
    dedicated_games=models.CharField(max_length=20,choices=CHOICE_YES_NO, null=True,blank=True)
    def __str__(self):
        return str(self.item)