import json
import stripe
from django.conf import settings
from django.http import JsonResponse
from cart.cart import Cart
from .models import Order, OrderItem

def start_order(request):
    cart = Cart(request)
    data = json.loads(request.body)
    total_price = 0
    items = []

    for item in cart:
        product = item['product']
        total_price += product.price * int(item['quantity'])

        items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product.name,
                },
                'unit_amount': int(product.price * 100),  # Convert to cents
            },
            'quantity': item['quantity']
        })

    stripe.api_key = settings.STRIPE_API_KEY_HIDDEN
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=items,
        mode='payment',
        success_url='http://127.0.0.1:8000/cart/success/',
        cancel_url='http://127.0.0.1:8000/cart/'
    )
    
    # Check if the Stripe session was created successfully
    if session:
        payment_intent = session.payment_intent
        order = Order.objects.create(
            user=request.user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data['phone'],
            address=data['address'],
            zipcode=data['zipcode'],
            place=data['place'],
            payment_intent=payment_intent,  # Make sure this field exists in your Order model
            paid=True,
            paid_amount=total_price
        )

        for item in cart:
            product = item['product']
            quantity = int(item['quantity'])
            price = product.price * quantity

            item = OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)

        # Clear the cart only if the order creation was successful
        cart.clear()
        
        return JsonResponse({'session': session, 'order': payment_intent})

    # Handle the case where the Stripe session creation failed
    return JsonResponse({'error': 'Failed to create a Stripe session'})
