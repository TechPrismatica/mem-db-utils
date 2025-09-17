# mem-db-utils - GitHub Copilot Instructions

**Python package for in-memory database utilities supporting Redis, Memcached, Dragonfly, and Valkey.**

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test Repository:
- `pip install -e .` -- installs the package in development mode. NEVER CANCEL: Takes 10-60 seconds, may timeout due to network issues. Set timeout to 120+ seconds (extra margin for slow mirrors or network issues).
- `pip install coverage pre-commit pytest pytest-cov pytest-dotenv ruff` -- installs development dependencies. NEVER CANCEL: Takes 30-120 seconds. Set timeout to 180+ seconds (extra margin for slow mirrors or network issues).
- `python -m pytest tests/ -v` -- runs unit tests (takes ~0.4 seconds, 20 passed, 5 skipped without database)
- `ruff check .` -- runs linting (takes ~0.01 seconds)
- `ruff format --check .` -- checks code formatting (takes ~0.01 seconds)

### Environment Configuration:
- Create `.env` file with `DB_URL=redis://localhost:6379/0` for basic testing
- Package requires `DB_URL` environment variable to be set at runtime
- Supported database URLs: `redis://`, `memcached://`, `dragonfly://`, `valkey://`
- Optional environment variables: `DB_TYPE`, `REDIS_CONNECTION_TYPE`, `REDIS_MASTER_SERVICE`, `DB_TIMEOUT`

### Run Integration Tests with Real Database:
- Start Redis: `docker run -d --name test-redis -p 6379:6379 redis:7-alpine` (NEVER CANCEL: Takes 30-60 seconds for first download)
- Wait for startup: `sleep 5`
- Run integration tests: `DB_URL=redis://localhost:6379/0 python -m pytest tests/test_integration.py -v` (takes ~0.4 seconds, 1 may fail on error handling test)
- Clean up: `docker stop test-redis && docker rm test-redis`

## Validation Scenarios

### Always Test After Making Changes:
1. **Import Test**: `DB_URL=redis://localhost:6379/0 python -c "from mem_db_utils import MemDBConnector; print('Import successful')"`
2. **Basic Functionality Test** (requires Redis running):
   ```bash
   DB_URL=redis://localhost:6379/0 python -c "
   from mem_db_utils import MemDBConnector
   conn = MemDBConnector().connect(db=0)
   conn.ping()
   conn.set('test', 'value')
   assert conn.get('test') == 'value'
   conn.delete('test')
   print('Validation PASSED')
   "
   ```
3. **Run Full Test Suite**: `python -m pytest tests/ -v --cov=src --cov-report=term-missing`
4. **Linting**: `ruff check . && ruff format --check .`

### Manual Testing Requirements:
- ALWAYS test basic database connection and operations after code changes
- Test with different database types by changing DB_URL protocol
- Verify configuration loading works with various environment variable combinations
- Test error handling with invalid database URLs or unreachable servers

## Common Tasks

### Repository Structure:
```
mem-db-utils/
├── .github/workflows/     # CI/CD pipelines
├── src/mem_db_utils/     # Main package source
│   ├── __init__.py       # MemDBConnector class
│   ├── config.py         # Environment configuration
│   └── py.typed          # Type hints marker
├── tests/                # Test files
├── pyproject.toml        # Project configuration
└── README.md            # Documentation
```

### Key Files to Check After Changes:
- Always verify `src/mem_db_utils/__init__.py` after changing MemDBConnector logic
- Check `src/mem_db_utils/config.py` after modifying configuration handling
- Update tests in `tests/` when adding new functionality
- Run integration tests in `tests/test_integration.py` with real database

### Development Dependencies:
- **Testing**: pytest, pytest-cov, pytest-dotenv, coverage
- **Linting**: ruff (replaces black, flake8, isort)
- **Git hooks**: pre-commit
- **Type checking**: Built into package with py.typed marker

### Build and Package:
- `python -m build` -- builds distribution packages. NEVER CANCEL: May fail due to network timeouts depending on the configured build backend and network environment (see `pyproject.toml` for the backend in use). Consider this command unreliable in constrained network environments.
- Package metadata in `pyproject.toml`
- Uses standard Python packaging; the build backend is specified in `pyproject.toml` (may require network access to a custom PyPI index depending on backend).
- **Note**: Package installation works fine, but building from source may be problematic due to external dependencies

## Database Types and Testing

### Supported Database Types:
- **Redis**: `redis://localhost:6379/0` (most common, full functionality)
- **Memcached**: `memcached://localhost:11211` (basic key-value operations)
- **Dragonfly**: `dragonfly://localhost:6380` (Redis-compatible)
- **Valkey**: `valkey://localhost:6381` (Redis-compatible)

### Database-Specific Testing:
- **Redis/Dragonfly/Valkey**: Support database selection (`db` parameter), ping, set/get/delete
- **Memcached**: Basic connection only, no database selection
- **Redis Sentinel**: Requires `REDIS_CONNECTION_TYPE=sentinel` and `REDIS_MASTER_SERVICE` environment variables

### Setting up Test Databases with Docker:
- Redis: `docker run -d --name test-redis -p 6379:6379 redis:7-alpine`
- Memcached: `docker run -d --name test-memcached -p 11211:11211 memcached:1.6-alpine`
- Dragonfly: `docker run -d --name test-dragonfly -p 6380:6380 docker.dragonflydb.io/dragonflydb/dragonfly`

## CI/CD Pipeline (.github/workflows)

### Linter Pipeline (linter.yaml):
- Runs on pull requests
- Uses `chartboost/ruff-action@v1` for linting and format checking
- ALWAYS run `ruff check .` and `ruff format --check .` before committing

### Package Publishing (publish_package.yaml):
- Triggers on git tags
- Builds with `python -m build`
- Publishes to PyPI
- Creates GitHub releases with sigstore signatures

## Critical Notes

### Environment Variable Loading:
- Package uses `pydantic-settings` with `python-dotenv` integration
- Environment variables are loaded from `.env` files automatically
- Configuration is validated at import time, not lazily
- Missing `DB_URL` will cause import failure with ValidationError

### Error Handling:
- Import failures occur when `DB_URL` is missing or invalid protocol
- Connection failures in integration tests are skipped (pytest.skip)
- Invalid database numbers may or may not raise exceptions depending on database type

### Memory and Performance:
- MemDBConnector uses `__slots__` for memory efficiency
- Connection objects are created per call to `connect()`
- No connection pooling implemented in base connector
- Timeouts configurable via `DB_TIMEOUT` environment variable (default: 30 seconds)

## Troubleshooting

### Common Issues:
1. **Import Error**: Ensure `DB_URL` environment variable is set
2. **Test Failures**: Start appropriate database container first
3. **Linting Failures**: Run `ruff format .` to auto-fix formatting issues
4. **Missing Dependencies**: Run `pip install -e .` to reinstall package
5. **Network Timeouts**: Package uses custom PyPI index (pypi.prismatica.in) which may be unreachable. pip install and python -m build commands may timeout.

### Network Dependencies:
- Package depends on custom PyPI index at pypi.prismatica.in
- Build commands may fail with network timeouts in restricted environments
- Runtime functionality works fine once dependencies are installed
- Consider using pre-installed environments or alternative package sources if network issues persist

### Database Connection Issues:
- Check if database container is running: `docker ps`
- Test connection manually: `docker exec -it test-redis redis-cli ping`
- Verify port availability: `netstat -tlnp | grep 6379`
- Check firewall settings if running on remote host
