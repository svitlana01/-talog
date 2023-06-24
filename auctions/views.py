from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required 
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Auction, Rate, Comment


# creating the main variable - the categories-list ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CATEGORIES = ["Tanks", "Armored_Cars", "Military_Aircraft", "Armored_trains", "Navy", "Air_Defence", "Artillery", "Oters"]
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def index(request):
    auctions = Auction.objects.all()
    couples_auction_price = []
    for auction in auctions:
        couple = []
        couple.append(auction)
        rates = Rate.objects.filter(auction = auction)
        if rates: 
            last_rate = rates.last()
            last_price = int(last_rate.rate)           
        else:
            last_price = int(auction.startprice)
        couple.append(last_price)
        couples_auction_price.append(couple)
    return render(request, "auctions/index.html", { 
        "auctions": auctions,
        "couples_auction_price": list(couples_auction_price)
    })
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++p+++++++
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            auctions = user.auctions.all()
            return HttpResponseRedirect(reverse("watchlist", args=(user.username, )))
        
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@login_required
def logout_view(request):    
    logout(request)
    return HttpResponseRedirect(reverse("index"))
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# creating the new auction +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@login_required 
def new(request):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")
 
    if request.method == "POST":
        if not request.POST["name"]:
            return render(request, "auctions/new.html", {
                "categories": CATEGORIES,
                "message": "You have not inputed the auction name!!!"
            })

        elif not request.POST["startprice"]:
            return render(request, "auctions/new.html", {
                "categories": CATEGORIES,
                "message": "You have not inputed the auction startprice!!!"
            })

        elif not request.POST["categories"]:
            return render(request, "auctions/new.html", {
                "categories": CATEGORIES,
                "message": "You have not inputed the auction categories!!!"
            })

        user_id = request.user.id
        user_creator = User.objects.get(pk = user_id)
        auction = Auction(user_creator = user_creator, name = request.POST["name"], 
                          information = request.POST["information"], startprice = request.POST["startprice"], 
                          photo = request.POST["photo"], category = request.POST["categories"], not_closed = True)
        auction.save()
        return HttpResponseRedirect(reverse("auction", args=(auction.id,)))

    return render(request, "auctions/new.html", {
        "categories": CATEGORIES
    })
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# view the choosen auction +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def auction(request, auction_id):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")   

    auction = Auction.objects.get(pk = auction_id)             # getting the auction we are watching 
    rates = Rate.objects.filter(auction = auction)             # getting the rates list
    comments = Comment.objects.filter(auction = auction)       # getiing the commens list
    # user = User.objects.get(username = request.user.username)  
    user = request.user                                        # getting our user
    auctions = user.auctions.all()                             # getting the all user's auctions list 
    user_creator = str(auction.user_creator)
    current_user = str(user)
    last_rate = rates.last()                                   # getting the last users rate

    # if method = POST for any (closed or active) auction
    if request.method == "POST":       
        if auction in auctions:                                                   
            user.auctions.remove(auction)            
            user.save()            
        else:
            user.auctions.add(auction) 
            user.save() 
        return HttpResponseRedirect(reverse("watchlist", args = (user.username,)))

    # if current auction is active and method = GET
    if auction.not_closed == True:   
        if last_rate:
            actual_price = last_rate.rate
        else:
            actual_price = auction.startprice

        return render(request, "auctions/auction.html", {
            "auctions": auctions,
            "auction": auction, 
            "rates": rates,
            "comments": comments,
            "actual_price": actual_price,
            "user_creator": user_creator,
            "current_user": current_user
        })

    # if current auction is closed and method = GET
    else:
        if last_rate:
            user_winner = last_rate.rating_user            
        else: 
            user_winner = auction.user_creator

        # if current user is a user-winner
        if user == user_winner:
            return render(request, "auctions/auction.html", {
                "auctions": auctions,
                "auction": auction,
                "rates": rates,
                "comments": comments,
                "message": "Congratulations!!!! You are the winner!!!!!!!"
            })

        # if current user is a user-creator and there were no intrested buyers
        if user == auction.user_creator and not last_rate:
            return render(request, "auctions/auction.html", {
                "auctions": auctions,
                "auction": auction,
                "rates": rates,
                "comments": comments,
                "message": "No interested buyers were found for your product!"
            })

        # if current user is NOT a user-winner
        return render(request, "auctions/auction.html", {
            "auctions": auctions,   
            "auction": auction,
            "rates": rates,
            "comments": comments,
        })
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# search the choosen auctions +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@login_required
def watchlist(request, user_username):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")

    user = User.objects.get(username = user_username)
    auctions = user.auctions.all()
    couples_auction_price = []
    for auction in auctions:
        couple = []
        couple.append(auction)
        rates = Rate.objects.filter(auction = auction)
        if rates: 
            last_rate = rates.last()
            last_price = int(last_rate.rate)           
        else:
            last_price = int(auction.startprice)
        couple.append(last_price)
        couples_auction_price.append(couple)    
    return render(request, "auctions/watchlist.html", {
        "user.username": user_username,  
        "auctions": auctions,
        "couples_auction_price": couples_auction_price
    }) 
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# comment the choosen auction +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@login_required
def comment(request, auction_id):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")

    if request.method == "POST":        
        comment_text = request.POST["comment"]                          # getting the new comment        
        commenting_user = request.user                                  # getting the user commenting th auction
        commented_auction = Auction.objects.get(pk = auction_id)        # getting the auction we are commenting
        new_comment = Comment(comment = comment_text, commenting_user = commenting_user, auction = commented_auction)
        new_comment.save()
        return HttpResponseRedirect(reverse("auction", args = (commented_auction.id,)))
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# rate the choosen auction +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@login_required
def rate(request, auction_id):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")

    if request.method == "POST":
        rate_value = int(request.POST["rate"])                         # getting data from the form
        rating_user = request.user                                     # getting the current user
        rated_auction = Auction.objects.get(pk = auction_id)           # getting the rated auction 
        auction_rates = Rate.objects.filter(auction = rated_auction)   # getting rates list for our user

        if rate_value <= int(rated_auction.startprice):
            return render(request, "auctions/auction.html", {                                                        
                "message": "The rate is too small",
                "auctions": rating_user.auctions.all(),
                "auction": rated_auction, 
                "rates": auction_rates,
                "comments": Comment.objects.filter(auction = rated_auction)
            })

        for auction_rate in auction_rates:
            if rate_value <= int(auction_rate.rate):
                return render(request, "auctions/auction.html", {                                                        
                    "message": "The rate is too small",
                    "auctions": rating_user.auctions.all(),
                    "auction": rated_auction, 
                    "rates": auction_rates,
                    "comments": Comment.objects.filter(auction = rated_auction)
                })

        new_rate = Rate(rate = rate_value, rating_user = rating_user, auction = rated_auction)   # creating the new rate
        new_rate.save()                                                                          # saving the new rate
        return HttpResponseRedirect(reverse("auction", args = (rated_auction.id,)))
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# getting all the categories ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": CATEGORIES
    })
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# getting the current category +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def category(request, category):
    category = request.GET["categories"]
    auctions = Auction.objects.filter(category = category)
    couples_auction_price = []
    for auction in auctions:
        couple = []
        couple.append(auction)
        rates = Rate.objects.filter(auction = auction)
        if rates: 
            last_rate = rates.last()
            last_price = int(last_rate.rate)           
        else:
            last_price = int(auction.startprice)
        couple.append(last_price)
        couples_auction_price.append(couple)

    return render(request, "auctions/category.html", {
        "category": category,
        "auctions": auctions,
        "couples_auction_price": couples_auction_price
    })
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# closing the auction ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@login_required
def close(request, auction_id):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html")

    auction = Auction.objects.get(pk = auction_id)
    user_creator = str(auction.user_creator)
    curent_user = str(request.user)
    if curent_user == user_creator:
        if request.method == "POST":
            auction.not_closed = False
            auction.save()
            return HttpResponseRedirect(reverse("auction", args = (auction.id,)))
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



