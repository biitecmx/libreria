from unicodedata import category
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, render

from .models import Book, Category, ExtraImage, OrderBook, Order, Address
from .forms import CheckoutForm, SearchForm

from django.views.generic import DetailView, View


# Home views
default_layout = 'agency'
default_header = 'dark'
# TODO: remove absolute path
default_header_image = '/static/assets/images/logo/logo-transparent.png'


# custom views

class BookDetailView(DetailView):
    model = Book
    context_object_name = 'book'
    template_name = "book_details/book_detail.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add data for the context
        data = {"layout":"agency",
        "header":"dark position-relative nav-lg"}
        context.update(data)
        return context
    
# class BookSearchView(View):
#     model = Book
from django.db.models import Q

def search_view(request):
    form = SearchForm(request.GET)
    results = []
    if form.is_valid():
        query = form.cleaned_data['query']
        # Perform search operation using the query
        # You can use Django ORM or any other method to fetch the search results
        results = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(tags__name__in=[query])
        )

    return render(request, 'search-book.html', {'form': form, 'results': results, "layout":default_layout,"header":"dark position-relative nav-lg"})

def index(request):
    # TODO: Change to class based view
    books = Book.objects.all().order_by('-id')
    categories =  Category.objects.all()
    context={
        'books': books[:10],
        'new_books': books[:5],
        'categories': categories,
        'header_classes':'ecommerce nav-fix',
        'header_image':default_header_image}
    return render(request,'home/ecommerce_layout/ecommerce_layout.html',context)

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'order': order,
                
                "layout":default_layout,
                "header":"dark position-relative nav-lg"
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("djbooks:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            if form.is_valid():
                save_address = form.cleaned_data.get(
                    'save_address')
                if save_address:
                    street_address = form.cleaned_data.get(
                        'street_address')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country') or "México"
                    shipping_city = form.cleaned_data.get(
                        'shipping_city')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([street_address, shipping_country, shipping_zip, shipping_city]):
                        shipping_address = Address(
                            user=self.request.user,
                            names=form.cleaned_data.get('names'),
                            last_names=form.cleaned_data.get('last_names'),
                            phone=form.cleaned_data.get('phone'),
                            email=form.cleaned_data.get('email'),
                            street_address=street_address,
                            shipping_country=shipping_country,
                            shipping_city=shipping_city,
                            shipping_zip=shipping_zip,
                            address_type='S'
                        )

                        order.shipping_address = shipping_address

                        shipping_option = form.cleaned_data.get('shipping_option')
                        order.shipping_option = shipping_option

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            #TODO: Use this for autofill
                            shipping_address.default = True
                        shipping_address.save()
                        order.save()
                        

                    else:
                        messages.warning(
                            self.request, "Please fill in the required shipping address fields")
                        
                payment_option = form.cleaned_data.get('payment_option')
                shipping_option = form.cleaned_data.get('shipping_option')

                from json import dumps #TODO: REMOOOOVE

                print("FORM: ", dumps(form.cleaned_data, indent=4))
                print("Ship: ", shipping_option)

                if payment_option == 'mercado_pago':
                    return redirect('djbooks:payment' )#,kwargs={'payment_option':'mercado_pago'})
                elif payment_option == 'paypal':
                    messages.info(self.request, "Pago con Paypal")
                    return redirect('djbooks:checkout')
                    #return redirect('djbooks:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option selected")
                    return redirect('djbooks:checkout')
            else:
                messages.warning(self.request, f"Form is not valid {form.errors.as_text()}")
                return redirect('djbooks:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("djbooks:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        # if order.billing_address:
        #     messages.info(self.request, "Agregaste una dirección")
        # else:
        #     messages.warning(self.request, "No agregaste una dirección")
        #     return redirect("core:checkout")
        context = {
            'order': order,
        }
        data = {"layout":default_layout,"header":"dark position-relative nav-lg"}
        context.update(data)
        return render(self.request, "payment.html", context)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist

class PaymentSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            data = {"layout":default_layout,"header":"dark position-relative nav-lg"}
            context.update(data)
            return render(self.request, 'purchases.html',context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "Tu carrito está vacío")
            return redirect("/")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            data = {"layout":default_layout,"header":"dark position-relative nav-lg"}
            context.update(data)
            return render(self.request, 'cart.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "Tu carrito está vacío")
            return render(self.request, 'cart.html')


# pages views 
from allauth.account.views import LoginView, SignupView
class CustomLoginView(LoginView):

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add data for the context
        data = {"layout":default_layout,"header":"dark position-relative nav-lg"}
        context.update(data)
        return context

class CustomSignupView(SignupView):

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add data for the context
        data = {"layout":default_layout,"header":"dark position-relative nav-lg"}
        context.update(data)
        return context

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def multiple_upload(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if request.method == 'POST':
        data = request.POST
        images = request.FILES.getlist('images')

        print("DATA: ", data)

        for image in images:
            print("IMG: ",image)
            ExtraImage.objects.create(
                book=book,
                image=image,
            )
        return redirect(reverse("admin:djbooks_book_change", args=(book.id,)))
    context = {
        "book": book,
    }
    return render(request,'admin/multiupload.html',context)



def pages_404(request):
    context = {"layout":default_layout,"header":default_header}
    return render(request,'pages/404/404.html',context)

def faqs(request):
    context={"header":"dark","layout":"agency"}
    return render(request,'pages/faq/faq.html',context)

def request_book(request):
    context={
        "header":"dark",
        "layout":"agency",
    }
    return render(request,'request-book.html',context)

from django.views.generic import ListView


def collection(request):
    context={
        "header":"dark",
        "layout":"agency", 
        # passing a dict with the total of books per category
        "data": Book.get_book_all_categories_count()
    }
    return render(request,'collection.html',context)


class CollectionListView(ListView):
    paginate_by = 4
    model = Book
    context_object_name = "category_books"
    template_name = "book_categories/book_category.html"

    def get_queryset(self, **kwargs):
       qs = super().get_queryset(**kwargs)
       return qs.filter(category__slug=self.kwargs['category'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['category']
        category = Category.objects.get(slug=slug)
        # Add data for the context
        data = {"layout":default_layout,
            "header":"dark position-relative nav-lg",
            "title": category.name,
        }
        context.update(data)
        return context

# cart views

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def add_to_cart(request, slug):
    book = get_object_or_404(Book, slug=slug)
    # Check availability of the book
    if book.stock == 0:
        messages.warning(request, "Lo sentimos, ya no hay ejemplares disponibles")
        return redirect("djbooks:order-summary")          
    order_item, created = OrderBook.objects.get_or_create(
        item=book,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order book is in the order
        if order.items.filter(item__slug=book.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Libro añadido al carrito.")
            return redirect("djbooks:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Libro añadido al carrito.")
            return redirect("djbooks:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This book was added to your cart.")
        return redirect("djbooks:order-summary")

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Book, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderBook.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "Libro retirado del carrito")
            return redirect("djbooks:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("djbooks:order-summary")
    else:
        messages.info(request, "You do not have an active order")
        return redirect("djbooks:order-summary")

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Book, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderBook.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "Libro retirado del carrito")
            return redirect("djbooks:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("djbooks:order-summary")
    else:
        messages.info(request, "You do not have an active order")
        return redirect("djbooks:order-summary")

# wishlist
@login_required
def wishlist(request):
    books = Book.objects.filter(users_wishlist=request.user)
    context = {"layout":default_layout,"header":"dark position-relative nav-lg","wishlist": books}
    return render(request,'wishlist.html',context)

@login_required
def add_to_wishlist(request, slug):
    book = get_object_or_404(Book, slug=slug)
    # Check availability of the book
    if not book.users_wishlist.filter(id=request.user.id).exists():
        book.users_wishlist.add(request.user)
        messages.success(request, "Agregaste " + book.title + " a tu wishlist")
    return redirect("djbooks:users-wishlist")


@login_required
def remove_from_wishlist(request, slug):
    book = get_object_or_404(Book, slug=slug)
    # Check availability of the book
    if book.users_wishlist.filter(id=request.user.id).exists():
        book.users_wishlist.remove(request.user)
        messages.success(request, "Quitaste " + book.title + " de tu wishlist")
    return redirect("djbooks:users-wishlist")

