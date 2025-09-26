import random

def generate_matrix(n, m):
    return [[random.randint(1, 100) for _ in range(m)] for _ in range(n)]

def multiply_matrices(A, B):
    n, m, p = len(A), len(B), len(B[0])
    result = [[0 for _ in range(p)] for _ in range(n)]
    for i in range(n):
        for j in range(p):
            for k in range(m):
                result[i][j] += A[i][k] * B[k][j]
    return result

def determinant(matrix):
    if len(matrix) == 1:
        return matrix[0][0]
    if len(matrix) == 2:
        return matrix[0][0]*matrix[1][1] - matrix[0][1]*matrix[1][0]
    det = 0
    for c in range(len(matrix)):
        minor = [row[:c] + row[c+1:] for row in matrix[1:]]
        det += ((-1)**c) * matrix[0][c] * determinant(minor)
    return det

def main():
    A = generate_matrix(3, 3)
    B = generate_matrix(3, 3)
    print("Matrix A:", A)
    print("Matrix B:", B)
    print("A x B:", multiply_matrices(A, B))
    print("det(A):", determinant(A))

if __name__ == "__main__":
    main()
