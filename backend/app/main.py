from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.admin_slots import router as admin_slots_router
from app.routes.availability import router as availability_router
from app.routes.bookings import router as bookings_router
from app.routes.payments import router as payments_router

app = FastAPI(title="Tattoo Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(admin_slots_router)
app.include_router(availability_router)
app.include_router(bookings_router)
app.include_router(payments_router)