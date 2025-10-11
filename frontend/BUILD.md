# Frontend Build Instructions

## Version Management

The frontend automatically displays the application version in the header. The version is sourced dynamically based on the environment:

### Local Development
Version is automatically read from the latest git tag:
```bash
npm run dev
```
The version will be extracted from `git describe --tags --abbrev=0` (e.g., `v0.3.0` → `0.3.0`)

### Docker Build

#### Using Git Tags (Recommended)
When building locally, the version can be passed as a build argument:
```bash
# Get the current git tag
VERSION=$(git describe --tags --abbrev=0 | sed 's/^v//')

# Build with version
docker build \
  --target production \
  --build-arg APP_VERSION=${VERSION} \
  -t poe2-pathofcrafting-frontend:${VERSION} \
  -t poe2-pathofcrafting-frontend:latest \
  .
```

#### Manual Version
Or specify the version manually:
```bash
docker build \
  --target production \
  --build-arg APP_VERSION=0.3.1 \
  -t poe2-pathofcrafting-frontend:0.3.1 \
  .
```

### GitHub Actions (Automatic)
When you push a new tag, the GitHub Actions workflow automatically:
1. Extracts the version from the tag (e.g., `v0.3.1` → `0.3.1`)
2. Passes it to the Docker build as `APP_VERSION`
3. Tags the image with:
   - `latest` (for main branch)
   - `0.3.1` (semver version)
   - `0.3` (semver major.minor)
   - `sha-<commit>` (git commit hash)

### Fly.io Deployment
The deployed application will use the version from the Docker image it was built with.

## Creating a New Release

1. Update any necessary files
2. Commit your changes
3. Create and push a new tag:
   ```bash
   git tag v0.3.1
   git push origin v0.3.1
   ```
4. GitHub Actions will automatically build and push the tagged image
5. Deploy to Fly.io:
   ```bash
   fly deploy --image ghcr.io/frankthetank001/poe2-pathofcrafting-frontend:0.3.1
   # or
   fly deploy  # uses latest
   ```

## Version Display
The version appears in the page header as: **POE2 - Path of Crafting (beta) v0.3.0**
