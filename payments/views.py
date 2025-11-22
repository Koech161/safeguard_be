import paypalrestsdk
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt




@csrf_exempt
def create_payment(request):
    amount = request.POST.get("amount", "5.00")
    
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "https://safeguard.vercel.app/paypal/success",
            "cancel_url": "https://safeguard.vercel.app/paypal/cancel",
        },
        "transactions": [{
            "amount": {"total": amount, "currency": "USD"},
            "description": "Support Payment"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.method == "REDIRECT":
                return JsonResponse({"approval_url": link.href})
    else:
        return JsonResponse({"error": payment.error}, status=400)    

@csrf_exempt
def execute_payment(request):
    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")
    
    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        return JsonResponse({"status": "success"})
    else:
        return JsonResponse({"error": payment.error}, status=400)    