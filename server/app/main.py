# https://youtu.be/0sOvCWFmrtA?si=EAkG_V_jVuxRmz_B&t=40468

from fastapi import FastAPI

from .routers import auth, budget, category, transaction, user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(budget.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(transaction.router)
