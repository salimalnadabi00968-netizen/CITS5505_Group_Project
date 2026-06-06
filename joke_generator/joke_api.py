"""
Joke Generator API Client Module
Fetches jokes from the JokeAPI (https://jokeapi.dev/)
"""

import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class JokeAPIClient:
    """Client for interacting with the JokeAPI service."""
    
    BASE_URL = "https://v2.jokeapi.dev/joke"
    
    # Available categories
    CATEGORIES = ["General", "Programming", "Knock-Knock", "Dark", "Spooky", "Christmas"]
    
    def __init__(self, timeout: int = 5):
        """
        Initialize the JokeAPI client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_joke(self, category: Optional[str] = None, 
                 joke_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch a random joke from the API.
        
        Args:
            category: Joke category (General, Programming, Knock-Knock, Dark, Spooky, Christmas)
                     If None, fetches from any category
            joke_type: Type of joke ('single' or 'twopart'). If None, gets either type
        
        Returns:
            Dictionary containing joke data
        
        Raises:
            requests.RequestException: If API request fails
        """
        try:
            # Build the endpoint URL
            if category and category in self.CATEGORIES:
                endpoint = f"{self.BASE_URL}/{category}"
            else:
                endpoint = f"{self.BASE_URL}/Any"
            
            # Build query parameters
            params = {"format": "json"}
            if joke_type and joke_type in ["single", "twopart"]:
                params["type"] = joke_type
            
            # Make the request
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if joke was successfully retrieved
            if data.get("error"):
                logger.error(f"JokeAPI Error: {data.get('message')}")
                return {"error": True, "message": data.get("message")}
            
            return data
        
        except requests.Timeout:
            logger.error("JokeAPI request timed out")
            return {"error": True, "message": "Request timed out"}
        
        except requests.RequestException as e:
            logger.error(f"JokeAPI request failed: {str(e)}")
            return {"error": True, "message": "Failed to fetch joke"}
    
    def get_random_joke(self) -> Dict[str, Any]:
        """
        Fetch a completely random joke from any category.
        
        Returns:
            Dictionary containing joke data
        """
        return self.get_joke()
    
    def get_joke_by_category(self, category: str) -> Dict[str, Any]:
        """
        Fetch a joke from a specific category.
        
        Args:
            category: Joke category
        
        Returns:
            Dictionary containing joke data
        """
        if category not in self.CATEGORIES:
            return {
                "error": True,
                "message": f"Invalid category. Available: {', '.join(self.CATEGORIES)}"
            }
        return self.get_joke(category=category)
    
    def format_joke(self, joke_data: Dict[str, Any]) -> str:
        """
        Format joke data into a readable string.
        
        Args:
            joke_data: Joke data from API
        
        Returns:
            Formatted joke string
        """
        if joke_data.get("error"):
            return f"Error: {joke_data.get('message', 'Unknown error')}"
        
        joke_type = joke_data.get("type", "unknown")
        category = joke_data.get("category", "Unknown")
        
        if joke_type == "single":
            return f"[{category}] {joke_data.get('joke', '')}"
        elif joke_type == "twopart":
            setup = joke_data.get("setup", "")
            delivery = joke_data.get("delivery", "")
            return f"[{category}]\nSetup: {setup}\nPunchline: {delivery}"
        else:
            return "Unable to format joke"
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
