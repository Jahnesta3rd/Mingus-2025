# Meme Splash Page Testing Examples

This document provides practical examples of how to use the meme splash page testing suite. These examples demonstrate common testing scenarios and best practices.

## 🎯 Quick Start Examples

### Running Your First Test

```bash
# Navigate to the test directory
cd tests/meme_splash

# Run a simple unit test
python -m pytest test_meme_selector_unit.py::TestMemeSelectorUnit::test_select_best_meme_returns_valid_object -v

# Run all unit tests
python -m pytest test_meme_selector_unit.py -v

# Run with coverage
python -m pytest test_meme_selector_unit.py --cov=../../../meme_selector --cov-report=html
```

### Frontend Testing

```bash
# Navigate to frontend directory
cd frontend

# Run component tests
npm test -- --testPathPattern=MemeSplashPage.test.tsx

# Run with coverage
npm test -- --coverage --watchAll=false
```

## 🧪 Backend Testing Examples

### Unit Test Examples

#### Testing Meme Selection

```python
def test_meme_selection_basic():
    """Example: Test basic meme selection functionality"""
    # Arrange
    selector = MemeSelector("test.db")
    user_id = 1
    
    # Act
    meme = selector.select_best_meme(user_id)
    
    # Assert
    assert meme is not None
    assert isinstance(meme, MemeObject)
    assert meme.id > 0
    assert meme.caption is not None
    assert meme.category in ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
```

#### Testing API Endpoints

```python
def test_get_user_meme_endpoint():
    """Example: Test GET /api/user-meme endpoint"""
    # Arrange
    client = test_client
    headers = {'X-User-ID': 'user123', 'X-Session-ID': 'session456'}
    
    # Act
    response = client.get('/api/user-meme', headers=headers)
    
    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert 'image_url' in data
    assert 'caption' in data
    assert 'category' in data
```

#### Testing Error Handling

```python
def test_database_error_handling():
    """Example: Test error handling when database fails"""
    # Arrange
    invalid_selector = MemeSelector("/invalid/path/database.db")
    
    # Act
    meme = invalid_selector.select_best_meme(1)
    
    # Assert
    assert meme is None  # Should return None without crashing
```

### Integration Test Examples

#### Complete User Journey

```python
def test_complete_user_journey():
    """Example: Test complete user journey from meme request to analytics"""
    # Step 1: User requests a meme
    response = client.get('/api/user-meme', headers={
        'X-User-ID': 'user123',
        'X-Session-ID': 'session456'
    })
    assert response.status_code == 200
    meme_data = response.get_json()
    
    # Step 2: User views the meme (analytics tracked automatically)
    # This happens when the meme is fetched
    
    # Step 3: User continues to dashboard
    analytics_data = {
        'meme_id': meme_data['id'],
        'action': 'continue',
        'user_id': 'user123',
        'session_id': 'session456'
    }
    
    response = client.post('/api/meme-analytics', json=analytics_data)
    assert response.status_code == 200
    
    # Step 4: Verify analytics were recorded
    with sqlite3.connect(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM meme_analytics 
            WHERE meme_id = ? AND user_id = ? AND action = 'continue'
        """, (meme_data['id'], 'user123'))
        
        result = cursor.fetchone()
        assert result is not None
```

#### Multi-User Scenario

```python
def test_multiple_users_same_meme():
    """Example: Test multiple users viewing the same meme"""
    users = [('user1', 'session1'), ('user2', 'session2'), ('user3', 'session3')]
    
    for user_id, session_id in users:
        # Each user requests a meme
        response = client.get('/api/user-meme', headers={
            'X-User-ID': user_id,
            'X-Session-ID': session_id
        })
        assert response.status_code == 200
        
        # Each user continues
        meme_data = response.get_json()
        analytics_data = {
            'meme_id': meme_data['id'],
            'action': 'continue',
            'user_id': user_id,
            'session_id': session_id
        }
        
        response = client.post('/api/meme-analytics', json=analytics_data)
        assert response.status_code == 200
    
    # Verify all analytics were recorded
    with sqlite3.connect(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM meme_analytics WHERE action = 'continue'")
        count = cursor.fetchone()[0]
        assert count >= 3
```

## 🎨 Frontend Testing Examples

### Component Rendering Tests

