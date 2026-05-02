from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from cart.models import Cart, CartItem
from cart.serializers import CartSerializer


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.prefetch_related('items__book').get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        book_id = request.data.get('book_id')
        quantity = int(request.data.get('quantity', 1))
        if not book_id:
            return Response({'error': 'book_id required'}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart, book_id=book_id, defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

        total_items = cart.items.count()
        return Response({'ok': True, 'total_items': total_items}, status=status.HTTP_200_OK)

    def patch(self, request):
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        if quantity < 1:
            return Response({'error': 'quantity must be >= 1'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = CartItem.objects.select_related('cart').get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        item.quantity = quantity
        item.save()
        total = sum(
            i.book.price * i.quantity
            for i in item.cart.items.select_related('book').all()
        )
        subtotal = item.book.price * item.quantity
        return Response({'ok': True, 'subtotal': str(subtotal), 'total': str(total)})

    def delete(self, request):
        item_id = request.data.get('item_id')
        CartItem.objects.filter(id=item_id, cart__user=request.user).delete()
        return Response({'ok': True})
