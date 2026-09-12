from get_api_through_token import get_token


def main():
    print("main function call")
    # execution_data_main()
    token_data = get_token()
    print(token_data, "token data")




if __name__=="__main__":
    main()