from fastapi import HTTPException, status

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)


EMAIL_CONFLICT = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="Email already in use."
)
EMAIL_INVALID = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="Email not valid."
)

USERNAME_CONFLICT = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="Username already in use."
)


NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found."
)


CREDENTIALS_NEEDED = HTTPException(
    status_code=status.HTTP_412_PRECONDITION_FAILED,
    detail="Please add apikey and subdomain first.",
)

BAD_REQUEST = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request."
)
