# Redis Environment Variables Setup

## Required Environment Variables

Add these variables to your `.env` file:

```bash
# Redis Configuration
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
REDIS_PASSWORD=your_redis_password  # Leave empty if no password is set
```

## Redis Database Allocation

The application uses different Redis databases for different purposes:

- **Database 0**: Session storage (`REDIS_SESSION_URL`)
- **Database 1**: Query caching (`REDIS_CACHE_URL`)
- **Database 2**: Rate limiting (`RATE_LIMIT_STORAGE_URL`)

## Configuration Examples

### Without Password (Development)
```bash
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
REDIS_PASSWORD=
```

### With Password (Production)
```bash
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
REDIS_PASSWORD=your_secure_redis_password_here
```

### With Password in URL (Alternative)
```bash
REDIS_SESSION_URL=redis://:your_password@localhost:6379/0
REDIS_CACHE_URL=redis://:your_password@localhost:6379/1
REDIS_PASSWORD=your_secure_redis_password_here
```

## How to Add to .env File

1. **Open your `.env` file** (create it if it doesn't exist)

2. **Add the Redis configuration section:**

```bash
# Redis Configuration
REDIS_SESSION_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
REDIS_PASSWORD=
```

3. **If you have a Redis password**, update the `REDIS_PASSWORD` value:
```bash
REDIS_PASSWORD=your_actual_redis_password
```

4. **Save the file**

5. **Restart your Flask application** for changes to take effect

## Verify Configuration

After adding the variables, test the connection:

```bash
# Test Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print('✅ Redis connected:', r.ping())"
```

## Troubleshooting

### Redis Not Running
If you get connection errors, make sure Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Password Issues
If Redis requires a password but you're getting authentication errors:
1. Check your Redis password: `redis-cli -a your_password ping`
2. Update `REDIS_PASSWORD` in `.env`
3. Restart the application

### Connection Refused
If you see "Connection refused":
1. Check Redis is running: `redis-cli ping`
2. Verify Redis is listening on port 6379: `netstat -an | grep 6379`
3. Check firewall settings if on remote server

## Production Recommendations

For production environments:

1. **Use strong passwords** for Redis
2. **Enable Redis AOF persistence** for data durability
3. **Configure Redis maxmemory** to prevent OOM errors
4. **Use Redis Sentinel** for high availability
5. **Monitor Redis memory usage** regularly

## Next Steps

After configuring environment variables:

1. ✅ Restart your Flask application
2. ✅ Check `/health` endpoint to verify Redis status
3. ✅ Test session persistence
4. ✅ Monitor cache hit rates

---

**Status:** Ready to configure
