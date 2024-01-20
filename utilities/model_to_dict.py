def user_to_dict(user):
    userdict = user.__dict__.copy()
    del userdict["hashed_pw"]
    return userdict
