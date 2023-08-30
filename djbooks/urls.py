from django.urls import path
from . import views

app_name = 'djbooks'

urlpatterns = [
    
    # home paths

    path('',views.index,name='index'),
    
    # pages paths
    path('pages_404',views.pages_404,name='pages_404'),
    path('faqs',views.faqs,name='faqs'),
    
    # custom types paths

    path('accounts/login/', views.CustomLoginView.as_view(),name='login'),
    path('accounts/signup/', views.CustomSignupView.as_view(),name='sign_up'),
    path('compras', views.PaymentSummaryView.as_view(), name='purchases'),
    path('carrito', views.OrderSummaryView.as_view(), name='order-summary'),
    path('checkout', views.CheckoutView.as_view(), name='checkout'),
    path("wishlist", views.wishlist, name="users-wishlist"),
    path('pago', views.PaymentView.as_view(), name='payment'),
    path('solicitar_libro',views.request_book,name='solicitar_libro'),
    path('buscar_libro', views.search_view, name='buscar_libro'),
    path('catalogo',views.collection,name='catalago'),
    path('categoria/<str:category>',views.CollectionListView.as_view(), name='categoria'),
    path('<slug:slug>', views.BookDetailView.as_view(), name='book_detail'),
    
    # Cart
    path('add-to-cart/<slug>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', views.remove_single_item_from_cart,name='remove-single-item-from-cart'),
    
    # Wish List
    path('add-to-wishlist/<slug>/', views.add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/<slug>/', views.remove_from_wishlist, name='remove-from-wishlist'),

    # Multiple upload
    path('multiple-upload/<slug>/', views.multiple_upload, name='multiple-upload'),

]
