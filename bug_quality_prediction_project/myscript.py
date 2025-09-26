def factorial(n):
    """Compute factorial with recursion (not the most efficient)."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def find_max(nums):
    """Find maximum in a list manually."""
    if not nums:
        return None
    max_val = nums[0]
    for num in nums:
        if num > max_val:
            max_val = num
    return max_val

def bubble_sort(arr):
    """Classic bubble sort implementation."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def main():
    numbers = [5, 2, 9, 1, 5, 6]
    print("Factorial of 5:", factorial(5))
    print("Max number:", find_max(numbers))
    print("Sorted numbers:", bubble_sort(numbers))

if __name__ == "__main__":
    main()
