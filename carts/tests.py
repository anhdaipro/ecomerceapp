from django.test import TestCase

# Create your tests here.
def discount_deal_by(self):
        return self.quantity * self.byproduct.discount_price_deal_shock()
    def price_by(self):
        return self.quantity*self.byproduct.price
    def discount_by(self):
        total_discount=0
        if self.item.program_valid():
            total_discount=self.quantity*self.product.price*(self.product.percent_discount/100)
        return total_discount
    def total_price(self):
        return self.price_by()-self.discount_deal_by()-self.discount_by()

    def get_image(self):
        image=self.item.get_image_cover()
        if self.product.color:
            if self.product.color.image:
                image=self.product.color.image.url
        return image