```typescript
describe('MemeSplashPage Component Rendering', () => {
  it('renders loading skeleton initially', () => {
    // Mock fetch to never resolve (loading state)
    (fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
    
    render(<MemeSplashPage {...defaultProps} />);
    
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.getByText('Loading your daily motivation...')).toBeInTheDocument();
  });

  it('renders meme content after successful fetch', async () => {
    // Mock successful API response
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMemeData
    });

    render(<MemeSplashPage {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
    });

    expect(screen.getByAltText('Faith meme showing trust')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
  });
});
```

### User Interaction Tests

```typescript
describe('User Interactions', () => {
  it('calls onContinue when continue button is clicked', async () => {
    const mockOnContinue = jest.fn();
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMemeData
    });

    render(<MemeSplashPage {...defaultProps} onContinue={mockOnContinue} />);

    await waitFor(() => {
      expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
    });

    const continueButton = screen.getByRole('button', { name: /continue to dashboard/i });
    fireEvent.click(continueButton);

    expect(mockOnContinue).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard navigation', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMemeData
    });

    render(<MemeSplashPage {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
    });

    const container = screen.getByText('Sunday motivation: Trust the process').closest('div');
    
    // Test Enter key
    fireEvent.keyDown(container!, { key: 'Enter' });
    expect(mockOnContinue).toHaveBeenCalledTimes(1);
    
    // Test Escape key
    fireEvent.keyDown(container!, { key: 'Escape' });
    expect(mockOnSkip).toHaveBeenCalledTimes(1);
  });
});
```

### Error Handling Tests

```typescript
describe('Error Handling', () => {
  it('shows error message when fetch fails', async () => {
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<MemeSplashPage {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('retries when retry button is clicked', async () => {
    (fetch as jest.Mock)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMemeData
      });

    render(<MemeSplashPage {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load meme')).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
```

### Accessibility Tests

```typescript
describe('Accessibility', () => {
  it('has proper ARIA labels', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMemeData
    });

    render(<MemeSplashPage {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Sunday motivation: Trust the process')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /continue to dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /skip this feature/i })).toBeInTheDocument();
  });

  it('has proper alt text for images', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMemeData
    });

    render(<MemeSplashPage {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByAltText('Faith meme showing trust')).toBeInTheDocument();
    });
  });
});
```

## ⚡ Performance Testing Examples

### Basic Performance Test

```python
def test_meme_selection_performance():
    """Example: Test meme selection performance"""
    selector = MemeSelector(test_database)
    user_id = 1
    num_selections = 100
    
    start_time = time.time()
    
    # Perform multiple meme selections
    for _ in range(num_selections):
        meme = selector.select_best_meme(user_id)
        assert meme is not None
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / num_selections
    
    # Performance assertions
    assert total_time < 10.0, f"Total time {total_time:.2f}s should be under 10s"
    assert avg_time < 0.1, f"Average time {avg_time:.3f}s should be under 100ms"
    
    print(f"✅ Performance: {num_selections} selections in {total_time:.2f}s")
    print(f"   Average: {avg_time:.3f}s per selection")
    print(f"   Rate: {num_selections / total_time:.1f} selections/second")
```

### Concurrent User Test

```python
def test_concurrent_user_performance():
    """Example: Test performance with concurrent users"""
    num_users = 20
    requests_per_user = 5
    
    def user_workflow(user_id):
        """Simulate a user workflow"""
        results = []
        for _ in range(requests_per_user):
            start_time = time.time()
            
            # Get meme
            response = client.get('/api/user-meme', headers={
                'X-User-ID': f'user{user_id}',
                'X-Session-ID': f'session{user_id}'
            })
            
            if response.status_code == 200:
                meme_data = response.get_json()
                
                # Track analytics
                analytics_data = {
                    'meme_id': meme_data['id'],
                    'action': 'continue',
                    'user_id': f'user{user_id}',
                    'session_id': f'session{user_id}'
                }
                
                response = client.post('/api/meme-analytics', json=analytics_data)
            
            end_time = time.time()
            results.append(end_time - start_time)
        
        return results
    
    # Run concurrent users
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(user_workflow, i) for i in range(num_users)]
        all_results = []
        
        for future in as_completed(futures):
            results = future.result()
            all_results.extend(results)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate statistics
    avg_time = statistics.mean(all_results)
    p95_time = statistics.quantiles(all_results, n=20)[18]  # 95th percentile
    
    # Performance assertions
    assert avg_time < 1.0, f"Average response time {avg_time:.3f}s should be under 1s"
    assert p95_time < 2.0, f"95th percentile {p95_time:.3f}s should be under 2s"
    
    print(f"✅ Concurrent Performance: {num_users} users, {requests_per_user} requests each")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average response: {avg_time:.3f}s")
    print(f"   95th percentile: {p95_time:.3f}s")
    print(f"   Total requests: {len(all_results)}")
    print(f"   Requests/second: {len(all_results) / total_time:.1f}")
```

