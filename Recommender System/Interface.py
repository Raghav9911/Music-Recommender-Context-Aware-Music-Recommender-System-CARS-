import pandas as pd
import numpy as np
import math
import sys
import warnings
from os import system
from device_detector import DeviceDetector
from Preprocessor import fetch_data
from Recommender import get_same_rated_items, compute_similarities, get_user_ratings, \
                        get_user_neighbourhood, compute_recommendations, get_r_best_recommendations, \
                        convert_context, get_user_mean_rating, get_recommendations
from Evaluation import MAE, precision_recall

warnings.filterwarnings("ignore", category=RuntimeWarning)

# reading in data
song_dataframe = pd.read_csv("dataset/song_data.csv", index_col=False,\
                                                     delimiter=",", encoding="utf-8-sig")
contexts = ['u', 'urban', 'm', 'mountains', 'cs', 'countryside', 'cl', 'coastline']

N = 17  # neighbourhood size
threshold = 0.1     # threshold for Filter PoF

main_dataframe, user_id_list, item_id_list = fetch_data()


# logs user in given that ID they provided was valid
def sign_in():

    print("Welcome to the Music Recommender System! Please enter your user ID:")

    is_valid_id = False

    while not is_valid_id:

        user_id = get_user_id_input()
        is_valid_id = validate_user(user_id)

        if not is_valid_id:
            print("The user " + str(user_id) + " does not exist. Please try again:")
    
    return user_id


# gets user's context explicitly
def set_context():

    print("Please enter the landscape:")
    print("u for urban")
    print("m for mountains")
    print("cs for countryside")
    print("cl for coastline")
    while True:
        context = str(input())
        context = context.lower()
        if context in contexts:
            break;
        elif context == 'v':
            print("u for urban")
            print("m for mountains")
            print("cs for countryside")
            print("cl for coastline")
        else:
            print("Invalid landscape. Please try again.")

    context = convert_context(context)

    return context


# displays menu when user signs in
def main_menu(user_id, context, R):

    print("Signed in as User " + str(user_id) + ".")
    print("Press G to generate your recommendations.")
    print("Press E to enter evaluation mode.")
    print("Press S to configure the settings.")
    print("Press X to sign out of your account.")
    print("Press Q to quit the Music Recommender System.")
    
    while True:
        command = str(input())
        command = command.upper()
        if command == 'G' or command == 'E' or command == 'S' or command == 'X' or command == 'Q':
            break;
        else:
            print("Invalid command. Please try again.")
    
    if command == 'G':
        original_recommendations, r_predicted_ratings, user_mean_rating =\
            get_recommendations(user_id, main_dataframe, context, R, N, threshold)

        # only return recommendations whose predicted rating is higher than user's average rating
        filtered_r_predicted_ratings =\
            filter_recommendations(r_predicted_ratings, user_mean_rating)

        display_recommendations(user_id, filtered_r_predicted_ratings, user_mean_rating)
        main_menu(user_id, context, R)

    elif command == 'E':
        evaluate(user_id, context, R)

    elif command == 'S':
        context, R = configure_settings(user_id, context, R)
        main_menu(user_id, context, R)

    elif command == 'X':
        main()

    else:
        sys.exit()


# takes user ID as input explicitly and logs them in
def get_user_id_input():

    while True:
        try:
            user_id = int(input())
            break;
        except ValueError:
            print("Invalid format. Please enter an integer and try again.")
    
    return user_id


def validate_user(user_id):
    
    # verifies that given user ID is a valid user
    if user_id in user_id_list:
        return True
    return False


