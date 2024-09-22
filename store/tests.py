from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from store.models import Order, Product, Category, Review

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

        self.category = Category.objects.create(name='Test Category')

        self.product = Product.objects.create(
            name='Test Product',
            price=50.00,
            description='Test description',
            category=self.category,
        )

    def test_order_creation(self):
        # Test the creation of an order
        order = Order.objects.create(
            user=self.user,
            total_price=100.00,
            status='delivered',
            shipping_cost=10.00,
            grand_total=110.00,
            address='123 Test St',
        )

        self.assertEqual(order.user.username, 'testuser')
        self.assertEqual(order.total_price, 100.00)
        self.assertEqual(order.status, 'delivered')
        self.assertEqual(order.grand_total, 110.00)

class CartTests(TestCase):
    def setUp(self):
        # Create a user for the test
        self.user = User.objects.create_user(username='testuser', password='testpass')

        # Create a category for products
        self.category = Category.objects.create(name='Electronics')

        # Create a product for the test
        self.product = Product.objects.create(
            name='Laptop',
            category=self.category,
            description='High-end gaming laptop',
            price=1500.00,
            stock=10,
            image=SimpleUploadedFile(
                name='test_image.jpg',
                content=b'fake image content',
                content_type='image/jpeg'
            )
        )

        self.client.login(username='testuser', password='testpass')

    def test_add_to_cart(self):
        """Test adding a product to the cart."""
        # Get the URL for adding to cart
        url = reverse('add_to_cart', args=[self.product.id])
        
        # Send a POST request to add the product
        response = self.client.post(url)

        # Verify the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Check if the session contains the product ID in the cart
        session = self.client.session
        self.assertIn(str(self.product.id), session['cart'])

        # Check if the correct quantity and price are stored
        cart_item = session['cart'][str(self.product.id)]
        self.assertEqual(cart_item['quantity'], 1)  # Check quantity
        self.assertEqual(cart_item['price'], "{:.2f}".format(self.product.price))  # Check price

    def test_cart_view(self):
        """Test the cart view functionality."""
        # Manually add a product to the cart session
        session = self.client.session
        session['cart'] = {str(self.product.id): {'quantity': 1, 'price': "{:.2f}".format(self.product.price)}}
        session.save()

        # Access the cart page
        url = reverse('cart_detail')
        response = self.client.get(url)

        # Verify that the response contains the product name
        self.assertContains(response, self.product.name)

        # Check if the correct quantity and price are displayed
        self.assertContains(response, 1)
        self.assertContains(response, "{:.2f}".format(self.product.price))

class ReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='reviewpass')
        self.category = Category.objects.create(name='Books')
        self.product = Product.objects.create(
            name='Django for Beginners',
            category=self.category,
            description='A comprehensive guide to Django',
            price=45.00,
            stock=20
        )
        self.client.login(username='reviewer', password='reviewpass')

    def test_add_review(self):
        url = reverse('product_detail', args=[self.product.id])
        data = {
            'comment': 'Great book for Django enthusiasts!',
            'rating': 5,
            # No image is provided
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        review_exists = Review.objects.filter(user=self.user, product=self.product).exists()
        self.assertTrue(review_exists)

    