### Memory Usage Test

```python
def test_memory_usage():
    """Example: Test memory usage during operations"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform many operations
    num_operations = 1000
    for i in range(num_operations):
        meme = selector.select_best_meme(i % 100 + 1)  # Cycle through users
        assert meme is not None
        
        # Force garbage collection every 100 operations
        if i % 100 == 0:
            gc.collect()
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory assertions
    assert memory_increase < 10, f"Memory increase {memory_increase:.2f}MB should be under 10MB"
    
    print(f"✅ Memory Usage:")
    print(f"   Initial: {initial_memory:.2f}MB")
    print(f"   Final: {final_memory:.2f}MB")
    print(f"   Increase: {memory_increase:.2f}MB")
    print(f"   Operations: {num_operations}")
    print(f"   Memory per operation: {memory_increase / num_operations * 1024:.2f}KB")
```

## 🔧 Using Test Fixtures

### Database Fixtures

```python
def test_with_test_database(test_database):
    """Example: Using the test database fixture"""
    # test_database is automatically provided by pytest
    selector = MemeSelector(test_database)
    
    meme = selector.select_best_meme(1)
    assert meme is not None
    assert meme.id > 0

def test_with_performance_database(performance_test_database):
    """Example: Using the performance test database fixture"""
    selector = MemeSelector(performance_test_database)
    
    # Test with larger dataset
    for i in range(100):
        meme = selector.select_best_meme(i + 1)
        assert meme is not None
```

### Flask App Fixtures

```python
def test_with_flask_app(test_client):
    """Example: Using the Flask test client fixture"""
    response = test_client.get('/api/user-meme', headers={
        'X-User-ID': 'user123',
        'X-Session-ID': 'session456'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
```

### Mock Fixtures

```python
def test_with_mock_data(mock_meme_response, mock_analytics_response):
    """Example: Using mock response fixtures"""
    # mock_meme_response and mock_analytics_response are automatically provided
    
    assert mock_meme_response['id'] == 1
    assert mock_meme_response['category'] == 'faith'
    assert mock_analytics_response['success'] is True
```

## 📊 Test Data Examples

### Generating Test Data

```python
def test_with_generated_data(generate_test_memes, generate_test_users):
    """Example: Using test data generators"""
    # Generate test memes
    memes = generate_test_memes(10)
    assert len(memes) == 10
    assert all(meme['id'] > 0 for meme in memes)
    
    # Generate test users
    users = generate_test_users(5)
    assert len(users) == 5
    assert all(user['username'].startswith('test_user_') for user in users)
```

### Using Sample Data

```python
def test_with_sample_data(sample_meme_data, sample_user_data):
    """Example: Using sample data fixtures"""
    # sample_meme_data and sample_user_data are automatically provided
    
    assert sample_meme_data['id'] == 1
    assert sample_meme_data['category'] == 'faith'
    assert sample_user_data['username'] == 'test_user_1'
```

## 🚀 Advanced Examples

### Custom Test Markers

```python
@pytest.mark.performance
def test_performance_feature():
    """Example: Using custom test markers"""
    # This test will only run when performance tests are requested
    # Run with: pytest -m performance
    pass

@pytest.mark.slow
def test_slow_feature():
    """Example: Marking slow tests"""
    # This test will be skipped in fast test runs
    # Run with: pytest -m "not slow"
    pass
```

### Parameterized Tests

```python
@pytest.mark.parametrize("user_id,expected_category", [
    (1, 'faith'),
    (2, 'work_life'),
    (3, 'health'),
])
def test_user_categories(user_id, expected_category):
    """Example: Parameterized test"""
    # This test will run multiple times with different parameters
    selector = MemeSelector(test_database)
    meme = selector.select_best_meme(user_id)
    
    # Note: In real implementation, category might depend on day of week
    assert meme is not None
    assert meme.category in ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
```

