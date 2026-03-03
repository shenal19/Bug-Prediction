export type User = {
  id: string;
  name: string;
  email?: string;
};

export function isValidEmail(email: string): boolean {
  const re = /^[\w.-]+@[\w.-]+\.[A-Za-z]{2,}$/;
  return re.test(email);
}

export function getDisplayName(user: User): string {
  if (user.name && user.name.length > 0) {
    return user.name;
  }
  if (user.email && isValidEmail(user.email)) {
    return user.email.split("@")[0];
  }
  return "Anonymous";
}

export function riskyFunction(values: number[]): number {
  let total = 0;
  for (let i = 0; i < values.length; i++) {
    if (values[i] && (values[i] > 100 || values[i] < -100)) {
      total += values[i] * 2;
    } else if (values[i]) {
      total += values[i];
    }
  }
  return total / (values.length || 1);
}
