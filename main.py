from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return{"message": "Hello World"}

@app.get("/email/{email_id}")
def read_email(email_id: int):
    return{"email_id": email_id, "subject": "Test email"}