# display specificed user's personalised recommendations
def display_recommendations(user_id, predicted_ratings, user_mean_rating):

    print("Your recommendations are:\n")

    # combine to display song titles and artists
    predicted_ratings_data = list(predicted_ratings.items())
    r_dataframe = pd.DataFrame(predicted_ratings_data, columns=['ItemID', 'Predicted Rating'])
    recommendations = pd.merge(song_dataframe, r_dataframe, on='ItemID', how='right')

    # reorder columns and sort from most to least recommended
    recommendations = recommendations[['ItemID', 'title', 'artist', 'Predicted Rating']]
    recommendations = recommendations.rename(columns={"title": "Song Title", "artist": "Artist"})
    recommendations = recommendations.sort_values(by=['Predicted Rating'], ascending=False)
    recommendations = recommendations.drop('Predicted Rating', axis=1)
    #recommendations = recommendations.drop('Predicted Rating', 1)
    recommendations = recommendations.reset_index(drop=True)

    print(recommendations, "\n")


# remove recommendations with rating of 0 or NaN and remove predicted rating column
def filter_recommendations(predicted_ratings, user_mean_rating):

    predicted_ratings_copy = predicted_ratings.copy()

    for item_id, predicted_rating in predicted_ratings_copy.items():

        if predicted_rating < user_mean_rating or math.isnan(predicted_rating):
            del predicted_ratings[item_id]
    
    if not(predicted_ratings) or len(predicted_ratings) < 2:
        return predicted_ratings_copy
    return predicted_ratings


# allow user to run one of the evaluation metrics
def evaluate(user_id, context, R):

    print("Press M to calculate the mean absolute error of the system.")
    print("Press P to calculate the precision of the system.")
    print("Press R to calculate the recall of the system.")
    print("Press B to return to the main menu.")

    while True:
        command = str(input())
        command = command.upper()
        if command == 'M' or command == 'P' or command == 'R' or command == 'B':
            break;
        else:
            print("Invalid command. Please try again.")

    if command == 'M':
        print("This calculation will take a few minutes. Please be patient...")
        error = MAE(main_dataframe, R, N, threshold)
        print("The Mean Absolute Error of the Music Recommender System is " + str(error) + ".")
        evaluate(user_id, context, R)

    elif command == 'P':
        print("This calculation will take a few seconds. Please be patient...")
        precision = precision_recall(main_dataframe, R, N, threshold, is_precision=True)
        print("The precision of the system is " + str(precision) + ".")
        evaluate(user_id, context, R)

    elif command == 'R':
        print("This calculation will take a few seconds. Please be patient...")
        recall = precision_recall(main_dataframe, R, N, threshold, is_precision=False)
        print("The recall of the system is " + str(recall))
        evaluate(user_id, context, R)

    else:
        main_menu(user_id, context, R)
    

# allows user to change settings based on their own preferences or due to device size/disability etc
def configure_settings(user_id, context, R):

    print("Press R to change the number of recommendations.")
    print("Press L to change the landscape.")
    print("Press B to return to the main menu.")

    while True:
        command = str(input())
        command = command.upper()
        if command == 'R' or command == 'L' or command == 'B':
            break;
        else:
            print("Invalid command. Please try again.")
    
    if command == 'R':
        R = set_num_recommendations(R)
        return context, R
    elif command == 'L':
        print("The current landscape is " + str(context) + ".")
        context = set_context()
        return context, R
    else:
        main_menu(user_id, context, R)


# sets number of recommendations to display
def set_num_recommendations(R):

    print("Please enter the number of recommendations you wish to get (default " + str(R) + "):")

    while True:
        try:
            R = int(input())
            break;
        except ValueError:
            print("Invalid format. Please enter an integer and try again.")

    return R


def get_device_type():

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"\
     + "(KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"

    device = DeviceDetector(ua).parse()
    device_type = device.device_type()

    return device_type


# basic process to call to start program
def main():

    system('cls')
    print("===================== Music Recommender System =====================")
    user_id = sign_in()
    print("Welcome, User " + str(user_id) + "!\n")

    device_type = get_device_type()
    R = 0   # number of recommendations to output

    if device_type == 'desktop':
        R = 5
    elif device_type == 'smartphone':
        R = 3

    context = set_context()
    main_menu(user_id, context, R)

main()
