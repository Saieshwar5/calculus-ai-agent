# Profile Store Tests

This directory contains comprehensive unit and integration tests for the Profile Store.

## Test Coverage

### Unit Tests

1. **Validation Functions**
   - `validateProfile()` - Tests all validation rules
   - `hasAllRequiredFields()` - Tests required field checks

2. **State Management Functions**
   - `setProfile()` - Setting profile data
   - `setError()` - Setting error messages
   - `setLoading()` - Setting loading state
   - `setSaving()` - Setting saving state
   - `clearError()` - Clearing errors
   - `clearProfile()` - Clearing all profile data

3. **Profile Actions**
   - `saveProfileData()` - Creating new profile
   - `updateProfileData()` - Updating existing profile
   - `fetchProfile()` - Fetching profile from server

### Integration Tests

- Full save workflow
- Full update workflow
- Fetch then update workflow
- Validation failure handling
- Clear profile after save

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Test Structure

Each test suite follows this pattern:
1. **Setup** - Reset store state and mocks
2. **Test** - Execute the function/action
3. **Assert** - Verify expected behavior
4. **Cleanup** - Restore original state

## Mocking

- API calls are mocked using `vi.mock()`
- sessionStorage is mocked for persistence testing
- All external dependencies are isolated

