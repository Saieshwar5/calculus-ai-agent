"""
Unit tests for auth_helpers module.
Tests authentication and authorization helper functions.
"""
import pytest
from fastapi import HTTPException
from app.utils.auth_helpers import get_user_id, check_admin


class TestGetUserId:
    """Test cases for get_user_id function."""
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_valid_header(self):
        """Test get_user_id returns user_id when valid header is provided."""
        # Arrange
        valid_user_id = "user123"
        
        # Act
        result = await get_user_id(x_user_id=valid_user_id)
        
        # Assert
        assert result == valid_user_id
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_empty_string(self):
        """Test get_user_id raises HTTPException when empty string is provided."""
        # Arrange
        empty_user_id = ""
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_id(x_user_id=empty_user_id)
        
        assert exc_info.value.status_code == 401
        assert "User ID is required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_none(self):
        """Test get_user_id raises HTTPException when None is provided."""
        # Arrange
        none_user_id = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_id(x_user_id=none_user_id)
        
        assert exc_info.value.status_code == 401
        assert "User ID is required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_whitespace_only(self):
        """Test get_user_id raises HTTPException when only whitespace is provided."""
        # Arrange
        whitespace_user_id = "   "
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_id(x_user_id=whitespace_user_id)
        
        assert exc_info.value.status_code == 401
        assert "User ID is required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_long_string(self):
        """Test get_user_id handles long user_id strings."""
        # Arrange
        long_user_id = "a" * 1000
        
        # Act
        result = await get_user_id(x_user_id=long_user_id)
        
        # Assert
        assert result == long_user_id
        assert len(result) == 1000
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_special_characters(self):
        """Test get_user_id handles special characters in user_id."""
        # Arrange
        special_user_id = "user-123_test@example.com"
        
        # Act
        result = await get_user_id(x_user_id=special_user_id)
        
        # Assert
        assert result == special_user_id
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_numeric_string(self):
        """Test get_user_id handles numeric strings."""
        # Arrange
        numeric_user_id = "12345"
        
        # Act
        result = await get_user_id(x_user_id=numeric_user_id)
        
        # Assert
        assert result == numeric_user_id
    
    @pytest.mark.asyncio
    async def test_get_user_id_with_unicode_characters(self):
        """Test get_user_id handles unicode characters."""
        # Arrange
        unicode_user_id = "user_测试_123"
        
        # Act
        result = await get_user_id(x_user_id=unicode_user_id)
        
        # Assert
        assert result == unicode_user_id


class TestCheckAdmin:
    """Test cases for check_admin function."""
    
    @pytest.mark.asyncio
    async def test_check_admin_with_valid_token(self):
        """Test check_admin returns True when valid admin token is provided."""
        # Arrange
        valid_token = "admin_secret_token"
        
        # Act
        result = await check_admin(x_admin_token=valid_token)
        
        # Assert
        assert result is True
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_check_admin_with_invalid_token(self):
        """Test check_admin raises HTTPException when invalid token is provided."""
        # Arrange
        invalid_token = "wrong_token"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(x_admin_token=invalid_token)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_admin_with_none(self):
        """Test check_admin raises HTTPException when None is provided."""
        # Arrange
        none_token = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(x_admin_token=none_token)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_admin_with_empty_string(self):
        """Test check_admin raises HTTPException when empty string is provided."""
        # Arrange
        empty_token = ""
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(x_admin_token=empty_token)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_admin_with_similar_token(self):
        """Test check_admin raises HTTPException with similar but incorrect token."""
        # Arrange
        similar_token = "admin_secret_toke"  # Missing 'n' at the end
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(x_admin_token=similar_token)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_admin_with_whitespace_token(self):
        """Test check_admin raises HTTPException when token has whitespace."""
        # Arrange
        whitespace_token = " admin_secret_token "
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(x_admin_token=whitespace_token)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_admin_case_sensitive(self):
        """Test check_admin is case sensitive."""
        # Arrange
        wrong_case_token = "Admin_Secret_Token"  # Different case
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(x_admin_token=wrong_case_token)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_check_admin_token_exact_match(self):
        """Test check_admin requires exact token match."""
        # Arrange
        exact_token = "admin_secret_token"
        
        # Act
        result = await check_admin(x_admin_token=exact_token)
        
        # Assert
        assert result is True


class TestAuthHelpersIntegration:
    """Integration tests for auth helpers working together."""
    
    @pytest.mark.asyncio
    async def test_get_user_id_then_check_admin_valid(self):
        """Test both functions work together with valid inputs."""
        # Arrange
        user_id = "user123"
        admin_token = "admin_secret_token"
        
        # Act
        user_result = await get_user_id(x_user_id=user_id)
        admin_result = await check_admin(x_admin_token=admin_token)
        
        # Assert
        assert user_result == user_id
        assert admin_result is True
    
    @pytest.mark.asyncio
    async def test_get_user_id_fails_then_check_admin_passes(self):
        """Test get_user_id fails but check_admin can still pass."""
        # Arrange
        invalid_user_id = None
        valid_admin_token = "admin_secret_token"
        
        # Act & Assert - get_user_id should fail
        with pytest.raises(HTTPException) as exc_info:
            await get_user_id(x_user_id=invalid_user_id)
        assert exc_info.value.status_code == 401
        
        # Act & Assert - check_admin should pass
        admin_result = await check_admin(x_admin_token=valid_admin_token)
        assert admin_result is True
    
    @pytest.mark.asyncio
    async def test_multiple_valid_user_ids(self):
        """Test get_user_id with multiple different valid user IDs."""
        # Arrange
        user_ids = ["user1", "user2", "admin_user", "test_user_123"]
        
        # Act & Assert
        for user_id in user_ids:
            result = await get_user_id(x_user_id=user_id)
            assert result == user_id

