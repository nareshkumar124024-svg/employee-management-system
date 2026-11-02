
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["employee_management"]

users_col = db["users"]
employees_col = db["employees"]
attendance_col = db["attendance"]
leave_col = db["leave_requests"]


def check_connection():
    client.admin.command("ping")
    print("MongoDB connected successfully!")


if __name__ == "__main__":
    try:
        check_connection()
        print("Database name:", db.name)
    except Exception as e:
        print("MongoDB connection failed:", e)
    finally:
        client.close()
