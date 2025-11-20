# MongoDB Setup Guide

## Option 1: Install MongoDB Locally

### Windows:
1. Download MongoDB Community Server from: https://www.mongodb.com/try/download/community
2. Run the installer and follow the setup wizard
3. Start MongoDB service:
   ```cmd
   net start MongoDB
   ```
4. MongoDB will be available at `mongodb://localhost:27017`

### Alternative: MongoDB Compass (GUI)
1. Download MongoDB Compass from: https://www.mongodb.com/try/download/compass
2. Install and connect to `mongodb://localhost:27017`
3. Create a database named `prospeak_ai`

## Option 2: Use MongoDB Atlas (Cloud)

1. Go to https://www.mongodb.com/atlas
2. Create a free account
3. Create a new cluster
4. Get your connection string
5. Update `app/config.py` with your connection string:
   ```python
   MONGO_URI = 'mongodb+srv://username:password@cluster.mongodb.net/prospeak_ai'
   ```

## Option 3: Use Docker

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## Current Setup

The application is currently using **in-memory storage** for development. To switch to MongoDB:

1. Install MongoDB using one of the options above
2. Update `app/routes/api.py` to use the MongoDB models from `app/models.py`
3. The database will be automatically created when you first register a user

## Database Collections

The application will create these collections:
- `users` - User accounts and profiles
- `sessions` - Practice session data and scores

## Testing the Connection

Once MongoDB is running, you can test the connection:
```python
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client.prospeak_ai
print("Connected to MongoDB successfully!")
```