### Test with Context Managers

```python
def test_with_context_manager():
    """Example: Using context managers for setup/teardown"""
    with tempfile.NamedTemporaryFile(suffix='.db') as temp_db:
        # Set up test database
        DatabaseTestSetup.create_test_database(temp_db.name)
        
        # Test with temporary database
        selector = MemeSelector(temp_db.name)
        meme = selector.select_best_meme(1)
        assert meme is not None
        
        # Database is automatically cleaned up when exiting the context
```

## 🎯 Best Practice Examples

### Test Organization

```python
class TestMemeSelector:
    """Example: Well-organized test class"""
    
    def setup_method(self):
        """Set up for each test method"""
        self.selector = MemeSelector(test_database)
        self.user_id = 1
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        meme = self.selector.select_best_meme(self.user_id)
        assert meme is not None
    
    def test_error_handling(self):
        """Test error handling"""
        invalid_selector = MemeSelector("/invalid/path")
        meme = invalid_selector.select_best_meme(self.user_id)
        assert meme is None
    
    def teardown_method(self):
        """Clean up after each test method"""
        # Cleanup code here
        pass
```

### Assertion Examples

```python
def test_comprehensive_assertions():
    """Example: Comprehensive assertions"""
    meme = selector.select_best_meme(1)
    
    # Basic assertions
    assert meme is not None
    assert isinstance(meme, MemeObject)
    
    # Property assertions
    assert meme.id > 0
    assert isinstance(meme.id, int)
    assert meme.image_url is not None
    assert len(meme.image_url) > 0
    assert meme.caption is not None
    assert len(meme.caption) > 0
    assert meme.category is not None
    assert meme.category in ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
    assert meme.alt_text is not None
    assert len(meme.alt_text) > 0
    assert meme.created_at is not None
    assert isinstance(meme.created_at, str)
    
    # URL validation
    assert meme.image_url.startswith('http')
    
    # Content validation
    assert len(meme.caption) < 1000  # Reasonable caption length
    assert len(meme.alt_text) < 500  # Reasonable alt text length
```

### Error Testing Examples

```python
def test_error_scenarios():
    """Example: Testing various error scenarios"""
    # Test with invalid user ID
    meme = selector.select_best_meme(-1)
    assert meme is None
    
    # Test with None user ID
    meme = selector.select_best_meme(None)
    assert meme is None
    
    # Test with invalid database path
    invalid_selector = MemeSelector("/invalid/path/database.db")
    meme = invalid_selector.select_best_meme(1)
    assert meme is None
    
    # Test with empty database
    empty_selector = MemeSelector(empty_database)
    meme = empty_selector.select_best_meme(1)
    assert meme is None
```

## 📈 Monitoring and Reporting

### Test Results Analysis

```python
def test_with_metrics():
    """Example: Test with performance metrics"""
    import time
    import statistics
    
    # Collect timing data
    times = []
    for _ in range(10):
        start_time = time.time()
        meme = selector.select_best_meme(1)
        end_time = time.time()
        
        assert meme is not None
        times.append(end_time - start_time)
    
    # Analyze results
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    max_time = max(times)
    min_time = min(times)
    
    # Performance assertions
    assert avg_time < 0.1, f"Average time {avg_time:.3f}s should be under 100ms"
    assert max_time < 0.5, f"Max time {max_time:.3f}s should be under 500ms"
    
    # Log results
    print(f"Performance Metrics:")
    print(f"  Average: {avg_time:.3f}s")
    print(f"  Median: {median_time:.3f}s")
    print(f"  Min: {min_time:.3f}s")
    print(f"  Max: {max_time:.3f}s")
```

### Coverage Analysis

```python
def test_coverage_example():
    """Example: Test that exercises all code paths"""
    # Test normal path
    meme = selector.select_best_meme(1)
    assert meme is not None
    
    # Test error path
    invalid_selector = MemeSelector("/invalid/path")
    meme = invalid_selector.select_best_meme(1)
    assert meme is None
    
    # Test edge case
    empty_selector = MemeSelector(empty_database)
    meme = empty_selector.select_best_meme(1)
    assert meme is None
```

---

These examples demonstrate the comprehensive testing capabilities of the meme splash page testing suite. Use them as templates for creating your own tests and adapt them to your specific testing needs.

**Happy Testing! 🧪✨**
