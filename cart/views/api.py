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

    def delete(self, request):
        item_id = request.data.get('item_id')
        CartItem.objects.filter(id=item_id, cart__user=request.user).delete()
        return Response({'ok': True})
