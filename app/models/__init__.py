from django.db import models

# Import all your models here
from app.models.blog import BlogPost
from app.models.customer import User, UserRoles, Role, Company, CompanyMembers
from app.models.forum import ForumComment, ForumPost, Thread, ThreadRoles
from app.models.product import Product
from app.models.order import Contracts, Orders, OrderHistory, OrderChangeRequest, ShippingAddress, Customer, OrdersList
from app.models.ticket import TicketComment, TicketForum, Resolution
from app.models.calendar import Event
from app.models.public import Home, About
from app.models.message import Message, Room, UserRoom
from app.models.job import Job
from app.models.application import Application, StatusCode


# Define relationships between models
# Company
Company.customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='company')

# User
User.roles = models.ManyToManyField(Role, through=UserRoles)
User.posts = models.ManyToManyField(ForumPost, related_name='author')
User.comments = models.ManyToManyField(ForumComment, related_name='author')
User.companies = models.ManyToManyField(Company, through=CompanyMembers)
User.customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='user')
User.tickets = models.ManyToManyField(TicketForum, related_name='user')
User.ticket_comments = models.ManyToManyField(TicketComment, related_name='user')
User.messages = models.ManyToManyField(Message, related_name='author')
User.rooms = models.ManyToManyField(Room, through=UserRoom)
User.jobs = models.ManyToManyField(Job, related_name='user')
User.applications = models.ManyToManyField(Application, related_name='user')

# Job
Job.user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job')

# Application
Application.user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='application')
Application.job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='application')

# User Roles
UserRoles.user = models.ForeignKey(User, on_delete=models.CASCADE)
UserRoles.role = models.ForeignKey(Role, on_delete=models.CASCADE)

# Company Members
CompanyMembers.company = models.ForeignKey(Company, on_delete=models.CASCADE)
CompanyMembers.user = models.ForeignKey(User, on_delete=models.CASCADE)
CompanyMembers.role = models.ForeignKey(Role, on_delete=models.CASCADE)

# Role
Role.event_info = models.ManyToManyField(Event, related_name='role_info')

# Customer
Customer.user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
Customer.company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='customer')
Customer.orders = models.ManyToManyField(Orders, related_name='customer')
Customer.contracts = models.ManyToManyField(Contracts, related_name='customer')
Customer.shipping_address = models.ManyToManyField(ShippingAddress, related_name='customer')

#ShippingAddress
ShippingAddress.customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='shipping_address')

#Orders
Orders.user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
Orders.orders_list = models.ManyToManyField(OrdersList, related_name='orders')
Orders.customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
Orders.order_history = models.ManyToManyField(OrderHistory, related_name='order')
Orders.order_change_request = models.ManyToManyField(OrderChangeRequest, related_name='order')

#OrderChangeRequest
OrderChangeRequest.order = models.ManyToManyField(Orders, related_name='order_change_request')
OrderChangeRequest.orders_list = models.ManyToManyField(OrdersList, related_name='order_change_request')

#OrdersList
OrdersList.orders = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='orders_list')
OrdersList.order_change_request = models.ForeignKey(OrderChangeRequest, on_delete=models.CASCADE, related_name='orders_list')
OrdersList.product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders_list')

#OrderHistory
OrderHistory.order = models.ManyToManyField(Orders, related_name='order_history')

#Contracts
Contracts.customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

#Thread
Thread.roles = models.ManyToManyField(Role, through=ThreadRoles)

#ThreadRoles
ThreadRoles.thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
ThreadRoles.role = models.ForeignKey(Role, on_delete=models.CASCADE)

#ForumPost
ForumPost.comments = models.ManyToManyField(ForumComment, related_name='post')
ForumPost.thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
ForumPost.author = models.ForeignKey(User, on_delete=models.CASCADE)

#ForumComment
ForumComment.author = models.ForeignKey(User, on_delete=models.CASCADE)
ForumComment.post = models.ForeignKey(ForumPost, on_delete=models.CASCADE)

#Event
Event.user = models.ForeignKey(User, on_delete=models.CASCADE)
Event.organizer = models.ForeignKey(User, on_delete=models.CASCADE)
Event.role = models.ForeignKey(Role, on_delete=models.CASCADE)
Event.role_info = models.ManyToManyField(Role, related_name='event_info')

#TicketForum
TicketForum.user = models.ForeignKey(User, on_delete=models.CASCADE)
TicketForum.customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

#TicketComment
TicketComment.ticket = models.ForeignKey(TicketForum, on_delete=models.CASCADE)
TicketComment.author = models.ForeignKey(User, on_delete=models.CASCADE)

# Message
Message.author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
Message.room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')

# Room
Room.messages = models.ManyToManyField(Message, related_name='room')
Room.members = models.ManyToManyField(User, through=UserRoom, related_name='rooms')

# User Room
UserRoom.user = models.ForeignKey(User, on_delete=models.CASCADE)
UserRoom.room = models.ForeignKey(Room, on_delete=models.CASCADE)