import random

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']


# This is where we'll store all the characters

password_char = []
  

print("Welcome to the PyPassword Generator!")

nr_letters = int(input("How many letters would you like in your password?\n"))

for _ in range(nr_letters):
    password_char.append(random.choice(letters))

nr_numbers = int(input("How many numbers would you like?\n"))

for _ in range(nr_numbers):
    password_char.append(random.choice(numbers))

nr_symbols = int(input("How many symbols would you like?\n"))

for _ in range(nr_symbols):
    password_char.append(random.choice(symbols))

# we'll shuffle here to avoid "ABD123!@#" pattern

password = random.shuffle(password_char)

# converting the $password_char to string

password = "".join(password_char)

# Your are not even using all the variables here azeem bro
# password=random.choice(letters)

print(password)
