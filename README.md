# mem-db-utils

Python package for in-memory database utilities supporting Redis, Memcached, Dragonfly, and Valkey. Provides both synchronous and asynchronous connection interfaces for high-performance caching and fast-access storage.

## Features

- **Multiple Database Support**: Redis, Memcached, Dragonfly, and Valkey
- **Sync & Async APIs**: Full support for both synchronous and asynchronous operations
- **Auto-Detection**: Automatic database type detection from connection URLs
- **Redis Sentinel Support**: High availability with Redis Sentinel configurations
- **Memory Efficient**: Uses `__slots__` for optimized memory usage
- **Environment Configuration**: Easy setup via environment variables or `.env` files
- **Type Safety**: Full type hints with `py.typed` marker

## Installation

```bash
pip install mem-db-utils
```

## Quick Start

### Environment Setup

Create a `.env` file or set environment variables:

```bash
# Required
DB_URL=redis://localhost:6379/0

# Optional
DB_TYPE=redis                    # Auto-detected from URL if not specified
REDIS_CONNECTION_TYPE=direct     # or 'sentinel'
REDIS_MASTER_SERVICE=mymaster    # Required for Sentinel
DB_TIMEOUT=30                    # Connection timeout in seconds
```

### Synchronous Usage

```python
from mem_db_utils import MemDBConnector

# Initialize connector
connector = MemDBConnector()

# Connect to database
conn = connector.connect(db=0)

# Basic operations (Redis-compatible databases)
conn.ping()                      # Test connection
conn.set("key", "value")         # Set a key
value = conn.get("key")          # Get a key
conn.delete("key")               # Delete a key
```

### Asynchronous Usage

```python
import asyncio
from mem_db_utils.asyncio import MemDBConnector

async def main():
    # Initialize async connector
    connector = MemDBConnector()
    
    # Connect to database
    conn = await connector.connect(db=0)
    
    # Basic async operations (Redis-compatible databases)
    await conn.ping()                      # Test connection
    await conn.set("key", "value")         # Set a key
    value = await conn.get("key")          # Get a key
    await conn.delete("key")               # Delete a key
    
    # Always close async connections
    await conn.aclose()

# Run async function
asyncio.run(main())
```

## Supported Database Types

| Database  | URL Scheme   | Sync Support | Async Support | Database Selection | Notes |
|-----------|--------------|--------------|---------------|-------------------|-------|
| Redis     | `redis://`   | ✅           | ✅            | ✅                | Full featured |
| Dragonfly | `dragonfly://` | ✅         | ✅            | ✅                | Redis-compatible |
| Valkey    | `valkey://`  | ✅           | ✅            | ✅                | Redis-compatible |
| Memcached | `memcached://` | ✅         | ❌            | ❌                | Basic connection only |

## Configuration Examples

### Redis (Standard)
```bash
DB_URL=redis://localhost:6379/0
DB_URL=redis://:password@localhost:6379/0
DB_URL=redis://username:password@localhost:6379/0
```

### Redis Sentinel
```bash
DB_URL=redis://sentinel-host:26379
REDIS_CONNECTION_TYPE=sentinel
REDIS_MASTER_SERVICE=mymaster
```

### Other Databases
```bash
# Dragonfly
DB_URL=dragonfly://localhost:6380/0

# Valkey  
DB_URL=valkey://localhost:6381/0

# Memcached
DB_URL=memcached://localhost:11211
```

## Async vs Sync API Comparison

| Feature | Sync API | Async API |
|---------|----------|-----------|
| **Import** | `from mem_db_utils import MemDBConnector` | `from mem_db_utils.asyncio import MemDBConnector` |
| **Connect** | `conn = connector.connect()` | `conn = await connector.connect()` |
| **Operations** | `conn.set("key", "value")` | `await conn.set("key", "value")` |
| **Close** | Automatic | `await conn.aclose()` |
| **Concurrency** | Thread-based | Native async/await |
| **Performance** | Good for I/O blocking | Excellent for high concurrency |

## Migration from Sync to Async

### Before (Sync)
```python
from mem_db_utils import MemDBConnector

connector = MemDBConnector()
conn = connector.connect()
conn.set("key", "value")
result = conn.get("key")
```

### After (Async)
```python
import asyncio
from mem_db_utils.asyncio import MemDBConnector

async def main():
    connector = MemDBConnector()
    conn = await connector.connect()
    await conn.set("key", "value")
    result = await conn.get("key")
    await conn.aclose()  # Important: close async connections

asyncio.run(main())
```

### Key Migration Points

1. **Import Change**: Use `mem_db_utils.asyncio` for async connector
2. **Async/Await**: Add `await` to all connection operations
3. **Function Definition**: Use `async def` for functions using async connector
4. **Connection Closing**: Always call `await conn.aclose()` for async connections
5. **Event Loop**: Use `asyncio.run()` or existing event loop

## Advanced Usage

### Concurrent Operations (Async)

