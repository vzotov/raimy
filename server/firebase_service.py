import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from firebase_admin import initialize_app, firestore, get_app, credentials
from pydantic import BaseModel

# Recipe models
class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None
    ingredients: Optional[List[str]] = None

class Recipe(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    ingredients: List[str]
    steps: List[RecipeStep]
    total_time_minutes: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None

class FirebaseService:
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase with emulator"""
        try:
            # Check if Firebase is already initialized
            get_app()
            self.db = firestore.client()
            print("Firebase already initialized")
        except ValueError:
            # Initialize the Firebase Admin SDK
            cred = credentials.Certificate("server/fake-creds.json")
            initialize_app(cred)


# Get a Firestore client
            self.db = firestore.client()
            print("Firebase initialized with emulator")
    
    async def save_recipe(self, recipe: Recipe) -> str:
        """Save a recipe to Firestore"""
        if not self.db:
            raise Exception("Firebase not initialized")
        
        # Set timestamps
        now = datetime.utcnow()
        if not recipe.created_at:
            recipe.created_at = now
        recipe.updated_at = now
        
        # Convert to dict for Firestore
        recipe_dict = recipe.dict(exclude={'id'})
        recipe_dict['created_at'] = recipe.created_at
        recipe_dict['updated_at'] = recipe.updated_at
        
        # Save to recipes collection
        doc_ref = self.db.collection('recipes').document()
        doc_ref.set(recipe_dict)
        
        # Also save to user_recipes if user_id is provided
        if recipe.user_id:
            user_recipe_ref = self.db.collection('user_recipes').document(recipe.user_id)
            user_recipe_ref.set({
                'recipes': firestore.ArrayUnion([doc_ref.id]),
                'updated_at': now
            }, merge=True)
        
        return doc_ref.id
    
    async def get_recipes(self) -> List[Dict[str, Any]]:
        """Get all recipes from Firestore"""
        if not self.db:
            raise Exception("Firebase not initialized")
        
        try:
            # Get all documents from recipes collection
            recipes_ref = self.db.collection('recipes')
            docs = recipes_ref.stream()
            
            recipes = []
            for doc in docs:
                recipe_data = doc.to_dict()
                recipe_data['id'] = doc.id
                recipes.append(recipe_data)
            
            return recipes
        except Exception as e:
            print(f"Error getting recipes: {e}")
            return []

    async def get_recipes_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recipes for a specific user from Firestore"""
        if not self.db:
            raise Exception("Firebase not initialized")
        
        try:
            # Query recipes by user_id
            recipes_ref = self.db.collection('recipes')
            docs = recipes_ref.where('user_id', '==', user_id).stream()
            
            recipes = []
            for doc in docs:
                recipe_data = doc.to_dict()
                recipe_data['id'] = doc.id
                recipes.append(recipe_data)
            
            return recipes
        except Exception as e:
            print(f"Error getting recipes for user {user_id}: {e}")
            return []

# Global instance
firebase_service = FirebaseService() 