#include <stdio.h>
#include <string.h>

struct Account {
    int id;
    char name[50];
    double balance;
};

void deposit(struct Account *acc, double amount) {
    if (amount > 0) {
        acc->balance += amount;
    }
}

int withdraw(struct Account *acc, double amount) {
    if (amount > acc->balance) {
        printf("Insufficient funds!\n");
        return 0;
    } else {
        acc->balance -= amount;
        return 1;
    }
}

void printAccount(struct Account acc) {
    printf("Account ID: %d, Name: %s, Balance: %.2f\n", acc.id, acc.name, acc.balance);
}

int main() {
    struct Account acc1 = {1, "Alice", 5000};
    deposit(&acc1, 1200);
    withdraw(&acc1, 3000);
    withdraw(&acc1, 4000); // edge case
    printAccount(acc1);
    return 0;
}