```python
import asyncio
from mem_db_utils.asyncio import MemDBConnector

async def worker(connector, worker_id):
    """Worker function for concurrent operations."""
    conn = await connector.connect(db=0)
    try:
        # Perform operations
        await conn.set(f"worker_{worker_id}", f"data_{worker_id}")
        result = await conn.get(f"worker_{worker_id}")
        await conn.delete(f"worker_{worker_id}")
        return f"Worker {worker_id}: {result}"
    finally:
        await conn.aclose()

async def concurrent_example():
    connector = MemDBConnector()
    
    # Run 5 concurrent workers
    tasks = [worker(connector, i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(result)

asyncio.run(concurrent_example())
```

### Custom Configuration

```python
from mem_db_utils import MemDBConnector

# Override defaults via constructor
connector = MemDBConnector(
    redis_type="sentinel",      # Force Sentinel mode
    master_service="my-master"  # Custom master service name
)

# Connect with custom options
conn = connector.connect(
    db=1,                       # Different database number
    decode_response=False,      # Get bytes instead of strings
    timeout=60                  # Custom timeout
)
```

### Error Handling

#### Sync Error Handling
```python
from mem_db_utils import MemDBConnector
import redis.exceptions

try:
    connector = MemDBConnector()
    conn = connector.connect(db=0)
    conn.ping()
except redis.exceptions.ConnectionError:
    print("Failed to connect to database")
except redis.exceptions.ResponseError:
    print("Invalid database operation")
except Exception as e:
    print(f"Unexpected error: {e}")
```

#### Async Error Handling
```python
import asyncio
from mem_db_utils.asyncio import MemDBConnector
import redis.exceptions

async def async_error_example():
    connector = MemDBConnector()
    conn = None
    
    try:
        conn = await connector.connect(db=0)
        await conn.ping()
    except redis.exceptions.ConnectionError:
        print("Failed to connect to database")
    except redis.exceptions.ResponseError:
        print("Invalid database operation")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if conn:
            await conn.aclose()

asyncio.run(async_error_example())
```

### Connection with Different Database Numbers

```python
# Sync - Redis/Dragonfly/Valkey only
connector = MemDBConnector()
conn = connector.connect(db=2)  # Connect to database 2

# Async - Redis/Dragonfly/Valkey only
async def connect_to_db():
    connector = MemDBConnector()
    conn = await connector.connect(db=2)  # Connect to database 2
    await conn.aclose()
```

## Testing Your Setup

### Basic Import Test
```python
# Test if package imports correctly
from mem_db_utils import MemDBConnector
from mem_db_utils.asyncio import MemDBConnector as AsyncMemDBConnector
print("Import successful!")
```

### Connection Test (Sync)
```python
from mem_db_utils import MemDBConnector

try:
    connector = MemDBConnector()
    conn = connector.connect(db=0)
    
    # Test Redis-compatible databases
    if hasattr(conn, 'ping'):
        result = conn.ping()
        print(f"Connection successful: {result}")
    else:
        print("Connection established (Memcached)")
        
except Exception as e:
    print(f"Connection failed: {e}")
```

### Connection Test (Async)
```python
import asyncio
from mem_db_utils.asyncio import MemDBConnector

async def test_async_connection():
    try:
        connector = MemDBConnector()
        conn = await connector.connect(db=0)
        
        # Test Redis-compatible databases
        if hasattr(conn, 'ping'):
            result = await conn.ping()
            print(f"Async connection successful: {result}")
            await conn.aclose()
        else:
            print("Async connection established")
            
    except Exception as e:
        print(f"Async connection failed: {e}")

asyncio.run(test_async_connection())
```

## Performance Considerations

### When to Use Sync vs Async

**Use Sync API when:**
- Simple scripts or applications with low concurrency
- Blocking I/O is acceptable
- Working within existing synchronous codebases
- Single-threaded applications

**Use Async API when:**
- High concurrency requirements (>100 concurrent operations)
- Non-blocking I/O is important
- Building async applications with FastAPI, aiohttp, etc.
- Maximum throughput is needed

### Memory Efficiency

Both connectors use `__slots__` for memory efficiency, reducing per-instance memory usage by restricting attribute storage.

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure `DB_URL` environment variable is set
   ```bash
   export DB_URL=redis://localhost:6379/0
   ```

2. **Connection Timeout**: Increase timeout value
   ```bash
   export DB_TIMEOUT=60
   ```

3. **Async Connection Not Closed**: Always call `await conn.aclose()`
   ```python
   conn = await connector.connect()
   try:
       # operations
   finally:
       await conn.aclose()
   ```

4. **Database Selection Not Supported**: Only Redis-compatible databases support database selection
   ```python
   # Works: Redis, Dragonfly, Valkey
   conn = connector.connect(db=1)
   
   # Not supported: Memcached
   ```

### Environment Variable Loading

The package automatically loads environment variables from `.env` files using `python-dotenv`. Ensure your `.env` file is in the working directory or parent directories.

## Contributing

Contributions are welcome! Please ensure your code passes all tests and follows the existing code style.

```bash
# Install development dependencies
pip install -e .
pip install coverage pre-commit pytest pytest-cov pytest-dotenv ruff pytest-asyncio

# Run tests
python -m pytest tests/ -v

# Check linting
ruff check . && ruff format --check .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
