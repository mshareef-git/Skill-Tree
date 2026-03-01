import nlpcloud


class NLPApp:
    def __init__(self):
        self.__database = {}
        self.__first_menu()

    def __first_menu(self):
        first_input = input("""
        Welcome!!
        How would you like to proceed?
        1. Not a member? Register
        2. Already a member? Login
        3. Exit
        """)

        if first_input == "1":
            self.__register()
        elif first_input == "2":
            self.__login()
        else:
            exit()

    def __second_menu(self):
        second_input = input("""
        How would you like to proceed?
        1. NER
        2. Language Detection
        3. Sentiment Analysis
        4. Logout
        """)

        if second_input == "1":
            self.__ner()
        elif second_input == "2":
            self.__language_detection()  # fixed typo from original
        elif second_input == "3":
            self.__sentiment_analysis()
        else:
            exit()

    def __register(self):
        name = input("Enter your name: ")
        email = input("Enter your email: ")
        password = input("Enter your password: ")

        # Check if the email is already registered
        if email in self.__database:
            print("Email already exists. Please try logging in.")
        else:
            self.__database[email] = [name, password]
            print("Registration Successful! Welcome,", name)
            self.__first_menu()

    def __login(self):
        email = input("Enter your email: ")
        password = input("Enter your password: ")

        # Verify email existence then match password
        if email in self.__database:
            if self.__database[email][1] == password:
                print("Login Successful! Welcome back,", self.__database[email][0])
                self.__second_menu()
            else:
                print("Wrong password! Please try again.")
                self.__login()
        else:
            print("Email is not registered. Please register first.")
            self.__first_menu()

    def __ner(self):
        # Named Entity Recognition — finds specific entities in a paragraph
        para = input("Enter the paragraph: ")
        search_term = input("What would you like to search for: ")

        client = nlpcloud.Client(
            "finetuned-gpt-neox-20b",
            "replace this line with your api from nlp website""
            gpu=True,
            lang="en",
        )
        response = client.entities(para, searched_entity=search_term)
        print(response)
        self.__second_menu()

    def __language_detection(self):
        # Detects the language of the given text
        para = input("Enter the text for language detection: ")

        client = nlpcloud.Client(
            "python-langdetect",
            "Replace this line with your api from nlp website",
            gpu=False,
        )
        response = client.langdetection(para)

        # Display each detected language and its score
        print("\n--- Language Detection Results ---")
        for lang in response["languages"]:
            for language, score in lang.items():
                print(f"  {language}: {round(score * 100, 2)}%")
        print("----------------------------------\n")

        self.__second_menu()

    def __sentiment_analysis(self):
        # Analyzes the emotional tone of the input paragraph
        para = input("Enter the paragraph: ")

        client = nlpcloud.Client(
            "distilbert-base-uncased-emotion",
            "replace this line with you api from nlp website",
            gpu=False,
            lang="en",
        )
        response = client.sentiment(para)

        # Sort all emotions by score in descending order (highest first)
        sorted_emotions = sorted(
            response["scored_labels"], key=lambda x: x["score"], reverse=True
        )

        # Print all emotions with their scores, highest scoring first
        print("\n--- Sentiment Analysis Results ---")
        for emotion in sorted_emotions:
            label = emotion["label"].capitalize()
            score = round(emotion["score"] * 100, 2)
            print(f"  {label}: {score}%")
        print("----------------------------------")

        # Highlight the dominant emotion
        top_emotion = sorted_emotions[0]["label"].capitalize()
        print(f"\n  Dominant Emotion: {top_emotion}\n")

        self.__second_menu()


obj = NLPApp()

