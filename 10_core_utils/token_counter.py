"""Token counting utilities for the context engineering framework."""

import re
import tiktoken
from typing import List, Dict, Any, Optional
from .logger import Logger


class TokenCounter:
    """Handles token counting for various models and text processing."""
    
    def __init__(self, model: str = "claude-3-sonnet-20241022"):
        self.model = model
        self.logger = Logger("TokenCounter")
        
        # Model-specific token limits
        self.model_limits = {
            "claude-3-sonnet-20241022": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-3-opus-20240229": 200000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
        }
        
        # Try to get the appropriate tokenizer
        self.tokenizer = self._get_tokenizer()
    
    def _get_tokenizer(self):
        """Get appropriate tokenizer for the model."""
        try:
            if "claude" in self.model.lower():
                # Claude models - use GPT-4 tokenizer as approximation
                return tiktoken.encoding_for_model("gpt-4")
            elif "gpt" in self.model.lower():
                return tiktoken.encoding_for_model(self.model)
            else:
                # Default to GPT-4 tokenizer
                return tiktoken.encoding_for_model("gpt-4")
        except Exception as e:
            self.logger.warning(f"Could not load tokenizer for {self.model}: {e}")
            try:
                # Fallback to cl100k_base encoding
                return tiktoken.get_encoding("cl100k_base")
            except:
                self.logger.error("Could not load any tokenizer")
                return None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                self.logger.error(f"Tokenizer error: {e}")
        
        # Fallback: rough estimation (4 characters per token)
        return max(1, len(text) // 4)
    
    def estimate_tokens_rough(self, text: str) -> int:
        """Rough token estimation without tokenizer."""
        if not text:
            return 0
        
        # More sophisticated estimation
        # Split by whitespace and punctuation
        words = re.findall(r'\w+|[^\w\s]', text)
        
        # Average tokens per word (varies by language and text type)
        avg_tokens_per_word = 1.3
        
        return max(1, int(len(words) * avg_tokens_per_word))
    
    def count_tokens_in_messages(self, messages: List[Dict[str, Any]]) -> int:
        """Count tokens in a list of messages."""
        total_tokens = 0
        
        for message in messages:
            if isinstance(message, dict):
                # Count tokens in all string values
                for key, value in message.items():
                    if isinstance(value, str):
                        total_tokens += self.count_tokens(value)
                    elif isinstance(value, (list, dict)):
                        # Handle nested structures
                        total_tokens += self.count_tokens(str(value))
            elif isinstance(message, str):
                total_tokens += self.count_tokens(message)
        
        # Add overhead for message formatting (approximate)
        overhead = len(messages) * 10
        return total_tokens + overhead
    
    def get_model_limit(self, model: Optional[str] = None) -> int:
        """Get token limit for model."""
        model = model or self.model
        return self.model_limits.get(model, 4096)  # Default limit
    
    def check_within_limit(self, text: str, model: Optional[str] = None, buffer: int = 500) -> bool:
        """Check if text is within model token limit."""
        token_count = self.count_tokens(text)
        limit = self.get_model_limit(model) - buffer
        return token_count <= limit
    
    def truncate_to_limit(self, text: str, model: Optional[str] = None, buffer: int = 500) -> str:
        """Truncate text to fit within model limits."""
        limit = self.get_model_limit(model) - buffer
        current_tokens = self.count_tokens(text)
        
        if current_tokens <= limit:
            return text
        
        # Binary search to find optimal truncation point
        left, right = 0, len(text)
        
        while left < right:
            mid = (left + right + 1) // 2
            truncated = text[:mid]
            
            if self.count_tokens(truncated) <= limit:
                left = mid
            else:
                right = mid - 1
        
        truncated_text = text[:left]
        
        # Try to end at a reasonable boundary (sentence, word)
        truncated_text = self._truncate_at_boundary(truncated_text)
        
        self.logger.info(f"Text truncated from {current_tokens} to {self.count_tokens(truncated_text)} tokens")
        return truncated_text
    
    def _truncate_at_boundary(self, text: str) -> str:
        """Truncate text at natural boundaries."""
        # Try to end at sentence boundary
        sentence_ends = ['.', '!', '?', '\n\n']
        for end in sentence_ends:
            last_pos = text.rfind(end)
            if last_pos > len(text) * 0.8:  # At least 80% of original
                return text[:last_pos + len(end)]
        
        # Try to end at word boundary
        last_space = text.rfind(' ')
        if last_space > len(text) * 0.9:  # At least 90% of original
            return text[:last_space]
        
        # Return as is if no good boundary found
        return text
    
    def split_text_by_tokens(self, text: str, max_tokens: int, overlap: int = 100) -> List[str]:
        """Split text into chunks by token count."""
        if not text:
            return []
        
        total_tokens = self.count_tokens(text)
        if total_tokens <= max_tokens:
            return [text]
        
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If single sentence is too long, split it further
            if sentence_tokens > max_tokens:
                # Add current chunk if not empty
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0
                
                # Split long sentence by words
                words = sentence.split()
                for word in words:
                    word_with_space = word + " "
                    word_tokens = self.count_tokens(word_with_space)
                    
                    if current_tokens + word_tokens > max_tokens:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = word_with_space
                        current_tokens = word_tokens
                    else:
                        current_chunk += word_with_space
                        current_tokens += word_tokens
            
            elif current_tokens + sentence_tokens > max_tokens:
                # Current sentence would exceed limit, start new chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Handle overlap
                if overlap > 0 and chunks:
                    overlap_text = self._get_overlap_text(current_chunk, overlap)
                    current_chunk = overlap_text + " " + sentence + " "
                    current_tokens = self.count_tokens(current_chunk)
                else:
                    current_chunk = sentence + " "
                    current_tokens = sentence_tokens
            else:
                # Add sentence to current chunk
                current_chunk += sentence + " "
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        self.logger.info(f"Text split into {len(chunks)} chunks")
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get overlap text from end of chunk."""
        words = text.split()
        overlap_text = ""
        current_tokens = 0
        
        for word in reversed(words):
            word_tokens = self.count_tokens(word + " ")
            if current_tokens + word_tokens > overlap_tokens:
                break
            overlap_text = word + " " + overlap_text
            current_tokens += word_tokens
        
        return overlap_text.strip()
    
    def get_token_usage_summary(self, texts: List[str]) -> Dict[str, Any]:
        """Get summary of token usage for multiple texts."""
        token_counts = [self.count_tokens(text) for text in texts]
        
        return {
            "total_texts": len(texts),
            "total_tokens": sum(token_counts),
            "average_tokens": sum(token_counts) / len(texts) if texts else 0,
            "min_tokens": min(token_counts) if token_counts else 0,
            "max_tokens": max(token_counts) if token_counts else 0,
            "model_limit": self.get_model_limit(),
            "within_limit": all(count <= self.get_model_limit() for count in token_counts)
        }
