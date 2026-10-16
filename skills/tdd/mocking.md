# When to Mock

Read [SKILL.md](SKILL.md) and the repository testing contract first. Mock only approved **process boundaries**, such as external payment/email APIs or an out-of-process service where the suite permits a substitute.

Prefer the established real/emulated database and endpoint path. Where required by repository rules, restrict mocks to process boundaries and use approved DAO/database assertions only after exercising the real/emulated endpoint. A database dependency is not automatic permission to mock a DAO.

Use the repository's approved controls for time/randomness or filesystem behavior rather than inventing broad mocks.

Don't mock:

- Your owned in-process classes/modules
- Internal collaborators, DAOs or repositories in a required real/emulated path
- The behavior under test merely to echo a preselected return value

## Designing for Mockability

At genuine process boundaries, reuse established interfaces; don't introduce new injection layers or SDK abstractions solely for tests. When a real design need exists, these shapes can make a boundary easier to exercise:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

When designing a genuinely needed external client, specific operations may be clearer than a generic fetcher. Preserve an existing client contract rather than adding a parallel SDK for test convenience:

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint
