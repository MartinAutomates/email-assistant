from pydantic import BaseModel, Field


class EmailInput(BaseModel):
    subject: str = Field(min_length=1, max_length=200, description="The email subject line")
    body: str = Field(min_length=10, max_length=50000, description="The full email body text")


class EmailToSummarize(BaseModel):
    subject: str = Field(min_length=1, max_length=200, description="The email subject line")
    body: str = Field(min_length=50, max_length=50000, description="The full email body text")
    max_sentences: int = Field(ge=1, le=10, default=3, description="The number of sentences")


class EmailForReply(BaseModel):
    subject: str = Field(min_length=1, max_length=200, description="The email subject line")
    body: str = Field(min_length=10, max_length=50000, description="The full email body text")
    tone: str = Field(default="professional", description="Reply tone: professional, friendly, or brief")
    decision: str | None = Field(default=None, description="Optional: 'accept' or 'decline' to guide the reply's stance")