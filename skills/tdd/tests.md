# Good and Bad Tests

Apply [SKILL.md](SKILL.md) and the repository testing contract first. Extend its existing suite. Keep tests for meaningful behavior, invariants, guards and transformations; avoid plumbing/copy/type tests and mock echoes.

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Characteristics:

- Tests behavior users/callers care about
- Exercises real behavior through the established interface, with repository-approved persistence assertions when appropriate
- Survives internal refactors
- Describes WHAT, not HOW
- One behavior per test; multiple assertions may establish that behavior's full invariant

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Replaces the required real/emulated path with an internal mock

Persistence verification is not automatically an implementation detail. Follow the repository contract. Where that contract requires it, call the real/emulated endpoint, then use approved DAO/database reads to assert the stored outcome. Do not bypass that endpoint or mock its in-process collaborators.

```typescript
// Valid shape where the repository permits DAO assertions after a real endpoint:
test("creating a user persists the requested name", async () => {
  const response = await emulatedApi.createUser({ name: "Alice" });
  expect(response.status).toBe(201);
  const stored = await userDao.get(response.body.id);
  expect(stored.name).toBe("Alice");
});

// Also useful when retrieval through the public API is the established seam:
test("created user is retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**Tautological tests**: Expected value restates the implementation, so the test passes by construction.

```typescript
// BAD: Expected value is recomputed the way the code computes it
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// GOOD: Expected value is an independent, known literal
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```
