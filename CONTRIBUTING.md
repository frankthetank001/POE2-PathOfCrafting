# Contributing to PoE2 TradeCraft

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/Poe2-AI-TradeCraft.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment (see README.md)

## Development Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pytest  # Run tests
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Run `ruff check .` before committing
- Run `mypy .` for type checking
- Write docstrings for public functions

### TypeScript
- Use TypeScript strictly (no `any` unless necessary)
- Follow React best practices
- Run `npm run lint` before committing
- Use functional components with hooks

## Testing

### Backend Tests
```bash
cd backend
pytest
```

All new features should include tests. Tests are located in `backend/tests/`.

### Test Coverage
- Crafting mechanics should have 100% test coverage
- Edge cases should be tested
- Integration tests for API endpoints

## Pull Request Process

1. **Update documentation** - Update README.md if you're adding features
2. **Write tests** - All new functionality must have tests
3. **Run tests** - Ensure all tests pass
4. **Update CHANGELOG** - Add your changes to docs/CHANGELOG.md
5. **Commit messages** - Use clear, descriptive commit messages
6. **Submit PR** - Provide a clear description of your changes

### Commit Message Format
```
type(scope): brief description

Longer description if needed

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(crafting): add support for Exalted Orb`
- `fix(parser): handle items without quality`
- `docs(readme): update installation instructions`

## Areas for Contribution

### High Priority
- **More currency support** - Implement additional crafting currencies
- **Bug fixes** - Report and fix bugs
- **Test coverage** - Add tests for uncovered code
- **Documentation** - Improve docs and add examples

### Medium Priority
- **UI/UX improvements** - Make the interface more intuitive
- **Performance** - Optimize slow operations
- **Mobile support** - Make the UI mobile-friendly

### Future Features
- Build import/export
- Probability calculations
- Crafting guides
- Currency cost estimation

## Reporting Bugs

Use GitHub Issues and include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Your environment (OS, Python/Node version)

## Adding New Crafting Mechanics

When adding new currencies, essences, or mechanics:

1. **Update source data** - Add to `backend/source_data/`
   - `currency_configs.json` for currencies
   - `essence_item_effects.json` for essences
   - `bone_configs.json` for desecration bones

2. **Implement mechanic** - Add to `backend/app/services/crafting/mechanics.py`
   - Inherit from `CraftingMechanic`
   - Implement `can_apply()` and `apply()` methods
   - Add to `MECHANIC_REGISTRY`

3. **Write tests** - Add to `backend/tests/`
   - Test `can_apply()` validation
   - Test `apply()` results
   - Test edge cases

4. **Update frontend** - If needed
   - Add currency descriptions to `frontend/src/data/currency-descriptions.ts`
   - Update UI components if special handling is needed

## Adding New Modifiers

Modifiers are in `backend/source_data/modifiers.json`:

```json
{
  "name": "Modifier Name",
  "mod_type": "prefix",
  "tier": 1,
  "stat_text": "+{} to Example Stat",
  "stat_ranges": [{"min": 10.0, "max": 20.0}],
  "stat_min": 10.0,
  "stat_max": 20.0,
  "required_ilvl": 1,
  "weight": 100,
  "mod_group": "example",
  "applicable_items": ["amulet", "ring"],
  "tags": ["example_tag"]
}
```

After updating modifiers:
```bash
cd backend
python scripts/populate_complete_crafting_data.py
```

## Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be recognized in the changelog

## Questions?

- Open an issue for questions about implementation
- Check existing issues and PRs first
- Join discussions on GitHub

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
