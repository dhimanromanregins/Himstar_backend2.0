from django.shortcuts import render

def main_page(request):
    return render(request, 'index.html')


def contact_us(request):
    return render(request, 'contact.html')


def payment_page(request):
    return render(request, 'payment.html')


def privacy_page(request):
    return render(request, 'privacy.html')


def terms_page(request):
    return render(request, 'terms.html')


def withdraw_page(request):
    return render(request, 'withdrawl.html')